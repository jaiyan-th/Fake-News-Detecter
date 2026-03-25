"""
Security validation and sanitization service
"""

import re
import html
import urllib.parse
from typing import Dict, Any, Optional, List
from urllib.parse import urlparse
import ipaddress

class SecurityValidator:
    """Service for input validation and sanitization"""
    
    def __init__(self):
        """Initialize security validator with security rules"""
        
        # Allowed URL schemes
        self.allowed_schemes = {'http', 'https'}
        
        # Blocked domains (malicious/suspicious)
        self.blocked_domains = {
            'localhost', '127.0.0.1', '0.0.0.0', '::1',
            'example.com', 'test.com', 'invalid.com'
        }
        
        # Allowed TLDs (top-level domains)
        self.allowed_tlds = {
            'com', 'org', 'net', 'edu', 'gov', 'mil', 'int',
            'co.uk', 'co.in', 'co.au', 'ca', 'de', 'fr', 'jp',
            'in', 'uk', 'au', 'br', 'cn', 'ru', 'it', 'es'
        }
        
        # SQL injection patterns
        self.sql_injection_patterns = [
            r"(\b(SELECT|INSERT|UPDATE|DELETE|DROP|CREATE|ALTER|EXEC|UNION)\b)",
            r"(\b(OR|AND)\s+\d+\s*=\s*\d+)",
            r"(\b(OR|AND)\s+['\"]?\w+['\"]?\s*=\s*['\"]?\w+['\"]?)",
            r"(--|#|/\*|\*/)",
            r"(\bxp_\w+)",
            r"(\bsp_\w+)",
            r"(\bEXEC\s*\()",
            r"(CHAR\s*\(\s*\d+\s*\))",
            r"(0x[0-9A-Fa-f]+)"
        ]
        
        # XSS patterns
        self.xss_patterns = [
            r"<script[^>]*>.*?</script>",
            r"javascript:",
            r"vbscript:",
            r"onload\s*=",
            r"onerror\s*=",
            r"onclick\s*=",
            r"onmouseover\s*=",
            r"<iframe[^>]*>",
            r"<object[^>]*>",
            r"<embed[^>]*>",
            r"<link[^>]*>",
            r"<meta[^>]*>"
        ]
        
        # Compile patterns for performance
        self.sql_patterns_compiled = [re.compile(pattern, re.IGNORECASE) for pattern in self.sql_injection_patterns]
        self.xss_patterns_compiled = [re.compile(pattern, re.IGNORECASE) for pattern in self.xss_patterns]
    
    def validate_url(self, url: str) -> Dict[str, Any]:
        """
        Comprehensive URL validation with security checks
        
        Returns:
            Dict with validation result and details
        """
        result = {
            'valid': False,
            'sanitized_url': None,
            'errors': [],
            'warnings': []
        }
        
        # Basic type and format validation
        if not url or not isinstance(url, str):
            result['errors'].append("URL must be a non-empty string")
            return result
        
        # Sanitize URL
        sanitized_url = self.sanitize_url(url)
        result['sanitized_url'] = sanitized_url
        
        try:
            # Parse URL
            parsed = urlparse(sanitized_url)
            
            # Validate scheme
            if parsed.scheme not in self.allowed_schemes:
                result['errors'].append(f"Invalid scheme '{parsed.scheme}'. Only HTTP/HTTPS allowed")
                return result
            
            # Validate domain exists
            if not parsed.netloc:
                result['errors'].append("Missing domain name")
                return result
            
            # Extract domain and port
            domain_with_port = parsed.netloc.lower()
            domain = domain_with_port.split(':')[0]
            
            # Check for blocked domains
            if domain in self.blocked_domains:
                result['errors'].append(f"Domain '{domain}' is blocked")
                return result
            
            # Validate domain format
            if not self._is_valid_domain(domain):
                result['errors'].append(f"Invalid domain format: '{domain}'")
                return result
            
            # Check for private/local IP addresses
            if self._is_private_ip(domain):
                result['errors'].append(f"Private/local IP addresses not allowed: '{domain}'")
                return result
            
            # Validate TLD
            tld_warning = self._validate_tld(domain)
            if tld_warning:
                result['warnings'].append(tld_warning)
            
            # Check URL length
            if len(sanitized_url) > 2048:
                result['errors'].append("URL too long (max 2048 characters)")
                return result
            
            # Check for suspicious patterns
            suspicious_patterns = self._check_suspicious_url_patterns(sanitized_url)
            if suspicious_patterns:
                result['warnings'].extend(suspicious_patterns)
            
            result['valid'] = True
            return result
            
        except Exception as e:
            result['errors'].append(f"URL parsing error: {str(e)}")
            return result
    
    def sanitize_url(self, url: str) -> str:
        """Sanitize URL by removing dangerous characters and normalizing"""
        if not url:
            return ""
        
        # Strip whitespace
        url = url.strip()
        
        # Remove null bytes and control characters
        url = ''.join(char for char in url if ord(char) >= 32)
        
        # URL encode any remaining dangerous characters
        # But preserve valid URL characters
        safe_chars = "ABCDEFGHIJKLMNOPQRSTUVWXYZabcdefghijklmnopqrstuvwxyz0123456789-._~:/?#[]@!$&'()*+,;="
        sanitized = ''.join(char if char in safe_chars else urllib.parse.quote(char) for char in url)
        
        return sanitized
    
    def sanitize_text_input(self, text: str, max_length: int = 10000) -> str:
        """Sanitize text input to prevent XSS and injection attacks"""
        if not text or not isinstance(text, str):
            return ""
        
        # Limit length
        text = text[:max_length]
        
        # HTML escape
        text = html.escape(text)
        
        # Remove null bytes and control characters (except newlines and tabs)
        text = ''.join(char for char in text if ord(char) >= 32 or char in '\n\t\r')
        
        # Remove potential XSS patterns
        for pattern in self.xss_patterns_compiled:
            text = pattern.sub('', text)
        
        return text.strip()
    
    def validate_json_input(self, data: Dict[str, Any]) -> Dict[str, Any]:
        """Validate and sanitize JSON input"""
        result = {
            'valid': False,
            'sanitized_data': {},
            'errors': [],
            'warnings': []
        }
        
        if not isinstance(data, dict):
            result['errors'].append("Input must be a JSON object")
            return result
        
        # Check for required fields
        if 'url' not in data:
            result['errors'].append("Missing required field: 'url'")
            return result
        
        # Validate and sanitize URL
        url_validation = self.validate_url(data['url'])
        if not url_validation['valid']:
            result['errors'].extend(url_validation['errors'])
            result['warnings'].extend(url_validation['warnings'])
            return result
        
        result['sanitized_data']['url'] = url_validation['sanitized_url']
        
        # Check for unexpected fields
        allowed_fields = {'url'}
        unexpected_fields = set(data.keys()) - allowed_fields
        if unexpected_fields:
            result['warnings'].append(f"Unexpected fields ignored: {', '.join(unexpected_fields)}")
        
        # Check for SQL injection patterns in all string values
        for key, value in data.items():
            if isinstance(value, str):
                if self._contains_sql_injection(value):
                    result['errors'].append(f"Potential SQL injection detected in field '{key}'")
                    return result
        
        result['valid'] = True
        return result
    
    def _is_valid_domain(self, domain: str) -> bool:
        """Validate domain name format"""
        if not domain or len(domain) > 253:
            return False
        
        # Domain pattern: allows letters, numbers, hyphens, and dots
        domain_pattern = re.compile(
            r'^[a-zA-Z0-9]([a-zA-Z0-9\-]{0,61}[a-zA-Z0-9])?(\.[a-zA-Z0-9]([a-zA-Z0-9\-]{0,61}[a-zA-Z0-9])?)*$'
        )
        
        return bool(domain_pattern.match(domain))
    
    def _is_private_ip(self, domain: str) -> bool:
        """Check if domain is a private/local IP address"""
        try:
            ip = ipaddress.ip_address(domain)
            return ip.is_private or ip.is_loopback or ip.is_link_local
        except ValueError:
            # Not an IP address, which is fine
            return False
    
    def _validate_tld(self, domain: str) -> Optional[str]:
        """Validate top-level domain"""
        parts = domain.split('.')
        if len(parts) < 2:
            return "Domain must have a valid TLD"
        
        # Check for common TLDs
        tld = '.'.join(parts[-2:]) if len(parts) >= 2 and len(parts[-2]) <= 3 else parts[-1]
        
        if tld not in self.allowed_tlds and parts[-1] not in self.allowed_tlds:
            return f"Uncommon TLD '{parts[-1]}' - proceed with caution"
        
        return None
    
    def _check_suspicious_url_patterns(self, url: str) -> List[str]:
        """Check for suspicious URL patterns"""
        warnings = []
        
        # Check for URL shorteners (could hide malicious links)
        shortener_domains = ['bit.ly', 'tinyurl.com', 't.co', 'goo.gl', 'ow.ly', 'short.link']
        parsed = urlparse(url)
        if any(shortener in parsed.netloc for shortener in shortener_domains):
            warnings.append("URL shortener detected - verify destination")
        
        # Check for suspicious patterns
        if re.search(r'\d+\.\d+\.\d+\.\d+', url):
            warnings.append("IP address in URL - verify legitimacy")
        
        if len(parsed.path) > 100:
            warnings.append("Very long URL path - verify legitimacy")
        
        if parsed.path.count('/') > 10:
            warnings.append("Deeply nested URL path - verify legitimacy")
        
        return warnings
    
    def _contains_sql_injection(self, text: str) -> bool:
        """Check if text contains SQL injection patterns"""
        for pattern in self.sql_patterns_compiled:
            if pattern.search(text):
                return True
        return False
    
    def get_security_headers(self) -> Dict[str, str]:
        """Get recommended security headers for HTTP responses"""
        return {
            'X-Content-Type-Options': 'nosniff',
            'X-Frame-Options': 'DENY',
            'X-XSS-Protection': '1; mode=block',
            'Strict-Transport-Security': 'max-age=31536000; includeSubDomains',
            'Content-Security-Policy': "default-src 'self'",
            'Referrer-Policy': 'strict-origin-when-cross-origin'
        }

# Global security validator instance
security_validator = SecurityValidator()