"""
Prompt module containing system prompts and conversation templates for the pharmacy chatbot.
"""

from typing import Optional, Dict, Any


class PromptTemplates:
    """Contains all prompt templates for the pharmacy chatbot."""

    # System prompt for the chatbot
    SYSTEM_PROMPT = """You are a professional pharmacy sales representative for Pharmesol, a company that provides advanced pharmacy management solutions. You handle inbound calls from pharmacies who reach out via phone.

Your role is to:
1. Greet callers professionally and identify if they are existing customers or new leads
2. For existing customers: reference their pharmacy data and discuss how Pharmesol can help optimize their operations
3. For new leads: collect basic information conversationally and explain how Pharmesol can support their pharmacy
4. Highlight how Pharmesol can support high Rx volume pharmacies specifically
5. Offer follow-up actions like email or callback scheduling
6. Be helpful, professional, and focused on understanding their needs

Key information about Pharmesol:
- We specialize in pharmacy management software and automation
- We help pharmacies optimize operations, reduce costs, and improve patient care
- We offer solutions for inventory management, prescription processing, and analytics
- We have special programs for high-volume pharmacies (1000+ prescriptions)
- We provide 24/7 support and custom integrations

Always be conversational, professional, and focus on understanding their specific needs."""

    # Greeting templates
    EXISTING_CUSTOMER_GREETING = """Hello! Thank you for calling Pharmesol. I can see you're calling from {pharmacy_name} in {location}. How can I help you today?

I notice you're currently processing {rx_volume} prescriptions. That's quite a volume! How are things going with your current pharmacy management system?"""

    NEW_LEAD_GREETING = """Hello! Thank you for calling Pharmesol. My name is {bot_name}, and I'm here to help you find the right pharmacy management solutions.

I don't have your pharmacy in our system yet. Could you tell me a bit about your pharmacy and what brings you to call us today?"""

    # Information collection prompts
    COLLECT_PHARMACY_INFO = """I'd love to learn more about your pharmacy to see how we can help. Could you tell me:

1. What's the name of your pharmacy?
2. Where are you located?
3. How many prescriptions do you typically process?
4. Who should I speak with about pharmacy management solutions?
5. Do you have an email address where I can send you some information?

Take your time - I want to make sure I understand your needs properly."""

    # High volume pharmacy messaging
    HIGH_VOLUME_MESSAGE = """That's impressive! With {rx_volume} prescriptions, you're definitely a high-volume pharmacy. We have specialized solutions designed specifically for pharmacies like yours.

Our high-volume pharmacy program includes:
• Priority implementation (2-week setup)
• Dedicated account manager
• Volume-based pricing discounts
• Advanced automation features
• Custom workflow optimization

Would you like to hear more about how we can help streamline your operations?"""

    # Follow-up action prompts
    EMAIL_OFFER = """I'd be happy to send you some detailed information about our solutions. I can email you a comprehensive overview of how Pharmesol can help {pharmacy_name}, including case studies from similar pharmacies.

Would you like me to send that information to {email}?"""

    CALLBACK_OFFER = """I'd love to schedule a more detailed consultation to discuss your specific needs. We can go through your current processes and show you exactly how Pharmesol can help optimize your operations.

What would be a good time for a follow-up call? I'm available most weekdays between 9 AM and 5 PM."""

    # Conversation flow prompts
    NEXT_STEPS = """Great! Let me summarize what we've discussed and our next steps:

{summary}

{follow_up_action}

Is there anything else you'd like to know about Pharmesol before we wrap up?"""

    # Error handling prompts
    API_ERROR_MESSAGE = """I apologize, but I'm having trouble accessing our system right now. Let me collect your information manually and we can follow up with you shortly.

Could you tell me about your pharmacy so I can help you get started?"""

    MISSING_INFO_MESSAGE = """I want to make sure I have all the information I need to help you properly. Could you please provide:

{missing_fields}

This will help me tailor our solutions to your specific needs."""

    # Closing templates
    SUCCESSFUL_CLOSING = """Perfect! I've {action_taken}. You should {expected_outcome}.

Thank you for calling Pharmesol today. We're excited about the opportunity to help {pharmacy_name} optimize your pharmacy operations.

Is there anything else I can help you with today?"""

    GENERAL_CLOSING = """Thank you for calling Pharmesol today. We appreciate your interest in our pharmacy management solutions.

If you have any questions or would like to follow up, please don't hesitate to call us back at 1-800-PHARMESOL.

Have a great day!"""

    @staticmethod
    def format_greeting(
        pharmacy_data: Optional[Dict[str, Any]] = None, bot_name: str = "Alex"
    ) -> str:
        """Format the appropriate greeting based on whether the caller is an existing customer."""
        if pharmacy_data:
            return PromptTemplates.EXISTING_CUSTOMER_GREETING.format(
                pharmacy_name=pharmacy_data.get("name", "your pharmacy"),
                location=pharmacy_data.get("location", "your area"),
                rx_volume=pharmacy_data.get("rx_volume", 0),
            )
        else:
            return PromptTemplates.NEW_LEAD_GREETING.format(bot_name=bot_name)

    @staticmethod
    def format_high_volume_message(rx_volume: int) -> str:
        """Format the high volume pharmacy message."""
        return PromptTemplates.HIGH_VOLUME_MESSAGE.format(rx_volume=rx_volume)

    @staticmethod
    def format_email_offer(pharmacy_name: str, email: str) -> str:
        """Format the email offer message."""
        return PromptTemplates.EMAIL_OFFER.format(
            pharmacy_name=pharmacy_name, email=email
        )

    @staticmethod
    def format_callback_offer() -> str:
        """Format the callback offer message."""
        return PromptTemplates.CALLBACK_OFFER

    @staticmethod
    def format_next_steps(summary: str, follow_up_action: str) -> str:
        """Format the next steps message."""
        return PromptTemplates.NEXT_STEPS.format(
            summary=summary, follow_up_action=follow_up_action
        )

    @staticmethod
    def format_successful_closing(
        action_taken: str, expected_outcome: str, pharmacy_name: str
    ) -> str:
        """Format the successful closing message."""
        return PromptTemplates.SUCCESSFUL_CLOSING.format(
            action_taken=action_taken,
            expected_outcome=expected_outcome,
            pharmacy_name=pharmacy_name,
        )

    @staticmethod
    def format_missing_info_message(missing_fields: list[str]) -> str:
        """Format the missing information message."""
        formatted_fields = "\n".join([f"• {field}" for field in missing_fields])
        return PromptTemplates.MISSING_INFO_MESSAGE.format(
            missing_fields=formatted_fields
        )


