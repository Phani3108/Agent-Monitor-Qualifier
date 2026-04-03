#!/usr/bin/env python3
import sys, os, yaml

CONNECTORS = 'connectors.yml'
with open(CONNECTORS) as f:
    allowlist = yaml.safe_load(f).get('allowlist', [])

fail = False
for root, dirs, files in os.walk('aah/backend/aah_api'):
    for f in files:
        if f.endswith('.py'):
            path = os.path.join(root, f)
            with open(path) as fp:
                for i, line in enumerate(fp):
                    if 'http' in line or 'requests' in line or 'httpx' in line:
                        if not any(domain in line for domain in allowlist):
                            print(f"External call in {path}:{i+1} not in allowlist")
                            fail = True
if fail:
    sys.exit(1)
