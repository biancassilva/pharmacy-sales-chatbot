# Pharmacy Sales Chatbot - Application Architecture & Workflow

## 🏥 **System Overview**

The Pharmacy Sales Chatbot is an intelligent inbound call handling system that integrates with external APIs and AI services to provide personalized pharmacy management solutions. The system automatically identifies callers, collects information, and manages follow-up actions.

---

## 🏗️ **System Architecture**

```mermaid
graph TB
    subgraph "External Services"
        API[Pharmacy API<br/>mockapi.io/pharmacies]
        AI[OpenAI GPT-4o-mini<br/>AI Processing]
    end

    subgraph "Core Application"
        subgraph "Main Components"
            LLM[LLM Module<br/>llm.py]
            INT[Integration Module<br/>integration.py]
            FUNC[Function Calls<br/>function_calls.py]
            PROMPT[Prompt Templates<br/>prompt.py]
        end

        subgraph "Data Models"
            PHARM[PharmacyData<br/>Class]
            STATE[ConversationState<br/>Enum]
        end

        subgraph "Demo Scripts"
            DEMO[demo.py]
            SIMPLE[simple_demo.py]
            MOCK[demo_with_mock_ai.py]
        end
    end

    subgraph "User Interface"
        CALLER[Inbound Caller<br/>Phone Number]
    end

    CALLER --> LLM
    LLM --> INT
    INT --> API
    LLM --> AI
    LLM --> FUNC
    LLM --> PROMPT
    INT --> PHARM
    LLM --> STATE

    DEMO --> LLM
    SIMPLE --> LLM
    MOCK --> LLM
```

---

## 🔄 **Core Workflow**

### **1. Call Start & Phone Lookup**

```mermaid
sequenceDiagram
    participant C as Caller
    participant CB as Chatbot
    participant API as Pharmacy API
    participant AI as OpenAI

    C->>CB: Start Call (Phone Number)
    CB->>API: Lookup Pharmacy by Phone
    API-->>CB: Pharmacy Data or None

    alt Existing Pharmacy Found
        CB->>AI: Generate Personalized Greeting
        AI-->>CB: Greeting with Pharmacy Name
        CB-->>C: "Hello! I see you're calling from [Pharmacy Name]..."
    else New Lead
        CB->>AI: Generate New Lead Greeting
        AI-->>CB: Information Collection Greeting
        CB-->>C: "I don't have your pharmacy in our system yet..."
    end
```

### **2. Conversation State Management**

```mermaid
stateDiagram-v2
    [*] --> GREETING
    GREETING --> COLLECTING_INFO: New Lead
    GREETING --> DISCUSSING_SOLUTIONS: Existing Customer

    COLLECTING_INFO --> DISCUSSING_SOLUTIONS: Info Complete
    COLLECTING_INFO --> COLLECTING_INFO: More Info Needed

    DISCUSSING_SOLUTIONS --> FOLLOW_UP_OFFER: Solutions Discussed
    DISCUSSING_SOLUTIONS --> DISCUSSING_SOLUTIONS: More Discussion

    FOLLOW_UP_OFFER --> SCHEDULING: Follow-up Requested
    FOLLOW_UP_OFFER --> CLOSING: No Follow-up

    SCHEDULING --> CLOSING: Scheduled
    CLOSING --> [*]
```

---

## 📁 **Module Breakdown**

### **1. LLM Module (`llm.py`)**

**Purpose**: Main chatbot logic and conversation management

```mermaid
graph LR
    subgraph "LLM Module"
        INIT[Initialize<br/>API Connection]
        STATE[State Management<br/>Conversation Flow]
        AI[AI Response<br/>Generation]
        FALLBACK[Fallback<br/>Behavior]
        INFO[Info Collection<br/>Logic]
    end

    INIT --> STATE
    STATE --> AI
    AI --> FALLBACK
    STATE --> INFO
```

**Key Features**:

- **AI Integration**: OpenAI GPT-4o-mini for intelligent responses
- **Fallback Mode**: Works without AI when API unavailable
- **State Management**: Tracks conversation progress
- **Info Collection**: Structured data gathering for new leads

