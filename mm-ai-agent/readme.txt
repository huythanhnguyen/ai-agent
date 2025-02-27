mega-market-ai-agent/
├── backend/
│   ├── api_gateway.py           # API Gateway module
│   ├── agent_orchestrator.py    # Agent Orchestrator module
│   ├── intent_analyzer.py       # Intent Analyzer module
│   ├── knowledge_manager.py     # Knowledge Manager module
│   ├── response_generator.py    # Response Generator module
│   ├── tool_manager.py          # Tool Manager module
│   ├── llm_orchestrator.py      # LLM Orchestrator module
│   ├── config.py                # Configuration module
│   ├── utils/
│   │   ├── __init__.py
│   │   ├── logging.py           # Logging utilities
│   │   └── security.py          # Security utilities
│   ├── models/
│   │   ├── __init__.py
│   │   └── schemas.py           # Pydantic models & schemas
│   ├── providers/
│   │   ├── __init__.py
│   │   ├── openai_provider.py
│   │   ├── anthropic_provider.py
│   │   └── google_provider.py
│   └── adapters/
│       ├── __init__.py
│       ├── magento_adapter.py
│       └── cdp_adapter.py
│
├── frontend/
│   ├── static/
│   │   ├── css/
│   │   │   └── style.css        # CSS styles
│   │   ├── js/
│   │   │   └── script.js        # JS script
│   │   └── images/
│   │       └── mega-market-logo.png
│   ├── index.html               # Main HTML file
│   └── templates/
│       └── embed.html           # Embed snippet for Magento
│
├── tests/
│   ├── unit/
│   │   ├── test_api_gateway.py
│   │   ├── test_intent_analyzer.py
│   │   └── ...
│   └── integration/
│       ├── test_magento_integration.py
│       └── test_cdp_integration.py
│
├── scripts/
│   ├── deploy.sh                # Deployment script
│   └── setup_redis.sh           # Redis setup script
│
├── docs/
│   ├── architecture.md          # Architecture documentation
│   ├── api.md                   # API documentation
│   └── setup.md                 # Setup guide
│
├── .env.example                 # Example environment variables
├── requirements.txt             # Python dependencies
├── docker-compose.yml           # Docker configuration
├── Dockerfile                   # Docker build configuration
├── main.py                      # Application entry point
└── README.md                    # Project documentation