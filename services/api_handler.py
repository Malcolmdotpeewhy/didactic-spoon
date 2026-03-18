"""
LCU API Handler
Manages communication with the League of Legends Client Update (LCU).
"""
import base64
import os
import sys
import threading
import time
from typing import Dict, Optional

import psutil
import requests
import urllib3
import warnings

from utils.logger import Logger


class LCUClient:
    """
    Handles communication with the Local League Client Update (LCU) API.
    Auto-detects the client's lockfile to get port and authentication.
    """

    def __init__(self):
        self._lock = threading.Lock()
        self.port: Optional[str] = None
        self.auth_token: Optional[str] = None
        self.protocol: str = "https"
        self.base_url: Optional[str] = None
        self.is_connected: bool = False
        self.headers: Dict[str, str] = {}
        self.session = requests.Session()
        self.session.verify = False
        self._client_pid: Optional[int] = None

        # Do NOT connect immediately to avoid blocking UI startup.
        # Connection is handled by the background loop in main.py.

    def connect(self, silent=False) -> bool:
        """Attempts to read the lockfile and establish connection details."""
        with self._lock:
            # Atomic check: If we connected while waiting for lock, return success
            if self.is_connected:
                return True

            try:
                # Look for League Client processes
                client_procs = [
                    "LeagueClientUx.exe",
                    "LeagueClient.exe",
                    "RiotClientUx.exe",
                ]
                process = None

                # Bolt Optimization: Iterate process list ONCE instead of up to 3 times.
                # Prioritize LeagueClientUx.exe, but scan for others in the same pass.
                found_procs = {}
                highest_priority = client_procs[0]

                scan_start = time.time()

                if self._client_pid is not None:
                    try:
                        p = psutil.Process(self._client_pid)
                        if p.is_running() and p.name() in client_procs:
                            process = p
                    except (psutil.NoSuchProcess, psutil.AccessDenied, psutil.ZombieProcess):
                        self._client_pid = None

                if not process:
                    for p in psutil.process_iter(["name"]):
                        try:
                            name = p.info["name"]
                            if name in client_procs:
                                found_procs[name] = p
                                # Optimization: Stop early if we found the best one
                                if name == highest_priority:
                                    break
                        except (psutil.NoSuchProcess, psutil.AccessDenied, psutil.ZombieProcess):
                            continue

                    scan_duration = time.time() - scan_start
                    if scan_duration > 0.5:
                        Logger.debug("LCU", f"Process scan took {scan_duration:.3f}s")

                    # Select best match based on priority
                    for p_name in client_procs:
                        if p_name in found_procs:
                            process = found_procs[p_name]
                            break

                    if process:
                        self._client_pid = process.pid

                if not process:
                    if not silent:
                        Logger.debug("LCU", "Client not found. Ensure League of Legends is running.")
                    self.is_connected = False
                    return False

                # Try to read lockfile from process info
                try:
                    cmdline = process.cmdline()
                    for arg in cmdline:
                        if "--app-port=" in arg:
                            self.port = arg.split("=")[1]
                        if "--remoting-auth-token=" in arg:
                            self.auth_token = arg.split("=")[1]
                except psutil.AccessDenied:
                    # Access Denied on cmdline is common if running non-admin. Fallback to lockfile.
                    Logger.warning("LCU", "Access denied reading process cmdline. Falling back to lockfile.")
                except Exception as e:  # pylint: disable=broad-exception-caught
                    Logger.debug("LCU", f"Could not read process cmdline: {e}. Falling back to lockfile.")

                # Fallback: Check for 'lockfile' in the process directory if we miss port/token
                if not self.port or not self.auth_token:
                    try:
                        exe_path = process.exe()
                        proc_dir = os.path.dirname(exe_path)
                        lockfile_path = os.path.join(proc_dir, "lockfile")

                        if os.path.exists(lockfile_path):
                            Logger.debug("LCU", f"Reading lockfile at {lockfile_path}")
                            with open(lockfile_path, "r", encoding="utf-8") as f:
                                data = f.read().split(":")
                                if len(data) >= 4:
                                    self.port = data[2]
                                    self.auth_token = data[3]
                                    Logger.debug(
                                        "LCU", f"Extracted from lockfile: Port {self.port}"
                                    )
                    except psutil.AccessDenied:
                        Logger.warning("LCU", "Access denied reading lockfile.")
                    except Exception as e:  # pylint: disable=broad-exception-caught
                        Logger.debug("LCU", f"Lockfile check failed: {e}")

                if self.port and self.auth_token:
                    auth_str = f"riot:{self.auth_token}"
                    b64_auth = base64.b64encode(auth_str.encode()).decode()
                    self.headers = {
                        "Authorization": f"Basic {b64_auth}",
                        "Content-Type": "application/json",
                        "Accept": "application/json",
                    }
                    self.session.headers.update(self.headers)
                    self.base_url = f"https://127.0.0.1:{self.port}"
                    self.is_connected = True
                    Logger.debug("LCU", f"Connected to port {self.port}")
                    return True

                Logger.debug("LCU", "Found process but could not extract credentials.")

            except Exception as e:  # pylint: disable=broad-exception-caught
                Logger.error("LCU", f"Connection Error: {e}")
                self.is_connected = False

            return False

    def request(
        self,
        method: str,
        endpoint: str,
        data: Optional[Dict] = None,
        silent: bool = False,
    ) -> Optional[requests.Response]:
        """Generic wrapper for LCU requests."""
        if not self.is_connected:
            if not self.connect():
                return None

        url = f"{self.base_url}{endpoint}"
        t_start = time.time()
        try:
            if not silent:
                Logger.debug("LCU", f"REQ -> {method} {endpoint}")
            
            # TRACE payload format
            if endpoint == "/lol-lobby/v2/lobby" and method == "POST":
                Logger.debug("LCU_TRACE", f"DATA TYPE: {type(data)} | RAW: {data}")
                
            with warnings.catch_warnings():
                warnings.simplefilter("ignore", urllib3.exceptions.InsecureRequestWarning)
                response = self.session.request(
                    method=method,
                    url=url,
                    # headers=self.headers, # Already in session
                    json=data,
                    verify=False,
                    timeout=2,  # Prevent blocking UI
                )

            dur = time.time() - t_start
            if not silent:
                Logger.debug(
                    "LCU", f"RES <- {response.status_code} [{dur:.3f}s] {endpoint}"
                )
            return response
        except requests.exceptions.ConnectionError:
            # Expected when the game is closed or restarting
            self.is_connected = False
            return None
        except requests.exceptions.ReadTimeout:
            # Expected for long-polling endpoints
            return None
        except requests.RequestException as e:
            dur = time.time() - t_start
            Logger.error("LCU", f"FAIL [{dur:.3f}s] {endpoint} : {e}")
            # Connection lost?
            self.is_connected = False
            return None

