import smtplib
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart
from typing import Optional, List
from app.core.config import settings
import logging
from jinja2 import Template

logger = logging.getLogger(__name__)


class EmailService:
    """Email service for sending emails"""
    
    @staticmethod
    def _get_smtp_connection():
        """Create SMTP connection"""
        try:
            if settings.MAIL_TLS:
                server = smtplib.SMTP(settings.MAIL_SERVER, settings.MAIL_PORT)
                server.starttls()
            else:
                server = smtplib.SMTP_SSL(settings.MAIL_SERVER, settings.MAIL_PORT)
            
            if settings.MAIL_USERNAME and settings.MAIL_PASSWORD:
                server.login(settings.MAIL_USERNAME, settings.MAIL_PASSWORD)
            
            return server
        except Exception as e:
            logger.error(f"Failed to connect to SMTP server: {e}")
            raise
    
    @staticmethod
    def send_email(
        to_email: str,
        subject: str,
        html_content: str,
        cc: Optional[List[str]] = None,
        bcc: Optional[List[str]] = None
    ) -> bool:
        """Send email"""
        try:
            message = MIMEMultipart("alternative")
            message["Subject"] = subject
            message["From"] = settings.MAIL_FROM
            message["To"] = to_email
            
            if cc:
                message["Cc"] = ", ".join(cc)
            
            # Attach HTML
            part = MIMEText(html_content, "html")
            message.attach(part)
            
            # Send
            server = EmailService._get_smtp_connection()
            recipients = [to_email]
            if cc:
                recipients.extend(cc)
            if bcc:
                recipients.extend(bcc)
            
            server.sendmail(settings.MAIL_FROM, recipients, message.as_string())
            server.quit()
            
            logger.info(f"Email sent to {to_email}")
            return True
        except Exception as e:
            logger.error(f"Failed to send email to {to_email}: {e}")
            return False
    
    @staticmethod
    def send_verification_email(email: str, user_id: int, token: str) -> bool:
        """Send email verification link"""
        verification_url = f"{settings.FRONTEND_URL}/verify-email?token={token}"
        
        html_content = f"""
        <html>
            <body>
                <h2>Verify Your Email Address</h2>
                <p>Thank you for registering! Click the link below to verify your email address.</p>
                <p><a href="{verification_url}">Verify Email</a></p>
                <p>This link will expire in 24 hours.</p>
                <p>If you didn't create this account, please ignore this email.</p>
            </body>
        </html>
        """
        
        return EmailService.send_email(
            to_email=email,
            subject="Verify Your Email Address",
            html_content=html_content
        )
    
    @staticmethod
    def send_password_reset_email(email: str, token: str) -> bool:
        """Send password reset email"""
        reset_url = f"{settings.FRONTEND_URL}/reset-password?token={token}"
        
        html_content = f"""
        <html>
            <body>
                <h2>Reset Your Password</h2>
                <p>We received a request to reset your password. Click the link below to proceed.</p>
                <p><a href="{reset_url}">Reset Password</a></p>
                <p>This link will expire in 1 hour.</p>
                <p>If you didn't request this, please ignore this email and your password will remain unchanged.</p>
            </body>
        </html>
        """
        
        return EmailService.send_email(
            to_email=email,
            subject="Password Reset Request",
            html_content=html_content
        )
    
    @staticmethod
    def send_password_changed_email(email: str, username: str) -> bool:
        """Send password changed notification"""
        html_content = f"""
        <html>
            <body>
                <h2>Password Changed</h2>
                <p>Hello {username},</p>
                <p>Your password has been successfully changed.</p>
                <p>If you didn't make this change, please contact support immediately.</p>
            </body>
        </html>
        """
        
        return EmailService.send_email(
            to_email=email,
            subject="Password Changed",
            html_content=html_content
        )
    
    @staticmethod
    def send_mfa_enabled_email(email: str, username: str) -> bool:
        """Send MFA enabled notification"""
        html_content = f"""
        <html>
            <body>
                <h2>Two-Factor Authentication Enabled</h2>
                <p>Hello {username},</p>
                <p>Two-factor authentication has been successfully enabled on your account.</p>
                <p>You will need to enter a code from your authenticator app every time you log in.</p>
                <p>If you didn't enable this, please contact support immediately.</p>
            </body>
        </html>
        """
        
        return EmailService.send_email(
            to_email=email,
            subject="Two-Factor Authentication Enabled",
            html_content=html_content
        )
    
    @staticmethod
    def send_login_alert_email(email: str, username: str, ip: str, user_agent: str) -> bool:
        """Send login alert email"""
        html_content = f"""
        <html>
            <body>
                <h2>New Login Detected</h2>
                <p>Hello {username},</p>
                <p>A new login to your account was detected:</p>
                <ul>
                    <li>IP Address: {ip}</li>
                    <li>Device: {user_agent}</li>
                </ul>
                <p>If this wasn't you, please change your password immediately.</p>
            </body>
        </html>
        """
        
        return EmailService.send_email(
            to_email=email,
            subject="New Login Detected",
            html_content=html_content
        )
    
    @staticmethod
    def send_account_locked_email(email: str, username: str) -> bool:
        """Send account locked notification"""
        html_content = f"""
        <html>
            <body>
                <h2>Account Locked</h2>
                <p>Hello {username},</p>
                <p>Your account has been locked due to multiple failed login attempts.</p>
                <p>Your account will be automatically unlocked in 30 minutes.</p>
                <p>If you have any questions, please contact support.</p>
            </body>
        </html>
        """
        
        return EmailService.send_email(
            to_email=email,
            subject="Account Locked",
            html_content=html_content
        )
