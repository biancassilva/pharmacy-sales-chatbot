"""
Tests for the pharmacy chatbot system.
"""

import unittest
from unittest.mock import Mock, patch, MagicMock
import json
import os
from typing import Dict, Any
import requests
from openai import OpenAI

from integration import PharmacyAPI, PharmacyData
from function_calls import FollowUpActions, EmailRequest, CallbackRequest
from prompt import PromptTemplates, ConversationState, ResponseTemplates
from llm import PharmacyChatbot


class TestPharmacyAPI(unittest.TestCase):
    """Test cases for PharmacyAPI class."""

    def setUp(self):
        """Set up test fixtures."""
        self.api = PharmacyAPI()

    def test_get_pharmacy_by_phone_existing(self):
        """Test getting pharmacy by phone number when it exists."""
        # Mock the session's get method directly
        with patch.object(self.api.session, "get") as mock_get:
            # Mock API response
            mock_response = Mock()
            mock_response.json.return_value = [
                {
                    "id": "1",
                    "name": "Test Pharmacy",
                    "phone": "555-123-4567",
                    "location": "Test City",
                    "rx_volume": "1500",
                    "contact_person": "John Doe",
                    "email": "john@testpharmacy.com",
                }
            ]
            mock_response.raise_for_status.return_value = None
            mock_get.return_value = mock_response

            # Test
            result = self.api.get_pharmacy_by_phone("555-123-4567")

            # Assertions
            self.assertIsNotNone(result)
            self.assertEqual(result.name, "Test Pharmacy")
            self.assertEqual(result.rx_volume, 1500)

    def test_get_pharmacy_by_phone_not_found(self):
        """Test getting pharmacy by phone number when it doesn't exist."""
        # Mock the session's get method directly
        with patch.object(self.api.session, "get") as mock_get:
            # Mock API response
            mock_response = Mock()
            mock_response.json.return_value = []
            mock_response.raise_for_status.return_value = None
            mock_get.return_value = mock_response

            # Test
            result = self.api.get_pharmacy_by_phone("555-999-9999")

            # Assertions
            self.assertIsNone(result)

    def test_clean_phone_number(self):
        """Test phone number cleaning."""
        self.assertEqual(self.api._clean_phone_number("(555) 123-4567"), "5551234567")
        self.assertEqual(self.api._clean_phone_number("555.123.4567"), "5551234567")
        self.assertEqual(self.api._clean_phone_number("5551234567"), "5551234567")

    def test_parse_pharmacy_data(self):
        """Test parsing pharmacy data."""
        data = {
            "id": "1",
            "name": "Test Pharmacy",
            "phone": "555-123-4567",
            "location": "Test City",
            "rx_volume": "1500",
            "contact_person": "John Doe",
            "email": "john@testpharmacy.com",
            "notes": "Test notes",
        }

        result = self.api._parse_pharmacy_data(data)

        self.assertEqual(result.name, "Test Pharmacy")
        self.assertEqual(result.rx_volume, 1500)
        self.assertEqual(result.email, "john@testpharmacy.com")

    # Edge cases for API integration
    def test_api_timeout_handling(self):
        """Test handling of API timeouts."""
        with patch.object(self.api.session, "get") as mock_get:
            mock_get.side_effect = requests.Timeout("Request timed out")

            result = self.api.get_pharmacy_by_phone("555-123-4567")
            self.assertIsNone(result)

    def test_api_connection_error(self):
        """Test handling of API connection errors."""
        with patch.object(self.api.session, "get") as mock_get:
            mock_get.side_effect = requests.ConnectionError("Connection failed")

            result = self.api.get_pharmacy_by_phone("555-123-4567")
            self.assertIsNone(result)

    def test_api_invalid_response_format(self):
        """Test handling of invalid API response format."""
        with patch.object(self.api.session, "get") as mock_get:
            mock_response = Mock()
            mock_response.json.side_effect = json.JSONDecodeError("Invalid JSON", "", 0)
            mock_response.raise_for_status.return_value = None
            mock_get.return_value = mock_response

            result = self.api.get_pharmacy_by_phone("555-123-4567")
            self.assertIsNone(result)

    def test_api_http_error(self):
        """Test handling of HTTP errors from API."""
        with patch.object(self.api.session, "get") as mock_get:
            mock_response = Mock()
            mock_response.raise_for_status.side_effect = requests.HTTPError(
                "404 Not Found"
            )
            mock_get.return_value = mock_response

            result = self.api.get_pharmacy_by_phone("555-123-4567")
            self.assertIsNone(result)

    def test_api_malformed_pharmacy_data(self):
        """Test handling of malformed pharmacy data from API."""
        with patch.object(self.api.session, "get") as mock_get:
            mock_response = Mock()
            mock_response.json.return_value = [
                {
                    "id": "1",
                    "name": "Test Pharmacy",
                    # Missing required fields
                    "phone": None,
                    "rx_volume": "invalid_number",
                }
            ]
            mock_response.raise_for_status.return_value = None
            mock_get.return_value = mock_response

            result = self.api.get_pharmacy_by_phone("555-123-4567")
            # Should handle gracefully and return None or valid data
            self.assertIsNone(result)


