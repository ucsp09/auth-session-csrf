# Auth Session CSRF — FastAPI Backend

This backend demonstrates cookie-based session authentication with CSRF protection using FastAPI. It exposes login, login status, logout, and a protected resources API that requires both a valid session cookie and a matching CSRF token header.

## Features

- Session cookie (`session_id`) with 60s expiry, `HttpOnly`, `SameSite=Lax`.
- Server-side session store in a local JSON file (`sessions.json`).
- CSRF protection via `X-CSRF-TOKEN` header matched against the session’s CSRF token.
- Basic in-memory user check for demo (`admin` / `P@ssword9`).
- CORS enabled for `http://localhost:3000` with credentials allowed.

## Requirements

- Python 3.9+
- Packages: `fastapi`, `uvicorn`, `aiofile`, `pydantic`

Install dependencies:

```bash
pip install fastapi uvicorn aiofile pydantic
```

## Run

From this directory:

```bash
uvicorn main:app --reload --host 0.0.0.0 --port 8000
```

On startup the server creates or reuses `sessions.json` in the same directory.

## API Overview

Base URL: `http://localhost:8000`

### POST /api/v1/login

Authenticates the user, creates a session, sets `session_id` cookie, and returns a CSRF token.

Request body:

```json
{
	"username": "admin",
	"password": "P@ssword9"
}
```

Response (200):

```json
{
	"message": "Logged in user: admin successfully",
	"sessionId": "<uuid>",
	"csrfToken": "<uuid>"
}
```

Notes:

- Cookie: `session_id` (HttpOnly, SameSite=Lax, `max_age=60`).
- Session expiry: 60 seconds (server-side check).

### GET /api/v1/login/status

Returns whether the current `session_id` cookie is valid and, if so, the CSRF token.

Response (200):

```json
{
	"isLoggedIn": true,
	"sessionId": "<uuid>",
	"csrfToken": "<uuid>"
}
```

### GET /api/v1/logout

Deletes the session server-side and clears the `session_id` cookie.

Response (200):

```json
{
	"message": "Logged out session_id:<uuid> for user: admin successfully"
}
```

### GET /api/v1/protected/resources

Protected endpoint that requires:

1) A valid `session_id` cookie, and
2) A header `X-CSRF-TOKEN` equal to the CSRF token from login.

Response (200):

```json
{
	"items": [
		{"name": "resource1", "properties": {"k1": "v1", "k2": "v2"}},
		{"name": "resource2", "properties": {"k1": 1, "k2": 2}}
	],
	"total": 2
}
```

## cURL Examples

Save and reuse cookies with a cookie jar file (`cookies.txt`).

1) Login and capture cookies:

```bash
curl -i \
	-X POST http://localhost:8000/api/v1/login \
	-H "Content-Type: application/json" \
	-d '{"username":"admin","password":"P@ssword9"}' \
	-c cookies.txt
```

Copy the `csrfToken` value from the JSON response for the next step.

2) Check login status:

```bash
curl -i \
	http://localhost:8000/api/v1/login/status \
	-b cookies.txt
```

3) Call protected endpoint (replace `<csrf>`):

```bash
curl -i \
	http://localhost:8000/api/v1/protected/resources \
	-H "X-CSRF-TOKEN: <csrf>" \
	-b cookies.txt
```

4) Logout:

```bash
curl -i \
	http://localhost:8000/api/v1/logout \
	-b cookies.txt
```

## How CSRF Protection Works Here

- On login, the server issues a random CSRF token and stores it with the session.
- The browser receives `session_id` as an `HttpOnly` cookie and the CSRF token in the JSON body.
- For state-changing or protected requests, the client must send `X-CSRF-TOKEN` that matches the one stored server-side for the current session.
- If the token is missing or mismatched, the request is rejected with 401.

## CORS and Frontend Integration

- CORS allows origin `http://localhost:3000` and credentials.
- When calling from a browser, enable `credentials: true` and ensure the frontend origin matches the allowed origin.

## Session Storage

- Sessions are stored in `sessions.json` with fields: `username`, `csrfToken`, `expires_at` (monotonic clock timestamp).
- Expiration is enforced on read. Expired sessions are removed.

## Troubleshooting

- 401 on protected calls: ensure you send both the `session_id` cookie and the correct `X-CSRF-TOKEN` value, and that the session hasn't expired (60s).
- 401 on status/logout: your `session_id` cookie may be missing, invalid, or expired.
- CORS errors in browser: confirm origin is `http://localhost:3000` and requests include credentials.

## Notes

- Credentials are hardcoded for demo only (`admin`/`P@ssword9`). Do not use in production.
- For production: use a database for sessions, HTTPS, robust user auth, secure cookie flags, and rotate CSRF tokens as appropriate.

