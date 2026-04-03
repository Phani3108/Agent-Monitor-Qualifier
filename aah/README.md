# AAH README (MVP)

## Quickstart

```bash
git clone <repo-url>
cd aah
cp backend/.env.example backend/.env
docker compose up --build
```

- API: http://localhost:8080
- Postgres: localhost:5432 (user/pass: aah)

## Run a test pack

```bash
curl -X POST localhost:8080/runs \
  -H "Content-Type: application/json" \
  -d @- <<'JSON'
{ "spec_yaml": "$(cat specs/examples/refund_mvp.yaml | sed 's/\"/\\\"/g')" }
JSON
```

## Project Structure

See `Master_file.md` for full repo layout, quality bars, and CI/CD flow.

## Contributing

- All code must pass the quality gates and CI described in `Master_file.md` and `Truth_policy.md`.
- PRs modifying policy/docs require CODEOWNERS approval and `policy-change` label.

## License
TBD