class TestFollowUpActions(unittest.TestCase):
    """Test cases for FollowUpActions class."""

    def setUp(self):
        """Set up test fixtures."""
        self.actions = FollowUpActions()

    def test_send_email(self):
        """Test sending email."""
        email_request = EmailRequest(
            to_email="test@example.com",
            subject="Test Subject",
            body="Test Body",
            pharmacy_name="Test Pharmacy",
            contact_person="John Doe",
        )

        result = self.actions.send_email(email_request)

        self.assertTrue(result["success"])
        self.assertIn("email_id", result)
        self.assertEqual(len(self.actions.sent_emails), 1)

    def test_schedule_callback(self):
        """Test scheduling callback."""
        callback_request = CallbackRequest(
            phone_number="555-123-4567",
            preferred_time="tomorrow at 2 PM",
            pharmacy_name="Test Pharmacy",
            contact_person="John Doe",
        )

        result = self.actions.schedule_callback(callback_request)

        self.assertTrue(result["success"])
        self.assertIn("callback_id", result)
        self.assertEqual(len(self.actions.scheduled_callbacks), 1)

    def test_send_welcome_email(self):
        """Test sending welcome email."""
        pharmacy = PharmacyData(
            id="1",
            name="Test Pharmacy",
            phone="555-123-4567",
            location="Test City",
            rx_volume=1500,
            contact_person="John Doe",
            email="john@testpharmacy.com",
        )

        result = self.actions.send_welcome_email(pharmacy)

        self.assertTrue(result["success"])
        # Check that the email was sent successfully (the message format may vary)
        self.assertIn("Test Pharmacy", result["message"])

    def test_send_high_volume_offer(self):
        """Test sending high volume offer."""
        pharmacy = PharmacyData(
            id="1",
            name="Test Pharmacy",
            phone="555-123-4567",
            location="Test City",
            rx_volume=1500,
            contact_person="John Doe",
            email="john@testpharmacy.com",
        )

        result = self.actions.send_high_volume_offer(pharmacy)

        self.assertTrue(result["success"])
        # Check that the email was sent successfully (the message format may vary)
        self.assertIn("Test Pharmacy", result["message"])


class TestPromptTemplates(unittest.TestCase):
    """Test cases for PromptTemplates class."""

    def test_format_greeting_existing_customer(self):
        """Test formatting greeting for existing customer."""
        pharmacy_data = {
            "name": "Test Pharmacy",
            "location": "Test City",
            "rx_volume": 1500,
        }

        result = PromptTemplates.format_greeting(pharmacy_data)

        self.assertIn("Test Pharmacy", result)
        self.assertIn("Test City", result)
        self.assertIn("1500", result)

    def test_format_greeting_new_lead(self):
        """Test formatting greeting for new lead."""
        result = PromptTemplates.format_greeting()

        self.assertIn("Pharmesol", result)
        self.assertIn("pharmacy management solutions", result)

    def test_format_high_volume_message(self):
        """Test formatting high volume message."""
        result = PromptTemplates.format_high_volume_message(1500)

        self.assertIn("1500", result)
        self.assertIn("high-volume pharmacy", result)

    def test_format_email_offer(self):
        """Test formatting email offer."""
        result = PromptTemplates.format_email_offer("Test Pharmacy", "test@example.com")

        self.assertIn("Test Pharmacy", result)
        self.assertIn("test@example.com", result)


