"""
Email notification service using SMTP
"""
import smtplib
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart
from datetime import datetime
from typing import Optional
import os
import logging

# Use standard logging instead of custom logger
logger = logging.getLogger('fake_news_detector.email')

class EmailService:
    """SMTP-based email notification service"""
    
    def __init__(self):
        self.smtp_host = os.getenv('SMTP_HOST', 'smtp.gmail.com')
        self.smtp_port = int(os.getenv('SMTP_PORT', '587'))
        self.username = os.getenv('SMTP_USERNAME', '')
        self.password = os.getenv('SMTP_PASSWORD', '')
        self.from_email = os.getenv('SMTP_FROM_EMAIL', self.username)
        self.use_tls = os.getenv('SMTP_USE_TLS', 'true').lower() == 'true'
        
        # Check if email is configured
        self.is_configured = bool(self.username and self.password)
        if not self.is_configured:
            logger.warning("Email service not configured - emails will not be sent")
    
    def send_welcome_email(self, user) -> bool:
        """
        Send welcome email to newly registered user
        Returns: True if sent successfully
        """
        if not self.is_configured:
            logger.info(f"Email not configured - skipping welcome email for {user.email}")
            return False
        
        subject = "Welcome to Fake News Detector!"
        body = f"""
        <html>
        <body>
            <h2>Welcome to Fake News Detector, {user.name}!</h2>
            <p>Your account was successfully created on {user.created_at.strftime('%Y-%m-%d %H:%M:%S')} UTC.</p>
            <p>You can now use our AI-powered tools to verify news articles, detect misinformation, and stay informed.</p>
            <p>Thank you for joining us in the fight against fake news!</p>
            <br>
            <p>Best regards,<br>The Fake News Detector Team</p>
        </body>
        </html>
        """
        
        return self._send_email(user.email, subject, body)
    
    def send_login_notification(self, user, login_time: datetime) -> bool:
        """
        Send login notification email
        Returns: True if sent successfully
        """
        if not self.is_configured:
            logger.info(f"Email not configured - skipping login notification for {user.email}")
            return False
        
        subject = "New Login to Your Fake News Detector Account"
        body = f"""
        <html>
        <body>
            <h2>Hello {user.name},</h2>
            <p>We detected a new login to your account at {login_time.strftime('%Y-%m-%d %H:%M:%S')} UTC.</p>
            <p>If this was you, no action is needed.</p>
            <p>If you did not log in, please secure your account immediately.</p>
            <br>
            <p>Best regards,<br>The Fake News Detector Team</p>
        </body>
        </html>
        """
        
        return self._send_email(user.email, subject, body)
    
    def send_password_change_notification(self, user) -> bool:
        """
        Send password change notification email
        Returns: True if sent successfully
        """
        if not self.is_configured:
            logger.info(f"Email not configured - skipping password change notification for {user.email}")
            return False
        
        subject = "Password Changed - Fake News Detector"
        body = f"""
        <html>
        <body>
            <h2>Hello {user.name},</h2>
            <p>Your password was successfully changed at {datetime.utcnow().strftime('%Y-%m-%d %H:%M:%S')} UTC.</p>
            <p>If you did not make this change, please contact support immediately.</p>
            <br>
            <p>Best regards,<br>The Fake News Detector Team</p>
        </body>
        </html>
        """
        
        return self._send_email(user.email, subject, body)
    
    def _send_email(self, to: str, subject: str, body: str) -> bool:
        """
        Internal method to send email via SMTP with TLS
        Logs errors but doesn't raise exceptions
        """
        try:
            msg = MIMEMultipart('alternative')
            msg['From'] = self.from_email
            msg['To'] = to
            msg['Subject'] = subject
            
            html_part = MIMEText(body, 'html')
            msg.attach(html_part)
            
            with smtplib.SMTP(self.smtp_host, self.smtp_port) as server:
                if self.use_tls:
                    server.starttls()
                server.login(self.username, self.password)
                server.send_message(msg)
            
            logger.info(f"Email sent successfully to {to}")
            return True
            
        except Exception as e:
            logger.error(f"Failed to send email to {to}: {str(e)}")
            return False

# Global instance
email_service = EmailService()
