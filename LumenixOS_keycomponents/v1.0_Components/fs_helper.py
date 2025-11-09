#!/usr/bin/env python3
import os
import json
import shutil
import base64
from http.server import BaseHTTPRequestHandler, HTTPServer
from urllib.parse import unquote, urlparse

HOST = "127.0.0.1"
PORT = 8765

def encode_array(array):
    """Return the given list as a base64-encoded JSON string."""
    raw = json.dumps(array)
    return base64.b64encode(raw.encode("utf-8")).decode("utf-8")

class FSHandler(BaseHTTPRequestHandler):
    def _set_headers(self, code=200):
        self.send_response(code)
        self.send_header("Content-Type", "application/json")
        self.send_header("Access-Control-Allow-Origin", "*")
        self.send_header("Access-Control-Allow-Methods", "GET, POST, OPTIONS")
        self.send_header("Access-Control-Allow-Headers", "Content-Type, Dir, Path")
        self.end_headers()

    def _send(self, code, payload):
        self._set_headers(code)
        self.wfile.write(json.dumps(payload).encode("utf-8"))

    def do_OPTIONS(self):
        self._set_headers(200)

    def do_GET(self):
        parsed = urlparse(self.path)
        path = unquote(parsed.path)

        if path == "/list":
            directory = self.headers.get("Dir", ".")
            try:
                entries = os.listdir(directory)
                result = []
                for name in entries:
                    full_path = os.path.abspath(os.path.join(directory, name))
                    if os.path.isdir(full_path):
                        entry_type = "[DIR]"
                        size = 0
                    else:
                        entry_type = "[FILE]"
                        size = os.path.getsize(full_path)
                    result.append(f"{entry_type}|{name}|{full_path}|{size}")
                self._send(200, {"ok": True, "items": encode_array(result)})
            except Exception as e:
                self._send(500, {"ok": False, "items": encode_array([f"[ERROR]|{e}|{directory}|0"])})

        elif path == "/read":
            file_path = self.headers.get("Path")
            try:
                full_path = os.path.abspath(file_path)
                mode = "rb" if file_path.lower().endswith(
                    (".png", ".jpg", ".jpeg", ".bin", ".dat")) else "r"
                with open(full_path, mode) as f:
                    data = f.read()
                if isinstance(data, bytes):
                    data = base64.b64encode(data).decode("utf-8")
                lines = data.splitlines() if isinstance(data, str) else [data]
                self._send(200, {"ok": True, "content": encode_array(lines)})
            except Exception as e:
                self._send(500, {"ok": False, "content": encode_array([f"[ERROR]|{e}|{file_path}|0"])})

        else:
            self._send(404, {"ok": False, "items": encode_array(["[ERROR]|Unknown route||0"])})

    def do_POST(self):
        parsed = urlparse(self.path)
        length = int(self.headers.get("Content-Length", 0))
        body = self.rfile.read(length).decode("utf-8")
        try:
            data = json.loads(body)
        except:
            data = {}

        if parsed.path == "/write":
            path = data.get("path")
            content = data.get("content", "")
            binary = data.get("binary", False)
            try:
                full_path = os.path.abspath(path)
                if binary:
                    with open(full_path, "wb") as f:
                        f.write(base64.b64decode(content))
                else:
                    with open(full_path, "w", encoding="utf-8") as f:
                        f.write(content)
                self._send(200, {"ok": True, "result": encode_array(
                    [f"[FILE]|{os.path.basename(full_path)}|{full_path}|{os.path.getsize(full_path)}"]
                )})
            except Exception as e:
                self._send(500, {"ok": False, "result": encode_array([f"[ERROR]|{e}|{path}|0"])})

        elif parsed.path == "/mkdir":
            path = data.get("path")
            try:
                full_path = os.path.abspath(path)
                os.makedirs(full_path, exist_ok=True)
                self._send(200, {"ok": True, "result": encode_array(
                    [f"[DIR]|{os.path.basename(full_path)}|{full_path}|0"]
                )})
            except Exception as e:
                self._send(500, {"ok": False, "result": encode_array([f"[ERROR]|{e}|{path}|0"])})

        elif parsed.path == "/delete":
            path = data.get("path")
            recursive = data.get("recursive", False)
            try:
                full_path = os.path.abspath(path)
                if os.path.isdir(full_path):
                    if recursive:
                        shutil.rmtree(full_path)
                    else:
                        os.rmdir(full_path)
                    entry_type = "[DIR]"
                else:
                    os.remove(full_path)
                    entry_type = "[FILE]"
                self._send(200, {"ok": True, "result": encode_array(
                    [f"{entry_type}|Deleted|{full_path}|0"]
                )})
            except Exception as e:
                self._send(500, {"ok": False, "result": encode_array([f"[ERROR]|{e}|{path}|0"])})

        else:
            self._send(404, {"ok": False, "result": encode_array(["[ERROR]|Unknown route||0"])})


def run():
    server = HTTPServer((HOST, PORT), FSHandler)
    print(f"File system helper running on http://{HOST}:{PORT}")
    server.serve_forever()

if __name__ == "__main__":
    run()
