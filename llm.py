"""
LLM module for handling OpenAI API interactions and conversation management.
"""

import os
import logging
import json
from typing import Dict, Any, Optional, List
from openai import OpenAI
from dotenv import load_dotenv

from prompt import PromptTemplates, ConversationState, ResponseTemplates
from integration import PharmacyAPI, PharmacyData
from function_calls import FollowUpActions

# Load environment variables
load_dotenv()

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


class PharmacyChatbot:
    """Main chatbot class that handles conversations with pharmacy callers."""

    def __init__(self, api_key: Optional[str] = None):
        """
        Initialize the pharmacy chatbot.

        Args:
            api_key: OpenAI API key (will use environment variable if not provided)
        """
        self.api_key = api_key or os.getenv("OPENAI_API_KEY")
        self.ai_available = False
        self.ai_extraction_failures = 0  # Track AI extraction failures

        if self.api_key:
            try:
                self.client = OpenAI(api_key=self.api_key)
                # Test the API connection with a working model
                self.client.chat.completions.create(
                    model="gpt-4o-mini",
                    messages=[{"role": "user", "content": "test"}],
                    max_tokens=5,
                )
                self.ai_available = True
                logger.info("OpenAI API connection successful")
            except Exception as e:
                logger.warning(f"OpenAI API not available: {e}")
                self.ai_available = False
        else:
            logger.warning("No OpenAI API key provided - using fallback mode")

        self.pharmacy_api = PharmacyAPI()
        self.follow_up_actions = FollowUpActions()

        # Conversation state
        self.current_state = ConversationState.GREETING
        self.conversation_history = []
        self.pharmacy_data = None
        self.collected_info = {}
        self.info_collection_fields = [
            "pharmacy_name",
            "location",
            "rx_volume",
            "contact_person",
            "email",
        ]
        self.current_info_field = 0

    def start_call(self, phone_number: str) -> str:
        """
        Start a new call and identify the caller.

        Args:
            phone_number: The caller's phone number

        Returns:
            Initial greeting message
        """
        try:
            # Check if caller is an existing pharmacy
            self.pharmacy_data = self.pharmacy_api.get_pharmacy_by_phone(phone_number)

            if self.pharmacy_data:
                # Existing customer
                greeting = PromptTemplates.format_greeting(
                    {
                        "name": self.pharmacy_data.name,
                        "location": self.pharmacy_data.location,
                        "rx_volume": self.pharmacy_data.rx_volume,
                    }
                )
                self.current_state = ConversationState.DISCUSSING_SOLUTIONS
            else:
                # New lead
                greeting = PromptTemplates.format_greeting()
                self.current_state = ConversationState.COLLECTING_INFO
                self.current_info_field = 0

            # Add to conversation history
            self.conversation_history.append(
                {
                    "role": "system",
                    "content": f"Call started from phone number: {phone_number}",
                }
            )
            self.conversation_history.append({"role": "assistant", "content": greeting})

            return greeting

        except Exception as e:
            logger.error(f"Error starting call: {e}")
            self.current_state = ConversationState.ERROR
            return PromptTemplates.API_ERROR_MESSAGE

    def process_message(self, user_message: str) -> str:
        """
        Process a user message and generate a response.

        Args:
            user_message: The user's message

        Returns:
            Bot response
        """
        try:
            # Add user message to history
            self.conversation_history.append({"role": "user", "content": user_message})

            # Route to appropriate handler based on current state
            if self.current_state == ConversationState.COLLECTING_INFO:
                response = self._handle_info_collection(user_message)
            elif self.current_state == ConversationState.DISCUSSING_SOLUTIONS:
                response = self._handle_solution_discussion(user_message)
            elif self.current_state == ConversationState.OFFERING_FOLLOW_UP:
                response = self._handle_follow_up_offer(user_message)
            elif self.current_state == ConversationState.SCHEDULING:
                response = self._handle_scheduling(user_message)
            elif self.current_state == ConversationState.CLOSING:
                response = self._handle_closing(user_message)
            elif self.current_state == ConversationState.ERROR:
                response = self._handle_error_recovery(user_message)
            else:
                response = (
                    self._generate_ai_response(user_message)
                    if self.ai_available
                    else "I'm here to help you with pharmacy management solutions. How can I assist you today?"
                )

            # Add bot response to history
            self.conversation_history.append({"role": "assistant", "content": response})

            return response

        except Exception as e:
            logger.error(f"Error processing message: {e}")
            return "I apologize, but I'm experiencing some technical difficulties. Could you please try again?"

    def _handle_info_collection(self, user_message: str) -> str:
        """Handle information collection for new leads."""
        try:
            # Get the current field we're collecting
            current_field = self._get_next_missing_field()

            # Disable AI extraction if it has failed too many times
            if self.ai_available and self.ai_extraction_failures < 3:
                # Try AI-powered extraction for the current field only
                logger.debug(f"Trying AI extraction for field: {current_field}")
                extracted_info = self._extract_pharmacy_info_for_field(
                    user_message, current_field
                )
                logger.debug(f"AI extraction result: {extracted_info}")
                if (
                    extracted_info
                    and current_field in extracted_info
                    and extracted_info[current_field]
                ):
                    # Validate that the extracted info makes sense
                    valid_extraction = True
                    if current_field == "rx_volume":
                        # Convert string to number if needed
                        value = extracted_info[current_field]
                        if isinstance(value, str) and value.isdigit():
                            extracted_info[current_field] = int(value)
                            value = int(value)

                        # Check if rx_volume is a reasonable number
                        if not isinstance(value, (int, float)) or value <= 0:
                            valid_extraction = False

                    if valid_extraction:
                        self.collected_info.update(extracted_info)
                        logger.info(
                            f"AI extracted {current_field}: {extracted_info[current_field]}"
                        )

                        # Check if we have all required information
                        if self._has_complete_info():
                            self.current_state = ConversationState.DISCUSSING_SOLUTIONS
                            rx_volume = self.collected_info.get("rx_volume", 0)
                            return ResponseTemplates.get_solution_benefits(rx_volume)
                        else:
                            # Ask for next missing information
                            next_field = self._get_next_missing_field()
                            return ResponseTemplates.get_collecting_info_response(
                                next_field
                            )
                    else:
                        logger.warning(
                            f"AI extraction returned invalid data for {current_field}: {extracted_info}"
                        )
                        self.ai_extraction_failures += 1
                else:
                    # AI extraction failed for this field, increment failure counter
                    self.ai_extraction_failures += 1
                    if self.ai_extraction_failures >= 3:
                        logger.warning(
                            "AI extraction failed 3 times, switching to manual mode"
                        )

            # Fallback to manual collection (also used when AI extraction fails)
            return self._handle_manual_info_collection(user_message)

        except Exception as e:
            logger.error(f"Error in info collection: {e}")
            return self._handle_manual_info_collection(user_message)

    def _handle_manual_info_collection(self, user_message: str) -> str:
        """Handle manual information collection when AI is unavailable."""
        if self.current_info_field >= len(self.info_collection_fields):
            # We have collected all fields, move to solution discussion
            self.current_state = ConversationState.DISCUSSING_SOLUTIONS
            rx_volume = self.collected_info.get("rx_volume", 0)
            return ResponseTemplates.get_solution_benefits(rx_volume)

        field = self.info_collection_fields[self.current_info_field]
        info_extracted = False

        logger.debug(
            f"Manual info collection: field={field}, message='{user_message}', current_info={self.collected_info}"
        )

        # Simple keyword-based extraction
        if field == "pharmacy_name":
            # First, try to extract pharmacy name if "pharmacy" keyword is present
            if "pharmacy" in user_message.lower():
                words = user_message.split()
                for i, word in enumerate(words):
                    if "pharmacy" in word.lower():
                        if i > 0:
                            self.collected_info["pharmacy_name"] = (
                                words[i - 1] + " " + word
                            )
                        else:
                            self.collected_info["pharmacy_name"] = word
                        info_extracted = True
                        break

            # If no pharmacy name found with keyword, extract any business name
            if not info_extracted:
                words = user_message.split()
                if len(words) <= 3:  # Short response likely a business name
                    self.collected_info["pharmacy_name"] = user_message.strip()
                    info_extracted = True
                elif any(
                    word.lower()
                    in [
                        "natural",
                        "health",
                        "care",
                        "medical",
                        "wellness",
                        "supplements",
                        "products",
                    ]
                    for word in words
                ):
                    # Extract business name containing health-related keywords
                    self.collected_info["pharmacy_name"] = user_message.strip()
                    info_extracted = True
        elif field == "location":
            # Extract location - be more flexible
            words = user_message.split()
            if len(words) <= 3:  # Likely a location name
                self.collected_info["location"] = user_message.strip()
                info_extracted = True
            elif any(
                city in user_message.lower()
                for city in ["city", "town", "street", "avenue", "road"]
            ):
                # Extract location (simple heuristic)
                for i, word in enumerate(words):
                    if any(
                        city in word.lower()
                        for city in ["city", "town", "street", "avenue", "road"]
                    ):
                        if i > 0:
                            self.collected_info["location"] = words[i - 1] + " " + word
                        else:
                            self.collected_info["location"] = word
                        info_extracted = True
                        break
        elif field == "rx_volume":
            # Extract numbers that could be prescription volume
            import re

            numbers = re.findall(r"\d+", user_message)
            if numbers:
                self.collected_info["rx_volume"] = int(numbers[0])
                info_extracted = True
        elif field == "contact_person":
            # Extract contact person - be more flexible
            words = user_message.split()
            if len(words) <= 3:  # Likely a person's name
                self.collected_info["contact_person"] = user_message.strip()
                info_extracted = True
            elif any(
                title in user_message.lower()
                for title in ["manager", "owner", "director", "pharmacist"]
            ):
                # Extract contact person (simple heuristic)
                for i, word in enumerate(words):
                    if any(
                        title in word.lower()
                        for title in ["manager", "owner", "director", "pharmacist"]
                    ):
                        if i > 0:
                            self.collected_info["contact_person"] = (
                                words[i - 1] + " " + word
                            )
                        else:
                            self.collected_info["contact_person"] = word
                        info_extracted = True
                        break
        elif field == "email":
            # Extract email address
            import re

            email_pattern = r"\b[A-Za-z0-9._%+-]+@[A-Za-z0-9.-]+\.[A-Z|a-z]{2,}\b"
            emails = re.findall(email_pattern, user_message)
            if emails:
                self.collected_info["email"] = emails[0]
                info_extracted = True

        # Only increment field if we successfully extracted information
        if info_extracted:
            self.current_info_field += 1
            logger.debug(
                f"Info extracted for {field}: {self.collected_info.get(field)}"
            )
        else:
            logger.debug(f"No info extracted for {field}, will repeat question")

        # Check if we have all required information
        if self._has_complete_info():
            self.current_state = ConversationState.DISCUSSING_SOLUTIONS
            rx_volume = self.collected_info.get("rx_volume", 0)
            logger.info(
                f"All info collected, moving to solution discussion. Collected: {self.collected_info}"
            )
            return ResponseTemplates.get_solution_benefits(rx_volume)
        else:
            # Ask for next field or repeat current field if no info was extracted
            if info_extracted:
                next_field = self.info_collection_fields[self.current_info_field]
                logger.debug(f"Moving to next field: {next_field}")
                return ResponseTemplates.get_collecting_info_response(next_field)
            else:
                # Repeat the same field if no information was extracted
                logger.debug(f"Repeating field: {field}")
                return ResponseTemplates.get_collecting_info_response(field)

    def _has_complete_info(self) -> bool:
        """Check if we have collected all required information."""
        required_fields = [
            "pharmacy_name",
            "location",
            "rx_volume",
            "contact_person",
            "email",
        ]
        return all(
            field in self.collected_info and self.collected_info[field]
            for field in required_fields
        )

    def _get_next_missing_field(self) -> str:
        """Get the next missing field to collect."""
        required_fields = [
            "pharmacy_name",
            "location",
            "rx_volume",
            "contact_person",
            "email",
        ]
        for field in required_fields:
            if field not in self.collected_info or not self.collected_info[field]:
                return field
        return "pharmacy_name"  # fallback

    def _handle_solution_discussion(self, user_message: str) -> str:
        """Handle solution discussion phase."""
        # Check if user is interested in follow-up
        if any(
            keyword in user_message.lower()
            for keyword in ["yes", "interested", "more", "information", "details"]
        ):
            self.current_state = ConversationState.OFFERING_FOLLOW_UP
            return ResponseTemplates.get_follow_up_options()
        else:
            # Continue discussing solutions
            if self.ai_available:
                return self._generate_ai_response(user_message)
            else:
                return "I'd be happy to help you get started. We can send you detailed information or schedule a consultation call. What would work best for you?"

    def _handle_follow_up_offer(self, user_message: str) -> str:
        """Handle follow-up action offers."""
        if "email" in user_message.lower():
            # Handle email request
            email = self._get_email_address()
            if email:
                pharmacy_name = self._get_pharmacy_name()
                result = self.follow_up_actions.send_welcome_email(
                    PharmacyData(
                        id="new",
                        name=pharmacy_name,
                        phone="",
                        location="",
                        rx_volume=self.collected_info.get("rx_volume", 0),
                        contact_person=self.collected_info.get("contact_person", ""),
                        email=email,
                    )
                )
                self.current_state = ConversationState.CLOSING
                return PromptTemplates.format_successful_closing(
                    "sent you detailed information via email",
                    "receive the email within the next few minutes",
                    pharmacy_name,
                )
            else:
                return (
                    "I'd be happy to send you information. What's your email address?"
                )
        elif "call" in user_message.lower() or "consultation" in user_message.lower():
            # Handle callback request
            self.current_state = ConversationState.SCHEDULING
            return PromptTemplates.format_callback_offer()
        else:
            return "I can send you detailed information via email or schedule a consultation call. Which would you prefer?"

    def _handle_scheduling(self, user_message: str) -> str:
        """Handle callback scheduling."""
        # Extract time preference from message
        time_keywords = [
            "tomorrow",
            "next week",
            "monday",
            "tuesday",
            "wednesday",
            "thursday",
            "friday",
            "morning",
            "afternoon",
            "evening",
        ]
        preferred_time = "tomorrow at 2 PM"  # default

        for keyword in time_keywords:
            if keyword in user_message.lower():
                preferred_time = f"{keyword} at 2 PM"
                break

        pharmacy_name = self._get_pharmacy_name()
        phone = self.pharmacy_data.phone if self.pharmacy_data else ""

        result = self.follow_up_actions.schedule_consultation(
            PharmacyData(
                id="new",
                name=pharmacy_name,
                phone=phone,
                location="",
                rx_volume=self.collected_info.get("rx_volume", 0),
                contact_person=self.collected_info.get("contact_person", ""),
                email="",
            ),
            preferred_time,
        )

        self.current_state = ConversationState.CLOSING
        return PromptTemplates.format_successful_closing(
            "scheduled a consultation call for you",
            "receive a confirmation email with the details",
            pharmacy_name,
        )

    def _handle_closing(self, user_message: str) -> str:
        """Handle conversation closing."""
        if any(
            keyword in user_message.lower()
            for keyword in ["no", "nothing", "goodbye", "bye", "thanks"]
        ):
            return PromptTemplates.GENERAL_CLOSING
        else:
            return "Is there anything else I can help you with today?"

    def _handle_error_recovery(self, user_message: str) -> str:
        """Handle error recovery."""
        try:
            # Try to recover by switching to manual mode
            self.ai_available = False
            self.current_state = ConversationState.COLLECTING_INFO
            return "I'm back online now. Let me help you with your pharmacy management needs. Could you tell me about your pharmacy?"
        except Exception as e:
            logger.error(f"Error in error recovery: {e}")
            return "I'm experiencing technical difficulties. Please try calling back later."

    def _get_email_address(self) -> Optional[str]:
        """Get email address from collected info or pharmacy data."""
        if self.collected_info.get("email"):
            return self.collected_info["email"]
        elif self.pharmacy_data and self.pharmacy_data.email:
            return self.pharmacy_data.email
        return None

    def _get_pharmacy_name(self) -> str:
        """Get pharmacy name from collected info or pharmacy data."""
        if self.collected_info.get("pharmacy_name"):
            return self.collected_info["pharmacy_name"]
        elif self.pharmacy_data:
            return self.pharmacy_data.name
        return "your pharmacy"

    def _extract_pharmacy_info_for_field(
        self, user_message: str, field: str
    ) -> Dict[str, Any]:
        """Extract pharmacy information for a specific field from user message using AI."""
        if not self.ai_available:
            return {}

        try:
            field_descriptions = {
                "pharmacy_name": "business name, pharmacy name, or company name",
                "location": "city, state, or address",
                "rx_volume": "number representing prescription volume",
                "contact_person": "person's name or title",
                "email": "email address",
            }

            field_examples = {
                "pharmacy_name": "Naturally, Natural Products, Main Street Pharmacy",
                "location": "Orlando, New York, Los Angeles",
                "rx_volume": "1000, 500, 2000",
                "contact_person": "John Smith, My manager, Sarah Johnson",
                "email": "john@pharmacy.com",
            }

            prompt = f"""
You are a data extraction assistant. Extract {field} information from this message: "{user_message}"

IMPORTANT: You must respond with ONLY a valid JSON object. No other text.

Return a JSON object with only the {field} field (use null if not found):
{{"{field}": "extracted_value"}}

Field description: {field_descriptions.get(field, field)}
Examples: {field_examples.get(field, "various")}

Extraction rules:
- {field}: Extract {field_descriptions.get(field, field)}
- For rx_volume: Return the number as a number, not a string (e.g., 1000 not "1000")
- For location: Extract place names like "Orlando", "New York", "Los Angeles"
- For contact_person: Extract person names like "John", "Sarah", "My manager"
- For email: Extract valid email addresses
- If no {field} information can be extracted, return: {{"{field}": null}}

Example response format:
{{"{field}": "extracted_value"}}
"""

            response = self.client.chat.completions.create(
                model="gpt-4o-mini",
                messages=[{"role": "user", "content": prompt}],
                temperature=0.0,  # Use 0 temperature for more consistent JSON output
                max_tokens=100,
            )

            content = response.choices[0].message.content.strip()
            if not content:
                logger.warning(f"AI returned empty response for {field} extraction")
                return {}

            # Try to clean the response if it contains extra text
            if content.startswith("```json"):
                content = content[7:]
            if content.endswith("```"):
                content = content[:-3]
            content = content.strip()

            result = json.loads(content)
            return {k: v for k, v in result.items() if v is not None}

        except json.JSONDecodeError as e:
            logger.error(f"Invalid JSON response from AI for {field}: {e}")
            logger.error(
                f"Raw response: {content if 'content' in locals() else 'No content'}"
            )
            return {}
        except Exception as e:
            logger.error(f"Error extracting {field} info: {e}")
            return {}

    def _extract_pharmacy_info(self, user_message: str) -> Dict[str, Any]:
        """Extract pharmacy information from user message using AI."""
        if not self.ai_available:
            return {}

        try:
            prompt = f"""
You are a data extraction assistant. Extract pharmacy information from this message: "{user_message}"

IMPORTANT: You must respond with ONLY a valid JSON object. No other text.

Return a JSON object with these fields (use null if not found):
- pharmacy_name: string (business name, pharmacy name, or company name)
- location: string (city, state, or address)
- rx_volume: number (extract numeric value for prescription volume)
- contact_person: string (person's name or title)
- email: string (email address)

Extraction rules:
- pharmacy_name: Extract business names like "Naturally", "Natural Products", "Main Street Pharmacy"
- location: Extract place names like "Orlando", "New York", "Los Angeles"
- rx_volume: Extract ONLY numbers that represent prescription volume (e.g., 1000, 500, 2000)
- contact_person: Extract person names or titles like "John Smith", "My manager", "Sarah Johnson"
- email: Extract valid email addresses

IMPORTANT: Only extract rx_volume if the message contains a number that could reasonably be prescription volume. Do not extract other numbers as rx_volume.

Example response format:
{{"pharmacy_name": "Main Street Pharmacy", "location": "New York", "rx_volume": 500, "contact_person": "John Smith", "email": "john@pharmacy.com"}}

If no information can be extracted, return:
{{"pharmacy_name": null, "location": null, "rx_volume": null, "contact_person": null, "email": null}}
"""

            response = self.client.chat.completions.create(
                model="gpt-4o-mini",
                messages=[{"role": "user", "content": prompt}],
                temperature=0.0,  # Use 0 temperature for more consistent JSON output
                max_tokens=200,
            )

            content = response.choices[0].message.content.strip()
            if not content:
                logger.warning(
                    "AI returned empty response for pharmacy info extraction"
                )
                return {}

            # Try to clean the response if it contains extra text
            if content.startswith("```json"):
                content = content[7:]
            if content.endswith("```"):
                content = content[:-3]
            content = content.strip()

            result = json.loads(content)
            return {k: v for k, v in result.items() if v is not None}

        except json.JSONDecodeError as e:
            logger.error(f"Invalid JSON response from AI: {e}")
            logger.error(
                f"Raw response: {content if 'content' in locals() else 'No content'}"
            )
            return {}
        except Exception as e:
            logger.error(f"Error extracting pharmacy info: {e}")
            return {}

    def _generate_ai_response(self, user_message: str) -> str:
        """Generate AI response using OpenAI API."""
        if not self.ai_available:
            return "I'm currently in fallback mode. Let me help you with your pharmacy management needs."

        try:
            # Prepare messages for the API
            messages = [{"role": "system", "content": PromptTemplates.SYSTEM_PROMPT}]

            # Add conversation history (limit to last 10 messages to avoid token limits)
            messages.extend(self.conversation_history[-10:])

            # Add current user message
            messages.append({"role": "user", "content": user_message})

            response = self.client.chat.completions.create(
                model="gpt-4o-mini",
                messages=messages,
                temperature=0.7,
                max_tokens=300,
            )

            return response.choices[0].message.content

        except Exception as e:
            logger.error(f"Error generating AI response: {e}")
            return "I apologize, but I'm having trouble generating a response right now. Could you please try again?"

    def get_conversation_summary(self) -> Dict[str, Any]:
        """Get a summary of the current conversation."""
        return {
            "state": self.current_state,
            "pharmacy_data": (
                self.pharmacy_data.__dict__ if self.pharmacy_data else None
            ),
            "collected_info": self.collected_info,
            "conversation_length": len(self.conversation_history),
            "ai_available": self.ai_available,
            "current_info_field": self.current_info_field,
            "info_collection_fields": self.info_collection_fields,
            "follow_up_actions": {
                "emails_sent": len(self.follow_up_actions.get_email_history()),
                "callbacks_scheduled": len(
                    self.follow_up_actions.get_callback_history()
                ),
            },
        }

    def reset_conversation(self):
        """Reset the conversation state."""
        self.current_state = ConversationState.GREETING
        self.conversation_history = []
        self.pharmacy_data = None
        self.collected_info = {}
        self.current_info_field = 0
        self.follow_up_actions.clear_history()
        logger.info("Conversation reset")
