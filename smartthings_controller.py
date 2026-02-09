# smartthings_controller.py
import time
import requests

class SmartThingsController:
    """
    Safe, optional SmartThings poller:
    - runs in background thread
    - never raises exception to caller
    - handles 429 with backoff
    - degrades polling frequency when repeatedly failing
    """

    def __init__(
        self,
        token: str,
        left_device_id: str,
        right_device_id: str,
        poll_interval: float = 1.0,
        cooldown_sec: float = 0.25,
        step_deg: int = 5,
        max_consecutive_failures: int = 8,
        failure_sleep_sec: float = 10.0,
        enabled: bool = True,
    ):
        self.token = (token or "").strip()
        self.left_id = (left_device_id or "").strip()
        self.right_id = (right_device_id or "").strip()

        self.base = "https://api.smartthings.com/v1"
        self.headers = {
            "Authorization": f"Bearer {self.token}",
            "Content-Type": "application/json",
        }

        self.poll_interval = float(poll_interval)
        self.cooldown_sec = float(cooldown_sec)
        self.step_deg = int(step_deg)

        self.max_consecutive_failures = int(max_consecutive_failures)
        self.failure_sleep_sec = float(failure_sleep_sec)

        self.enabled = bool(enabled)

        self._stop = False
        self._last_action_ts = 0.0
        self._failures = 0

    def stop(self):
        self._stop = True

    def is_config_valid(self) -> bool:
        return bool(self.token and self.left_id and self.right_id)

    # ---- API helpers ----
    def _get_switch_state(self, device_id: str) -> str:
        r = requests.get(
            f"{self.base}/devices/{device_id}/status",
            headers=self.headers,
            timeout=6
        )
        r.raise_for_status()
        return r.json()["components"]["main"]["switch"]["switch"]["value"]

    def _set_switch(self, device_id: str, on: bool) -> None:
        payload = {
            "commands": [{
                "component": "main",
                "capability": "switch",
                "command": "on" if on else "off"
            }]
        }
        r = requests.post(
            f"{self.base}/devices/{device_id}/commands",
            headers=self.headers,
            json=payload,
            timeout=6
        )
        r.raise_for_status()

    def run(self, on_left, on_right):
        """
        on_left/on_right callbacks should be fast.
        UI updates must be scheduled by caller via app.after.
        """
        if not self.enabled:
            print("ℹ️ SmartThings disabled (enabled=False)")
            return
        if not self.is_config_valid():
            print("ℹ️ SmartThings disabled (missing token/device IDs)")
            return

        print("✅ SmartThings poller running (optional)")

        check_left = True
        backoff_sec = 0.0

        while not self._stop:
            try:
                # backoff if needed (429 or repeated failures)
                if backoff_sec > 0:
                    time.sleep(backoff_sec)
                    backoff_sec = 0.0

                # alternate checking one device per loop to reduce rate
                device_id = self.left_id if check_left else self.right_id
                is_left = check_left
                check_left = not check_left

                state = self._get_switch_state(device_id)

                if state == "on":
                    now = time.time()
                    if now - self._last_action_ts >= self.cooldown_sec:
                        if is_left:
                            on_left(self.step_deg)
                        else:
                            on_right(self.step_deg)
                        self._last_action_ts = now

                    # reset OFF so it can be triggered again
                    self._set_switch(device_id, False)

                # success path: reset failures counter
                self._failures = 0
                time.sleep(self.poll_interval)

            except requests.HTTPError as e:
                resp = getattr(e, "response", None)

                if resp is not None and resp.status_code == 429:
                    # Use Retry-After header if present
                    ra = resp.headers.get("Retry-After")
                    backoff_sec = float(ra) if ra else 8.0
                    print(f"⚠️ SmartThings 429 rate-limited. Backoff {backoff_sec}s")
                else:
                    self._failures += 1
                    print(f"⚠️ SmartThings HTTP error ({self._failures}): {e}")

                # too many consecutive failures → sleep longer (degrade) but DO NOT block UI
                if self._failures >= self.max_consecutive_failures:
                    print(f"⚠️ SmartThings unstable. Sleeping {self.failure_sleep_sec}s then retry...")
                    time.sleep(self.failure_sleep_sec)
                    self._failures = 0  # reset after long sleep

                time.sleep(1.0)

            except Exception as e:
                # any other network/JSON/timeout errors
                self._failures += 1
                print(f"⚠️ SmartThings poll error ({self._failures}): {e}")

                if self._failures >= self.max_consecutive_failures:
                    print(f"⚠️ SmartThings unstable. Sleeping {self.failure_sleep_sec}s then retry...")
                    time.sleep(self.failure_sleep_sec)
                    self._failures = 0

                time.sleep(1.0)
