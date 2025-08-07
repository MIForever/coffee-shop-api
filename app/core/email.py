import logging
import smtplib
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart
from typing import Dict, Any
from jinja2 import Environment, BaseLoader

from app.core.config import settings

logger = logging.getLogger(__name__)


class EmailService:
    def __init__(self):
        self.smtp_host = settings.SMTP_HOST
        self.smtp_port = settings.SMTP_PORT
        self.smtp_user = settings.SMTP_USER
        self.smtp_password = settings.SMTP_PASSWORD
        self.smtp_tls = settings.SMTP_TLS
        self.from_email = settings.SMTP_FROM_EMAIL
        self.template_env = Environment(loader=BaseLoader())
    
    async def send_email(
        self,
        to_email: str,
        subject: str,
        template_name: str,
        context: Dict[str, Any]
    ) -> bool:
        try:
            if template_name == "email_verification.html":
                html_content = self._get_verification_template(context)
            else:
                html_content = self._get_default_template(subject, context)
            
            msg = MIMEMultipart('alternative')
            msg['Subject'] = subject
            msg['From'] = self.from_email
            msg['To'] = to_email
            
            html_part = MIMEText(html_content, 'html')
            msg.attach(html_part)
            
            if settings.EMAIL_VERIFICATION_ENABLED and self.smtp_user and self.smtp_password:
                await self._send_smtp_email(msg)
            else:
                logger.info(f"Mock email sent to {to_email}")
                logger.info(f"URL: {context.get('verification_url', 'N/A')}")
            
            return True
            
        except Exception as e:
            logger.error(f"Failed to send email to {to_email}: {e}")
            return False
    
    async def _send_smtp_email(self, msg: MIMEMultipart) -> None:
        try:
            with smtplib.SMTP(self.smtp_host, self.smtp_port) as server:
                if self.smtp_tls:
                    server.starttls()
                
                if self.smtp_user and self.smtp_password:
                    server.login(self.smtp_user, self.smtp_password)
                
                server.send_message(msg)
                logger.info("Email sent via SMTP")
                
        except Exception as e:
            logger.error(f"SMTP error: {e}")
            raise
    
    def _get_verification_template(self, context: Dict[str, Any]) -> str:
        verification_url = context.get('verification_url', '#')
        
        return f"""
        <!DOCTYPE html>
        <html>
        <head>
            <meta charset="utf-8">
            <title>Verify Your Email</title>
            <style>
                body {{ font-family: Arial, sans-serif; line-height: 1.6; color: #333; }}
                .container {{ max-width: 600px; margin: 0 auto; padding: 20px; }}
                .header {{ background-color: #4CAF50; color: white; padding: 20px; text-align: center; }}
                .content {{ padding: 20px; background-color: #f9f9f9; }}
                .button {{ display: inline-block; padding: 12px 24px; background-color: #4CAF50; color: white; text-decoration: none; border-radius: 4px; }}
                .footer {{ text-align: center; padding: 20px; color: #666; font-size: 12px; }}
            </style>
        </head>
        <body>
            <div class="container">
                <div class="header">
                    <h1>Coffee Shop API</h1>
                </div>
                <div class="content">
                    <h2>Verify Your Email Address</h2>
                    <p>Thank you for registering with Coffee Shop API!</p>
                    <p>Click the button below to verify your email:</p>
                    <p style="text-align: center;">
                        <a href="{verification_url}" class="button">Verify Email</a>
                    </p>
                    <p>Or copy this link: {verification_url}</p>
                    <p>This link expires in 15 minutes.</p>
                </div>
                <div class="footer">
                    <p>If you didn't create an account, ignore this email.</p>
                </div>
            </div>
        </body>
        </html>
        """
    
    def _get_default_template(self, subject: str, context: Dict[str, Any]) -> str:
        return f"""
        <!DOCTYPE html>
        <html>
        <head>
            <meta charset="utf-8">
            <title>{subject}</title>
        </head>
        <body>
            <h1>{subject}</h1>
            <p>{context.get('message', 'No message provided')}</p>
        </body>
        </html>
        """


email_service = EmailService()


async def send_email(
    to_email: str,
    subject: str,
    template_name: str,
    context: Dict[str, Any]
) -> bool:
    return await email_service.send_email(to_email, subject, template_name, context)