import argparse
from pathlib import Path
from aah_api.services.sign import verify_manifest
from aah_api.services.orchestrator import RUNS_DIR

def main():
    parser = argparse.ArgumentParser(description="Promote a run to production if artifact verification passes.")
    parser.add_argument("run_id", help="Run ID to promote")
    parser.add_argument("--require-hmac", action="store_true", help="Require HMAC verification")
    args = parser.parse_args()

    run_dir = RUNS_DIR / args.run_id
    result = verify_manifest(run_dir, require_hmac=args.require_hmac)
    if not result["ok"]:
        print(f"Verification failed for run {args.run_id}:")
        for item in result["items"]:
            print(f"  {item['file']}: sha_ok={item['sha_ok']} hmac_ok={item.get('hmac_ok')}")
        exit(1)
    # Mark as promoted (touch a file or update a manifest)
    promoted_flag = run_dir / "PROMOTED"
    promoted_flag.write_text("promoted\n")
    print(f"Run {args.run_id} promoted to production.")

if __name__ == "__main__":
    main()
