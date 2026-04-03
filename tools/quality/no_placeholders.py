#!/usr/bin/env python3
import sys, os, re

PROHIBITED = [r'TODO', r'FIXME', r'HACK', r'WIP', r'TBD', r'NotImplementedError', r'pass  # TODO']
ALLOWED_EMPTY_INIT = '# empty by design'

fail = False
for root, dirs, files in os.walk('.'):
    for f in files:
        if f.endswith('.py'):
            path = os.path.join(root, f)
            with open(path) as fp:
                lines = fp.readlines()
            for i, line in enumerate(lines):
                for p in PROHIBITED:
                    if re.search(p, line) and ALLOWED_EMPTY_INIT not in line:
                        print(f"Prohibited marker '{p}' in {path}:{i+1}")
                        fail = True
                if f == '__init__.py' and len(lines) == 1 and ALLOWED_EMPTY_INIT not in lines[0]:
                    print(f"Empty __init__.py in {path} must have comment: {ALLOWED_EMPTY_INIT}")
                    fail = True
if fail:
    sys.exit(1)
