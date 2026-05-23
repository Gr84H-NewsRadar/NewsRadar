import logging
from email.mime.multipart import MIMEMultipart
from email.mime.text import MIMEText

import aiosmtplib

from app.config import settings

logger = logging.getLogger(__name__)


async def send_email(to_email: str, subject: str, body: str, html_body: str = None):
    """Envía un email usando SMTP"""
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
        smtp_kwargs = {
            "hostname": settings.SMTP_HOST,
            "port": settings.SMTP_PORT,
            "use_tls": False,
        }
        if settings.SMTP_USER and settings.SMTP_PASSWORD:
            smtp_kwargs["username"] = settings.SMTP_USER
            smtp_kwargs["password"] = settings.SMTP_PASSWORD

        await aiosmtplib.send(message, **smtp_kwargs)
        logger.info("Email sent successfully to %s", to_email)
        return True
    except Exception as e:  # pylint: disable=broad-except
        logger.error("Failed to send email to %s: %s", to_email, str(e))
        return False


async def send_verification_email(to_email: str, verification_token: str):
    """Envía email de verificación con token válido 24h"""
    verification_link = (
        f"http://localhost:8000/api/v1/auth/verify?token={verification_token}"
    )

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


async def send_cycle_summary(
    to_email: str,
    alert_name: str,
    timestamp_display: str,
    matched_news: list,
    statistics: dict,
):
    """Envía email resumen con todas las noticias que coincidieron con la alerta"""
    subject = f"Actualización de {alert_name} en {timestamp_display}"

    news_processed = statistics.get("news_processed", 0)
    matches_count = statistics.get("matches_count", 0)
    feeds_ok = statistics.get("feeds_ok", 0)
    feeds_ko = statistics.get("feeds_ko", 0)
    sources = statistics.get("sources", [])
    matched_keywords = statistics.get("matched_keywords", [])

    # Build matched news list for the body
    def _source_name(n):
        try:
            return n.rss_channel.information_source.name
        except Exception:
            return ""

    def _news_line(n):
        source = _source_name(n)
        keywords = ", ".join(n.matched_keywords or [])
        date = (
            n.published_date.strftime("%d/%m/%Y %H:%M")
            if n.published_date
            else "sin fecha"
        )
        summary = (
            (n.description[:120] + "...")
            if n.description and len(n.description) > 120
            else (n.description or "")
        )
        return f"- {n.title} ({source}) [{keywords}] ({date})\n  {summary}\n  {n.link}"

    news_lines = "\n".join(_news_line(n) for n in matched_news)

    body = f"""
Actualización de {alert_name} en {timestamp_display}

Estadísticas del ciclo:
- Noticias procesadas: {news_processed}
- Matches en esta alerta: {matches_count}
- Feeds OK: {feeds_ok}
- Feeds KO: {feeds_ko}
- Keywords coincidentes: {', '.join(matched_keywords)}
- Fuentes con matches: {', '.join(sources)}

Noticias coincidentes:
{news_lines}
    """

    def _news_html(n):
        source = _source_name(n)
        keywords = ", ".join(n.matched_keywords or [])
        date = (
            n.published_date.strftime("%d/%m/%Y %H:%M")
            if n.published_date
            else "sin fecha"
        )
        summary = (
            (n.description[:200] + "...")
            if n.description and len(n.description) > 200
            else (n.description or "")
        )
        return (
            f'<li style="margin-bottom:10px;">'
            f'<a href="{n.link}"><strong>{n.title}</strong></a><br/>'
            f"<small>{source} &middot; {date} &middot; [{keywords}]</small><br/>"
            f'<span style="color:#555;">{summary}</span>'
            f"</li>"
        )

    # First 20 always visible
    visible_items = "".join(_news_html(n) for n in matched_news[:20])

    # Remaining inside a collapsible <details> block
    extra_section = ""
    if len(matched_news) > 20:
        hidden_items = "".join(_news_html(n) for n in matched_news[20:])
        extra_section = f"""
            <details>
                <summary style="cursor:pointer;color:#2196F3;font-weight:bold;">
                    Ver {len(matched_news) - 20} noticias más...
                </summary>
                <ul>{hidden_items}</ul>
            </details>"""

    html_body = f"""
    <html>
        <body>
            <h2>Actualización de {alert_name}</h2>
            <p><strong>Fecha:</strong> {timestamp_display}</p>

            <h3>Estadísticas del ciclo</h3>
            <table style="border-collapse:collapse;" border="1" cellpadding="6">
                <tr><td>Noticias procesadas</td><td><strong>{news_processed}</strong></td></tr>
                <tr><td>Matches en esta alerta</td><td><strong>{matches_count}</strong></td></tr>
                <tr><td>Feeds OK</td><td><strong>{feeds_ok}</strong></td></tr>
                <tr><td>Feeds KO</td><td><strong>{feeds_ko}</strong></td></tr>
                <tr><td>Keywords coincidentes</td><td>{', '.join(matched_keywords)}</td></tr>
                <tr><td>Fuentes con matches</td><td>{', '.join(sources)}</td></tr>
            </table>

            <h3>Noticias coincidentes ({matches_count})</h3>
            <ul>{visible_items}</ul>
            {extra_section}
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
