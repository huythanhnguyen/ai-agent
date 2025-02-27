#!/usr/bin/env python3
# -*- coding: utf-8 -*-

"""
Intent Analyzer Module cho Mega Market AI Agent.

Module này chịu trách nhiệm phân tích ý định (intent) của người dùng từ message
và phân loại thành các loại intent khác nhau như product_search, order_status, etc.
"""

import json
import hashlib
from typing import Dict, Any, List, Optional

import redis.asyncio as redis

from llm_orchestrator import LLMOrchestrator
from utils.logging import setup_logger
from config import CacheConfig, LLMConfig

# Setup logging
logger = setup_logger("intent_analyzer")

# Load configuration
cache_config = CacheConfig()
llm_config = LLMConfig()


class IntentAnalyzer:
    """
    Phân tích intent từ tin nhắn của người dùng.
    
    Sử dụng LLM để phân tích intent và cache kết quả
    để tăng hiệu suất hệ thống.
    """
    
    def __init__(self):
        """Khởi tạo Intent Analyzer."""
        self.llm_orchestrator = LLMOrchestrator()
        
        # Setup Redis connection
        self.redis = redis.Redis(
            host=cache_config.REDIS_HOST,
            port=cache_config.REDIS_PORT,
            db=cache_config.REDIS_INTENT_DB,
            decode_responses=True
        )
        
        logger.info("Intent Analyzer initialized")
    
    async def analyze(
        self, 
        message: str,
        conversation_history: Optional[List[Dict[str, Any]]] = None
    ) -> Dict[str, Any]:
        """
        Phân tích intent từ tin nhắn của người dùng.
        
        Parameters:
        -----------
        message : str
            Tin nhắn từ người dùng
        conversation_history : List[Dict[str, Any]], optional
            Lịch sử hội thoại
            
        Returns:
        --------
        Dict[str, Any]
            Intent được phân tích, bao gồm loại intent và các thông tin liên quan
        """
        # Generate cache key
        cache_key = self._generate_cache_key(message)
        
        # Try to get from cache first
        cached_intent = await self._get_from_cache(cache_key)
        if cached_intent:
            logger.info(f"Intent found in cache: {cached_intent.get('type')}")
            return cached_intent
            
        # If not in cache, use LLM to analyze
        intent = await self._analyze_with_llm(message, conversation_history)
        
        # Cache the result
        await self._cache_intent(cache_key, intent)
        
        return intent
    
    def _generate_cache_key(self, message: str) -> str:
        """
        Generate a cache key for the message.
        
        Parameters:
        -----------
        message : str
            Tin nhắn từ người dùng
            
        Returns:
        --------
        str
            Cache key
        """
        # Normalize and hash the message
        normalized_message = message.lower().strip()
        hash_key = hashlib.md5(normalized_message.encode()).hexdigest()
        return f"intent:{hash_key}"
    
    async def _get_from_cache(self, cache_key: str) -> Optional[Dict[str, Any]]:
        """
        Lấy intent từ cache.
        
        Parameters:
        -----------
        cache_key : str
            Cache key
            
        Returns:
        --------
        Dict[str, Any] or None
            Intent từ cache hoặc None nếu không tìm thấy
        """
        try:
            cached_data = await self.redis.get(cache_key)
            if cached_data:
                return json.loads(cached_data)
        except Exception as e:
            logger.error(f"Error retrieving from cache: {str(e)}")
        
        return None
    
    async def _cache_intent(self, cache_key: str, intent: Dict[str, Any]) -> None:
        """
        Lưu intent vào cache.
        
        Parameters:
        -----------
        cache_key : str
            Cache key
        intent : Dict[str, Any]
            Intent cần lưu
        """
        try:
            await self.redis.set(
                cache_key,
                json.dumps(intent),
                ex=cache_config.INTENT_CACHE_TTL
            )
        except Exception as e:
            logger.error(f"Error saving to cache: {str(e)}")
    
    async def _analyze_with_llm(
        self, 
        message: str,
        conversation_history: Optional[List[Dict[str, Any]]] = None
    ) -> Dict[str, Any]:
        """
        Sử dụng LLM để phân tích intent.
        
        Parameters:
        -----------
        message : str
            Tin nhắn từ người dùng
        conversation_history : List[Dict[str, Any]], optional
            Lịch sử hội thoại
            
        Returns:
        --------
        Dict[str, Any]
            Intent được phân tích
        """
        prompt = self._construct_intent_prompt(message)
        
        try:
            # Call LLM to analyze intent
            response = await self.llm_orchestrator.generate_structured_response(
                prompt=prompt,
                output_schema={
                    "type": "object",
                    "properties": {
                        "type": {
                            "type": "string",
                            "enum": ["product_search", "order_status", "customer_support", "general"]
                        },
                        "keywords": {
                            "type": "array",
                            "items": {"type": "string"}
                        },
                        "order_id": {"type": "string"},
                        "issue": {"type": "string"},
                        "query": {"type": "string"}
                    },
                    "required": ["type"]
                }
            )
            
            return response
            
        except Exception as e:
            logger.error(f"Error analyzing intent with LLM: {str(e)}")
            # Default to general intent on error
            return {"type": "general", "query": message}
    
    def _construct_intent_prompt(self, message: str) -> str:
        """
        Tạo prompt để phân tích intent.
        
        Parameters:
        -----------
        message : str
            Tin nhắn từ người dùng
            
        Returns:
        --------
        str
            Prompt cho LLM
        """
        return f"""
        Phân tích ý định trong tin nhắn sau của người dùng: "{message}"
        
        Trả về kết quả dưới dạng JSON với cấu trúc sau:
        
        1. Nếu người dùng đang tìm sản phẩm:
        {{
            "type": "product_search",
            "keywords": ["từ khóa 1", "từ khóa 2", ...]
        }}
        
        2. Nếu người dùng đang hỏi về trạng thái đơn hàng:
        {{
            "type": "order_status",
            "order_id": "mã đơn hàng nếu có"
        }}
        
        3. Nếu người dùng cần hỗ trợ khách hàng:
        {{
            "type": "customer_support",
            "issue": "vấn đề cần hỗ trợ"
        }}
        
        4. Nếu là câu hỏi khác:
        {{
            "type": "general",
            "query": "nội dung câu hỏi"
        }}
        """