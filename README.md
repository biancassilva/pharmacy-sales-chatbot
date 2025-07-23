# Pharmacy Sales Chatbot

A sophisticated chatbot simulation for handling inbound calls from pharmacies, built with Python and OpenAI's GPT models. The system intelligently manages conversations, recognizes returning customers, collects information from new leads, and handles follow-up actions.

## Features

### 🤖 Core Functionality

- **Caller Recognition**: Identifies existing pharmacies using phone number lookup
- **Intelligent Conversations**: Uses OpenAI GPT for natural language processing
- **Information Collection**: Conversationally gathers pharmacy details from new leads with robust fallback logic
- **High Volume Support**: Special handling for pharmacies with 1000+ prescriptions
- **Follow-up Actions**: Email sending and callback scheduling (mocked)
- **Conversation State Management**: Intelligent tracking of conversation flow and collected information

### 🔌 API Integration

- **External Pharmacy API**: Integrates with `https://67e14fb758cc6bf785254550.mockapi.io/pharmacies`
- **Phone Number Lookup**: Checks caller ID against existing pharmacy database
- **Data Management**: Fetches, creates, and updates pharmacy records

### 📧 Follow-up Management

- **Email Automation**: Sends welcome emails and high-volume offers
- **Callback Scheduling**: Books consultation calls with pharmacy staff
- **Action Tracking**: Maintains history of all follow-up activities

## Project Structure

```
pharmacy-sales-chatbot/
├── integration.py      # API integration and data management
├── function_calls.py   # Follow-up actions (emails, callbacks)
├── prompt.py          # Conversation templates and prompts
├── llm.py             # OpenAI integration and conversation logic
├── tests.py           # Comprehensive test suite
├── demo.py            # Interactive demo and examples
├── requirements.txt   # Python dependencies
├── env_example.txt    # Environment variables template
└── README.md          # This file
```

## Installation

1. **Clone the repository**

   ```bash
   git clone <repository-url>
   cd pharmacy-sales-chatbot
   ```

2. **Install dependencies**

   ```bash
   pip install -r requirements.txt
   ```

3. **Set up environment variables**

   ```bash
   # Copy the example file
   cp env_example.txt .env

   # Edit .env and add your OpenAI API key
   OPENAI_API_KEY=your_openai_api_key_here
   ```

## Recent Updates

### 🔧 Bug Fixes (Latest)

- **Fixed Interactive Demo Conversation Flow**: Resolved issue where the bot would ask the same questions repeatedly during information collection
- **Improved Information Extraction**: Enhanced manual fallback logic to better extract pharmacy information when AI is unavailable
- **Better Error Handling**: Added robust error handling for AI extraction failures and JSON parsing issues
- **Conversation State Tracking**: Fixed logic to properly track collected information and prevent duplicate questions
- **AI Extraction Robustness**: Improved AI extraction prompts and added validation to prevent invalid data extraction
- **Automatic Fallback**: System now automatically switches to manual extraction after 3 AI extraction failures
- **Field-Specific AI Extraction**: Implemented targeted AI extraction for individual fields to prevent cross-field contamination and improve accuracy

## Usage

### Running the Demo

The easiest way to explore the system is through the interactive demo:

```bash
python demo.py
```

This will present you with several demo options:

- Existing Customer Demo
- New Lead Demo
- High Volume Pharmacy Demo
- API Integration Demo
- Follow-up Actions Demo
- Interactive Demo (requires OpenAI API key)

### Programmatic Usage

```python
from llm import PharmacyChatbot

# Initialize the chatbot
chatbot = PharmacyChatbot()

# Start a call
greeting = chatbot.start_call("555-123-4567")
print(greeting)

# Process user messages
response = chatbot.process_message("Hi, we're interested in your pharmacy software")
print(response)

# Get conversation summary
summary = chatbot.get_conversation_summary()
print(summary)
```

### API Integration

```python
from integration import PharmacyAPI

# Initialize API client
api = PharmacyAPI()

# Look up pharmacy by phone
pharmacy = api.get_pharmacy_by_phone("555-123-4567")

# Get all pharmacies
all_pharmacies = api.get_all_pharmacies()

# Get high volume pharmacies
high_volume = api.get_high_volume_pharmacies(threshold=1000)
```

### Follow-up Actions

