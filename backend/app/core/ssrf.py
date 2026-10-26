import ipaddress
import socket
from urllib.parse import urlparse
from typing import Tuple, Optional


# Disallowed schemes and blocked hostname keywords
BLOCKED_HOSTNAMES = {
    "localhost", "127.0.0.1", "0.0.0.0", "::1", "metadata.google.internal",
    "instance-data", "metadata"
}

ALLOWED_SCHEMES = {"http", "https"}


def is_safe_ip(ip_str: str) -> Tuple[bool, str]:
    """
    Checks if an IP address string is safe from SSRF.
    Returns (is_safe, error_message).
    """
    try:
        ip = ipaddress.ip_address(ip_str)
    except ValueError:
        return False, f"Invalid IP address format: {ip_str}"

    if ip.is_loopback:
        return False, f"Access to loopback IP {ip_str} is forbidden."
    if ip.is_private:
        return False, f"Access to private RFC1918 / RFC4193 IP {ip_str} is forbidden."
    if ip.is_link_local:
        return False, f"Access to link-local IP {ip_str} (e.g. cloud metadata) is forbidden."
    if ip.is_multicast:
        return False, f"Access to multicast IP {ip_str} is forbidden."
    if ip.is_reserved:
        return False, f"Access to reserved IP {ip_str} is forbidden."
    if ip.is_unspecified:
        return False, f"Access to unspecified IP {ip_str} is forbidden."
    
    # Specific cloud metadata checks
    if str(ip) in {"169.254.169.254", "100.100.100.200"}:
        return False, "Access to cloud instance metadata service is forbidden."

    return True, "IP is safe"


def validate_url_for_ssrf(url: str) -> Tuple[bool, Optional[str], Optional[str]]:
    """
    Validates a URL before making any external HTTP request.
    Returns: (is_safe, error_reason, resolved_ip)
    """
    if not url:
        return False, "URL cannot be empty.", None

    try:
        parsed = urlparse(url.strip())
    except Exception as e:
        return False, f"Malformed URL: {str(e)}", None

    scheme = (parsed.scheme or "").lower()
    if scheme not in ALLOWED_SCHEMES:
        return False, f"Unsupported URL scheme '{scheme}'. Only http and https are permitted.", None

    hostname = (parsed.hostname or "").lower().strip()
    if not hostname:
        return False, "URL has no valid hostname.", None

    if hostname in BLOCKED_HOSTNAMES:
        return False, f"Host '{hostname}' is explicitly blocked.", None

    # Check if hostname directly represents an IP
    try:
        ip = ipaddress.ip_address(hostname)
        is_safe, reason = is_safe_ip(str(ip))
        if not is_safe:
            return False, reason, str(ip)
        return True, None, str(ip)
    except ValueError:
        # Not a direct IP string; resolve DNS
        pass

    try:
        # Resolve hostname via DNS
        addr_info = socket.getaddrinfo(hostname, None, socket.AF_UNSPEC, socket.SOCK_STREAM)
        if not addr_info:
            return False, f"Failed to resolve DNS for hostname '{hostname}'.", None
        
        # Verify all resolved IPs
        for item in addr_info:
            resolved_ip = item[4][0]
            is_safe, reason = is_safe_ip(resolved_ip)
            if not is_safe:
                return False, f"Host '{hostname}' resolved to prohibited address ({reason})", resolved_ip
        
        primary_ip = addr_info[0][4][0]
        return True, None, primary_ip
    except socket.gaierror as e:
        return False, f"DNS resolution failed for '{hostname}': {str(e)}", None
    except Exception as e:
        return False, f"Validation error for '{hostname}': {str(e)}", None
