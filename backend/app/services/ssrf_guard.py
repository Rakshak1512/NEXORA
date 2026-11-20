import ipaddress
import socket
import urllib.parse
from typing import Tuple, List

BLOCKED_HOSTNAMES = {
    "localhost", "127.0.0.1", "::1", "0.0.0.0",
    "metadata.google.internal", "instance-data",
    "169.254.169.254"
}

def is_ip_private_or_restricted(ip_str: str) -> bool:
    """Checks whether an IP address belongs to loopback, private, link-local or reserved ranges."""
    try:
        ip = ipaddress.ip_address(ip_str)
        return (
            ip.is_private or
            ip.is_loopback or
            ip.is_link_local or
            ip.is_multicast or
            ip.is_reserved or
            ip.is_unspecified
        )
    except ValueError:
        return True

def validate_public_url(url: str) -> Tuple[bool, str, str, List[str]]:
    """
    Validates a website or endpoint URL against SSRF vulnerabilities.
    Returns: (is_safe, error_message, normalized_url, resolved_ips)
    """
    if not url:
        return False, "URL cannot be empty.", "", []

    url = url.strip()
    if not (url.startswith("http://") or url.startswith("https://")):
        url = "https://" + url

    try:
        parsed = urllib.parse.urlparse(url)
    except Exception as e:
        return False, f"Malformed URL syntax: {e}", "", []

    if parsed.scheme not in ("http", "https"):
        return False, f"Unsupported URL protocol '{parsed.scheme}'. Only HTTP and HTTPS are permitted.", "", []

    hostname = parsed.hostname
    if not hostname:
        return False, "URL must contain a valid domain name or hostname.", "", []

    hostname_lower = hostname.lower().strip()

    # Check blocked keywords and local suffixes
    if hostname_lower in BLOCKED_HOSTNAMES:
        return False, f"Access to '{hostname}' is blocked by SSRF perimeter protection.", "", []

    if hostname_lower.endswith(".local") or hostname_lower.endswith(".internal") or hostname_lower.endswith(".localhost"):
        return False, f"Internal TLD destinations are blocked by SSRF policy.", "", []

    # Check literal IP in hostname
    try:
        ip = ipaddress.ip_address(hostname_lower)
        if is_ip_private_or_restricted(str(ip)):
            return False, f"Target IP '{ip}' is in a private, loopback, or reserved range.", "", []
    except ValueError:
        # Hostname is a domain name, proceed to DNS resolution
        pass

    # Resolve hostname to verify destination addresses
    try:
        addr_info = socket.getaddrinfo(hostname_lower, None, socket.AF_UNSPEC, socket.SOCK_STREAM)
        resolved_ips = list(set([item[4][0] for item in addr_info]))
    except socket.gaierror:
        # Domain cannot be resolved via DNS
        return False, f"DNS resolution failed for '{hostname_lower}'. Domain does not exist or has no A/AAAA records.", "", []
    except Exception as e:
        return False, f"DNS check error: {e}", "", []

    if not resolved_ips:
        return False, f"No IP addresses could be resolved for '{hostname_lower}'.", "", []

    # Verify EVERY resolved IP against private and restricted ranges (prevents DNS rebinding attacks)
    for ip_addr in resolved_ips:
        if is_ip_private_or_restricted(ip_addr):
            return False, f"SSRF Security Violation: '{hostname_lower}' resolves to private/internal IP {ip_addr}.", "", []

    # Block metadata IP explicitly
    if "169.254.169.254" in resolved_ips:
        return False, "Target destination resolves to cloud instance metadata service.", "", []

    normalized_url = parsed.geturl()
    return True, "URL is safe and verified.", normalized_url, resolved_ips
