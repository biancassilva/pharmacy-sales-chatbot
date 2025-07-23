"""
Demo script for the pharmacy chatbot system.
"""

import os
import sys
from typing import Optional
from dotenv import load_dotenv

from llm import PharmacyChatbot
from integration import PharmacyAPI
from function_calls import FollowUpActions

# Load environment variables
load_dotenv()


def print_separator():
    """Print a separator line."""
    print("\n" + "=" * 60 + "\n")


def print_header(title: str):
    """Print a formatted header."""
    print_separator()
    print(f"🤖 {title}")
    print_separator()


def demo_existing_customer():
    """Demo conversation with an existing customer."""
    print_header("DEMO: Existing Customer Call")

    # Initialize chatbot
    chatbot = PharmacyChatbot()

    # Start call with existing pharmacy phone number
    print("📞 Starting call from existing customer...")
    greeting = chatbot.start_call("555-123-4567")
    print(f"Bot: {greeting}")

    # Simulate conversation
    conversation = [
        "Hi, we're having some issues with our current system and wanted to see what you can offer.",
        "Yes, we're definitely interested in upgrading. Our current system is quite outdated.",
        "That sounds great! We'd love to see a demo of your system.",
        "Perfect, let's schedule that for next week. How about Tuesday at 2 PM?",
        "Great! Looking forward to it. Thanks for your help.",
    ]

    for i, user_message in enumerate(conversation, 1):
        print(f"\nUser: {user_message}")
        response = chatbot.process_message(user_message)
        print(f"Bot: {response}")

    # Show conversation summary
    print_separator()
    print("📊 CONVERSATION SUMMARY")
    summary = chatbot.get_conversation_summary()
    print(f"State: {summary['state']}")
    print(
        f"Pharmacy: {summary['pharmacy_data']['name'] if summary['pharmacy_data'] else 'New Lead'}"
    )
    print(
        f"Rx Volume: {summary['pharmacy_data']['rx_volume'] if summary['pharmacy_data'] else 'Unknown'}"
    )
    print(f"Emails Sent: {summary['follow_up_actions']['emails_sent']}")
    print(f"Callbacks Scheduled: {summary['follow_up_actions']['callbacks_scheduled']}")


def demo_new_lead():
    """Demo conversation with a new lead."""
    print_header("DEMO: New Lead Call")

    # Initialize chatbot
    chatbot = PharmacyChatbot()

    # Start call with new phone number
    print("📞 Starting call from new lead...")
    greeting = chatbot.start_call("555-999-9999")
    print(f"Bot: {greeting}")

    # Simulate conversation
    conversation = [
        "Hi, I'm calling about pharmacy management software. We're opening a new pharmacy next month.",
        "Our pharmacy will be called 'Sunset Pharmacy' and we'll be located in San Diego.",
        "We're expecting to process about 800 prescriptions per month initially.",
        "I'm Sarah Johnson, the pharmacy manager. My email is sarah@sunsetpharmacy.com",
        "Yes, we're very interested in learning more about your solutions.",
        "Email would be great! Please send us the information.",
        "Thank you so much for your help!",
    ]

    for i, user_message in enumerate(conversation, 1):
        print(f"\nUser: {user_message}")
        response = chatbot.process_message(user_message)
        print(f"Bot: {response}")

    # Show conversation summary
    print_separator()
    print("📊 CONVERSATION SUMMARY")
    summary = chatbot.get_conversation_summary()
    print(f"State: {summary['state']}")
    print(f"Collected Info: {summary['collected_info']}")
    print(f"Emails Sent: {summary['follow_up_actions']['emails_sent']}")
    print(f"Callbacks Scheduled: {summary['follow_up_actions']['callbacks_scheduled']}")


def demo_high_volume_pharmacy():
    """Demo conversation with a high volume pharmacy."""
    print_header("DEMO: High Volume Pharmacy Call")

    # Initialize chatbot
    chatbot = PharmacyChatbot()

    # Start call with new phone number
    print("📞 Starting call from high volume pharmacy...")
    greeting = chatbot.start_call("555-777-8888")
    print(f"Bot: {greeting}")

    # Simulate conversation
    conversation = [
        "Hello, we're looking to upgrade our pharmacy management system. We're processing about 2000 prescriptions per month.",
        "We're 'Mega Pharmacy' located in Los Angeles. I'm Mike Rodriguez, the owner.",
        "Our current system is struggling with the volume. We need something more robust.",
        "That sounds exactly like what we need! The priority implementation is very appealing.",
        "Yes, please send us the detailed information about your high-volume program.",
        "My email is mike@megapharmacy.com",
        "Perfect! We're very excited about this opportunity.",
    ]

    for i, user_message in enumerate(conversation, 1):
        print(f"\nUser: {user_message}")
        response = chatbot.process_message(user_message)
        print(f"Bot: {response}")

    # Show conversation summary
    print_separator()
    print("📊 CONVERSATION SUMMARY")
    summary = chatbot.get_conversation_summary()
    print(f"State: {summary['state']}")
    print(f"Collected Info: {summary['collected_info']}")
    print(f"Emails Sent: {summary['follow_up_actions']['emails_sent']}")
    print(f"Callbacks Scheduled: {summary['follow_up_actions']['callbacks_scheduled']}")