# Conversation flow states
class ConversationState:
    """Defines the different states of the conversation."""

    GREETING = "greeting"
    COLLECTING_INFO = "collecting_info"
    DISCUSSING_SOLUTIONS = "discussing_solutions"
    OFFERING_FOLLOW_UP = "offering_follow_up"
    SCHEDULING = "scheduling"
    CLOSING = "closing"
    ERROR = "error"


# Response templates for different conversation states
class ResponseTemplates:
    """Contains response templates for different conversation states."""

    @staticmethod
    def get_collecting_info_response(field: str) -> str:
        """Get response for collecting specific information."""
        responses = {
            "pharmacy_name": "What's the name of your pharmacy?",
            "location": "Where is your pharmacy located?",
            "rx_volume": "How many prescriptions do you typically process each month?",
            "contact_person": "Who should I speak with about pharmacy management solutions?",
            "email": "What's the best email address to send you information?",
        }
        return responses.get(field, "Could you provide that information?")

    @staticmethod
    def get_solution_benefits(rx_volume: int) -> str:
        """Get solution benefits based on Rx volume."""
        if rx_volume >= 1000:
            return """For high-volume pharmacies like yours, we offer:
• Advanced automation that can save 20+ hours per week
• Real-time inventory management with predictive ordering
• Custom workflow optimization
• Priority support and dedicated account management
• Volume-based pricing that scales with your business"""
        elif rx_volume >= 500:
            return """For pharmacies of your size, we provide:
• Streamlined prescription processing
• Automated inventory tracking
• Comprehensive reporting and analytics
• Integration with major pharmacy systems
• 24/7 technical support"""
        else:
            return """We can help you:
• Automate routine tasks
• Improve inventory management
• Enhance patient care coordination
• Reduce operational costs
• Scale as your business grows"""

    @staticmethod
    def get_follow_up_options() -> str:
        """Get follow-up action options."""
        return """I'd be happy to help you get started. We can:

1. Send you detailed information via email
2. Schedule a consultation call to discuss your specific needs
3. Arrange a demo of our system
4. Connect you with one of our pharmacy specialists

What would work best for you?"""

    @staticmethod
    def get_confirmation_message(action: str) -> str:
        """Get confirmation message for actions."""
        confirmations = {
            "email_sent": "I've sent you detailed information about our solutions. You should receive it within the next few minutes.",
            "callback_scheduled": "I've scheduled a consultation call for you. You'll receive a confirmation email with the details.",
            "demo_scheduled": "I've arranged a demo of our system. Our team will contact you to confirm the details.",
            "specialist_contact": "I've connected you with one of our pharmacy specialists. They'll reach out within 24 hours.",
        }
        return confirmations.get(
            action, "I've processed your request. You'll hear from us soon."
        )
