"""
Rate limiting service for API protection
"""

import time
import threading
from typing import Dict, Optional, Tuple
from collections import defaultdict, deque
from datetime import datetime, timedelta

class RateLimiter:
    """Rate limiting service to prevent abuse and DoS attacks"""
    
    def __init__(self):
        """Initialize rate limiter with default limits"""
        self.requests = defaultdict(deque)  # IP -> deque of request timestamps
        self.blocked_ips = {}  # IP -> block_until_timestamp
        self.lock = threading.Lock()
        
        # Rate limiting configuration
        self.limits = {
            'requests_per_minute': 30,      # 30 requests per minute per IP
            'requests_per_hour': 200,       # 200 requests per hour per IP
            'burst_limit': 10,              # Max 10 requests in 10 seconds
            'burst_window': 10,             # 10 second burst window
            'block_duration': 300,          # 5 minutes block for violations
            'max_violations': 3             # Block after 3 violations
        }
        
        # Violation tracking
        self.violations = defaultdict(int)  # IP -> violation count
        
        # Cleanup thread
        self.cleanup_interval = 300  # 5 minutes
        self.last_cleanup = time.time()
    
    def is_allowed(self, client_ip: str) -> Tuple[bool, Dict[str, any]]:
        """
        Check if request from client IP is allowed
        
        Returns:
            Tuple of (allowed: bool, info: dict)
        """
        with self.lock:
            current_time = time.time()
            
            # Cleanup old data periodically
            if current_time - self.last_cleanup > self.cleanup_interval:
                self._cleanup_old_data(current_time)
                self.last_cleanup = current_time
            
            # Check if IP is currently blocked
            if client_ip in self.blocked_ips:
                if current_time < self.blocked_ips[client_ip]:
                    remaining_time = int(self.blocked_ips[client_ip] - current_time)
                    return False, {
                        'reason': 'ip_blocked',
                        'message': f'IP blocked for {remaining_time} seconds due to rate limit violations',
                        'retry_after': remaining_time
                    }
                else:
                    # Block expired, remove it
                    del self.blocked_ips[client_ip]
            
            # Get request history for this IP
            request_times = self.requests[client_ip]
            
            # Check burst limit (requests in last burst_window seconds)
            burst_cutoff = current_time - self.limits['burst_window']
            burst_requests = sum(1 for req_time in request_times if req_time > burst_cutoff)
            
            if burst_requests >= self.limits['burst_limit']:
                self._handle_violation(client_ip, current_time, 'burst_limit')
                return False, {
                    'reason': 'burst_limit_exceeded',
                    'message': f'Too many requests in {self.limits["burst_window"]} seconds',
                    'retry_after': self.limits['burst_window']
                }
            
            # Check per-minute limit
            minute_cutoff = current_time - 60
            minute_requests = sum(1 for req_time in request_times if req_time > minute_cutoff)
            
            if minute_requests >= self.limits['requests_per_minute']:
                self._handle_violation(client_ip, current_time, 'minute_limit')
                return False, {
                    'reason': 'minute_limit_exceeded',
                    'message': f'Too many requests per minute',
                    'retry_after': 60
                }
            
            # Check per-hour limit
            hour_cutoff = current_time - 3600
            hour_requests = sum(1 for req_time in request_times if req_time > hour_cutoff)
            
            if hour_requests >= self.limits['requests_per_hour']:
                self._handle_violation(client_ip, current_time, 'hour_limit')
                return False, {
                    'reason': 'hour_limit_exceeded',
                    'message': f'Too many requests per hour',
                    'retry_after': 3600
                }
            
            # Request is allowed, record it
            request_times.append(current_time)
            
            # Calculate remaining limits for response headers
            remaining_info = {
                'requests_remaining_minute': self.limits['requests_per_minute'] - minute_requests - 1,
                'requests_remaining_hour': self.limits['requests_per_hour'] - hour_requests - 1,
                'reset_time_minute': int(current_time + 60),
                'reset_time_hour': int(current_time + 3600)
            }
            
            return True, remaining_info
    
    def _handle_violation(self, client_ip: str, current_time: float, violation_type: str):
        """Handle rate limit violation"""
        self.violations[client_ip] += 1
        
        # Block IP if too many violations
        if self.violations[client_ip] >= self.limits['max_violations']:
            block_until = current_time + self.limits['block_duration']
            self.blocked_ips[client_ip] = block_until
            
            # Reset violation count after blocking
            self.violations[client_ip] = 0
    
    def _cleanup_old_data(self, current_time: float):
        """Clean up old request data to prevent memory buildup"""
        hour_cutoff = current_time - 3600
        
        # Clean up request histories
        for ip in list(self.requests.keys()):
            request_times = self.requests[ip]
            
            # Remove old requests
            while request_times and request_times[0] < hour_cutoff:
                request_times.popleft()
            
            # Remove empty entries
            if not request_times:
                del self.requests[ip]
        
        # Clean up expired blocks
        for ip in list(self.blocked_ips.keys()):
            if current_time >= self.blocked_ips[ip]:
                del self.blocked_ips[ip]
        
        # Clean up old violations (reset after 24 hours)
        violation_cutoff = current_time - 86400  # 24 hours
        for ip in list(self.violations.keys()):
            # This is a simple approach - in production, you'd want more sophisticated violation tracking
            if len(self.requests.get(ip, [])) == 0:
                # No recent requests, reset violations
                del self.violations[ip]
    
    def get_rate_limit_headers(self, client_ip: str) -> Dict[str, str]:
        """Get rate limit headers for response"""
        with self.lock:
            current_time = time.time()
            request_times = self.requests.get(client_ip, deque())
            
            # Calculate current usage
            minute_cutoff = current_time - 60
            hour_cutoff = current_time - 3600
            
            minute_requests = sum(1 for req_time in request_times if req_time > minute_cutoff)
            hour_requests = sum(1 for req_time in request_times if req_time > hour_cutoff)
            
            return {
                'X-RateLimit-Limit-Minute': str(self.limits['requests_per_minute']),
                'X-RateLimit-Remaining-Minute': str(max(0, self.limits['requests_per_minute'] - minute_requests)),
                'X-RateLimit-Reset-Minute': str(int(current_time + 60)),
                'X-RateLimit-Limit-Hour': str(self.limits['requests_per_hour']),
                'X-RateLimit-Remaining-Hour': str(max(0, self.limits['requests_per_hour'] - hour_requests)),
                'X-RateLimit-Reset-Hour': str(int(current_time + 3600))
            }
    
    def get_stats(self) -> Dict[str, any]:
        """Get rate limiter statistics"""
        with self.lock:
            return {
                'active_ips': len(self.requests),
                'blocked_ips': len(self.blocked_ips),
                'total_violations': sum(self.violations.values()),
                'limits': self.limits.copy()
            }

# Global rate limiter instance
rate_limiter = RateLimiter()