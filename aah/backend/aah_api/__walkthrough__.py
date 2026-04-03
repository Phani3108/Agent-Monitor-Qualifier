from __future__ import annotations
import sys
from pathlib import Path

def main():
    root = Path(__file__).resolve().parents[2]
    script = root / "tools" / "docs" / "build_master_walkthrough.py"
    if not script.exists():
        print("Walkthrough builder not found at tools/docs/build_master_walkthrough.py", file=sys.stderr)
        sys.exit(1)
    code = compile(script.read_text(encoding="utf-8"), str(script), "exec")
    g = {"__name__":"__main__"}
    exec(code, g)

if __name__ == "__main__":
    main()
