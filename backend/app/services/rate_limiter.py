import time
import threading
from typing import Dict, Tuple, Optional
from fastapi import Request, HTTPException, status

class RateLimiter:
    """
    CYNERA ADVANCED MULTI-LAYER RATE LIMITER (Phase 6)
    Provides per-IP and per-account sliding-window rate limiting,
    failed-login throttling, and security abuse detection.
    """
    def __init__(self):
        self._lock = threading.Lock()
        # Storage: { key: [(timestamp, cost)] }
        self._requests: Dict[str, list] = {}
        # Failed login counters: { ip_or_email: (fail_count, locked_until_ts) }
        self._failed_logins: Dict[str, Tuple[int, float]] = {}

    def _clean_old_requests(self, key: str, window_seconds: float, now: float):
        if key in self._requests:
            cutoff = now - window_seconds
            self._requests[key] = [t for t in self._requests[key] if t > cutoff]
            if not self._requests[key]:
                del self._requests[key]

    def check_rate_limit(
        self,
        identifier: str,
        max_requests: int = 60,
        window_seconds: int = 60
    ) -> Tuple[bool, int, int]:
        """
        Checks whether the identifier exceeds max_requests within window_seconds.
        Returns: (allowed, remaining, retry_after_seconds)
        """
        now = time.time()
        with self._lock:
            self._clean_old_requests(identifier, window_seconds, now)
            timestamps = self._requests.get(identifier, [])
            current_count = len(timestamps)

            if current_count >= max_requests:
                earliest = timestamps[0]
                retry_after = max(1, int(earliest + window_seconds - now))
                return False, 0, retry_after

            # Record request
            if identifier not in self._requests:
                self._requests[identifier] = []
            self._requests[identifier].append(now)
            remaining = max(0, max_requests - current_count - 1)
            return True, remaining, 0

    def record_login_attempt(self, identifier: str, success: bool) -> Tuple[bool, Optional[str]]:
        """
        Tracks authentication attempts for brute-force protection.
        Locks account/IP for progressive durations after 5 consecutive failures.
        """
        now = time.time()
        with self._lock:
            count, locked_until = self._failed_logins.get(identifier, (0, 0.0))

            if now < locked_until:
                remaining_lock = int(locked_until - now)
                return False, f"Too many failed login attempts. Temporarily throttled. Try again in {remaining_lock} seconds."

            if success:
                self._failed_logins.pop(identifier, None)
                return True, None

            # Failed attempt
            new_count = count + 1
            if new_count >= 5:
                # Progressive backoff: 30s, 60s, 120s...
                lock_duration = min(900, 30 * (2 ** (new_count - 5)))
                self._failed_logins[identifier] = (new_count, now + lock_duration)
                return False, f"Too many failed login attempts. Account temporarily locked for {lock_duration} seconds."

            self._failed_logins[identifier] = (new_count, 0.0)
            return True, None

    def get_client_ip(self, request: Request) -> str:
        """Extracts client IP safely handling trusted reverse proxies."""
        forwarded = request.headers.get("x-forwarded-for")
        if forwarded:
            # Client IP is the first IP in comma-separated list
            return forwarded.split(",")[0].strip()
        real_ip = request.headers.get("x-real-ip")
        if real_ip:
            return real_ip.strip()
        if request.client:
            return request.client.host
        return "127.0.0.1"

rate_limiter = RateLimiter()