def demo_api_integration():
    """Demo the API integration functionality."""
    print_header("DEMO: API Integration")

    api = PharmacyAPI()

    print("🔍 Fetching all pharmacies from API...")
    try:
        pharmacies = api.get_all_pharmacies()
        print(f"Found {len(pharmacies)} pharmacies in the system")

        if pharmacies:
            print("\n📋 Sample pharmacy data:")
            for i, pharmacy in enumerate(pharmacies[:3], 1):
                print(
                    f"{i}. {pharmacy.name} - {pharmacy.location} - {pharmacy.rx_volume} Rx/month"
                )

        print("\n🔍 Looking up specific pharmacy by phone...")
        pharmacy = api.get_pharmacy_by_phone("555-123-4567")
        if pharmacy:
            print(f"Found: {pharmacy.name} in {pharmacy.location}")
        else:
            print("Pharmacy not found")

        print("\n🏆 High volume pharmacies (1000+ Rx/month):")
        high_volume = api.get_high_volume_pharmacies()
        for pharmacy in high_volume:
            print(f"• {pharmacy.name}: {pharmacy.rx_volume} Rx/month")

    except Exception as e:
        print(f"Error accessing API: {e}")


def demo_follow_up_actions():
    """Demo the follow-up actions functionality."""
    print_header("DEMO: Follow-up Actions")

    actions = FollowUpActions()

    # Demo email sending
    print("📧 Testing email functionality...")
    from integration import PharmacyData

    pharmacy = PharmacyData(
        id="1",
        name="Demo Pharmacy",
        phone="555-123-4567",
        location="Demo City",
        rx_volume=1500,
        contact_person="Demo Manager",
        email="demo@pharmacy.com",
    )

    # Send welcome email
    result = actions.send_welcome_email(pharmacy)
    print(f"Welcome email result: {result['success']}")

    # Send high volume offer
    result = actions.send_high_volume_offer(pharmacy)
    print(f"High volume offer result: {result['success']}")

    # Schedule consultation
    result = actions.schedule_consultation(pharmacy, "tomorrow at 3 PM")
    print(f"Consultation scheduling result: {result['success']}")

    # Show history
    print(f"\n📊 Action History:")
    print(f"Emails sent: {len(actions.get_email_history())}")
    print(f"Callbacks scheduled: {len(actions.get_callback_history())}")


def interactive_demo():
    """Interactive demo where user can chat with the bot."""
    print_header("INTERACTIVE DEMO")

    # Check for API key
    if not os.getenv("OPENAI_API_KEY"):
        print("❌ OPENAI_API_KEY not found in environment variables.")
        print("Please set your OpenAI API key to use the interactive demo.")
        return

    # Initialize chatbot
    chatbot = PharmacyChatbot()

    # Get phone number
    phone_number = input("Enter a phone number to simulate the call: ").strip()
    if not phone_number:
        phone_number = "555-123-4567"

    # Start call
    print(f"\n📞 Starting call from {phone_number}...")
    greeting = chatbot.start_call(phone_number)
    print(f"Bot: {greeting}")

    # Interactive conversation
    print("\n💬 Start chatting with the bot! (Type 'quit' to exit)")

    while True:
        user_input = input("\nYou: ").strip()

        if user_input.lower() in ["quit", "exit", "bye"]:
            print("Bot: Thank you for calling Pharmesol! Have a great day!")
            break

        if user_input:
            response = chatbot.process_message(user_input)
            print(f"Bot: {response}")

    # Show summary
    print_separator()
    print("📊 CONVERSATION SUMMARY")
    summary = chatbot.get_conversation_summary()
    print(f"State: {summary['state']}")
    print(f"Conversation length: {summary['conversation_length']} messages")
    print(f"Collected Info: {summary['collected_info']}")
    print(f"Current Info Field: {summary['current_info_field']}")
    print(f"AI Available: {summary['ai_available']}")
    print(f"Emails sent: {summary['follow_up_actions']['emails_sent']}")
    print(f"Callbacks scheduled: {summary['follow_up_actions']['callbacks_scheduled']}")


def main():
    """Main demo function."""
    print_header("PHARMACY SALES CHATBOT DEMO")

    print("Welcome to the Pharmesol Pharmacy Sales Chatbot Demo!")
    print("\nThis demo showcases:")
    print("• Existing customer recognition and personalized service")
    print("• New lead information collection")
    print("• High volume pharmacy special handling")
    print("• API integration with pharmacy database")
    print("• Follow-up action management (emails, callbacks)")
    print("• Intelligent conversation flow management")

    while True:
        print_separator()
        print("Choose a demo option:")
        print("1. Existing Customer Demo")
        print("2. New Lead Demo")
        print("3. High Volume Pharmacy Demo")
        print("4. API Integration Demo")
        print("5. Follow-up Actions Demo")
        print("6. Interactive Demo (requires OpenAI API key)")
        print("7. Run All Demos")
        print("0. Exit")

        choice = input("\nEnter your choice (0-7): ").strip()

        if choice == "0":
            print("Thanks for trying the demo!")
            break
        elif choice == "1":
            demo_existing_customer()
        elif choice == "2":
            demo_new_lead()
        elif choice == "3":
            demo_high_volume_pharmacy()
        elif choice == "4":
            demo_api_integration()
        elif choice == "5":
            demo_follow_up_actions()
        elif choice == "6":
            interactive_demo()
        elif choice == "7":
            demo_api_integration()
            demo_follow_up_actions()
            demo_existing_customer()
            demo_new_lead()
            demo_high_volume_pharmacy()
        else:
            print("Invalid choice. Please try again.")


if __name__ == "__main__":
    main()
