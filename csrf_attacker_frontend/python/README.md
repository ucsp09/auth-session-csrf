# CSRF Attacker Frontend (Demo)

This app serves a simple page that attempts CSRF attacks against the demo application. It runs on a separate origin to simulate a malicious site and tries to access protected resources without a valid CSRF token or with a fake token.

Important: For educational and testing purposes only.

## Requirements

- Python 3.9+
- Dependencies: `fastapi`, `uvicorn`, `aiofile`

Install dependencies:

```bash
pip install fastapi uvicorn aiofile
```

## Run (Port 4000)

From this directory:

```bash
uvicorn main:app --reload --host 0.0.0.0 --port 4000
```

Open the attacker UI:
- Home: http://localhost:4000/ui/home
- Static example: http://localhost:4000/ui/static/app.js

## What It Does

- Renders a page with two buttons:
  - "performCSRFAttackWithNoCSRFToken": Tries to call the victim app’s protected endpoint without any CSRF header.
  - "PerformCSRFAttackWithFakeCSRFToken": Sends a bogus header `X-CSRF-Token: fake-csrf-token-12345`.
- Both requests use `credentials: 'include'` so the browser will automatically send cookies for `localhost` if present.

## Target/Victim Setup

This attacker is meant to target the companion frontend running at port 3000, which proxies to the backend at port 8000.

- Victim frontend: http://localhost:3000 (route used by the attacker: `/ui/protected/resources`)
- Backend (API): http://localhost:8000

Make sure you have an active session on the victim app (login via the victim frontend or directly to the backend) so a `session_id` cookie exists for `localhost`.

## Demo Steps

1) Start the victim services
   - Frontend (port 3000) and Backend (port 8000). See their READMEs.
2) Login on the victim app to set `session_id` and obtain `csrfToken`.
3) Start the attacker app on port 4000:
   ```bash
   uvicorn main:app --reload --host 0.0.0.0 --port 4000
   ```
4) Visit http://localhost:4000/ui/home and click:
   - "performCSRFAttackWithNoCSRFToken" (no header)
   - "PerformCSRFAttackWithFakeCSRFToken" (`X-CSRF-Token: fake-csrf-token-12345`)

Expected result: Both requests should fail with 401 from the victim backend, demonstrating that CSRF protection is working.

## Routes (Attacker App)

- GET `/ui/{page}`: Serves HTML from `ui/` (e.g., `home.html`).
- GET `/ui/static/{file_path}`: Serves static assets from `ui/static/` (e.g., `app.js`).

## Notes & Safety

- The attacker app has permissive CORS (`*`) only to simplify the demo. It does not need credentials to load its own content.
- Do not deploy this setup publicly. It is a learning tool for CSRF defenses: `HttpOnly` session cookie and server-validated `X-CSRF-TOKEN` header.
