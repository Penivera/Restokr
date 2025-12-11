from typing import Optional
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart
import aiosmtplib
from app.config import settings


async def send_confirmation_email(
    to_email: str,
    full_name: str,
    role: str
) -> bool:
    """
    Send confirmation email to early access signup.
    
    Args:
        to_email: Recipient email address
        full_name: Recipient's full name
        role: User role (customer, vendor, rider)
        
    Returns:
        True if email sent successfully, False otherwise
    """
    # Skip if SMTP not configured
    if not settings.SMTP_USER or not settings.SMTP_PASSWORD:
        print(f"SMTP not configured. Skipping email to {to_email}")
        return False
    
    try:
        # Create message
        message = MIMEMultipart("alternative")
        message["Subject"] = f"Welcome to ReStockr Early Access - {role.capitalize()}"
        message["From"] = f"{settings.SMTP_FROM_NAME} <{settings.SMTP_FROM_EMAIL}>"
        message["To"] = to_email
        
        # Create HTML content
        html_content = f"""
        <!DOCTYPE html>
        <html>
        <head>
            <style>
                body {{ font-family: Arial, sans-serif; line-height: 1.6; color: #333; }}
                .container {{ max-width: 600px; margin: 0 auto; padding: 20px; }}
                .header {{ background: linear-gradient(135deg, #667eea 0%, #764ba2 100%); 
                          color: white; padding: 30px; text-align: center; border-radius: 10px 10px 0 0; }}
                .content {{ background: #f9f9f9; padding: 30px; border-radius: 0 0 10px 10px; }}
                .footer {{ text-align: center; margin-top: 20px; color: #888; font-size: 12px; }}
                .role-badge {{ display: inline-block; background: #667eea; color: white; 
                              padding: 5px 15px; border-radius: 20px; font-weight: bold; }}
            </style>
        </head>
        <body>
            <div class="container">
                <div class="header">
                    <h1>🎉 Welcome to ReStockr!</h1>
                </div>
                <div class="content">
                    <p>Hi {full_name},</p>
                    
                    <p>Thank you for joining the <strong>ReStockr Early Access</strong> program as a 
                    <span class="role-badge">{role.upper()}</span>!</p>
                    
                    <p>We're building Nigeria's first hyper-local restocking platform, and you're among 
                    the first to experience it when we launch in <strong>Abuja</strong>.</p>
                    
                    <h3>What happens next?</h3>
                    <ul>
                        <li>✅ You're now on our priority list</li>
                        <li>📧 We'll send you exclusive updates</li>
                        <li>🚀 Early access when we launch</li>
                        <li>🎁 Special offers for early adopters</li>
                    </ul>
                    
                    <p>Stay tuned for more updates!</p>
                    
                    <p>Best regards,<br>
                    <strong>The ReStockr Team</strong><br>
                    Akodu Resources Limited</p>
                </div>
                <div class="footer">
                    <p>This is an automated message. Please do not reply to this email.</p>
                    <p>&copy; 2025 ReStockr by Akodu Resources Limited. All rights reserved.</p>
                </div>
            </div>
        </body>
        </html>
        """
        
        # Attach HTML content
        html_part = MIMEText(html_content, "html")
        message.attach(html_part)
        
        # Send email
        await aiosmtplib.send(
            message,
            hostname=settings.SMTP_HOST,
            port=settings.SMTP_PORT,
            username=settings.SMTP_USER,
            password=settings.SMTP_PASSWORD,
            start_tls=True,
        )
        
        print(f"✅ Confirmation email sent to {to_email}")
        return True
        
    except Exception as e:
        print(f"❌ Failed to send email to {to_email}: {str(e)}")
        return False
