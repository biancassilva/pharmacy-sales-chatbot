"""
Function calls module for handling follow-up actions like email sending and callback scheduling.
"""

import logging
from typing import Dict, Any, Optional
from datetime import datetime, timedelta
from dataclasses import dataclass

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


@dataclass
class EmailRequest:
    """Data class for email requests."""

    to_email: str
    subject: str
    body: str
    pharmacy_name: str
    contact_person: str


@dataclass
class CallbackRequest:
    """Data class for callback scheduling requests."""

    phone_number: str
    preferred_time: str
    pharmacy_name: str
    contact_person: str
    notes: Optional[str] = None


class FollowUpActions:
    """Handles follow-up actions like email sending and callback scheduling."""

    def __init__(self):
        self.sent_emails = []
        self.scheduled_callbacks = []

    def send_email(self, email_request: EmailRequest) -> Dict[str, Any]:
        """
        Mock function to send email to pharmacy.

        Args:
            email_request: EmailRequest object containing email details

        Returns:
            Dictionary with status and details
        """
        try:
            # Mock email sending - in production this would integrate with email service
            email_data = {
                "id": len(self.sent_emails) + 1,
                "to_email": email_request.to_email,
                "subject": email_request.subject,
                "body": email_request.body,
                "pharmacy_name": email_request.pharmacy_name,
                "contact_person": email_request.contact_person,
                "sent_at": datetime.now().isoformat(),
                "status": "sent",
            }

            self.sent_emails.append(email_data)

            logger.info(
                f"Email sent to {email_request.to_email} for {email_request.pharmacy_name}"
            )

            return {
                "success": True,
                "message": f"Email sent successfully to {email_request.contact_person} at {email_request.pharmacy_name}",
                "email_id": email_data["id"],
                "sent_at": email_data["sent_at"],
            }

        except Exception as e:
            logger.error(f"Error sending email: {e}")
            return {"success": False, "message": f"Failed to send email: {str(e)}"}

    def schedule_callback(self, callback_request: CallbackRequest) -> Dict[str, Any]:
        """
        Mock function to schedule a callback.

        Args:
            callback_request: CallbackRequest object containing callback details

        Returns:
            Dictionary with status and details
        """
        try:
            # Mock callback scheduling - in production this would integrate with calendar/scheduling service
            callback_data = {
                "id": len(self.scheduled_callbacks) + 1,
                "phone_number": callback_request.phone_number,
                "preferred_time": callback_request.preferred_time,
                "pharmacy_name": callback_request.pharmacy_name,
                "contact_person": callback_request.contact_person,
                "notes": callback_request.notes,
                "scheduled_at": datetime.now().isoformat(),
                "status": "scheduled",
            }

            self.scheduled_callbacks.append(callback_data)

            logger.info(
                f"Callback scheduled for {callback_request.contact_person} at {callback_request.pharmacy_name}"
            )

            return {
                "success": True,
                "message": f"Callback scheduled successfully for {callback_request.contact_person} at {callback_request.preferred_time}",
                "callback_id": callback_data["id"],
                "scheduled_at": callback_data["scheduled_at"],
            }

        except Exception as e:
            logger.error(f"Error scheduling callback: {e}")
            return {
                "success": False,
                "message": f"Failed to schedule callback: {str(e)}",
            }

    def send_welcome_email(self, pharmacy_data: "PharmacyData") -> Dict[str, Any]:
        """
        Send a welcome email to a new pharmacy.

        Args:
            pharmacy_data: PharmacyData object containing pharmacy information

        Returns:
            Dictionary with status and details
        """
        subject = f"Welcome to Pharmesol - Supporting {pharmacy_data.name}"

        body = f"""
Dear {pharmacy_data.contact_person},

Thank you for your interest in Pharmesol! We're excited to help {pharmacy_data.name} optimize your pharmacy operations.

Based on your current Rx volume of {pharmacy_data.rx_volume} prescriptions, we can offer you:

• Advanced inventory management solutions
• Automated prescription processing
• Real-time analytics and reporting
• 24/7 technical support
• Custom integration with your existing systems

Our team will be in touch within 24 hours to discuss how we can best serve your pharmacy.

Best regards,
The Pharmesol Team
        """.strip()

        email_request = EmailRequest(
            to_email=pharmacy_data.email or "contact@pharmacy.com",
            subject=subject,
            body=body,
            pharmacy_name=pharmacy_data.name,
            contact_person=pharmacy_data.contact_person,
        )

        return self.send_email(email_request)

    def send_high_volume_offer(self, pharmacy_data: "PharmacyData") -> Dict[str, Any]:
        """
        Send a special offer email to high volume pharmacies.

        Args:
            pharmacy_data: PharmacyData object containing pharmacy information

        Returns:
            Dictionary with status and details
        """
        subject = (
            f"Special Offer for {pharmacy_data.name} - High Volume Pharmacy Solutions"
        )

        body = f"""
Dear {pharmacy_data.contact_person},

We noticed that {pharmacy_data.name} processes {pharmacy_data.rx_volume} prescriptions, making you a high-volume pharmacy that could greatly benefit from our advanced solutions.

As a high-volume pharmacy, you're eligible for:

• Priority implementation (2-week setup)
• Dedicated account manager
• Volume-based pricing discounts
• Advanced automation features
• Custom workflow optimization

Would you like to schedule a consultation to discuss how we can help streamline your operations?

Best regards,
The Pharmesol Team
        """.strip()

        email_request = EmailRequest(
            to_email=pharmacy_data.email or "contact@pharmacy.com",
            subject=subject,
            body=body,
            pharmacy_name=pharmacy_data.name,
            contact_person=pharmacy_data.contact_person,
        )

        return self.send_email(email_request)

    def schedule_consultation(
        self, pharmacy_data: "PharmacyData", preferred_time: str = "tomorrow at 2 PM"
    ) -> Dict[str, Any]:
        """
        Schedule a consultation callback for a pharmacy.

        Args:
            pharmacy_data: PharmacyData object containing pharmacy information
            preferred_time: Preferred time for the callback

        Returns:
            Dictionary with status and details
        """
        callback_request = CallbackRequest(
            phone_number=pharmacy_data.phone,
            preferred_time=preferred_time,
            pharmacy_name=pharmacy_data.name,
            contact_person=pharmacy_data.contact_person,
            notes=f"Consultation call for {pharmacy_data.name} with Rx volume of {pharmacy_data.rx_volume}",
        )

        return self.schedule_callback(callback_request)

    def get_email_history(self) -> list[Dict[str, Any]]:
        """Get history of sent emails."""
        return self.sent_emails.copy()

    def get_callback_history(self) -> list[Dict[str, Any]]:
        """Get history of scheduled callbacks."""
        return self.scheduled_callbacks.copy()

    def clear_history(self):
        """Clear email and callback history (useful for testing)."""
        self.sent_emails.clear()
        self.scheduled_callbacks.clear()
        logger.info("Follow-up action history cleared")
