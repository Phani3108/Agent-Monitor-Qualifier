#!/usr/bin/env python3
import sys, os, yaml, jsonschema

SCHEMA = 'specs/schemas/test_spec.schema.json'

for root, dirs, files in os.walk('specs/examples'):
    for f in files:
        if f.endswith('.yaml') or f.endswith('.yml'):
            path = os.path.join(root, f)
            with open(path) as fp:
                data = yaml.safe_load(fp)
            with open(SCHEMA) as sf:
                schema = yaml.safe_load(sf)
            try:
                jsonschema.validate(instance=data, schema=schema)
            except jsonschema.ValidationError as e:
                print(f"Spec {path} failed validation: {e.message}")
                sys.exit(1)
