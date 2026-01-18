"""
Email service for sending transactional emails via SendGrid.

Handles:
- Password reset emails
- Welcome emails (future)
- Report completion notifications (future)
"""

import os
import logging
from typing import Optional
from sendgrid import SendGridAPIClient
from sendgrid.helpers.mail import Mail, Email, To, Content

logger = logging.getLogger(__name__)

# Configuration
SENDGRID_API_KEY = os.getenv("SENDGRID_API_KEY")
EMAIL_FROM = os.getenv("EMAIL_FROM", "noreply@propertyvaluation.com")
FRONTEND_URL = os.getenv("FRONTEND_URL", "http://localhost:5173")


class EmailService:
    """Service for sending emails via SendGrid."""

    @staticmethod
    def is_configured() -> bool:
        """Check if email service is properly configured."""
        return bool(SENDGRID_API_KEY)

    @staticmethod
    def send_email(
        to_email: str,
        subject: str,
        html_content: str,
        plain_content: Optional[str] = None
    ) -> bool:
        """
        Send an email via SendGrid.

        Args:
            to_email: Recipient email address
            subject: Email subject
            html_content: HTML body content
            plain_content: Optional plain text content

        Returns:
            True if sent successfully, False otherwise
        """
        if not EmailService.is_configured():
            logger.warning("SendGrid not configured - email not sent")
            return False

        try:
            message = Mail(
                from_email=Email(EMAIL_FROM),
                to_emails=To(to_email),
                subject=subject,
                html_content=Content("text/html", html_content)
            )

            if plain_content:
                message.add_content(Content("text/plain", plain_content))

            sg = SendGridAPIClient(SENDGRID_API_KEY)
            response = sg.send(message)

            if response.status_code in [200, 201, 202]:
                logger.info(f"Email sent successfully to {to_email}")
                return True
            else:
                logger.error(f"Email send failed with status {response.status_code}")
                return False

        except Exception as e:
            logger.exception(f"Failed to send email to {to_email}: {e}")
            return False

    @staticmethod
    def send_password_reset_email(email: str, reset_token: str) -> bool:
        """
        Send password reset email.

        Args:
            email: User's email address
            reset_token: Password reset token

        Returns:
            True if sent successfully, False otherwise
        """
        reset_url = f"{FRONTEND_URL}/reset-password?token={reset_token}"

        subject = "Reset Your Password - Property Valuation Platform"

        html_content = f"""
        <!DOCTYPE html>
        <html>
        <head>
            <style>
                body {{
                    font-family: Arial, sans-serif;
                    line-height: 1.6;
                    color: #333;
                }}
                .container {{
                    max-width: 600px;
                    margin: 0 auto;
                    padding: 20px;
                }}
                .header {{
                    background-color: #2563eb;
                    color: white;
                    padding: 20px;
                    text-align: center;
                }}
                .content {{
                    padding: 20px;
                    background-color: #f9fafb;
                }}
                .button {{
                    display: inline-block;
                    background-color: #2563eb;
                    color: white;
                    padding: 12px 24px;
                    text-decoration: none;
                    border-radius: 6px;
                    margin: 20px 0;
                }}
                .footer {{
                    padding: 20px;
                    text-align: center;
                    font-size: 12px;
                    color: #666;
                }}
                .warning {{
                    background-color: #fef3c7;
                    border: 1px solid #f59e0b;
                    padding: 10px;
                    border-radius: 4px;
                    margin-top: 20px;
                }}
            </style>
        </head>
        <body>
            <div class="container">
                <div class="header">
                    <h1>Password Reset Request</h1>
                </div>
                <div class="content">
                    <p>Hello,</p>
                    <p>We received a request to reset the password for your Property Valuation Platform account associated with this email address.</p>
                    <p>Click the button below to reset your password:</p>
                    <p style="text-align: center;">
                        <a href="{reset_url}" class="button">Reset Password</a>
                    </p>
                    <p>Or copy and paste this link into your browser:</p>
                    <p style="word-break: break-all; font-size: 14px; color: #666;">
                        {reset_url}
                    </p>
                    <div class="warning">
                        <strong>Note:</strong> This link will expire in 1 hour. If you did not request a password reset, you can safely ignore this email.
                    </div>
                </div>
                <div class="footer">
                    <p>This is an automated message from Property Valuation Platform.</p>
                    <p>Please do not reply to this email.</p>
                </div>
            </div>
        </body>
        </html>
        """

        plain_content = f"""
        Password Reset Request

        Hello,

        We received a request to reset the password for your Property Valuation Platform account.

        Click here to reset your password: {reset_url}

        This link will expire in 1 hour.

        If you did not request a password reset, you can safely ignore this email.

        ---
        Property Valuation Platform
        """

        return EmailService.send_email(email, subject, html_content, plain_content)

    @staticmethod
    def send_welcome_email(email: str, full_name: str) -> bool:
        """
        Send welcome email to new users.

        Args:
            email: User's email address
            full_name: User's full name

        Returns:
            True if sent successfully, False otherwise
        """
        login_url = f"{FRONTEND_URL}/login"

        subject = "Welcome to Property Valuation Platform"

        html_content = f"""
        <!DOCTYPE html>
        <html>
        <head>
            <style>
                body {{
                    font-family: Arial, sans-serif;
                    line-height: 1.6;
                    color: #333;
                }}
                .container {{
                    max-width: 600px;
                    margin: 0 auto;
                    padding: 20px;
                }}
                .header {{
                    background-color: #2563eb;
                    color: white;
                    padding: 20px;
                    text-align: center;
                }}
                .content {{
                    padding: 20px;
                    background-color: #f9fafb;
                }}
                .button {{
                    display: inline-block;
                    background-color: #2563eb;
                    color: white;
                    padding: 12px 24px;
                    text-decoration: none;
                    border-radius: 6px;
                    margin: 20px 0;
                }}
                .footer {{
                    padding: 20px;
                    text-align: center;
                    font-size: 12px;
                    color: #666;
                }}
            </style>
        </head>
        <body>
            <div class="container">
                <div class="header">
                    <h1>Welcome!</h1>
                </div>
                <div class="content">
                    <p>Hello {full_name},</p>
                    <p>Welcome to the Property Valuation Platform! Your account has been created successfully.</p>
                    <p>You can now log in and start creating professional valuation reports.</p>
                    <p style="text-align: center;">
                        <a href="{login_url}" class="button">Log In Now</a>
                    </p>
                    <p>If you have any questions, please don't hesitate to reach out to our support team.</p>
                </div>
                <div class="footer">
                    <p>Property Valuation Platform</p>
                </div>
            </div>
        </body>
        </html>
        """

        return EmailService.send_email(email, subject, html_content)


# Export
__all__ = ['EmailService']
