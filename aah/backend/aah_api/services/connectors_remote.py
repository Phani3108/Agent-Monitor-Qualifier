from __future__ import annotations
from typing import List, Dict, Any
import hashlib
import html
import logging
import os
import re

import yaml
from pathlib import Path

logger = logging.getLogger(__name__)

REPO_ROOT = Path(__file__).resolve().parents[2]
_CONNECTORS_YML = REPO_ROOT / "connectors.yml"


def _load_allowlist() -> List[str]:
    if not _CONNECTORS_YML.exists():
        return []
    data = yaml.safe_load(_CONNECTORS_YML.read_text(encoding="utf-8")) or {}
    return [str(d).lower().strip() for d in (data.get("allowlist") or [])]


def allowed_domain(domain: str) -> bool:
    allow = _load_allowlist()
    if not allow:
        return False
    return domain.lower().strip() in allow


def _passage(source_id: str, text: str, title: str = "", file: str = "", chunk: int = 0) -> Dict[str, Any]:
    return {
        "source_id": source_id,
        "title": title,
        "text": text,
        "file": file,
        "chunk": chunk,
        "sha256": hashlib.sha256(text.encode("utf-8")).hexdigest()[:16],
    }


# ── GitHub (REST API v3) ────────────────────────────────────────────────

def fetch_github(repo: str, dir: str = "", branch: str = "main") -> List[Dict[str, Any]]:
    """Fetch markdown files from a GitHub repo directory via the REST API.

    Requires GITHUB_TOKEN env var.  The repo domain (api.github.com) must be
    in connectors.yml allowlist.
    """
    token = os.getenv("GITHUB_TOKEN", "").strip()
    if not token:
        logger.warning("fetch_github: GITHUB_TOKEN not set, skipping")
        return []
    if not allowed_domain("api.github.com"):
        logger.warning("fetch_github: api.github.com not in connectors allowlist")
        return []

    import urllib.request
    import json

    headers = {
        "Authorization": f"Bearer {token}",
        "Accept": "application/vnd.github.v3+json",
        "User-Agent": "aah-connector/1.0",
    }
    api_url = f"https://api.github.com/repos/{repo}/contents/{dir}?ref={branch}"
    req = urllib.request.Request(api_url, headers=headers)
    try:
        with urllib.request.urlopen(req, timeout=30) as resp:
            items = json.loads(resp.read())
    except Exception as exc:
        logger.error("fetch_github: failed listing %s — %s", api_url, exc)
        return []

    passages: List[Dict[str, Any]] = []
    for item in items:
        if item.get("type") != "file" or not item["name"].endswith(".md"):
            continue
        dl_url = item.get("download_url", "")
        if not dl_url:
            continue
        try:
            dl_req = urllib.request.Request(dl_url, headers=headers)
            with urllib.request.urlopen(dl_req, timeout=30) as f:
                content = f.read().decode("utf-8", errors="replace")
            for i, chunk in enumerate(_split_md(content)):
                passages.append(_passage(
                    source_id=f"github:{repo}/{dir}",
                    text=chunk,
                    title=item["name"],
                    file=item["path"],
                    chunk=i,
                ))
        except Exception as exc:
            logger.error("fetch_github: failed downloading %s — %s", dl_url, exc)
    return passages


# ── Confluence (REST API v2) ─────────────────────────────────────────────

def fetch_confluence(space: str, base_url: str, user_env: str = "CONFLUENCE_USER",
                     token_env: str = "CONFLUENCE_TOKEN") -> List[Dict[str, Any]]:
    """Fetch all pages from a Confluence space."""
    user = os.getenv(user_env, "").strip()
    token = os.getenv(token_env, "").strip()
    if not user or not token:
        logger.warning("fetch_confluence: credentials not set (%s / %s)", user_env, token_env)
        return []

    domain = base_url.rstrip("/").split("/")[2] if "//" in base_url else base_url
    if not allowed_domain(domain):
        logger.warning("fetch_confluence: %s not in connectors allowlist", domain)
        return []

    import urllib.request
    import json
    import base64

    auth = base64.b64encode(f"{user}:{token}".encode()).decode()
    headers = {"Authorization": f"Basic {auth}", "Accept": "application/json"}

    passages: List[Dict[str, Any]] = []
    url = f"{base_url.rstrip('/')}/wiki/api/v2/spaces/{space}/pages?limit=50&body-format=storage"

    while url:
        req = urllib.request.Request(url, headers=headers)
        try:
            with urllib.request.urlopen(req, timeout=30) as resp:
                data = json.loads(resp.read())
        except Exception as exc:
            logger.error("fetch_confluence: %s — %s", url, exc)
            break

        for page in data.get("results", []):
            body_html = page.get("body", {}).get("storage", {}).get("value", "")
            text = _strip_html(body_html)
            if not text.strip():
                continue
            for i, chunk in enumerate(_split_md(text)):
                passages.append(_passage(
                    source_id=f"confluence:{space}",
                    text=chunk,
                    title=page.get("title", ""),
                    file=f"page/{page.get('id', '')}",
                    chunk=i,
                ))
        url = data.get("_links", {}).get("next", "")
        if url and not url.startswith("http"):
            url = f"{base_url.rstrip('/')}{url}"

    return passages


