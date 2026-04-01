import aiosmtplib
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart
from typing import List, Dict
from app.config import settings
import logging

logger = logging.getLogger(__name__)


async def send_email(to_email: str, subject: str, body: str, html_body: str = None):
    """Send email using SMTP"""
    try:
        message = MIMEMultipart("alternative")
        message["From"] = settings.SMTP_FROM
        message["To"] = to_email
        message["Subject"] = subject

        # Add plain text part
        text_part = MIMEText(body, "plain")
        message.attach(text_part)

        # Add HTML part if provided
        if html_body:
            html_part = MIMEText(html_body, "html")
            message.attach(html_part)

        # Send email
        await aiosmtplib.send(
            message,
            hostname=settings.SMTP_HOST,
            port=settings.SMTP_PORT,
            username=settings.SMTP_USER,
            password=settings.SMTP_PASSWORD,
            use_tls=False,
        )
        logger.info(f"Email sent successfully to {to_email}")
        return True
    except Exception as e:
        logger.error(f"Failed to send email to {to_email}: {str(e)}")
        return False


async def send_verification_email(to_email: str, verification_token: str):
    """Send email verification link"""
    verification_link = f"http://localhost:3000/verify?token={verification_token}"
    
    subject = "Verify your NewsRadar account"
    body = f"""
    Welcome to NewsRadar!
    
    Please verify your email address by clicking the link below:
    {verification_link}
    
    This link will expire in 24 hours.
    
    If you didn't create an account, please ignore this email.
    """
    
    html_body = f"""
    <html>
        <body>
            <h2>Welcome to NewsRadar!</h2>
            <p>Please verify your email address by clicking the button below:</p>
            <p><a href="{verification_link}" style="background-color: #4CAF50; color: white; padding: 14px 20px; text-decoration: none; border-radius: 4px;">Verify Email</a></p>
            <p>Or copy this link: {verification_link}</p>
            <p>This link will expire in 24 hours.</p>
            <p>If you didn't create an account, please ignore this email.</p>
        </body>
    </html>
    """
    
    return await send_email(to_email, subject, body, html_body)


async def send_alert_notification(to_email: str, alert_name: str, statistics: Dict):
    """Send alert notification with processing statistics"""
    timestamp = statistics.get("timestamp", "")
    news_count = statistics.get("news_count", 0)
    sources = statistics.get("sources", [])
    
    subject = f"NewsRadar Alert: {alert_name} - {timestamp}"
    
    body = f"""
    Alert Update: {alert_name}
    Time: {timestamp}
    
    Processing Statistics:
    - News items found: {news_count}
    - Sources monitored: {len(sources)}
    
    News sources:
    {chr(10).join(f"- {source}" for source in sources)}
    
    Visit NewsRadar dashboard to see full details.
    """
    
    html_body = f"""
    <html>
        <body>
            <h2>Alert Update: {alert_name}</h2>
            <p><strong>Time:</strong> {timestamp}</p>
            
            <h3>Processing Statistics</h3>
            <ul>
                <li>News items found: {news_count}</li>
                <li>Sources monitored: {len(sources)}</li>
            </ul>
            
            <h3>News Sources</h3>
            <ul>
                {''.join(f"<li>{source}</li>" for source in sources)}
            </ul>
            
            <p><a href="http://localhost:3000/dashboard">Visit NewsRadar Dashboard</a></p>
        </body>
    </html>
    """
    
    return await send_email(to_email, subject, body, html_body)


async def send_password_reset_email(to_email: str, reset_token: str):
    """Send password reset link"""
    reset_link = f"http://localhost:3000/reset-password?token={reset_token}"
    
    subject = "Reset your NewsRadar password"
    body = f"""
    You requested to reset your NewsRadar password.
    
    Click the link below to reset your password:
    {reset_link}
    
    This link will expire in 1 hour.
    
    If you didn't request this, please ignore this email.
    """
    
    html_body = f"""
    <html>
        <body>
            <h2>Reset Your Password</h2>
            <p>You requested to reset your NewsRadar password.</p>
            <p><a href="{reset_link}" style="background-color: #2196F3; color: white; padding: 14px 20px; text-decoration: none; border-radius: 4px;">Reset Password</a></p>
            <p>Or copy this link: {reset_link}</p>
            <p>This link will expire in 1 hour.</p>
            <p>If you didn't request this, please ignore this email.</p>
        </body>
    </html>
    """
    
    return await send_email(to_email, subject, body, html_body)