### **2. Integration Module (`integration.py`)**

**Purpose**: External API communication and data handling

```mermaid
graph LR
    subgraph "Integration Module"
        API[API Client<br/>HTTP Requests]
        RETRY[Retry Logic<br/>Exponential Backoff]
        PARSE[Data Parsing<br/>Safe Defaults]
        CACHE[Response<br/>Caching]
    end

    API --> RETRY
    API --> PARSE
    API --> CACHE
```

**Key Features**:

- **Robust API Calls**: Retry mechanism with exponential backoff
- **Safe Data Parsing**: Handles malformed/missing data gracefully
- **Error Recovery**: Graceful degradation on API failures
- **Response Caching**: Optimizes repeated requests

### **3. Function Calls (`function_calls.py`)**

**Purpose**: Mock follow-up actions (email, callback scheduling)

```mermaid
graph LR
    subgraph "Function Calls"
        EMAIL[Email Sending<br/>Mock Implementation]
        CALLBACK[Callback Scheduling<br/>Mock Implementation]
        HIGH_VOL[High Volume<br/>Offers]
        LOG[Action Logging<br/>Tracking]
    end

    EMAIL --> LOG
    CALLBACK --> LOG
    HIGH_VOL --> LOG
```

**Key Features**:

- **Mock Email System**: Simulates email sending with logging
- **Callback Scheduling**: Mock appointment booking system
- **High Volume Offers**: Special handling for large pharmacies
- **Action Tracking**: Records all follow-up activities

### **4. Prompt Templates (`prompt.py`)**

**Purpose**: Conversation templates and response formatting

```mermaid
graph LR
    subgraph "Prompt Templates"
        GREET[Greeting<br/>Templates]
        INFO[Info Collection<br/>Prompts]
        SOLUTIONS[Solution<br/>Benefits]
        FOLLOW[Follow-up<br/>Offers]
    end

    GREET --> INFO
    INFO --> SOLUTIONS
    SOLUTIONS --> FOLLOW
```

**Key Features**:

- **Dynamic Templates**: Context-aware conversation prompts
- **Volume-Based Benefits**: Different messaging for different pharmacy sizes
- **Response Templates**: Structured AI response formatting
- **State-Specific Prompts**: Tailored prompts for each conversation stage

---

## 🎯 **Key Workflows**

### **Workflow 1: Existing Customer Call**

```mermaid
flowchart TD
    A[Call Start] --> B[Phone Lookup]
    B --> C{Pharmacy Found?}
    C -->|Yes| D[Load Pharmacy Data]
    D --> E[Generate Personalized Greeting]
    E --> F[Discuss Current System]
    F --> G[Present Solutions]
    G --> H[Offer Follow-up]
    H --> I[Execute Follow-up Action]
    I --> J[Close Call]

    C -->|No| K[New Lead Flow]
```

**Steps**:

1. **Phone Lookup**: Check API for existing pharmacy
2. **Data Retrieval**: Load pharmacy name, location, Rx volume
3. **Personalized Greeting**: AI-generated greeting with pharmacy details
4. **Solution Discussion**: Present relevant benefits based on Rx volume
5. **Follow-up Action**: Send email or schedule callback
6. **Call Closure**: Professional closing with next steps

### **Workflow 2: New Lead Call**

```mermaid
flowchart TD
    A[Call Start] --> B[Phone Lookup]
    B --> C{Pharmacy Found?}
    C -->|No| D[Start Info Collection]
    D --> E[Collect Pharmacy Name]
    E --> F[Collect Location]
    F --> G[Collect Rx Volume]
    G --> H[Collect Contact Person]
    H --> I[Collect Email]
    I --> J[Present Solutions]
    J --> K[Offer Follow-up]
    K --> L[Execute Follow-up Action]
    L --> M[Close Call]

    C -->|Yes| N[Existing Customer Flow]
```

**Steps**:

