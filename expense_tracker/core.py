import threading
import webbrowser
from wsgiref.simple_server import make_server

from .server import application


class ExpenseTrackerApp:
    def __call__(self, environ, start_response):
        return application(environ, start_response)

    def run(self, host: str = "0.0.0.0", port: int = 8000) -> None:
        browser_url = f"http://localhost:{port}"
        print(f"Serving Living Expenses Tracker at http://{host}:{port}")
        print(f"Opening {browser_url}")
        threading.Timer(1.0, webbrowser.open, args=(browser_url,)).start()
        with make_server(host, port, self) as server:
            server.serve_forever()


app = ExpenseTrackerApp()


def run(host: str = "0.0.0.0", port: int = 8000) -> None:
    app.run(host=host, port=port)