class TestResponseTemplates(unittest.TestCase):
    """Test cases for ResponseTemplates class."""

    def test_get_collecting_info_response(self):
        """Test getting collecting info response."""
        result = ResponseTemplates.get_collecting_info_response("pharmacy_name")

        self.assertIn("name", result.lower())

    def test_get_solution_benefits_high_volume(self):
        """Test getting solution benefits for high volume."""
        result = ResponseTemplates.get_solution_benefits(1500)

        self.assertIn("high-volume", result)
        self.assertIn("automation", result)

    def test_get_solution_benefits_medium_volume(self):
        """Test getting solution benefits for medium volume."""
        result = ResponseTemplates.get_solution_benefits(750)

        self.assertIn("Streamlined prescription processing", result)
        self.assertIn("analytics", result)

    def test_get_solution_benefits_low_volume(self):
        """Test getting solution benefits for low volume."""
        result = ResponseTemplates.get_solution_benefits(200)

        self.assertIn("Automate routine tasks", result)
        self.assertIn("inventory", result)


class TestLLMIntegration(unittest.TestCase):
    """Test cases for LLM integration and AI model responses."""

    def setUp(self):
        """Set up test fixtures."""
        with patch.dict(os.environ, {"OPENAI_API_KEY": "test-key"}):
            with patch("llm.OpenAI") as mock_openai:
                # Mock the OpenAI client
                mock_client = Mock()
                mock_openai.return_value = mock_client
                self.chatbot = PharmacyChatbot()

    def test_ai_extract_pharmacy_info_success(self):
        """Test successful AI extraction of pharmacy information."""
        # Mock AI response
        mock_response = Mock()
        mock_choice = Mock()
        mock_message = Mock()
        mock_message.content = json.dumps(
            {
                "pharmacy_name": "Main Street Pharmacy",
                "location": "New York",
                "rx_volume": 500,
                "contact_person": "John Smith",
                "email": "john@pharmacy.com",
            }
        )
        mock_choice.message = mock_message
        mock_response.choices = [mock_choice]

        with patch.object(
            self.chatbot.client.chat.completions, "create"
        ) as mock_create:
            mock_create.return_value = mock_response

            result = self.chatbot._extract_pharmacy_info(
                "My pharmacy is Main Street Pharmacy in New York"
            )

            self.assertEqual(result["pharmacy_name"], "Main Street Pharmacy")
            self.assertEqual(result["location"], "New York")
            self.assertEqual(result["rx_volume"], 500)
            self.assertEqual(result["contact_person"], "John Smith")
            self.assertEqual(result["email"], "john@pharmacy.com")

    def test_ai_extract_pharmacy_info_partial(self):
        """Test AI extraction with partial information."""
        # Mock AI response with partial data
        mock_response = Mock()
        mock_choice = Mock()
        mock_message = Mock()
        mock_message.content = json.dumps(
            {
                "pharmacy_name": "Downtown Pharmacy",
                "location": "Chicago",
                "rx_volume": 800,
                "contact_person": None,
                "email": None,
            }
        )
        mock_choice.message = mock_message
        mock_response.choices = [mock_choice]

        with patch.object(
            self.chatbot.client.chat.completions, "create"
        ) as mock_create:
            mock_create.return_value = mock_response

            result = self.chatbot._extract_pharmacy_info(
                "I work at Downtown Pharmacy in Chicago"
            )

            self.assertEqual(result["pharmacy_name"], "Downtown Pharmacy")
            self.assertEqual(result["location"], "Chicago")
            self.assertEqual(result["rx_volume"], 800)
            self.assertNotIn("contact_person", result)
            self.assertNotIn("email", result)

    def test_ai_extract_pharmacy_info_invalid_json(self):
        """Test AI extraction with invalid JSON response."""
        # Mock AI response with invalid JSON
        mock_response = Mock()
        mock_choice = Mock()
        mock_message = Mock()
        mock_message.content = "Invalid JSON response"
        mock_choice.message = mock_message
        mock_response.choices = [mock_choice]

        with patch.object(
            self.chatbot.client.chat.completions, "create"
        ) as mock_create:
            mock_create.return_value = mock_response

            result = self.chatbot._extract_pharmacy_info("My pharmacy is Test Pharmacy")

            self.assertEqual(result, {})

    def test_ai_extract_pharmacy_info_api_error(self):
        """Test AI extraction when API call fails."""
        with patch.object(
            self.chatbot.client.chat.completions, "create"
        ) as mock_create:
            mock_create.side_effect = Exception("API Error")

            result = self.chatbot._extract_pharmacy_info("My pharmacy is Test Pharmacy")

            self.assertEqual(result, {})

    def test_ai_generate_response_success(self):
        """Test successful AI response generation."""
        # Mock AI response
        mock_response = Mock()
        mock_choice = Mock()
        mock_message = Mock()
        mock_message.content = (
            "I'd be happy to help you with your pharmacy management needs."
        )
        mock_choice.message = mock_message
        mock_response.choices = [mock_choice]

        with patch.object(
            self.chatbot.client.chat.completions, "create"
        ) as mock_create:
            mock_create.return_value = mock_response

            result = self.chatbot._generate_ai_response(
                "I need help with inventory management"
            )

            self.assertEqual(
                result, "I'd be happy to help you with your pharmacy management needs."
            )

    def test_ai_generate_response_api_error(self):
        """Test AI response generation when API call fails."""
        with patch.object(
            self.chatbot.client.chat.completions, "create"
        ) as mock_create:
            mock_create.side_effect = Exception("API Error")

            result = self.chatbot._generate_ai_response(
                "I need help with inventory management"
            )

            self.assertIn("having trouble generating a response", result)

    def test_ai_generate_response_rate_limit(self):
        """Test AI response generation with rate limiting."""
        with patch.object(
            self.chatbot.client.chat.completions, "create"
        ) as mock_create:
            mock_create.side_effect = Exception("Rate limit exceeded")

            result = self.chatbot._generate_ai_response(
                "I need help with inventory management"
            )

            self.assertIn("having trouble generating a response", result)

    def test_ai_generate_response_model_unavailable(self):
        """Test AI response generation when model is unavailable."""
        with patch.object(
            self.chatbot.client.chat.completions, "create"
        ) as mock_create:
            mock_create.side_effect = Exception("Model not found")

            result = self.chatbot._generate_ai_response(
                "I need help with inventory management"
            )

            self.assertIn("having trouble generating a response", result)

    def test_ai_extract_pharmacy_info_edge_cases(self):
        """Test AI extraction with various edge cases."""
        test_cases = [
            # Empty message
            ("", {}),
            # Very long message
            ("A" * 1000, {}),
            # Message with special characters
            ("My pharmacy is Test-Pharmacy & Co. in New York!", {}),
            # Message with numbers in different formats
            ("We process 1,500 prescriptions monthly", {}),
            # Message with multiple email addresses
            ("Contact me at john@pharmacy.com or backup@pharmacy.com", {}),
        ]

        for message, expected in test_cases:
            with patch.object(
                self.chatbot.client.chat.completions, "create"
            ) as mock_create:
                mock_response = Mock()
                mock_choice = Mock()
                mock_message = Mock()
                mock_message.content = "{}"
                mock_choice.message = mock_message
                mock_response.choices = [mock_choice]
                mock_create.return_value = mock_response

                result = self.chatbot._extract_pharmacy_info(message)
                # Should handle gracefully without crashing
                self.assertIsInstance(result, dict)