1. **Phone Lookup**: Confirm new lead status
2. **Information Collection**: Structured data gathering
3. **Volume Assessment**: Determine appropriate solutions
4. **Solution Presentation**: Tailored benefits based on collected data
5. **Follow-up Action**: Send information or schedule consultation
6. **Call Closure**: Professional closing with next steps

---

## 🔧 **Technical Implementation**

### **Data Flow Architecture**

```mermaid
graph TB
    subgraph "Input Layer"
        PHONE[Phone Number]
        MESSAGE[User Message]
    end

    subgraph "Processing Layer"
        LOOKUP[API Lookup]
        AI_PROCESS[AI Processing]
        STATE_MANAGE[State Management]
    end

    subgraph "Output Layer"
        RESPONSE[AI Response]
        ACTION[Follow-up Action]
        LOG[System Log]
    end

    PHONE --> LOOKUP
    MESSAGE --> AI_PROCESS
    LOOKUP --> STATE_MANAGE
    AI_PROCESS --> STATE_MANAGE
    STATE_MANAGE --> RESPONSE
    STATE_MANAGE --> ACTION
    STATE_MANAGE --> LOG
```

### **Error Handling & Fallback**

```mermaid
graph LR
    subgraph "Error Handling"
        API_ERR[API Error]
        AI_ERR[AI Error]
        DATA_ERR[Data Error]
    end

    subgraph "Fallback Mechanisms"
        RETRY[Retry Logic]
        FALLBACK[Manual Mode]
        SAFE_DEFAULTS[Safe Defaults]
    end

    API_ERR --> RETRY
    AI_ERR --> FALLBACK
    DATA_ERR --> SAFE_DEFAULTS
```

---

## 🚀 **Key Features**

### **1. Intelligent Customer Recognition**

- **API Integration**: Real-time pharmacy lookup
- **Personalized Greetings**: AI-generated context-aware responses
- **Data-Driven Conversations**: Uses actual pharmacy data

### **2. Volume-Based Solution Tailoring**

- **High Volume (1000+ Rx)**: Advanced automation, priority support
- **Standard Volume (<1000 Rx)**: Basic automation, standard support
- **Dynamic Benefits**: Real-time solution customization

### **3. Robust Error Handling**

- **API Failures**: Automatic retry with exponential backoff
- **AI Unavailability**: Graceful fallback to manual mode
- **Data Issues**: Safe defaults for missing/malformed data

### **4. Complete Follow-up Management**

- **Email System**: Mock email sending with tracking
- **Callback Scheduling**: Mock appointment booking
- **Action Logging**: Comprehensive activity tracking

### **5. Production-Ready Architecture**

- **Modular Design**: Clean separation of concerns
- **Comprehensive Logging**: Full system observability
- **Scalable Structure**: Easy to extend and maintain

---

## 📊 **System Capabilities**

| Feature               | Description                        | Status     |
| --------------------- | ---------------------------------- | ---------- |
| **Phone Lookup**      | Real-time pharmacy identification  | ✅ Working |
| **AI Integration**    | GPT-4o-mini powered conversations  | ✅ Working |
| **Fallback Mode**     | Manual operation without AI        | ✅ Working |
| **Error Recovery**    | Graceful handling of failures      | ✅ Working |
| **Follow-up Actions** | Email and callback management      | ✅ Working |
| **Volume Analysis**   | Rx volume-based solution tailoring | ✅ Working |
| **State Management**  | Complete conversation flow control | ✅ Working |
| **Data Parsing**      | Safe handling of API responses     | ✅ Working |

---

## 🎯 **Conclusion**

The Pharmacy Sales Chatbot is a **production-ready, intelligent system** that:

- ✅ **Automatically identifies** existing vs new customers
- ✅ **Provides personalized** solutions based on pharmacy data
- ✅ **Handles errors gracefully** with robust fallback mechanisms
- ✅ **Manages complete** follow-up workflows
- ✅ **Scales efficiently** with modular architecture
- ✅ **Integrates seamlessly** with external APIs and AI services

The system demonstrates **enterprise-grade reliability** while maintaining **user-friendly simplicity** and **extensive customization capabilities**.
