"""
Mail service for PyCommerce.

This module provides email sending functionality for the platform,
specifically for order confirmation and notifications.
"""

import logging
import os
import smtplib
from email.mime.multipart import MIMEMultipart
from email.mime.text import MIMEText
from typing import Dict, List, Optional, Union, Any
from jinja2 import Environment, FileSystemLoader, select_autoescape
from datetime import datetime

logger = logging.getLogger("pycommerce.services.mail")

# Configure Jinja2 environment for email templates
try:
    template_dir = os.path.join(os.path.dirname(os.path.dirname(os.path.dirname(__file__))), "templates", "emails")
    if not os.path.exists(template_dir):
        os.makedirs(template_dir)
    
    env = Environment(
        loader=FileSystemLoader(template_dir),
        autoescape=select_autoescape(['html', 'xml'])
    )
    logger.info(f"Email template directory: {template_dir}")
except Exception as e:
    logger.error(f"Error setting up email templates: {str(e)}")
    env = None


class EmailConfig:
    """Configuration for email service."""
    
    def __init__(
        self,
        smtp_host: str = "smtp.gmail.com",
        smtp_port: int = 587,
        smtp_username: Optional[str] = None,
        smtp_password: Optional[str] = None,
        default_sender: str = "noreply@pycommerce.example.com",
        use_tls: bool = True,
        enabled: bool = True
    ):
        """
        Initialize email configuration.
        
        Args:
            smtp_host: SMTP server hostname
            smtp_port: SMTP server port
            smtp_username: SMTP server username (if authentication required)
            smtp_password: SMTP server password (if authentication required)
            default_sender: Default sender email address
            use_tls: Whether to use TLS encryption
            enabled: Whether email sending is enabled
        """
        self.smtp_host = smtp_host
        self.smtp_port = smtp_port
        self.smtp_username = smtp_username or os.environ.get("SMTP_USERNAME")
        self.smtp_password = smtp_password or os.environ.get("SMTP_PASSWORD")
        self.default_sender = default_sender
        self.use_tls = use_tls
        self.enabled = enabled
        
        # Validate required settings if enabled
        if self.enabled and (not self.smtp_username or not self.smtp_password):
            logger.warning("Email service is enabled but SMTP credentials are missing")
            self.enabled = False


