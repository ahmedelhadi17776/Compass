"""Email service for sending notifications."""
import os
from typing import List, Optional
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart
import smtplib
from jinja2 import Environment, FileSystemLoader
from pathlib import Path
from fastapi import HTTPException, status

class EmailService:
    def __init__(self):
        self.smtp_server = os.getenv("SMTP_SERVER", "smtp.gmail.com")
        self.smtp_port = int(os.getenv("SMTP_PORT", "587"))
        self.smtp_username = os.getenv("SMTP_USERNAME")
        self.smtp_password = os.getenv("SMTP_PASSWORD")
        self.from_email = os.getenv("FROM_EMAIL")
        self.frontend_url = os.getenv("FRONTEND_URL", "http://localhost:3000")
        
        if not all([self.smtp_username, self.smtp_password, self.from_email]):
            raise ValueError("Missing required email configuration")
        
        # Set up Jinja2 template environment
        template_dir = Path(__file__).parent / "templates"
        self.jinja_env = Environment(
            loader=FileSystemLoader(str(template_dir)),
            autoescape=True
        )
    
    async def send_email(
        self,
        to_email: str,
        subject: str,
        template_name: str,
        template_data: dict,
        cc: Optional[List[str]] = None,
        bcc: Optional[List[str]] = None
    ) -> bool:
        """
        Send an email using a template.
        
        Args:
            to_email: Recipient email address
            subject: Email subject
            template_name: Name of the template file (e.g., 'reset_password.html')
            template_data: Dictionary of data to pass to the template
            cc: List of CC recipients
            bcc: List of BCC recipients
            
        Returns:
            bool: True if email was sent successfully
            
        Raises:
            HTTPException: If email sending fails
        """
        try:
            # Create message
            msg = MIMEMultipart()
            msg["From"] = self.from_email
            msg["To"] = to_email
            msg["Subject"] = subject
            
            if cc:
                msg["Cc"] = ", ".join(cc)
            if bcc:
                msg["Bcc"] = ", ".join(bcc)
            
            # Render template
            template = self.jinja_env.get_template(template_name)
            html_content = template.render(**template_data)
            
            # Attach HTML content
            msg.attach(MIMEText(html_content, "html"))
            
            # Create SMTP connection
            with smtplib.SMTP(self.smtp_server, self.smtp_port) as server:
                server.starttls()
                server.login(self.smtp_username, self.smtp_password)
                
                # Prepare recipients
                recipients = [to_email]
                if cc:
                    recipients.extend(cc)
                if bcc:
                    recipients.extend(bcc)
                
                # Send email
                server.sendmail(self.from_email, recipients, msg.as_string())
                
            return True
            
        except Exception as e:
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail=f"Failed to send email: {str(e)}"
            )
    
    async def send_verification_email(self, to_email: str, verification_token: str) -> bool:
        """Send email verification link."""
        verification_url = f"{self.frontend_url}/verify-email"
        subject = "Verify Your Email Address"
        template_data = {
            "verification_url": f"{verification_url}?token={verification_token}",
            "expiry_hours": 24
        }
        return await self.send_email(
            to_email=to_email,
            subject=subject,
            template_name="email_verification.html",
            template_data=template_data
        )
    
    async def send_password_reset_email(self, to_email: str, reset_token: str) -> bool:
        """Send password reset email."""
        reset_url = f"{self.frontend_url}/reset-password"
        subject = "Password Reset Request"
        template_data = {
            "reset_url": f"{reset_url}?token={reset_token}",
            "expiry_hours": 1
        }
        return await self.send_email(
            to_email=to_email,
            subject=subject,
            template_name="password_reset.html",
            template_data=template_data
        )
    
    async def send_password_changed_notification(self, to_email: str) -> bool:
        """Send password changed notification."""
        subject = "Password Changed Successfully"
        template_data = {
            "support_email": self.from_email
        }
        return await self.send_email(
            to_email=to_email,
            subject=subject,
            template_name="password_changed.html",
            template_data=template_data
        )

# Create a global instance only if not in test mode
if os.getenv("ENVIRONMENT") != "test":
    email_service = EmailService()
else:
    email_service = None
