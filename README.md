# Auth Session CSRF — Project Overview

Session-based authentication demo using HttpOnly cookies and CSRF protection with FastAPI. The project includes:
- Backend API (port 8000)
- Frontend UI and proxy (port 3000)
- CSRF attacker demo site (port 4000)

This setup demonstrates how CSRF defenses block cross-site requests even when a browser automatically includes cookies.

## Scope & Intent

- Show cookie-based sessions with server-side storage and short expiry.
- Demonstrate CSRF protection via a per-session token sent in header `X-CSRF-TOKEN`.
- Provide a minimal frontend that proxies protected resource calls to the backend.
- Provide an attacker site that attempts to access protected resources without or with a fake CSRF token.

## Architecture

- Backend (FastAPI @ 8000): Auth, sessions (`sessions.json`), CSRF token validation.
- Frontend (FastAPI @ 3000): Serves pages and proxies `/ui/protected/resources` → backend.
- Attacker Frontend (FastAPI @ 4000): Malicious demo page issuing cross-site requests to the victim frontend proxy.

## Prerequisites

- Python 3.9+
- Separate terminal sessions for each service.

## Install Dependencies

- Backend (8000):
	```bash
	cd backend/python
	pip install fastapi uvicorn aiofile pydantic
	```

- Frontend (3000):
	```bash
	cd frontend/python
	pip install fastapi uvicorn aiofile aiohttp
	```

- CSRF Attacker Frontend (4000):
	```bash
	cd csrf_attacker_frontend/python
	pip install fastapi uvicorn aiofile
	```

## Run Services

Open three terminals (or tabs):

1) Backend (8000):
	 ```bash
	 cd backend/python
	 uvicorn main:app --reload --host 0.0.0.0 --port 8000
	 ```

2) Frontend (3000):
	 ```bash
	 cd frontend/python
	 uvicorn main:app --reload --host 0.0.0.0 --port 3000
	 ```

3) Attacker Frontend (4000):
	 ```bash
	 cd csrf_attacker_frontend/python
	 uvicorn main:app --reload --host 0.0.0.0 --port 4000
	 ```

## Quick Test (Browser)

1) Visit the victim app:
	 - Frontend pages: http://localhost:3000/ui/home and http://localhost:3000/ui/login
2) Log in with the demo credentials on the victim app:
	 - Username: `admin`
	 - Password: `P@ssword9`
	 - On success, the browser stores `session_id` (HttpOnly cookie) and the backend returns a `csrfToken` in the JSON response (frontend may surface it).
3) Access the protected resources through the victim frontend proxy:
	 - Call `http://localhost:3000/ui/protected/resources` with header `X-CSRF-TOKEN: <csrfToken>`.
	 - Expected: 200 with resource list.
4) Try the attacker site:
	 - Open http://localhost:4000/ui/home
	 - Click both buttons to attempt a request without a token and with a fake token.
	 - Expected: 401 responses (CSRF protection blocks these attempts).

## Quick Test (cURL)

Use a cookie jar to persist the `session_id`:

1) Login (backend):
```bash
curl -i \
	-X POST http://localhost:8000/api/v1/login \
	-H "Content-Type: application/json" \
	-d '{"username":"admin","password":"P@ssword9"}' \
	-c cookies.txt
```
Copy the `csrfToken` from the response.

2) Check login status:
```bash
curl -i \
	http://localhost:8000/api/v1/login/status \
	-b cookies.txt
```

3) Protected via frontend proxy (replace `<csrf>`):
```bash
curl -i \
	http://localhost:3000/ui/protected/resources \
	-H "X-CSRF-TOKEN: <csrf>" \
	-b cookies.txt
```

4) Logout:
```bash
curl -i \
	http://localhost:8000/api/v1/logout \
	-b cookies.txt
```

## Behavior Highlights

- Session cookie: `session_id`, `HttpOnly`, `SameSite=Lax`, ~60s expiry.
- Session store: `sessions.json` in backend directory; expired sessions are pruned on access.
- CSRF protection: server compares `X-CSRF-TOKEN` header with token saved in the session.
- CORS: backend allows origin `http://localhost:3000` with credentials.

## Known Limitations

- Demo credentials and logic only (`admin`/`P@ssword9`). No real user store.
- Session persistence via local JSON file; not suitable for production or multi-instance.
- Short session duration (60s) for demonstration.
- CSRF token returned in response JSON and not rotated per-request.
- Limited error handling, no rate limiting, no HTTPS in dev.
- CORS configured for a single origin; adjust as needed.

## Troubleshooting

- 401 on protected calls: ensure both `session_id` cookie and correct `X-CSRF-TOKEN` are sent; confirm session not expired.
- 401 on attacker tests: this is expected; indicates CSRF is working.
- CORS issues: verify backend allows `http://localhost:3000` and requests include credentials where needed.
- Missing `sessions.json`: backend creates it at startup; check permissions and working directory.

## Component READMEs

- Backend: [auth-session-csrf/backend/python/README.md](auth-session-csrf/backend/python/README.md)
- Frontend: [auth-session-csrf/frontend/python/README.md](auth-session-csrf/frontend/python/README.md)
- CSRF Attacker: [auth-session-csrf/csrf_attacker_frontend/python/README.md](auth-session-csrf/csrf_attacker_frontend/python/README.md)

