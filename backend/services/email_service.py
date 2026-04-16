"""
Servicio de Email - Hotel Boutique
Envío de correos para registro y reservas
"""
import smtplib
import ssl
import os
import logging
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart
from typing import Optional

logger = logging.getLogger(__name__)

# Configuración SMTP
SMTP_SERVER = os.environ.get("SMTP_SERVER", "smtp.office365.com")
SMTP_PORT = int(os.environ.get("SMTP_PORT", "587"))
SMTP_EMAIL = os.environ.get("SMTP_EMAIL", "bcastiblancod@ucentral.edu.co")
SMTP_PASSWORD = os.environ.get("SMTP_PASSWORD", "")

# Nombre del hotel para los correos
HOTEL_NAME = "Hotel Imperium"
HOTEL_PHONE = "+57 300 123 4567"
HOTEL_ADDRESS = "Calle Principal #123, Bogotá, Colombia"


def get_email_template(content: str, title: str) -> str:
    """Genera el template HTML del email"""
    return f"""
    <!DOCTYPE html>
    <html>
    <head>
        <meta charset="utf-8">
        <style>
            body {{
                font-family: 'Segoe UI', Tahoma, Geneva, Verdana, sans-serif;
                line-height: 1.6;
                color: #333;
                margin: 0;
                padding: 0;
                background-color: #f5f5f5;
            }}
            .container {{
                max-width: 600px;
                margin: 0 auto;
                background-color: #ffffff;
            }}
            .header {{
                background-color: #1e3a34;
                color: white;
                padding: 30px;
                text-align: center;
            }}
            .header h1 {{
                margin: 0;
                font-size: 28px;
                font-weight: 400;
                letter-spacing: 2px;
            }}
            .header p {{
                margin: 5px 0 0 0;
                font-size: 12px;
                letter-spacing: 3px;
                opacity: 0.8;
            }}
            .content {{
                padding: 40px 30px;
            }}
            .content h2 {{
                color: #1e3a34;
                font-size: 22px;
                margin-top: 0;
                border-bottom: 2px solid #10b981;
                padding-bottom: 10px;
            }}
            .info-box {{
                background-color: #f8f9fa;
                border-left: 4px solid #10b981;
                padding: 15px 20px;
                margin: 20px 0;
            }}
            .info-box p {{
                margin: 5px 0;
            }}
            .info-box strong {{
                color: #1e3a34;
            }}
            .footer {{
                background-color: #1e3a34;
                color: white;
                padding: 20px 30px;
                text-align: center;
                font-size: 12px;
            }}
            .footer a {{
                color: #10b981;
                text-decoration: none;
            }}
            .button {{
                display: inline-block;
                background-color: #10b981;
                color: white;
                padding: 12px 30px;
                text-decoration: none;
                border-radius: 4px;
                margin: 20px 0;
            }}
            .divider {{
                border-top: 1px solid #eee;
                margin: 20px 0;
            }}
        </style>
    </head>
    <body>
        <div class="container">
            <div class="header">
                <h1>{HOTEL_NAME}</h1>
                <p>BOUTIQUE HOTEL</p>
            </div>
            <div class="content">
                <h2>{title}</h2>
                {content}
            </div>
            <div class="footer">
                <p><strong>{HOTEL_NAME}</strong></p>
                <p>{HOTEL_ADDRESS}</p>
                <p>Tel: {HOTEL_PHONE}</p>
                <p>Este es un correo automático, por favor no responda directamente.</p>
            </div>
        </div>
    </body>
    </html>
    """


async def send_email(to_email: str, subject: str, html_content: str) -> bool:
    """
    Envía un correo electrónico usando SMTP.
    Retorna True si se envió correctamente, False en caso contrario.
    """
    if not SMTP_PASSWORD:
        logger.warning("SMTP_PASSWORD no configurado. No se enviará el correo.")
        return False
    
    try:
        # Crear mensaje
        message = MIMEMultipart("alternative")
        message["Subject"] = subject
        message["From"] = f"{HOTEL_NAME} <{SMTP_EMAIL}>"
        message["To"] = to_email
        
        # Agregar contenido HTML
        html_part = MIMEText(html_content, "html")
        message.attach(html_part)
        
        # Crear conexión segura
        context = ssl.create_default_context()
        
        with smtplib.SMTP(SMTP_SERVER, SMTP_PORT) as server:
            server.starttls(context=context)
            server.login(SMTP_EMAIL, SMTP_PASSWORD)
            server.sendmail(SMTP_EMAIL, to_email, message.as_string())
        
        logger.info(f"Email enviado exitosamente a {to_email}")
        return True
        
    except smtplib.SMTPAuthenticationError:
        logger.error(f"Error de autenticación SMTP. Verifique las credenciales.")
        return False
    except smtplib.SMTPException as e:
        logger.error(f"Error SMTP al enviar email: {str(e)}")
        return False
    except Exception as e:
        logger.error(f"Error inesperado al enviar email: {str(e)}")
        return False


