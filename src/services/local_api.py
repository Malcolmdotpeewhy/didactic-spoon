import json
import threading
import socket
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer

class LeagueLoopAPIHandler(BaseHTTPRequestHandler):
    # Pass the app instance via the server object
    @property
    def app_instance(self):
        return self.server.app_instance

    def _set_cors_headers(self):
        self.send_header('Access-Control-Allow-Origin', '*')
        self.send_header('Access-Control-Allow-Methods', 'GET, POST, OPTIONS')
        self.send_header('Access-Control-Allow-Headers', 'Content-Type')

    def do_OPTIONS(self):
        self.send_response(200)
        self._set_cors_headers()
        self.end_headers()

    def do_GET(self):
        if self.path == '/status':
            self.send_response(200)
            self._set_cors_headers()
            self.send_header('Content-type', 'application/json')
            self.end_headers()
            
            # Fetch data safely from the app
            phase = "Unknown"
            power_state = False
            queue_mode = "None"
            
            app = self.app_instance
            if app:
                if hasattr(app, "automation") and app.automation:
                    phase = app.automation.last_phase
                if hasattr(app, "sidebar") and app.sidebar:
                    power_state = getattr(app.sidebar, "power_state", False)
                    if hasattr(app.sidebar, "var_game_mode"):
                        queue_mode = app.sidebar.var_game_mode.get()

            data = {
                "phase": phase,
                "automation_enabled": power_state,
                "queue_mode": queue_mode
            }
            self.wfile.write(json.dumps(data).encode('utf-8'))
        else:
            self.send_response(404)
            self.end_headers()

    def do_POST(self):
        if self.path == '/action':
            content_length = int(self.headers.get('Content-Length', 0))
            post_data = self.rfile.read(content_length)
            
            action = ""
            try:
                body = json.loads(post_data.decode('utf-8'))
                action = body.get("action", "")
            except:
                pass
                
            app = self.app_instance
            if app:
                if action == "find_match":
                    app.after(0, app._hotkey_find_match)
                elif action == "launch_client":
                    app.after(0, app._hotkey_launch_client)
                elif action == "toggle_automation":
                    app.after(0, app._hotkey_toggle_automation)
            
            self.send_response(200)
            self._set_cors_headers()
            self.send_header('Content-type', 'application/json')
            self.end_headers()
            self.wfile.write(json.dumps({"status": "success", "action": action}).encode('utf-8'))
        else:
            self.send_response(404)
            self.end_headers()

    # Disable default logging to avoid terminal spam
    def log_message(self, format, *args):
        pass

def get_local_ip():
    try:
        # Create a dummy socket to find the local IP acting towards the internet
        s = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
        s.settimeout(0)
        s.connect(('10.254.254.254', 1))
        ip = s.getsockname()[0]
        s.close()
        return ip
    except Exception:
        return '127.0.0.1'

def start_api_server(app_instance, port=8337):
    # Port 8337 = LEET -> L E E T -> 8337 (sort of)
    host = '0.0.0.0'
    try:
        server = ThreadingHTTPServer((host, port), LeagueLoopAPIHandler)
        server.app_instance = app_instance
        
        server_thread = threading.Thread(target=server.serve_forever, daemon=True)
        server_thread.start()
        
        local_ip = get_local_ip()
        from utils.logger import Logger
        Logger.info("API", f"Remote Link API started on http://{local_ip}:{port}")
        return local_ip, port
    except Exception as e:
        from utils.logger import Logger
        Logger.error("API", f"Failed to start API server: {e}")
        return None, None