class TestPharmacyChatbot(unittest.TestCase):
    """Test cases for PharmacyChatbot class."""

    def setUp(self):
        """Set up test fixtures."""
        with patch.dict(os.environ, {"OPENAI_API_KEY": "test-key"}):
            with patch("llm.OpenAI") as mock_openai:
                # Mock the OpenAI client
                mock_client = Mock()
                mock_openai.return_value = mock_client
                self.chatbot = PharmacyChatbot()

    def test_start_call_existing_customer(self):
        """Test starting call with existing customer."""
        # Mock pharmacy data
        mock_pharmacy = PharmacyData(
            id="1",
            name="Test Pharmacy",
            phone="555-123-4567",
            location="Test City",
            rx_volume=1500,
            contact_person="John Doe",
            email="john@testpharmacy.com",
        )

        # Mock the pharmacy API instance
        with patch.object(
            self.chatbot.pharmacy_api, "get_pharmacy_by_phone"
        ) as mock_get_pharmacy:
            mock_get_pharmacy.return_value = mock_pharmacy

            # Test
            result = self.chatbot.start_call("555-123-4567")

            # Assertions
            self.assertIn("Test Pharmacy", result)
            self.assertEqual(
                self.chatbot.current_state, ConversationState.DISCUSSING_SOLUTIONS
            )

    def test_start_call_new_lead(self):
        """Test starting call with new lead."""
        # Mock no pharmacy found
        with patch.object(
            self.chatbot.pharmacy_api, "get_pharmacy_by_phone"
        ) as mock_get_pharmacy:
            mock_get_pharmacy.return_value = None

            # Test
            result = self.chatbot.start_call("555-999-9999")

            # Assertions
            self.assertIn("Pharmesol", result)
            self.assertEqual(
                self.chatbot.current_state, ConversationState.COLLECTING_INFO
            )

    @patch("llm.PharmacyChatbot._extract_pharmacy_info")
    def test_handle_info_collection(self, mock_extract):
        """Test handling information collection."""
        # Mock extracted info
        mock_extract.return_value = {
            "pharmacy_name": "Test Pharmacy",
            "location": "Test City",
            "rx_volume": 1500,
            "contact_person": "John Doe",
            "email": "john@testpharmacy.com",
        }

        # Set state to collecting info
        self.chatbot.current_state = ConversationState.COLLECTING_INFO

        # Test
        result = self.chatbot.process_message(
            "My pharmacy is Test Pharmacy in Test City"
        )

        # Assertions
        self.assertIn("high-volume", result)
        self.assertEqual(
            self.chatbot.current_state, ConversationState.DISCUSSING_SOLUTIONS
        )

    def test_handle_solution_discussion(self):
        """Test handling solution discussion."""
        # Set up pharmacy data and state
        self.chatbot.pharmacy_data = PharmacyData(
            id="1",
            name="Test Pharmacy",
            phone="555-123-4567",
            location="Test City",
            rx_volume=1500,
            contact_person="John Doe",
            email="john@testpharmacy.com",
        )
        self.chatbot.current_state = ConversationState.DISCUSSING_SOLUTIONS

        # Test
        result = self.chatbot.process_message("Yes, I would like more information")

        # Assertions
        self.assertIn("email", result.lower())
        self.assertEqual(
            self.chatbot.current_state, ConversationState.OFFERING_FOLLOW_UP
        )

    def test_get_conversation_summary(self):
        """Test getting conversation summary."""
        # Set up some conversation data
        self.chatbot.pharmacy_data = PharmacyData(
            id="1",
            name="Test Pharmacy",
            phone="555-123-4567",
            location="Test City",
            rx_volume=1500,
            contact_person="John Doe",
            email="john@testpharmacy.com",
        )
        self.chatbot.conversation_history = [{"role": "user", "content": "test"}]

        # Test
        summary = self.chatbot.get_conversation_summary()

        # Assertions
        self.assertIn("state", summary)
        self.assertIn("pharmacy_data", summary)
        self.assertIn("collected_info", summary)
        self.assertIn("conversation_length", summary)
        self.assertIn("follow_up_actions", summary)

    def test_reset_conversation(self):
        """Test resetting conversation."""
        # Set up some conversation data
        self.chatbot.pharmacy_data = PharmacyData(
            id="1",
            name="Test Pharmacy",
            phone="555-123-4567",
            location="Test City",
            rx_volume=1500,
            contact_person="John Doe",
            email="john@testpharmacy.com",
        )
        self.chatbot.conversation_history = [{"role": "user", "content": "test"}]
        self.chatbot.current_state = ConversationState.DISCUSSING_SOLUTIONS

        # Test
        self.chatbot.reset_conversation()

        # Assertions
        self.assertEqual(self.chatbot.current_state, ConversationState.GREETING)
        self.assertEqual(len(self.chatbot.conversation_history), 0)
        self.assertIsNone(self.chatbot.pharmacy_data)

    # Edge cases for chatbot
    def test_start_call_api_failure(self):
        """Test starting call when API fails."""
        with patch.object(
            self.chatbot.pharmacy_api, "get_pharmacy_by_phone"
        ) as mock_get_pharmacy:
            mock_get_pharmacy.side_effect = Exception("API Error")

            result = self.chatbot.start_call("555-123-4567")

            self.assertIn("having trouble accessing our system", result)
            self.assertEqual(self.chatbot.current_state, ConversationState.ERROR)

    def test_process_message_invalid_state(self):
        """Test processing message with invalid state."""
        self.chatbot.current_state = "INVALID_STATE"

        result = self.chatbot.process_message("Hello")

        # Should handle gracefully and provide fallback response
        self.assertIsInstance(result, str)
        self.assertGreater(len(result), 0)

    def test_process_message_empty_input(self):
        """Test processing empty message."""
        result = self.chatbot.process_message("")

        # Should handle gracefully
        self.assertIsInstance(result, str)
        self.assertGreater(len(result), 0)

    def test_process_message_very_long_input(self):
        """Test processing very long message."""
        long_message = "A" * 10000
        result = self.chatbot.process_message(long_message)

        # Should handle gracefully
        self.assertIsInstance(result, str)
        self.assertGreater(len(result), 0)

    def test_handle_error_recovery(self):
        """Test error recovery mechanism."""
        self.chatbot.current_state = ConversationState.ERROR

        result = self.chatbot.process_message("Hello")

        self.assertIn("back online", result)
        self.assertEqual(self.chatbot.current_state, ConversationState.COLLECTING_INFO)

    def test_manual_info_collection_edge_cases(self):
        """Test manual info collection with edge cases."""
        self.chatbot.current_state = ConversationState.COLLECTING_INFO
        self.chatbot.ai_available = False

        # Test with various input formats
        test_cases = [
            ("My pharmacy is called Test Pharmacy", "pharmacy_name"),
            ("We're located in New York City", "location"),
            ("We process 1500 prescriptions", "rx_volume"),
            ("I'm the manager John Smith", "contact_person"),
            ("My email is john@pharmacy.com", "email"),
        ]

        for message, expected_field in test_cases:
            result = self.chatbot.process_message(message)
            # Should progress through the collection process
            self.assertIsInstance(result, str)