# ── SharePoint (Microsoft Graph API) ────────────────────────────────────

def fetch_sharepoint(site: str, doclib: str = "Documents") -> List[Dict[str, Any]]:
    """Fetch documents from a SharePoint site via Microsoft Graph.

    Requires SHAREPOINT_ACCESS_TOKEN env var (OAuth2 bearer token).
    """
    token = os.getenv("SHAREPOINT_ACCESS_TOKEN", "").strip()
    if not token:
        logger.warning("fetch_sharepoint: SHAREPOINT_ACCESS_TOKEN not set")
        return []
    if not allowed_domain("graph.microsoft.com"):
        logger.warning("fetch_sharepoint: graph.microsoft.com not in connectors allowlist")
        return []

    import urllib.request
    import json

    headers = {"Authorization": f"Bearer {token}", "Accept": "application/json"}
    api_url = f"https://graph.microsoft.com/v1.0/sites/{site}/drive/root:/{doclib}:/children"
    req = urllib.request.Request(api_url, headers=headers)

    passages: List[Dict[str, Any]] = []
    try:
        with urllib.request.urlopen(req, timeout=30) as resp:
            data = json.loads(resp.read())
    except Exception as exc:
        logger.error("fetch_sharepoint: %s — %s", api_url, exc)
        return []

    for item in data.get("value", []):
        name = item.get("name", "")
        if not name.endswith((".md", ".txt")):
            continue
        dl_url = item.get("@microsoft.graph.downloadUrl", "")
        if not dl_url:
            continue
        try:
            dl_req = urllib.request.Request(dl_url, headers=headers)
            with urllib.request.urlopen(dl_req, timeout=30) as f:
                content = f.read().decode("utf-8", errors="replace")
            for i, chunk in enumerate(_split_md(content)):
                passages.append(_passage(
                    source_id=f"sharepoint:{site}/{doclib}",
                    text=chunk,
                    title=name,
                    file=name,
                    chunk=i,
                ))
        except Exception as exc:
            logger.error("fetch_sharepoint: download failed %s — %s", name, exc)

    return passages


# ── Azure AI Search ─────────────────────────────────────────────────────

def fetch_azure_ai_search(endpoint_env: str = "AZURE_SEARCH_ENDPOINT",
                          key_env: str = "AZURE_SEARCH_KEY",
                          index: str = "default",
                          query: str = "*") -> List[Dict[str, Any]]:
    """Query Azure AI Search (formerly Cognitive Search) and return passages."""
    endpoint = os.getenv(endpoint_env, "").strip().rstrip("/")
    key = os.getenv(key_env, "").strip()
    if not endpoint or not key:
        logger.warning("fetch_azure_ai_search: credentials not set (%s / %s)", endpoint_env, key_env)
        return []

    domain = endpoint.split("/")[2] if "//" in endpoint else endpoint
    if not allowed_domain(domain):
        logger.warning("fetch_azure_ai_search: %s not in connectors allowlist", domain)
        return []

    import urllib.request
    import json

    api_url = f"{endpoint}/indexes/{index}/docs/search?api-version=2024-07-01"
    body = json.dumps({"search": query, "top": 50, "queryType": "semantic"}).encode()
    headers = {
        "Content-Type": "application/json",
        "api-key": key,
    }
    req = urllib.request.Request(api_url, data=body, headers=headers, method="POST")

    passages: List[Dict[str, Any]] = []
    try:
        with urllib.request.urlopen(req, timeout=30) as resp:
            data = json.loads(resp.read())
    except Exception as exc:
        logger.error("fetch_azure_ai_search: %s — %s", api_url, exc)
        return []

    for doc in data.get("value", []):
        content = doc.get("content", "") or doc.get("merged_content", "") or ""
        title = doc.get("title", "") or doc.get("metadata_storage_name", "")
        if not content.strip():
            continue
        for i, chunk in enumerate(_split_md(content)):
            passages.append(_passage(
                source_id=f"azure_search:{index}",
                text=chunk,
                title=title,
                file=doc.get("metadata_storage_path", ""),
                chunk=i,
            ))

    return passages


# ── Helpers ──────────────────────────────────────────────────────────────

_HTML_TAG = re.compile(r"<[^>]+>")


def _strip_html(raw: str) -> str:
    text = _HTML_TAG.sub(" ", raw)
    return html.unescape(text)


def _split_md(text: str, max_chars: int = 800) -> List[str]:
    """Split text into chunks on paragraph boundaries."""
    paragraphs = re.split(r"\n{2,}", text.strip())
    chunks: List[str] = []
    buf = ""
    for p in paragraphs:
        p = p.strip()
        if not p:
            continue
        if len(buf) + len(p) > max_chars and buf:
            chunks.append(buf.strip())
            buf = ""
        buf += p + "\n\n"
    if buf.strip():
        chunks.append(buf.strip())
    return chunks or [text[:max_chars]] if text.strip() else []
