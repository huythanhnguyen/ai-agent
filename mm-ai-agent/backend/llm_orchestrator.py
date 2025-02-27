#!/usr/bin/env python3
# -*- coding: utf-8 -*-

"""
LLM Orchestrator Module cho Mega Market AI Agent.

Module này cung cấp một abstraction layer trên các LLM khác nhau,
cho phép hệ thống dễ dàng chuyển đổi giữa các nhà cung cấp LLM mà không
ảnh hưởng đến code nghiệp vụ.
"""

import json
import time
from typing import Dict, Any, List, Optional, Union, Type

from langchain_core.messages import HumanMessage, AIMessage, SystemMessage
from langchain_openai import ChatOpenAI
from langchain_anthropic import ChatAnthropic
from langchain_google_genai import ChatGoogleGenerativeAI

from utils.logging import setup_logger
from config import LLMConfig

# Setup logging
logger = setup_logger("llm_orchestrator")

# Load configuration
config = LLMConfig()


class LLMProviderInterface:
    """Interface cho tất cả các LLM Provider."""
    
    async def generate(self, messages: List[Dict[str, str]], **kwargs) -> str:
        """
        Generate text từ list các messages.
        
        Parameters:
        -----------
        messages : List[Dict[str, str]]
            Danh sách các message dạng {"role": "user|assistant|system", "content": "..."}
        
        Returns:
        --------
        str
            Text được generate
        """
        raise NotImplementedError("Must be implemented by subclass")
    
    async def generate_json(self, messages: List[Dict[str, str]], **kwargs) -> Dict[str, Any]:
        """
        Generate JSON từ list các messages.
        
        Parameters:
        -----------
        messages : List[Dict[str, str]]
            Danh sách các message dạng {"role": "user|assistant|system", "content": "..."}
        
        Returns:
        --------
        Dict[str, Any]
            JSON được generate
        """
        raise NotImplementedError("Must be implemented by subclass")


class OpenAIProvider(LLMProviderInterface):
    """OpenAI (GPT) Provider."""
    
    def __init__(self, model_name=None, api_key=None, **kwargs):
        """
        Initialize OpenAI provider.
        
        Parameters:
        -----------
        model_name : str, optional
            Tên model (default: config.OPENAI_MODEL)
        api_key : str, optional
            API key (default: config.OPENAI_API_KEY)
        """
        model_name = model_name or config.OPENAI_MODEL
        api_key = api_key or config.OPENAI_API_KEY
        
        self.model = ChatOpenAI(
            model_name=model_name,
            api_key=api_key,
            temperature=kwargs.get("temperature", 0.3)
        )
        
        logger.info(f"OpenAI provider initialized with model: {model_name}")
    
    async def generate(self, messages: List[Dict[str, str]], **kwargs) -> str:
        """Generate text từ OpenAI."""
        try:
            # Convert messages format for langchain
            lc_messages = self._convert_to_langchain_messages(messages)
            
            # Call OpenAI
            response = await self.model.ainvoke(lc_messages)
            
            return response.content
            
        except Exception as e:
            logger.error(f"Error generating from OpenAI: {str(e)}")
            raise
    
    async def generate_json(self, messages: List[Dict[str, str]], **kwargs) -> Dict[str, Any]:
        """Generate JSON từ OpenAI."""
        try:
            # Add instruction to return valid JSON
            messages.append({
                "role": "system",
                "content": "You must respond with valid JSON only, no other text."
            })
            
            # Convert messages format for langchain
            lc_messages = self._convert_to_langchain_messages(messages)
            
            # Call OpenAI
            response = await self.model.ainvoke(lc_messages)
            content = response.content.strip()
            
            # Clean up any markdown wrapping
            if content.startswith("```json"):
                content = content.replace("```json", "").replace("```", "").strip()
            
            # Parse JSON
            return json.loads(content)
            
        except Exception as e:
            logger.error(f"Error generating JSON from OpenAI: {str(e)}")
            raise
    
    def _convert_to_langchain_messages(self, messages: List[Dict[str, str]]):
        """Convert messages to langchain format."""
        lc_messages = []
        for msg in messages:
            if msg["role"] == "user":
                lc_messages.append(HumanMessage(content=msg["content"]))
            elif msg["role"] == "assistant":
                lc_messages.append(AIMessage(content=msg["content"]))
            elif msg["role"] == "system":
                lc_messages.append(SystemMessage(content=msg["content"]))
        return lc_messages


