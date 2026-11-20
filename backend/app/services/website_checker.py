import re
import time
import ssl
import socket
import datetime
import urllib.parse
from typing import Dict, Any, List, Optional, Tuple
import httpx
from .ssrf_guard import validate_public_url

def parse_ssl_certificate(hostname: str, port: int = 443, timeout: float = 5.0) -> Dict[str, Any]:
    """Inspects the live SSL/TLS certificate of a hostname."""
    context = ssl.create_default_context()
    conn = context.wrap_socket(socket.socket(socket.AF_INET), server_hostname=hostname)
    conn.settimeout(timeout)

    try:
        t0 = time.perf_counter()
        conn.connect((hostname, port))
        handshake_ms = round((time.perf_counter() - t0) * 1000, 2)
        cert = conn.getpeercert()
        conn.close()

        if not cert:
            return {
                "valid": False,
                "status": "INVALID",
                "days_remaining": 0,
                "issuer": "Unknown",
                "expiry_date": None,
                "handshake_ms": handshake_ms,
                "error": "Empty certificate presented."
            }

        # Expiry date parsing: e.g. 'May 15 12:00:00 2026 GMT'
        not_after_str = cert.get("notAfter")
        expiry_dt = None
        days_remaining = None
        if not_after_str:
            try:
                expiry_dt = datetime.datetime.strptime(not_after_str, "%b %d %H:%M:%S %Y %Z").replace(tzinfo=datetime.timezone.utc)
                now = datetime.datetime.now(datetime.timezone.utc)
                days_remaining = (expiry_dt - now).days
            except Exception:
                pass

        # Issuer extraction
        issuer_tuple = cert.get("issuer", ())
        issuer_parts = []
        for rdn in issuer_tuple:
            for k, v in rdn:
                if k == "organizationName" or k == "commonName":
                    issuer_parts.append(v)
        issuer_str = ", ".join(issuer_parts) or "Public Trusted CA"

        # Determine certificate health status
        if days_remaining is not None and days_remaining <= 0:
            cert_status = "EXPIRED"
        elif days_remaining is not None and days_remaining <= 14:
            cert_status = "WARNING"
        elif days_remaining is not None and days_remaining <= 30:
            cert_status = "WARNING"
        else:
            cert_status = "VALID"

        return {
            "valid": True,
            "status": cert_status,
            "days_remaining": max(0, days_remaining) if days_remaining is not None else 90,
            "issuer": issuer_str,
            "expiry_date": expiry_dt.isoformat() if expiry_dt else None,
            "handshake_ms": handshake_ms,
            "error": None
        }
    except ssl.SSLCertVerificationError as e:
        return {
            "valid": False,
            "status": "INVALID",
            "days_remaining": 0,
            "issuer": "Untrusted / Self-Signed",
            "expiry_date": None,
            "handshake_ms": 0.0,
            "error": f"TLS Certificate Verification Error: {e.verify_message}"
        }
    except Exception as e:
        return {
            "valid": False,
            "status": "TLS_ERROR",
            "days_remaining": 0,
            "issuer": None,
            "expiry_date": None,
            "handshake_ms": 0.0,
            "error": str(e)
        }

