import ipaddress
import re
import socket
import urllib.parse
from typing import List, Tuple


BLOCKED_HOSTNAMES = {
    "localhost",
    "localhost.localdomain",
    "metadata.google.internal",
    "instance-data",
    "metadata",
}
BLOCKED_SUFFIXES = (
    ".localhost",
    ".local",
    ".internal",
    ".home",
    ".lan",
    ".test",
    ".invalid",
)


def is_ip_private_or_restricted(ip_str: str) -> bool:
    """
    Return True unless the address is globally routable.

    Using is_global instead of only is_private also rejects shared address space,
    documentation networks, benchmarking ranges, multicast, link-local and other
    special-purpose ranges. IPv4-mapped IPv6 addresses are checked as IPv4.
    """
    try:
        address = ipaddress.ip_address(str(ip_str).split("%", 1)[0])
    except (TypeError, ValueError):
        return True

    if isinstance(address, ipaddress.IPv6Address) and address.ipv4_mapped:
        return not address.ipv4_mapped.is_global

    return not address.is_global


def _normalise_hostname(hostname: str) -> Tuple[bool, str, str]:
    """Return (is_valid, ASCII hostname, error)."""
    host = (hostname or "").strip().rstrip(".").lower()
    if not host:
        return False, "", "URL must contain a valid hostname."

    if "%" in host:
        return False, "", "Scoped IP addresses are not permitted."

    try:
        host = host.encode("idna").decode("ascii").lower()
    except UnicodeError:
        return False, "", "Hostname is not a valid internationalised domain name."

    if len(host) > 253:
        return False, "", "Hostname exceeds the maximum DNS length."

    labels = host.split(".")
    if len(labels) < 2:
        return False, "", "Use a fully qualified public domain name, not a local hostname."

    label_pattern = re.compile(r"^[a-z0-9](?:[a-z0-9-]{0,61}[a-z0-9])?$")
    if any(not label_pattern.fullmatch(label) for label in labels):
        return False, "", "Hostname contains invalid DNS label characters."

    if host in BLOCKED_HOSTNAMES or any(host.endswith(suffix) for suffix in BLOCKED_SUFFIXES):
        return False, "", "Local or reserved hostnames are blocked by SSRF protection."

    return True, host, ""


def validate_public_url(url: str) -> Tuple[bool, str, str, List[str]]:
    """
    Validate a public HTTP(S) URL against SSRF.

    Public IPv4/IPv6 literals and public DNS hostnames are accepted. Every
    address returned by DNS must be globally routable; mixed public/private
    answers are rejected to prevent DNS-rebinding and split-answer bypasses.

    Returns: (is_safe, error_message, normalized_url, resolved_ips).
    """
    if not isinstance(url, str) or not url.strip():
        return False, "URL cannot be empty.", "", []

    candidate = url.strip()
    if any(ord(char) < 32 for char in candidate) or "\\" in candidate:
        return False, "URL contains invalid control or escape characters.", "", []

    if "://" not in candidate:
        # A bare IPv6 literal contains colons; wrap it in brackets before
        # adding the URL scheme so urlsplit does not mistake it for a port.
        raw_host = candidate.strip()
        if raw_host.startswith("[") and raw_host.endswith("]"):
            raw_host = raw_host[1:-1]
        try:
            bare_ip = ipaddress.ip_address(raw_host)
        except ValueError:
            bare_ip = None

        if isinstance(bare_ip, ipaddress.IPv6Address):
            candidate = f"https://[{bare_ip.compressed}]"
        else:
            candidate = "https://" + candidate.lstrip("/")

    try:
        parsed = urllib.parse.urlsplit(candidate)
        port = parsed.port  # Access validates malformed and out-of-range ports.
    except ValueError:
        return False, "URL has an invalid port or authority section.", "", []

    scheme = parsed.scheme.lower()
    if scheme not in ("http", "https"):
        return False, "Only HTTP and HTTPS URLs are permitted.", "", []

    if parsed.username is not None or parsed.password is not None or "@" in parsed.netloc:
        return False, "URLs containing embedded usernames or passwords are not permitted.", "", []

    if parsed.netloc.endswith(":"):
        return False, "URL contains an empty port.", "", []

    hostname = parsed.hostname
    if not hostname:
        return False, "URL must contain a valid domain name or IP address.", "", []

    resolved_ips: List[str] = []
    literal_ip = None

    # Handle IP literals directly. This avoids passing IPv6 literals through
    # DNS and supports both public IPv4 and bracketed IPv6 URLs.
    try:
        if "%" in hostname:
            return False, "Scoped IP addresses are not permitted.", "", []
        literal_ip = ipaddress.ip_address(hostname)
    except ValueError:
        literal_ip = None

    if literal_ip is not None:
        if is_ip_private_or_restricted(str(literal_ip)):
            return False, f"Target IP '{literal_ip}' is not globally routable and is blocked.", "", []
        resolved_ips = [str(literal_ip)]
        normalized_host = (
            f"[{literal_ip.compressed}]"
            if isinstance(literal_ip, ipaddress.IPv6Address)
            else literal_ip.compressed
        )
    else:
        valid_host, normalized_host, host_error = _normalise_hostname(hostname)
        if not valid_host:
            return False, host_error, "", []

        try:
            addr_info = socket.getaddrinfo(
                normalized_host,
                None,
                socket.AF_UNSPEC,
                socket.SOCK_STREAM,
            )
        except socket.gaierror as exc:
            return (
                False,
                f"DNS lookup failed for '{normalized_host}'. Verify that the domain exists and has public A/AAAA records. ({exc})",
                "",
                [],
            )
        except OSError as exc:
            return False, f"Public DNS lookup could not be completed for '{normalized_host}'. ({exc})", "", []

        for item in addr_info:
            try:
                address = ipaddress.ip_address(item[4][0].split("%", 1)[0])
            except (IndexError, TypeError, ValueError):
                return False, "DNS returned an invalid IP address; the target was blocked.", "", []

            address_text = str(address)
            if is_ip_private_or_restricted(address_text):
                return (
                    False,
                    f"SSRF protection blocked '{normalized_host}' because DNS returned a non-public IP address ({address_text}).",
                    "",
                    [],
                )
            if address_text not in resolved_ips:
                resolved_ips.append(address_text)

        if not resolved_ips:
            return False, f"No public A/AAAA addresses were returned for '{normalized_host}'.", "", []

    # Drop default ports and fragments for a stable canonical URL.
    if port in (80 if scheme == "http" else 443,):
        port = None
    netloc = normalized_host if port is None else f"{normalized_host}:{port}"
    normalized_url = urllib.parse.urlunsplit((
        scheme,
        netloc,
        parsed.path or "/",
        parsed.query,
        "",
    ))
    return True, "URL is public and passed SSRF validation.", normalized_url, sorted(resolved_ips)
