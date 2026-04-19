import sys

with open("src/services/api_handler.py", "r", encoding="utf-8") as f:
    content = f.read()

# 1. Update Init
init_target = """        self.session = requests.Session()
        self.session.verify = False
        self._client_pid: Optional[int] = None"""

init_replacement = """        self.session = requests.Session()
        self.session.verify = False
        
        # 3.2 Connection pooling
        adapter = requests.adapters.HTTPAdapter(pool_connections=10, pool_maxsize=10, max_retries=1)
        self.session.mount("https://", adapter)
        self.session.mount("http://", adapter)
        
        self._client_pid: Optional[int] = None
        
        # 3.1 & 3.3 State
        self._backoff = 1.0
        self._last_scan_time = 0.0
        
        self._tokens = 20.0
        self._token_capacity = 20.0
        self._token_rate = 5.0
        self._last_token_update = time.time()
        self._rate_lock = threading.Lock()
        
        # 3.5 Offline Retry Queue
        self._offline_queue = []"""
if init_target in content:
    content = content.replace(init_target, init_replacement)
else:
    print("Init target not found")

# 2. Update connect()
connect_target = """                    # Throttle process scans to once every 5 seconds to save CPU
                    now = time.time()
                    if now - getattr(self, "_last_scan_time", 0) < 5.0:
                        return False
                    self._last_scan_time = now"""

connect_replacement = """                    # Throttle heavily using Exponential Backoff (3.1)
                    now = time.time()
                    if now - getattr(self, "_last_scan_time", 0) < getattr(self, "_backoff", 1.0):
                        return False
                    self._last_scan_time = now"""
if connect_target in content:
    content = content.replace(connect_target, connect_replacement)
else:
    print("Connect scan target not found")

connect_fail_target = """                if not process:
                    if not silent:
                        Logger.debug("LCU", "Client not found. Ensure League of Legends is running.")
                    self.is_connected = False
                    return False"""

connect_fail_replacement = """                if not process:
                    if not silent:
                        Logger.debug("LCU", "Client not found. Ensure League of Legends is running.")
                    self.is_connected = False
                    self._backoff = min(getattr(self, "_backoff", 1.0) * 1.5, 30.0)
                    return False"""
if connect_fail_target in content:
    content = content.replace(connect_fail_target, connect_fail_replacement)
else:
    print("Connect fail target not found")

connect_success_target = """                    self.is_connected = True
                    Logger.debug("LCU", f"Connected to port {self.port}")
                    return True"""

connect_success_replacement = """                    self.is_connected = True
                    self._backoff = 1.0  # Reset backoff on success
                    Logger.debug("LCU", f"Connected to port {self.port}")
                    return True"""
if connect_success_target in content:
    content = content.replace(connect_success_target, connect_success_replacement)
else:
    print("Connect success target not found")

# 3. Update request()
request_target = """        if not self.is_connected:
            if not self.connect():
                return None

        url = f"{self.base_url}{endpoint}"
        t_start = time.time()"""

request_replacement = """        if not self.is_connected:
            if not self.connect(silent=silent):
                if method in ["POST", "PUT", "PATCH", "DELETE"]:
                    # 3.5 Offline Retry Queue: save state mutations for when we reconnect
                    self._offline_queue.append((method, endpoint, data))
                return None

        # Flush 3.5 Offline Retry Queue on successful connection
        if getattr(self, "_offline_queue", []):
            oq = self._offline_queue.copy()
            self._offline_queue.clear()
            for m, e, d in oq:
                threading.Thread(target=self.request, args=(m, e, d, True), daemon=True).start()

        # 3.3 Strict Token Bucket Rate-Limiter
        with getattr(self, "_rate_lock", threading.Lock()):
            now = time.time()
            if hasattr(self, "_tokens"):
                self._tokens = min(self._token_capacity, self._tokens + (now - self._last_token_update) * self._token_rate)
                self._last_token_update = now
                if self._tokens < 1.0:
                    time.sleep((1.0 - self._tokens) / self._token_rate)
                    self._tokens = 0.0
                    self._last_token_update = time.time()
                else:
                    self._tokens -= 1.0

        url = f"{self.base_url}{endpoint}"
        t_start = time.time()"""
if request_target in content:
    content = content.replace(request_target, request_replacement)
else:
    print("Request target not found")

# 4. WAMP normalization
wamp_target = """                                # Find callbacks
                                callbacks = []
                                with self._lock:
                                    if event_name in self._subscriptions:
                                        callbacks = self._subscriptions[event_name].copy()
                                    if "OnJsonApiEvent" in self._subscriptions:
                                        callbacks.extend(self._subscriptions["OnJsonApiEvent"])"""

wamp_replacement = """                                # 3.4 WAMP auto-normalization
                                try:
                                    if isinstance(payload, dict) and 'data' in payload and 'eventType' in payload:
                                        payload = payload['data']  # Normalize nested WAMP payload to flat data
                                except Exception:
                                    pass

                                # Find callbacks
                                callbacks = []
                                with self._lock:
                                    if event_name in self._subscriptions:
                                        callbacks = self._subscriptions[event_name].copy()
                                    if "OnJsonApiEvent" in self._subscriptions:
                                        callbacks.extend(self._subscriptions["OnJsonApiEvent"])"""
if wamp_target in content:
    content = content.replace(wamp_target, wamp_replacement)
else:
    print("WAMP target not found")

with open("src/services/api_handler.py", "w", encoding="utf-8") as f:
    f.write(content)

print("Modification complete")