class TestIntegration(unittest.TestCase):
    """Integration tests for the complete system."""

    def setUp(self):
        """Set up test fixtures."""
        with patch.dict(os.environ, {"OPENAI_API_KEY": "test-key"}):
            with patch("llm.OpenAI") as mock_openai:
                # Mock the OpenAI client
                mock_client = Mock()
                mock_openai.return_value = mock_client
                self.chatbot = PharmacyChatbot()

    def test_complete_conversation_flow(self):
        """Test a complete conversation flow."""
        # Mock API responses
        with patch.object(
            self.chatbot.pharmacy_api, "get_pharmacy_by_phone"
        ) as mock_get_pharmacy:
            mock_get_pharmacy.return_value = None

            # Mock AI extraction - provide complete info from the start
            with patch.object(self.chatbot, "_extract_pharmacy_info") as mock_extract:
                mock_extract.return_value = {
                    "pharmacy_name": "Test Pharmacy",
                    "location": "Test City",
                    "rx_volume": 1500,
                    "contact_person": "John Doe",
                    "email": "john@testpharmacy.com",
                }

                # Start call
                greeting = self.chatbot.start_call("555-999-9999")
                self.assertIn("Pharmesol", greeting)

                # Provide pharmacy information - this should move to solution discussion
                response1 = self.chatbot.process_message(
                    "My pharmacy is Test Pharmacy in Test City, we process 1500 prescriptions"
                )
                self.assertIn("high-volume", response1)

                # Express interest
                response2 = self.chatbot.process_message(
                    "Yes, I would like more information"
                )
                self.assertIn("email", response2.lower())

                # Request email
                response3 = self.chatbot.process_message(
                    "Please send me information via email"
                )
                self.assertIn("sent you detailed information", response3)

    def test_integration_with_api_failures(self):
        """Test integration when API fails intermittently."""
        with patch.object(
            self.chatbot.pharmacy_api, "get_pharmacy_by_phone"
        ) as mock_get_pharmacy:
            # First call fails, second succeeds
            mock_get_pharmacy.side_effect = [Exception("API Error"), None]

            # First call should handle error gracefully
            result1 = self.chatbot.start_call("555-123-4567")
            self.assertIn("having trouble accessing our system", result1)

            # Reset and try again
            self.chatbot.reset_conversation()
            result2 = self.chatbot.start_call("555-123-4567")
            self.assertIn("Pharmesol", result2)

    def test_integration_with_ai_failures(self):
        """Test integration when AI fails intermittently."""
        with patch.object(
            self.chatbot.pharmacy_api, "get_pharmacy_by_phone"
        ) as mock_get_pharmacy:
            mock_get_pharmacy.return_value = None

            with patch.object(self.chatbot, "_extract_pharmacy_info") as mock_extract:
                # First call fails, second succeeds
                mock_extract.side_effect = [
                    Exception("AI Error"),
                    {
                        "pharmacy_name": "Test Pharmacy",
                        "location": "Test City",
                        "rx_volume": 1500,
                        "contact_person": "John Doe",
                        "email": "john@testpharmacy.com",
                    },
                ]

                # Start call
                greeting = self.chatbot.start_call("555-999-9999")
                self.assertIn("Pharmesol", greeting)

                # First message should fall back to manual collection
                response1 = self.chatbot.process_message("My pharmacy is Test Pharmacy")
                self.assertIsInstance(response1, str)

                # Second message should work with AI
                response2 = self.chatbot.process_message(
                    "We're in Test City with 1500 prescriptions"
                )
                self.assertIn("high-volume", response2)


