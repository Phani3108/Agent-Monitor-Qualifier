import argparse, sys
from pathlib import Path
from .main import sha256_of, TRUTH_POLICY_PATH, SPEC_SCHEMA_PATH

def main():
    p = argparse.ArgumentParser(prog="aah-cli")
    sub = p.add_subparsers(dest="cmd", required=True)
    sub.add_parser("print-policy-hash")
    sub.add_parser("print-schema-hash")
    args = p.parse_args()

    if args.cmd == "print-policy-hash":
        print(sha256_of(TRUTH_POLICY_PATH))
        return 0
    if args.cmd == "print-schema-hash":
        print(sha256_of(SPEC_SCHEMA_PATH))
        return 0
    return 1

if __name__ == "__main__":
    sys.exit(main())