async def execute_website_check(
    url: str,
    expected_status_codes: Optional[List[int]] = None,
    timeout_sec: float = 10.0,
    check_ssl: bool = True
) -> Dict[str, Any]:
    """
    Performs a real, complete health, availability, performance, DNS and SSL check on a target URL.
    Returns structured results for recording into the database and broadcasting.
    """
    if expected_status_codes is None:
        expected_status_codes = [200, 201, 204, 301, 302, 307, 308]

    # 1. SSRF and Domain Validation
    t_dns_start = time.perf_counter()
    is_safe, ssrf_msg, norm_url, resolved_ips = validate_public_url(url)
    dns_time_ms = round((time.perf_counter() - t_dns_start) * 1000, 2)

    if not is_safe:
        return {
            "status": "DNS_FAILURE" if "DNS" in ssrf_msg else "BLOCKED_SSRF",
            "status_code": 0,
            "response_time_ms": 0.0,
            "dns_lookup_time_ms": dns_time_ms,
            "tls_handshake_time_ms": 0.0,
            "dns_resolved_ips": [],
            "dns_status": "FAILED",
            "ssl_valid": False,
            "ssl_status": "UNKNOWN",
            "ssl_days_remaining": 0,
            "ssl_issuer": None,
            "ssl_expiry_date": None,
            "error_message": ssrf_msg,
            "is_online": False,
            "checked_at": datetime.datetime.now(datetime.timezone.utc).isoformat()
        }

    parsed = urllib.parse.urlparse(norm_url)
    hostname = parsed.hostname
    port = parsed.port or (443 if parsed.scheme == "https" else 80)

    # 2. SSL/TLS Inspection (for HTTPS)
    ssl_info = {
        "valid": True,
        "status": "VALID",
        "days_remaining": 90,
        "issuer": "N/A (HTTP)",
        "expiry_date": None,
        "handshake_ms": 0.0,
        "error": None
    }
    if parsed.scheme == "https" and check_ssl:
        ssl_info = parse_ssl_certificate(hostname, port, timeout=5.0)

    # 3. HTTP Availability & Latency Check
    t_req_start = time.perf_counter()
    status_code = 0
    resp_time_ms = 0.0
    check_status = "ONLINE"
    error_msg = None

    headers = {
        "User-Agent": "CYNERA-Observability-Monitor/1.4 (Two-Tier Zero-Trust; +https://cynera.io)"
    }

    try:
        async with httpx.AsyncClient(timeout=timeout_sec, follow_redirects=True, verify=False) as client:
            resp = await client.get(norm_url, headers=headers)
            resp_time_ms = round((time.perf_counter() - t_req_start) * 1000, 2)
            status_code = resp.status_code

            if status_code in expected_status_codes:
                if resp_time_ms > 2500:
                    check_status = "DEGRADED"
                else:
                    check_status = "ONLINE"
            else:
                if status_code >= 500:
                    check_status = "DOWN"
                    error_msg = f"HTTP {status_code} Internal Server Error"
                elif status_code >= 400:
                    check_status = "HTTP_ERROR"
                    error_msg = f"HTTP {status_code} Client Error (Expected: {expected_status_codes})"
                else:
                    check_status = "DEGRADED"

    except httpx.ConnectTimeout:
        resp_time_ms = round(timeout_sec * 1000, 2)
        check_status = "TIMEOUT"
        error_msg = f"Connection timed out after {timeout_sec} seconds."
    except httpx.ReadTimeout:
        resp_time_ms = round(timeout_sec * 1000, 2)
        check_status = "TIMEOUT"
        error_msg = f"Read timeout reached after {timeout_sec} seconds."
    except httpx.ConnectError as e:
        resp_time_ms = round((time.perf_counter() - t_req_start) * 1000, 2)
        check_status = "DOWN"
        error_msg = f"Failed to establish connection: {e}"
    except Exception as e:
        resp_time_ms = round((time.perf_counter() - t_req_start) * 1000, 2)
        check_status = "DOWN"
        error_msg = f"Monitoring probe error: {str(e)}"

    # If SSL is expired or invalid, downgrade status
    if ssl_info.get("status") in ("EXPIRED", "INVALID"):
        check_status = "TLS_FAILURE"
        error_msg = ssl_info.get("error") or "SSL Certificate is expired or invalid."

    is_online = check_status in ("ONLINE", "DEGRADED")

    return {
        "status": check_status,
        "status_code": status_code,
        "response_time_ms": resp_time_ms,
        "dns_lookup_time_ms": dns_time_ms,
        "tls_handshake_time_ms": ssl_info.get("handshake_ms", 0.0),
        "dns_resolved_ips": resolved_ips,
        "dns_status": "HEALTHY",
        "ssl_valid": ssl_info.get("valid", True),
        "ssl_status": ssl_info.get("status", "VALID"),
        "ssl_days_remaining": ssl_info.get("days_remaining", 0),
        "ssl_issuer": ssl_info.get("issuer"),
        "ssl_expiry_date": ssl_info.get("expiry_date"),
        "error_message": error_msg,
        "is_online": is_online,
        "checked_at": datetime.datetime.now(datetime.timezone.utc).isoformat()
    }

async def verify_website_ownership(
    url: str,
    expected_token: str,
    method: str = "dns_txt"
) -> Tuple[bool, str]:
    """Verifies domain control using an exact, live challenge proof."""
    if method in ("manual", "instant"):
        return False, "Manual/instant verification is disabled. Publish the supplied DNS or HTTP challenge."

    parsed = urllib.parse.urlparse(url)
    hostname = parsed.hostname
    if not hostname:
        return False, "Invalid target domain."

    if method == "dns_txt":
        try:
            import dns.resolver
            answers = dns.resolver.resolve(f"_cynera-verification.{hostname}", "TXT", lifetime=5.0)
            for answer in answers:
                value = b"".join(answer.strings).decode("utf-8", errors="ignore").strip()
                if value == expected_token:
                    return True, "Ownership verified via the _cynera-verification DNS TXT record."
            return False, "The DNS TXT record did not contain the exact verification token."
        except Exception as exc:
            return False, f"DNS TXT verification failed: {exc}"

    if method == "meta_tag":
        safe, reason, safe_url, _ = validate_public_url(url)
        if not safe:
            return False, f"Verification target blocked: {reason}"
        try:
            async with httpx.AsyncClient(timeout=10.0, verify=True, follow_redirects=False) as client:
                response = await client.get(safe_url, headers={"User-Agent": "CYNERA-Domain-Verifier/1.4"})
            if response.status_code != 200:
                return False, f"Verification failed: target returned HTTP {response.status_code}."
            tag = re.compile(
                r'<meta\\s+[^>]*(?:name=["\\'](?:cynera-verification|cynera-site-verification)["\\'][^>]*content=["\\']'
                + re.escape(expected_token) +
                r'["\\']|content=["\\']' + re.escape(expected_token) +
                r'["\\'][^>]*name=["\\'](?:cynera-verification|cynera-site-verification)["\\'])',
                re.IGNORECASE
            )
            return (True, "Ownership verified via HTML meta tag.") if tag.search(response.text) else (False, "Expected ownership meta tag was not detected.")
        except Exception as exc:
            return False, f"HTML meta tag verification request failed: {exc}"

    if method == "http_file":
        verify_url = f"{parsed.scheme}://{hostname}/.well-known/cynera-verify.txt"
        safe, reason, safe_url, _ = validate_public_url(verify_url)
        if not safe:
            return False, f"Verification target blocked: {reason}"
        try:
            async with httpx.AsyncClient(timeout=8.0, verify=True, follow_redirects=False) as client:
                response = await client.get(safe_url)
            if response.status_code == 200 and response.text.strip() == expected_token:
                return True, "Ownership verified via HTTP token file."
            return False, "HTTP verification file did not exactly match the challenge token."
        except Exception as exc:
            return False, f"HTTP verification request failed: {exc}"

    return False, "Unsupported ownership verification method."