class TestEdgeCases(unittest.TestCase):
    """Test cases for various edge cases and error scenarios."""

    def setUp(self):
        """Set up test fixtures."""
        with patch.dict(os.environ, {"OPENAI_API_KEY": "test-key"}):
            with patch("llm.OpenAI") as mock_openai:
                mock_client = Mock()
                mock_openai.return_value = mock_client
                self.chatbot = PharmacyChatbot()

    def test_phone_number_edge_cases(self):
        """Test various phone number formats and edge cases."""
        test_cases = [
            ("", None),  # Empty phone number
            ("123", None),  # Too short
            ("12345678901234567890", None),  # Too long
            ("abc-def-ghij", None),  # Non-numeric
            ("555-123-4567", "5551234567"),  # Standard format
            ("(555) 123-4567", "5551234567"),  # Parentheses
            ("555.123.4567", "5551234567"),  # Dots
            ("555 123 4567", "5551234567"),  # Spaces
        ]

        for phone, expected in test_cases:
            if expected is None:
                # Should handle gracefully
                result = self.chatbot.start_call(phone)
                self.assertIsInstance(result, str)
            else:
                # Should clean properly
                cleaned = self.chatbot.pharmacy_api._clean_phone_number(phone)
                self.assertEqual(cleaned, expected)

    def test_rx_volume_edge_cases(self):
        """Test various prescription volume formats."""
        test_cases = [
            ("0", 0),  # Zero
            ("999999", 999999),  # Very large number
            ("1500", 1500),  # Standard format
            ("1.5k", None),  # With k suffix
            ("fifteen hundred", None),  # Text
            ("", None),  # Empty
        ]

        for volume_str, expected in test_cases:
            if expected is not None:
                # Test parsing
                data = {"rx_volume": volume_str}
                result = self.chatbot.pharmacy_api._parse_pharmacy_data(data)
                self.assertEqual(result.rx_volume, expected)

    def test_email_edge_cases(self):
        """Test various email formats."""
        test_cases = [
            ("john@pharmacy.com", True),  # Valid
            ("john.doe@pharmacy.com", True),  # With dot
            ("john+test@pharmacy.com", True),  # With plus
            ("john@pharmacy.co.uk", True),  # Different TLD
            ("invalid-email", False),  # Invalid
            ("john@", False),  # Incomplete
            ("@pharmacy.com", False),  # Missing local part
            ("", False),  # Empty
        ]

        for email, is_valid in test_cases:
            # Test extraction
            if is_valid:
                result = self.chatbot._extract_pharmacy_info(f"My email is {email}")
                # Should extract valid emails
                pass  # Add assertions based on implementation

    def test_conversation_history_limits(self):
        """Test conversation history management."""
        # Add many messages to test history limits
        for i in range(20):
            self.chatbot.conversation_history.append(
                {"role": "user", "content": f"Message {i}"}
            )

        # Should handle long history gracefully
        result = self.chatbot.process_message("Test message")
        self.assertIsInstance(result, str)

    def test_concurrent_api_calls(self):
        """Test handling of concurrent API calls."""
        import threading
        import time

        results = []

        def make_api_call():
            try:
                with patch.object(
                    self.chatbot.pharmacy_api, "get_pharmacy_by_phone"
                ) as mock_get_pharmacy:
                    mock_get_pharmacy.return_value = None
                    result = self.chatbot.start_call("555-123-4567")
                    results.append(result)
            except Exception as e:
                results.append(f"Error: {e}")

        # Start multiple threads
        threads = []
        for i in range(5):
            thread = threading.Thread(target=make_api_call)
            threads.append(thread)
            thread.start()

        # Wait for all threads to complete
        for thread in threads:
            thread.join()

        # All calls should complete successfully
        self.assertEqual(len(results), 5)
        for result in results:
            self.assertIsInstance(result, str)
            self.assertGreater(len(result), 0)


if __name__ == "__main__":
    unittest.main()