async def send_registration_email(user_email: str, user_name: str) -> bool:
    """Envía correo de bienvenida al registrarse"""
    content = f"""
    <p>Estimado/a <strong>{user_name}</strong>,</p>
    
    <p>¡Bienvenido/a a {HOTEL_NAME}! Su cuenta ha sido creada exitosamente.</p>
    
    <div class="info-box">
        <p><strong>Email de acceso:</strong> {user_email}</p>
        <p><strong>Fecha de registro:</strong> {__import__('datetime').datetime.now().strftime('%d/%m/%Y %H:%M')}</p>
    </div>
    
    <p>Ahora puede acceder a nuestro sistema para:</p>
    <ul>
        <li>Consultar disponibilidad de habitaciones</li>
        <li>Realizar reservas</li>
        <li>Ver el historial de sus estadías</li>
        <li>Gestionar sus facturas</li>
    </ul>
    
    <p>Si tiene alguna pregunta o necesita asistencia, no dude en contactarnos.</p>
    
    <div class="divider"></div>
    
    <p>Atentamente,<br><strong>Equipo de {HOTEL_NAME}</strong></p>
    """
    
    subject = f"¡Bienvenido/a a {HOTEL_NAME}! - Registro exitoso"
    html = get_email_template(content, "Registro Exitoso")
    
    return await send_email(user_email, subject, html)


async def send_reservation_email(
    user_email: str,
    user_name: str,
    reservation_code: str,
    room_number: str,
    room_type: str,
    check_in: str,
    check_out: str,
    total: float,
    guests: int
) -> bool:
    """Envía correo de confirmación de reserva"""
    
    # Formatear fechas
    try:
        check_in_formatted = __import__('datetime').datetime.fromisoformat(check_in.replace('Z', '+00:00')).strftime('%d/%m/%Y')
        check_out_formatted = __import__('datetime').datetime.fromisoformat(check_out.replace('Z', '+00:00')).strftime('%d/%m/%Y')
    except:
        check_in_formatted = check_in
        check_out_formatted = check_out
    
    # Formatear total
    total_formatted = f"${total:,.0f} COP"
    
    content = f"""
    <p>Estimado/a <strong>{user_name}</strong>,</p>
    
    <p>¡Su reserva ha sido confirmada exitosamente! A continuación encontrará los detalles:</p>
    
    <div class="info-box">
        <p><strong>Código de Reserva:</strong> {reservation_code}</p>
        <p><strong>Habitación:</strong> {room_number} - {room_type}</p>
        <p><strong>Check-in:</strong> {check_in_formatted} (desde las 15:00)</p>
        <p><strong>Check-out:</strong> {check_out_formatted} (hasta las 12:00)</p>
        <p><strong>Huéspedes:</strong> {guests}</p>
        <p><strong>Total:</strong> {total_formatted}</p>
    </div>
    
    <h3 style="color: #1e3a34;">Información importante:</h3>
    <ul>
        <li><strong>Check-in:</strong> A partir de las 15:00 horas</li>
        <li><strong>Check-out:</strong> Hasta las 12:00 horas</li>
        <li>Presente su documento de identidad al momento del check-in</li>
        <li>Guarde este código de reserva: <strong>{reservation_code}</strong></li>
    </ul>
    
    <p>Para cualquier modificación o cancelación, contáctenos con al menos 24 horas de anticipación.</p>
    
    <div class="divider"></div>
    
    <p>¡Le esperamos!</p>
    <p>Atentamente,<br><strong>Equipo de {HOTEL_NAME}</strong></p>
    """
    
    subject = f"Confirmación de Reserva {reservation_code} - {HOTEL_NAME}"
    html = get_email_template(content, "Confirmación de Reserva")
    
    return await send_email(user_email, subject, html)


async def send_cancellation_email(
    user_email: str,
    user_name: str,
    reservation_code: str,
    reason: Optional[str] = None
) -> bool:
    """Envía correo de cancelación de reserva"""
    
    reason_text = f"<p><strong>Motivo:</strong> {reason}</p>" if reason else ""
    
    content = f"""
    <p>Estimado/a <strong>{user_name}</strong>,</p>
    
    <p>Le confirmamos que su reserva ha sido cancelada.</p>
    
    <div class="info-box">
        <p><strong>Código de Reserva:</strong> {reservation_code}</p>
        <p><strong>Fecha de cancelación:</strong> {__import__('datetime').datetime.now().strftime('%d/%m/%Y %H:%M')}</p>
        {reason_text}
    </div>
    
    <p>Si tiene alguna pregunta sobre el reembolso o desea realizar una nueva reserva, 
    no dude en contactarnos.</p>
    
    <div class="divider"></div>
    
    <p>Atentamente,<br><strong>Equipo de {HOTEL_NAME}</strong></p>
    """
    
    subject = f"Cancelación de Reserva {reservation_code} - {HOTEL_NAME}"
    html = get_email_template(content, "Reserva Cancelada")
    
    return await send_email(user_email, subject, html)
