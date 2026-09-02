"""
WSGI / ASGI Universal Entry Point for Production Servers (Render, Gunicorn, Uvicorn)
Supports ALL Python web interfaces:
- ASGI 3: application(scope, receive, send)
- ASGI 2: application(scope)(receive, send)
- WSGI:   application(environ, start_response)
"""
import os
import sys

# Ensure root workspace directory is in sys.path
ROOT_DIR = os.path.dirname(os.path.abspath(__file__))
if ROOT_DIR not in sys.path:
    sys.path.insert(0, ROOT_DIR)

from backend.main import app as asgi_app


class UniversalApp:
    """
    Adapter that detects whether the caller is:
    1. ASGI 3: (scope, receive, send)
    2. ASGI 2: (scope)
    3. WSGI:   (environ, start_response)
    """
    def __init__(self, target_asgi_app):
        self.asgi_app = target_asgi_app
        self._wsgi_adapter = None

    def _get_wsgi_adapter(self):
        if self._wsgi_adapter is None:
            try:
                from a2wsgi import ASGIMiddleware
                self._wsgi_adapter = ASGIMiddleware(self.asgi_app)
            except Exception:
                from starlette.testclient import TestClient
                client = TestClient(self.asgi_app, raise_server_exceptions=False)

                def fallback_adapter(environ, start_response):
                    path = environ.get("PATH_INFO", "/")
                    query = environ.get("QUERY_STRING", "")
                    if query:
                        path = f"{path}?{query}"
                    method = environ.get("REQUEST_METHOD", "GET")
                    headers = {}
                    for k, v in environ.items():
                        if k.startswith("HTTP_"):
                            h_name = k[5:].replace("_", "-").title()
                            headers[h_name] = str(v)
                    body = environ.get("wsgi.input")
                    content = body.read() if body else None

                    resp = client.request(method, path, headers=headers, content=content)
                    status_line = f"{resp.status_code} OK"
                    resp_headers = [(k, v) for k, v in resp.headers.items()]
                    start_response(status_line, resp_headers)
                    return [resp.content]

                self._wsgi_adapter = fallback_adapter
        return self._wsgi_adapter

    def __call__(self, *args, **kwargs):
        # Case 1: WSGI signature (environ, start_response)
        if len(args) == 2 and callable(args[1]):
            adapter = self._get_wsgi_adapter()
            return adapter(args[0], args[1])

        # Case 2: ASGI 2 signature (scope)
        if len(args) == 1:
            scope = args[0]
            async def asgi_instance(receive, send):
                return await self.asgi_app(scope, receive, send)
            return asgi_instance

        # Case 3: ASGI 3 signature (scope, receive, send)
        return self.asgi_app(*args, **kwargs)

    def __getattr__(self, name):
        return getattr(self.asgi_app, name)


app = UniversalApp(asgi_app)
application = app

if __name__ == "__main__":
    import uvicorn
    port = int(os.environ.get("PORT", 8000))
    uvicorn.run("backend.main:app", host="0.0.0.0", port=port)