```python
from function_calls import FollowUpActions
from integration import PharmacyData

# Initialize actions
actions = FollowUpActions()

# Create pharmacy data
pharmacy = PharmacyData(
    id='1',
    name='Test Pharmacy',
    phone='555-123-4567',
    location='Test City',
    rx_volume=1500,
    contact_person='John Doe',
    email='john@pharmacy.com'
)

# Send welcome email
result = actions.send_welcome_email(pharmacy)

# Schedule consultation
result = actions.schedule_consultation(pharmacy, "tomorrow at 2 PM")
```

## Testing

Run the comprehensive test suite:

```bash
python -m pytest tests.py -v
```

Or run specific test classes:

```bash
python -m pytest tests.py::TestPharmacyAPI -v
python -m pytest tests.py::TestPharmacyChatbot -v
```

## Architecture

### Module Overview

#### `integration.py`

- **PharmacyAPI**: Handles all external API interactions
- **PharmacyData**: Data class for pharmacy information
- Phone number cleaning and data parsing utilities

#### `function_calls.py`

- **FollowUpActions**: Manages email sending and callback scheduling
- **EmailRequest/CallbackRequest**: Data classes for action requests
- Mock implementations for production-ready integrations

#### `prompt.py`

- **PromptTemplates**: System prompts and conversation templates
- **ConversationState**: Enum for conversation flow states
- **ResponseTemplates**: Contextual response generation

#### `llm.py`

- **PharmacyChatbot**: Main chatbot class with conversation management
- OpenAI API integration for natural language processing
- State machine for conversation flow control

#### `tests.py`

- Comprehensive unit tests for all modules
- Mock implementations for external dependencies
- Integration tests for complete conversation flows

### Conversation Flow

1. **Call Start**: Phone number lookup against API
2. **Greeting**: Personalized greeting based on caller type
3. **Information Collection**: For new leads, gather pharmacy details
4. **Solution Discussion**: Present relevant Pharmesol solutions
5. **Follow-up Offer**: Propose email or callback options
6. **Action Execution**: Send emails or schedule callbacks
7. **Closing**: Professional conversation conclusion

### Error Handling

- **API Failures**: Graceful degradation with manual information collection
- **Missing Data**: Intelligent prompting for required information
- **Invalid Input**: Robust parsing and validation
- **Network Issues**: Retry logic and fallback responses

## Configuration

### Environment Variables

| Variable         | Description                        | Required |
| ---------------- | ---------------------------------- | -------- |
| `OPENAI_API_KEY` | OpenAI API key for GPT integration | Yes      |

### API Configuration

The system integrates with the pharmacy API at:

```
https://67e14fb758cc6bf785254550.mockapi.io/pharmacies
```

No authentication is required for this demo API.

## Features in Detail

### Existing Customer Recognition

When a call comes in from a known phone number:

- System looks up pharmacy in API
- Greets caller by pharmacy name and location
- References their current Rx volume
- Offers personalized solutions based on their profile

### New Lead Information Collection

For unknown callers:

- Conversationally collects pharmacy details
- Uses AI to extract information from natural language
- Validates and stores collected data
- Transitions to solution discussion

### High Volume Pharmacy Handling

Special features for pharmacies with 1000+ prescriptions:

- Priority implementation offers
- Dedicated account management
- Volume-based pricing
- Advanced automation features
- Custom workflow optimization

### Follow-up Action Management

Automated follow-up capabilities:

- **Welcome Emails**: Personalized introduction to Pharmesol
- **High Volume Offers**: Special programs for large pharmacies
- **Consultation Scheduling**: Calendar integration for callbacks
- **Action Tracking**: Complete history of all interactions

## Development

### Adding New Features

1. **New Conversation States**: Add to `ConversationState` enum in `prompt.py`
2. **New API Endpoints**: Extend `PharmacyAPI` class in `integration.py`
3. **New Follow-up Actions**: Add methods to `FollowUpActions` class
4. **New Prompts**: Add templates to `PromptTemplates` class

### Testing New Features

1. Add unit tests to `tests.py`
2. Update integration tests for conversation flows
3. Test with various pharmacy profiles and scenarios


## License

This project is for demonstration purposes. Please ensure compliance with OpenAI's usage policies and any applicable regulations.

## Support

For questions or issues:

1. Check the test suite for usage examples
2. Review the demo script for implementation patterns
3. Examine the module documentation for API details
