# Auth Session CSRF — Frontend (FastAPI)

This service serves simple HTML pages and static assets, and proxies the protected resources request to the backend. It’s designed to demonstrate cookie-based sessions and CSRF protection end-to-end.

## Requirements

- Python 3.9+
- Dependencies: `fastapi`, `uvicorn`, `aiofile`, `aiohttp`

Install dependencies:

```bash
pip install fastapi uvicorn aiofile aiohttp
```

## Run

From this directory:

```bash
uvicorn main:app --reload --host 0.0.0.0 --port 3000
```

Open the UI pages in your browser:
- Home: http://localhost:3000/ui/home
- Login: http://localhost:3000/ui/login
- Static files (example): http://localhost:3000/ui/static/app.js

## Routes

- GET `/ui/{page}`: Serves HTML pages from `ui/` (e.g., `home.html`, `login.html`).
- GET `/ui/static/{file_path}`: Serves static assets from `ui/static/`.
- GET `/ui/protected/resources`: Server-side proxy to the backend’s `GET /api/v1/protected/resources`.

## How It Works

- The backend (default) runs at `http://localhost:8000` and issues the session cookie `session_id` and a CSRF token on login.
- Cookies are host-based and not port-specific, so a cookie set on `localhost` at port 8000 is also sent to `localhost` at port 3000. The frontend proxy forwards incoming headers (including `Cookie` and `X-CSRF-TOKEN`) to the backend.
- To call a protected endpoint from the browser, send the request to the frontend proxy at `/ui/protected/resources` with header `X-CSRF-TOKEN` equal to the CSRF token you received at login. The browser will include the `session_id` cookie automatically.

## Expected Backend

- Backend base URL: `http://localhost:8000`
- Login: `POST /api/v1/login` returns `csrfToken` and sets `session_id` cookie.
- Status: `GET /api/v1/login/status`
- Logout: `GET /api/v1/logout`
- Protected: `GET /api/v1/protected/resources`

Refer to the backend README for full details.

## Usage Flow

1) Login via backend to obtain a session and CSRF token.
2) The browser stores `session_id` cookie (HttpOnly) and you hold the CSRF token (from JSON response).
3) For protected calls from the UI, hit the frontend proxy `/ui/protected/resources` and include header `X-CSRF-TOKEN: <csrf>`.
4) To end the session, call backend logout.

## cURL Examples

1) Login (directly to backend):

```bash
curl -i \
  -X POST http://localhost:8000/api/v1/login \
  -H "Content-Type: application/json" \
  -d '{"username":"admin","password":"P@ssword9"}' \
  -c cookies.txt
```

Copy the `csrfToken` from the response JSON.

2) Call protected via frontend proxy (replace `<csrf>`):

```bash
curl -i \
  http://localhost:3000/ui/protected/resources \
  -H "X-CSRF-TOKEN: <csrf>" \
  -b cookies.txt
```

3) Logout (directly to backend):

```bash
curl -i \
  http://localhost:8000/api/v1/logout \
  -b cookies.txt
```

## CORS Notes

- This frontend enables CORS for `http://localhost:3000` (itself). It primarily serves pages and proxies protected calls, avoiding browser CORS issues for those requests.
- If your UI makes direct XHR/fetch calls to the backend from the browser, ensure the backend allows your frontend origin.

## Troubleshooting

- 401 on protected proxy call: ensure `cookies.txt` is used and `X-CSRF-TOKEN` matches the token returned at login; also verify the session (60s expiry by default) hasn’t expired.
- 404 for pages: ensure the files exist under `ui/` (e.g., `home.html`, `login.html`).
- Mixed-origin issues: prefer the proxy route for protected calls. If calling the backend directly from the browser, align allowed origins.

## Notes

- This is a demo. For production, use HTTPS, strict cookie settings, robust auth, and consider a dedicated reverse proxy for header/cookie management.
