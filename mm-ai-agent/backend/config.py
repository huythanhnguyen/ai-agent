#!/usr/bin/env python3
# -*- coding: utf-8 -*-

"""
Configuration Module cho Mega Market AI Agent.

Module này cung cấp các lớp configuration cho các thành phần
khác nhau trong hệ thống, được tải từ biến môi trường hoặc file.
"""

import os
from typing import Dict, Any, List, Optional
from dotenv import load_dotenv

# Load environment variables from .env file
load_dotenv()


class APIConfig:
    """Configuration cho API Gateway."""
    
    def __init__(self):
        """Load configuration từ biến môi trường."""
        # Server settings
        self.HOST = os.getenv("API_HOST", "0.0.0.0")
        self.PORT = int(os.getenv("API_PORT", "5000"))
        self.DEBUG = os.getenv("DEBUG", "False").lower() == "true"
        self.VERSION = os.getenv("API_VERSION", "1.0.0")
        
        # Security settings
        self.REQUIRE_API_KEY = os.getenv("REQUIRE_API_KEY", "False").lower() == "true"
        self.API_KEYS = os.getenv("API_KEYS", "").split(",")
        
        # CORS settings
        self.CORS_ORIGINS = os.getenv("CORS_ORIGINS", "*").split(",")
        
        # Rate limiting
        self.RATE_LIMIT = int(os.getenv("RATE_LIMIT", "60"))  # Requests per minute


class AgentConfig:
    """Configuration cho Agent Orchestrator."""
    
    def __init__(self):
        """Load configuration từ biến môi trường."""
        # Agent settings
        self.MAX_CONVERSATION_TURNS = int(os.getenv("MAX_CONVERSATION_TURNS", "10"))
        self.DEFAULT_LANGUAGE = os.getenv("DEFAULT_LANGUAGE", "vi")
        
        # Timeout settings
        self.TOOL_TIMEOUT = int(os.getenv("TOOL_TIMEOUT", "10"))  # seconds
        self.LLM_TIMEOUT = int(os.getenv("LLM_TIMEOUT", "15"))  # seconds


class LLMConfig:
    """Configuration cho LLM Orchestrator và các LLM Providers."""
    
    def __init__(self):
        """Load configuration từ biến môi trường."""
        # Default provider
        self.DEFAULT_PROVIDER = os.getenv("DEFAULT_LLM_PROVIDER", "openai")
        
        # Enabled providers
        self.ENABLED_PROVIDERS = {
            "openai": os.getenv("ENABLE_OPENAI", "True").lower() == "true",
            "anthropic": os.getenv("ENABLE_ANTHROPIC", "False").lower() == "true",
            "google": os.getenv("ENABLE_GOOGLE", "False").lower() == "true"
        }
        
        # OpenAI settings
        self.OPENAI_API_KEY = os.getenv("OPENAI_API_KEY", "")
        self.OPENAI_MODEL = os.getenv("OPENAI_MODEL", "gpt-3.5-turbo")
        self.OPENAI_TEMPERATURE = float(os.getenv("OPENAI_TEMPERATURE", "0.3"))
        
        # Anthropic settings
        self.ANTHROPIC_API_KEY = os.getenv("ANTHROPIC_API_KEY", "")
        self.ANTHROPIC_MODEL = os.getenv("ANTHROPIC_MODEL", "claude-3-sonnet-20240229")
        self.ANTHROPIC_TEMPERATURE = float(os.getenv("ANTHROPIC_TEMPERATURE", "0.3"))
        
        # Google settings
        self.GOOGLE_API_KEY = os.getenv("GOOGLE_API_KEY", "")
        self.GOOGLE_MODEL = os.getenv("GOOGLE_MODEL", "gemini-pro")
        self.GOOGLE_TEMPERATURE = float(os.getenv("GOOGLE_TEMPERATURE", "0.3"))


class CacheConfig:
    """Configuration cho Redis và các cache khác."""
    
    def __init__(self):
        """Load configuration từ biến môi trường."""
        # Redis connection
        self.REDIS_HOST = os.getenv("REDIS_HOST", "localhost")
        self.REDIS_PORT = int(os.getenv("REDIS_PORT", "6379"))
        self.REDIS_PASSWORD = os.getenv("REDIS_PASSWORD", "")
        
        # Redis databases
        self.REDIS_INTENT_DB = int(os.getenv("REDIS_INTENT_DB", "0"))
        self.REDIS_TOOL_DB = int(os.getenv("REDIS_TOOL_DB", "1"))
        self.REDIS_KNOWLEDGE_DB = int(os.getenv("REDIS_KNOWLEDGE_DB", "2"))
        
        # Cache TTL (time-to-live) in seconds
        self.INTENT_CACHE_TTL = int(os.getenv("INTENT_CACHE_TTL", "3600"))  # 1 hour
        self.PRODUCT_CACHE_TTL = int(os.getenv("PRODUCT_CACHE_TTL", "1800"))  # 30 minutes
        self.ORDER_CACHE_TTL = int(os.getenv("ORDER_CACHE_TTL", "300"))  # 5 minutes
        self.CUSTOMER_CACHE_TTL = int(os.getenv("CUSTOMER_CACHE_TTL", "600"))  # 10 minutes
        self.CDP_CACHE_TTL = int(os.getenv("CDP_CACHE_TTL", "600"))  # 10 minutes
        self.SUPPORT_CACHE_TTL = int(os.getenv("SUPPORT_CACHE_TTL", "86400"))  # 24 hours
        self.CATEGORY_CACHE_TTL = int(os.getenv("CATEGORY_CACHE_TTL", "86400"))  # 24 hours
        self.CONVERSATION_TTL = int(os.getenv("CONVERSATION_TTL", "86400"))  # 24 hours


class ToolsConfig:
    """Configuration cho Tool Manager và các API connections."""
    
    def __init__(self):
        """Load configuration từ biến môi trường."""
        # API URLs
        self.SEARCH_API_URL = os.getenv("SEARCH_API_URL", "https://megamarket.vn/graphql")
        self.ORDER_API_URL = os.getenv("ORDER_API_URL", "https://megamarket.vn/api/orders")
        self.CUSTOMER_API_URL = os.getenv("CUSTOMER_API_URL", "https://megamarket.vn/api/customers")
        self.CDP_API_URL = os.getenv("CDP_API_URL", "https://cdp.megamarket.vn/api")
        
        # API authentication
        self.API_TOKEN = os.getenv("MAGENTO_API_TOKEN", "")
        self.STORE_CODE = os.getenv("STORE_CODE", "default")
        self.CDP_API_KEY = os.getenv("CDP_API_KEY", "")


class KnowledgeConfig:
    """Configuration cho Knowledge Manager."""
    
    def __init__(self):
        """Load configuration từ biến môi trường."""
        # Conversation history
        self.MAX_HISTORY_MESSAGES = int(os.getenv("MAX_HISTORY_MESSAGES", "20"))
        
        # Embedding model (nếu dùng vector search)
        self.EMBEDDING_MODEL = os.getenv("EMBEDDING_MODEL", "text-embedding-ada-002")