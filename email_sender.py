"""
Módulo para envio de emails via Gmail SMTP.
"""

import os
import smtplib
from email.mime.multipart import MIMEMultipart
from email.mime.text import MIMEText


def send_email(recipient: str, subject: str, body_html: str) -> None:
    """
    Envia um email via Gmail SMTP.

    Variáveis de ambiente necessárias:
        GMAIL_ADDRESS: Endereço Gmail do remetente
        GMAIL_APP_PASSWORD: Senha de app do Gmail (não a senha normal)

    Args:
        recipient: Endereço de email do destinatário
        subject: Assunto do email
        body_html: Corpo do email em HTML
    """
    sender_email = os.environ.get("GMAIL_ADDRESS")
    sender_password = os.environ.get("GMAIL_APP_PASSWORD")

    if not sender_email or not sender_password:
        raise ValueError(
            "GMAIL_ADDRESS e GMAIL_APP_PASSWORD devem estar configurados "
            "como variáveis de ambiente. Para gerar uma senha de app, acesse: "
            "https://myaccount.google.com/apppasswords"
        )

    msg = MIMEMultipart("alternative")
    msg["From"] = sender_email
    msg["To"] = recipient
    msg["Subject"] = subject

    # Wraps the AI-generated HTML in a basic email template
    full_html = f"""\
<!DOCTYPE html>
<html>
<head>
    <meta charset="utf-8">
    <style>
        body {{
            font-family: -apple-system, BlinkMacSystemFont, 'Segoe UI', Roboto, sans-serif;
            line-height: 1.6;
            color: #333;
            max-width: 700px;
            margin: 0 auto;
            padding: 20px;
        }}
        h1 {{
            color: #1a1a2e;
            border-bottom: 2px solid #e94560;
            padding-bottom: 10px;
        }}
        h2 {{
            color: #16213e;
            margin-top: 30px;
        }}
        a {{
            color: #e94560;
            text-decoration: none;
        }}
        a:hover {{
            text-decoration: underline;
        }}
        .footer {{
            margin-top: 40px;
            padding-top: 20px;
            border-top: 1px solid #eee;
            font-size: 12px;
            color: #999;
        }}
    </style>
</head>
<body>
    {body_html}
    <div class="footer">
        <p>Este email foi gerado automaticamente pelo News Agent.</p>
    </div>
</body>
</html>"""

    msg.attach(MIMEText(full_html, "html"))

    with smtplib.SMTP_SSL("smtp.gmail.com", 465) as server:
        server.login(sender_email, sender_password)
        server.sendmail(sender_email, recipient, msg.as_string())