class AnthropicProvider(LLMProviderInterface):
    """Anthropic (Claude) Provider."""
    
    def __init__(self, model_name=None, api_key=None, **kwargs):
        """
        Initialize Anthropic provider.
        
        Parameters:
        -----------
        model_name : str, optional
            Tên model (default: config.ANTHROPIC_MODEL)
        api_key : str, optional
            API key (default: config.ANTHROPIC_API_KEY)
        """
        model_name = model_name or config.ANTHROPIC_MODEL
        api_key = api_key or config.ANTHROPIC_API_KEY
        
        self.model = ChatAnthropic(
            model_name=model_name,
            api_key=api_key,
            temperature=kwargs.get("temperature", 0.3)
        )
        
        logger.info(f"Anthropic provider initialized with model: {model_name}")
    
    async def generate(self, messages: List[Dict[str, str]], **kwargs) -> str:
        """Generate text từ Anthropic."""
        try:
            # Convert messages format for langchain
            lc_messages = self._convert_to_langchain_messages(messages)
            
            # Call Anthropic
            response = await self.model.ainvoke(lc_messages)
            
            return response.content
            
        except Exception as e:
            logger.error(f"Error generating from Anthropic: {str(e)}")
            raise
    
    async def generate_json(self, messages: List[Dict[str, str]], **kwargs) -> Dict[str, Any]:
        """Generate JSON từ Anthropic."""
        try:
            # Add instruction to return valid JSON
            messages.append({
                "role": "system",
                "content": "You must respond with valid JSON only, no other text."
            })
            
            # Convert messages format for langchain
            lc_messages = self._convert_to_langchain_messages(messages)
            
            # Call Anthropic
            response = await self.model.ainvoke(lc_messages)
            content = response.content.strip()
            
            # Clean up any markdown wrapping
            if content.startswith("```json"):
                content = content.replace("```json", "").replace("```", "").strip()
            
            # Parse JSON
            return json.loads(content)
            
        except Exception as e:
            logger.error(f"Error generating JSON from Anthropic: {str(e)}")
            raise
    
    def _convert_to_langchain_messages(self, messages: List[Dict[str, str]]):
        """Convert messages to langchain format."""
        lc_messages = []
        for msg in messages:
            if msg["role"] == "user":
                lc_messages.append(HumanMessage(content=msg["content"]))
            elif msg["role"] == "assistant":
                lc_messages.append(AIMessage(content=msg["content"]))
            elif msg["role"] == "system":
                lc_messages.append(SystemMessage(content=msg["content"]))
        return lc_messages


class GoogleProvider(LLMProviderInterface):
    """Google (Gemini) Provider."""
    
    def __init__(self, model_name=None, api_key=None, **kwargs):
        """
        Initialize Google provider.
        
        Parameters:
        -----------
        model_name : str, optional
            Tên model (default: config.GOOGLE_MODEL)
        api_key : str, optional
            API key (default: config.GOOGLE_API_KEY)
        """
        model_name = model_name or config.GOOGLE_MODEL
        api_key = api_key or config.GOOGLE_API_KEY
        
        self.model = ChatGoogleGenerativeAI(
            model=model_name,
            google_api_key=api_key,
            temperature=kwargs.get("temperature", 0.3)
        )
        
        logger.info(f"Google provider initialized with model: {model_name}")
    
    async def generate(self, messages: List[Dict[str, str]], **kwargs) -> str:
        """Generate text từ Google."""
        try:
            # Convert messages format for langchain
            lc_messages = self._convert_to_langchain_messages(messages)
            
            # Call Google
            response = await self.model.ainvoke(lc_messages)
            
            return response.content
            
        except Exception as e:
            logger.error(f"Error generating from Google: {str(e)}")
            raise
    
    async def generate_json(self, messages: List[Dict[str, str]], **kwargs) -> Dict[str, Any]:
        """Generate JSON từ Google."""
        try:
            # Add instruction to return valid JSON
            messages.append({
                "role": "system",
                "content": "You must respond with valid JSON only, no other text."
            })
            
            # Convert messages format for langchain
            lc_messages = self._convert_to_langchain_messages(messages)
            
            # Call Google
            response = await self.model.ainvoke(lc_messages)
            content = response.content.strip()
            
            # Clean up any markdown wrapping
            if content.startswith("```json"):
                content = content.replace("```json", "").replace("```", "").strip()
            
            # Parse JSON
            return json.loads(content)
            
        except Exception as e:
            logger.error(f"Error generating JSON from Google: {str(e)}")
            raise
    
    def _convert_to_langchain_messages(self, messages: List[Dict[str, str]]):
        """Convert messages to langchain format."""
        lc_messages = []
        for msg in messages:
            if msg["role"] == "user":
                lc_messages.append(HumanMessage(content=msg["content"]))
            elif msg["role"] == "assistant":
                lc_messages.append(AIMessage(content=msg["content"]))
            elif msg["role"] == "system":
                lc_messages.append(SystemMessage(content=msg["content"]))
        return lc_messages


