
import json
import time
import threading
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer
from urllib.parse import urlparse, parse_qs

STATE = {
    "messages": []
}


class LocalHandler(BaseHTTPRequestHandler):

    def send_cors_headers(self):
        self.send_header("Access-Control-Allow-Origin", "*")
        self.send_header("Access-Control-Allow-Methods", "GET, POST, OPTIONS")
        self.send_header("Access-Control-Allow-Headers", "Content-Type")

    def do_OPTIONS(self):
        self.send_response(204)
        self.send_cors_headers()
        self.end_headers()

    def do_GET(self):
        parsed = urlparse(self.path)

        if parsed.path == "/overlay":
            try:
                with open("overlay.html", "r", encoding="utf-8") as f:
                    content = f.read()

                self.send_response(200)
                self.send_header("Content-Type", "text/html; charset=utf-8")
                self.send_cors_headers()
                self.end_headers()
                self.wfile.write(content.encode("utf-8"))

            except FileNotFoundError:
                self.send_error(404, "overlay.html introuvable")

        elif parsed.path == "/messages":
            self.send_response(200)
            self.send_header("Content-Type", "application/json; charset=utf-8")
            self.send_cors_headers()
            self.end_headers()

            data = json.dumps(STATE["messages"], ensure_ascii=False)
            self.wfile.write(data.encode("utf-8"))

        else:
            self.send_error(404)

    def do_POST(self):
        if self.path in ("/chat", "/event"):
            try:
                length = int(self.headers.get("Content-Length", "0"))
                raw_data = self.rfile.read(length).decode("utf-8")
                item = json.loads(raw_data)

                kind = (
                    "gift"
                    if self.path == "/event" and item.get("type") == "gift"
                    else "message"
                )

                msg = {
                    "type": kind,
                    "name": str(item.get("name", "Spectateur"))[:80],
                    "text": str(item.get("text", ""))[:500],
                    "avatar": item.get("avatar"),
                    "giftImage": item.get("giftImage"),
                    "time": item.get("time", time.time())
                }

                if msg["text"]:
                    STATE["messages"].append(msg)
                    STATE["messages"] = STATE["messages"][-100:]

                self.send_response(204)
                self.send_cors_headers()
                self.end_headers()

            except Exception as error:
                print("Erreur réception événement :", error)
                self.send_error(400)

        else:
            self.send_error(404)

    def log_message(self, *_):
        pass


def start_local_server():
    try:
        server = ThreadingHTTPServer(
            ("127.0.0.1", 8765),
            LocalHandler
        )

        threading.Thread(
            target=server.serve_forever,
            daemon=True
        ).start()

        return server

    except OSError as error:
        print("Impossible de démarrer le serveur local :", error)
        return None