class EmailService:
    """Service for sending emails."""
    
    def __init__(self, config: EmailConfig = None):
        """
        Initialize email service.
        
        Args:
            config: Email configuration (optional, uses environment vars if not provided)
        """
        self.config = config or EmailConfig()
        self._test_mode = False
        self._test_emails = []
    
    def enable_test_mode(self):
        """
        Enable test mode - emails are stored in memory instead of being sent.
        """
        self._test_mode = True
        self._test_emails = []
        logger.info("Email service test mode enabled")
    
    def disable_test_mode(self):
        """
        Disable test mode.
        """
        self._test_mode = False
        self._test_emails = []
        logger.info("Email service test mode disabled")
    
    def get_test_emails(self) -> List[Dict[str, Any]]:
        """
        Get test emails that would have been sent.
        
        Returns:
            List of email data dictionaries
        """
        return self._test_emails
    
    def send_email(
        self,
        to_email: Union[str, List[str]],
        subject: str,
        html_content: str,
        text_content: Optional[str] = None,
        from_email: Optional[str] = None,
        cc: Optional[Union[str, List[str]]] = None,
        bcc: Optional[Union[str, List[str]]] = None,
        reply_to: Optional[str] = None,
        attachments: Optional[List[Dict[str, Any]]] = None
    ) -> bool:
        """
        Send an email.
        
        Args:
            to_email: Recipient email address or list of addresses
            subject: Email subject
            html_content: HTML email content
            text_content: Plain text email content (optional)
            from_email: Sender email address (optional, uses default_sender if not provided)
            cc: Carbon copy recipients (optional)
            bcc: Blind carbon copy recipients (optional)
            reply_to: Reply-to email address (optional)
            attachments: List of attachment dictionaries with keys: 
                         'filename', 'content', 'mime_type' (optional)
            
        Returns:
            True if email was sent successfully, False otherwise
        """
        if not self.config.enabled and not self._test_mode:
            logger.warning("Email service is disabled")
            return False
        
        # Normalize inputs
        if isinstance(to_email, str):
            to_email = [to_email]
        if isinstance(cc, str):
            cc = [cc]
        if isinstance(bcc, str):
            bcc = [bcc]
            
        sender = from_email or self.config.default_sender
        
        # Create message
        msg = MIMEMultipart('alternative')
        msg['Subject'] = subject
        msg['From'] = sender
        msg['To'] = ", ".join(to_email)
        
        if cc:
            msg['Cc'] = ", ".join(cc)
        if reply_to:
            msg['Reply-To'] = reply_to
            
        # Add content
        if text_content:
            msg.attach(MIMEText(text_content, 'plain'))
        if html_content:
            msg.attach(MIMEText(html_content, 'html'))
            
        # Add attachments (basic implementation, can be expanded)
        if attachments:
            for attachment in attachments:
                # Not implemented yet - would require additional imports and handling
                pass
            
        # Test mode: store email instead of sending
        if self._test_mode:
            test_email = {
                'to': to_email,
                'subject': subject,
                'html': html_content,
                'text': text_content,
                'from': sender,
                'cc': cc,
                'bcc': bcc
            }
            self._test_emails.append(test_email)
            logger.info(f"Test email queued: {subject} to {to_email}")
            return True
            
        # Send email
        try:
            smtp = smtplib.SMTP(self.config.smtp_host, self.config.smtp_port)
            
            if self.config.use_tls:
                smtp.starttls()
                
            if self.config.smtp_username and self.config.smtp_password:
                smtp.login(self.config.smtp_username, self.config.smtp_password)
                
            all_recipients = to_email.copy()
            if cc:
                all_recipients.extend(cc)
            if bcc:
                all_recipients.extend(bcc)
                
            smtp.sendmail(sender, all_recipients, msg.as_string())
            smtp.quit()
            
            logger.info(f"Email sent: {subject} to {to_email}")
            return True
            
        except Exception as e:
            logger.error(f"Error sending email: {str(e)}")
            return False
    
    def send_template_email(
        self,
        to_email: Union[str, List[str]],
        subject: str,
        template_name: str,
        template_data: Dict[str, Any],
        from_email: Optional[str] = None,
        cc: Optional[Union[str, List[str]]] = None,
        bcc: Optional[Union[str, List[str]]] = None,
        reply_to: Optional[str] = None
    ) -> bool:
        """
        Send an email using a template.
        
        Args:
            to_email: Recipient email address or list of addresses
            subject: Email subject
            template_name: Template filename (without extension)
            template_data: Dictionary of data to pass to the template
            from_email: Sender email address (optional, uses default_sender if not provided)
            cc: Carbon copy recipients (optional)
            bcc: Blind carbon copy recipients (optional)
            reply_to: Reply-to email address (optional)
            
        Returns:
            True if email was sent successfully, False otherwise
        """
        if env is None:
            logger.error("Email templates not configured")
            return False
            
        try:
            # Load template
            template_html = f"{template_name}.html"
            template_text = f"{template_name}.txt"
            
            # Render HTML version
            html_content = None
            try:
                html_template = env.get_template(template_html)
                html_content = html_template.render(**template_data)
            except Exception as e:
                logger.warning(f"Error rendering HTML template {template_html}: {str(e)}")
                
            # Render text version
            text_content = None
            try:
                text_template = env.get_template(template_text)
                text_content = text_template.render(**template_data)
            except Exception as e:
                logger.warning(f"Error rendering text template {template_text}: {str(e)}")
                
            # Ensure at least one version is available
            if not html_content and not text_content:
                logger.error(f"No email templates found for {template_name}")
                return False
                
            # Send email
            return self.send_email(
                to_email=to_email,
                subject=subject,
                html_content=html_content or "",
                text_content=text_content,
                from_email=from_email,
                cc=cc,
                bcc=bcc,
                reply_to=reply_to
            )
            
        except Exception as e:
            logger.error(f"Error sending template email: {str(e)}")
            return False
    
    def send_order_confirmation(
        self,
        order: Any,
        to_email: str,
        store_name: str,
        store_url: str,
        store_logo_url: Optional[str] = None,
        contact_email: Optional[str] = None,
        from_email: Optional[str] = None
    ) -> bool:
        """
        Send an order confirmation email.
        
        Args:
            order: Order object with details
            to_email: Customer email address
            store_name: Name of the store
            store_url: URL of the store
            store_logo_url: URL of the store logo (optional)
            contact_email: Contact email for customer inquiries (optional)
            from_email: Sender email address (optional)
            
        Returns:
            True if email was sent successfully, False otherwise
        """
        try:
            # Prepare template data
            template_data = {
                'order': order,
                'store_name': store_name,
                'store_url': store_url,
                'store_logo_url': store_logo_url,
                'contact_email': contact_email or self.config.default_sender,
                'year': datetime.now().year
            }
            
            # Send email using template
            return self.send_template_email(
                to_email=to_email,
                subject=f"{store_name} - Order Confirmation #{order.id}",
                template_name="order_confirmation",
                template_data=template_data,
                from_email=from_email,
                reply_to=contact_email
            )
            
        except Exception as e:
            logger.error(f"Error sending order confirmation: {str(e)}")
            return False
            
    def send_shipping_notification(
        self,
        order: Any,
        shipment: Any,
        to_email: str,
        store_name: str,
        store_url: str,
        store_logo_url: Optional[str] = None,
        contact_email: Optional[str] = None,
        from_email: Optional[str] = None
    ) -> bool:
        """
        Send a shipping notification email.
        
        Args:
            order: Order object with details
            shipment: Shipment object with tracking information
            to_email: Customer email address
            store_name: Name of the store
            store_url: URL of the store
            store_logo_url: URL of the store logo (optional)
            contact_email: Contact email for customer inquiries (optional)
            from_email: Sender email address (optional)
            
        Returns:
            True if email was sent successfully, False otherwise
        """
        try:
            # Prepare template data
            template_data = {
                'order': order,
                'shipment': shipment,
                'store_name': store_name,
                'store_url': store_url,
                'store_logo_url': store_logo_url,
                'contact_email': contact_email or self.config.default_sender,
                'year': datetime.now().year
            }
            
            # Send email using template
            return self.send_template_email(
                to_email=to_email,
                subject=f"{store_name} - Your Order Has Shipped! #{order.id}",
                template_name="shipping_notification",
                template_data=template_data,
                from_email=from_email,
                reply_to=contact_email
            )
            
        except Exception as e:
            logger.error(f"Error sending shipping notification: {str(e)}")
            return False


# Global instance for convenience
_default_service = None

def init_email_service(config: EmailConfig = None) -> EmailService:
    """
    Initialize the default email service.
    
    Args:
        config: Email configuration (optional)
        
    Returns:
        The initialized email service
    """
    global _default_service
    _default_service = EmailService(config)
    return _default_service

def get_email_service() -> Optional[EmailService]:
    """
    Get the default email service.
    
    Returns:
        The default email service or None if not initialized
    """
    return _default_service