class LLMOrchestrator:
    """
    Orchestrator cho các LLM, cung cấp một interface thống nhất
    và khả năng chuyển đổi giữa các provider.
    """
    
    def __init__(self, default_provider: str = None):
        """
        Khởi tạo LLM Orchestrator.
        
        Parameters:
        -----------
        default_provider : str, optional
            Provider mặc định ("openai", "anthropic", "google")
        """
        self.providers = {}
        self.default_provider = default_provider or config.DEFAULT_PROVIDER
        
        # Initialize providers based on config
        if config.ENABLED_PROVIDERS.get("openai", False):
            self.providers["openai"] = OpenAIProvider()
        
        if config.ENABLED_PROVIDERS.get("anthropic", False):
            self.providers["anthropic"] = AnthropicProvider()
        
        if config.ENABLED_PROVIDERS.get("google", False):
            self.providers["google"] = GoogleProvider()
        
        if not self.providers:
            raise ValueError("No LLM providers configured")
        
        if self.default_provider not in self.providers:
            self.default_provider = list(self.providers.keys())[0]
        
        logger.info(f"LLM Orchestrator initialized with default provider: {self.default_provider}")
    
    def get_provider(self, provider_name: Optional[str] = None) -> LLMProviderInterface:
        """
        Lấy provider dựa trên tên.
        
        Parameters:
        -----------
        provider_name : str, optional
            Tên provider, nếu None sẽ dùng default
            
        Returns:
        --------
        LLMProviderInterface
            Provider instance
        """
        provider_name = provider_name or self.default_provider
        if provider_name not in self.providers:
            raise ValueError(f"Provider {provider_name} not configured")
        
        return self.providers[provider_name]
    
    async def generate_response(
        self, 
        query: str,
        conversation_history: Optional[List[Dict[str, Any]]] = None,
        system_prompt: Optional[str] = None,
        provider_name: Optional[str] = None
    ) -> str:
        """
        Generate text response dựa trên query và history.
        
        Parameters:
        -----------
        query : str
            Câu hỏi của người dùng
        conversation_history : List[Dict[str, Any]], optional
            Lịch sử hội thoại
        system_prompt : str, optional
            System prompt
        provider_name : str, optional
            Tên provider, nếu None sẽ dùng default
            
        Returns:
        --------
        str
            Text response
        """
        # Get provider
        provider = self.get_provider(provider_name)
        
        # Format conversation history
        messages = []
        
        # Add system prompt if provided
        if system_prompt:
            messages.append({
                "role": "system",
                "content": system_prompt
            })
        else:
            # Default system prompt
            messages.append({
                "role": "system",
                "content": "Bạn là trợ lý AI của Mega Market, một hệ thống siêu thị bán lẻ lớn tại Việt Nam. "
                           "Hãy trả lời ngắn gọn, hữu ích và thân thiện. Nếu bạn không biết câu trả lời, "
                           "hãy đề xuất khách hàng liên hệ tổng đài 1900 1234 để được hỗ trợ."
            })
        
        # Add conversation history
        if conversation_history:
            for msg in conversation_history[-10:]:  # Limit to last 10 messages
                if "user_message" in msg:
                    messages.append({
                        "role": "user",
                        "content": msg["user_message"]
                    })
                if "agent_message" in msg:
                    messages.append({
                        "role": "assistant",
                        "content": msg["agent_message"]
                    })
        
        # Add current query
        messages.append({
            "role": "user",
            "content": query
        })
        
        # Generate response
        try:
            start_time = time.time()
            response = await provider.generate(messages)
            duration = time.time() - start_time
            
            logger.info(f"Generated response in {duration:.2f}s using {provider_name or self.default_provider}")
            
            return response
            
        except Exception as e:
            logger.error(f"Error generating response: {str(e)}")
            
            # Fallback to another provider if available
            if provider_name != self.default_provider and provider_name is not None:
                logger.info(f"Falling back to default provider {self.default_provider}")
                return await self.generate_response(query, conversation_history, system_prompt)
            
            # If all fails, return generic message
            return "Xin lỗi, tôi không thể trả lời câu hỏi của bạn lúc này. Vui lòng thử lại sau hoặc liên hệ tổng đài 1900 1234 để được hỗ trợ."
    
    async def generate_structured_response(
        self,
        prompt: str,
        output_schema: Dict[str, Any],
        provider_name: Optional[str] = None
    ) -> Dict[str, Any]:
        """
        Generate structured response (JSON) theo schema.
        
        Parameters:
        -----------
        prompt : str
            Prompt cho LLM
        output_schema : Dict[str, Any]
            JSON schema for the output
        provider_name : str, optional
            Tên provider, nếu None sẽ dùng default
            
        Returns:
        --------
        Dict[str, Any]
            Structured response
        """
        # Get provider
        provider = self.get_provider(provider_name)
        
        # Format prompt
        schema_str = json.dumps(output_schema, ensure_ascii=False)
        structured_prompt = f"{prompt}\n\nOutput must follow this JSON schema:\n{schema_str}"
        
        messages = [
            {
                "role": "system",
                "content": "You are a structured data extraction assistant. Extract information from the user's input and return it as valid JSON according to the specified schema."
            },
            {
                "role": "user",
                "content": structured_prompt
            }
        ]
        
        # Generate JSON response
        try:
            start_time = time.time()
            response = await provider.generate_json(messages)
            duration = time.time() - start_time
            
            logger.info(f"Generated structured response in {duration:.2f}s using {provider_name or self.default_provider}")
            
            return response
            
        except Exception as e:
            logger.error(f"Error generating structured response: {str(e)}")
            
            # Fallback to another provider if available
            if provider_name != self.default_provider and provider_name is not None:
                logger.info(f"Falling back to default provider {self.default_provider}")
                return await self.generate_structured_response(prompt, output_schema)
            
            # If all fails, return minimal valid structure
            minimal_response = {"error": "Could not generate structured response"}
            for key, val in output_schema.get("properties", {}).items():
                if key in output_schema.get("required", []):
                    if val.get("type") == "string":
                        minimal_response[key] = ""
                    elif val.get("type") == "array":
                        minimal_response[key] = []
                    elif val.get("type") == "object":
                        minimal_response[key] = {}
                    else:
                        minimal_response[key] = None
            
            return minimal_response
    
    async def generate_support_response(
        self,
        query: str,
        support_info: Optional[Dict[str, Any]] = None,
        provider_name: Optional[str] = None
    ) -> str:
        """
        Generate customer support response.
        
        Parameters:
        -----------
        query : str
            Câu hỏi của người dùng
        support_info : Dict[str, Any], optional
            Thông tin hỗ trợ từ knowledge base
        provider_name : str, optional
            Tên provider, nếu None sẽ dùng default
            
        Returns:
        --------
        str
            Support response
        """
        system_prompt = """
        Bạn là trợ lý hỗ trợ khách hàng của Mega Market, một hệ thống siêu thị bán lẻ lớn tại Việt Nam.
        Hãy trả lời câu hỏi của khách hàng một cách ngắn gọn, hữu ích và thân thiện.
        Nếu bạn không biết câu trả lời, hãy đề xuất khách hàng liên hệ tổng đài 1900 1234 để được hỗ trợ.
        """
        
        # Add support info to prompt if available
        prompt = query
        if support_info:
            support_data = json.dumps(support_info, ensure_ascii=False)
            prompt = f"Người dùng hỏi: {query}\n\nThông tin hỗ trợ: {support_data}\n\nHãy trả lời dựa trên thông tin trên."
        
        return await self.generate_response(prompt, system_prompt=system_prompt, provider_name=provider_name)