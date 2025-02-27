#!/usr/bin/env python3
# -*- coding: utf-8 -*-

"""
Agent Orchestrator Module cho Mega Market AI Agent.

Module này đóng vai trò điều phối trung tâm, nhận request từ API Gateway
và điều phối các thành phần khác nhau của hệ thống để xử lý request và trả về response.
"""

import asyncio
import time
from typing import Dict, Any, Optional, List

from pydantic import BaseModel

# Import các module khác
from intent_analyzer import IntentAnalyzer
from knowledge_manager import KnowledgeManager
from response_generator import ResponseGenerator
from tool_manager import ToolManager
from llm_orchestrator import LLMOrchestrator
from utils.logging import setup_logger
from config import AgentConfig

# Setup logging
logger = setup_logger("agent_orchestrator")

# Load configuration
config = AgentConfig()


class AgentResponse(BaseModel):
    """Model cho response từ AI Agent."""
    message: str
    data: Optional[Dict[str, Any]] = None
    type: str  # 'text', 'product', 'order', etc.


class AgentOrchestrator:
    """
    Điều phối viên chính của AI Agent.
    
    Chịu trách nhiệm:
    1. Phân tích intent từ người dùng
    2. Quyết định các tool cần sử dụng
    3. Điều phối quá trình xử lý
    4. Tổng hợp response cuối cùng
    """
    
    def __init__(self):
        """Khởi tạo Orchestrator và các component cần thiết."""
        self.intent_analyzer = IntentAnalyzer()
        self.knowledge_manager = KnowledgeManager()
        self.tool_manager = ToolManager()
        self.response_generator = ResponseGenerator()
        self.llm_orchestrator = LLMOrchestrator()
        
        logger.info("Agent Orchestrator initialized")
    
    async def process_query(
        self,
        message: str,
        session_id: str,
        user_id: Optional[str] = None,
        context: Optional[Dict[str, Any]] = None,
        request_id: Optional[str] = None
    ) -> AgentResponse:
        """
        Xử lý truy vấn từ người dùng và trả về response.
        
        Parameters:
        -----------
        message : str
            Tin nhắn từ người dùng
        session_id : str
            ID phiên làm việc
        user_id : str, optional
            ID của người dùng nếu đã xác thực
        context : Dict[str, Any], optional
            Context bổ sung
        request_id : str, optional
            ID của request để tracking
            
        Returns:
        --------
        AgentResponse
            Phản hồi của agent
        """
        try:
            # Log the incoming query
            logger.info(
                f"Processing query. Session: {session_id}, Request ID: {request_id}",
                extra={
                    "session_id": session_id,
                    "request_id": request_id,
                    "user_id": user_id
                }
            )
            
            # Track execution time
            start_time = time.time()
            
            # Step 1: Retrieve conversation history and context
            conversation_history = await self.knowledge_manager.get_conversation_history(session_id)
            
            # Step 2: Analyze user intent
            intent = await self.intent_analyzer.analyze(
                message, 
                conversation_history=conversation_history
            )
            
            logger.info(
                f"Intent detected: {intent.get('type')}",
                extra={
                    "session_id": session_id,
                    "request_id": request_id,
                    "intent_type": intent.get("type")
                }
            )
            
            # Step 3: Execute tools based on intent
            tool_results = {}
            if intent.get("type") == "product_search":
                keywords = intent.get("keywords", [])
                tool_results["products"] = await self.tool_manager.search_products(keywords)
                
            elif intent.get("type") == "order_status":
                order_id = intent.get("order_id")
                tool_results["order"] = await self.tool_manager.get_order_info(order_id, user_id)
                
            elif intent.get("type") == "customer_support":
                # For customer support, we may want to retrieve relevant knowledge
                issue = intent.get("issue", "")
                tool_results["support_info"] = await self.knowledge_manager.get_support_knowledge(issue)
            
            # Step 4: Generate response based on intent and tool results
            response = await self.generate_response(
                message=message,
                intent=intent,
                tool_results=tool_results,
                conversation_history=conversation_history,
                user_id=user_id
            )
            
            # Step 5: Save conversation to history
            await self.knowledge_manager.save_conversation(
                session_id=session_id,
                user_message=message,
                agent_response=response
            )
            
            # Log execution time
            execution_time = time.time() - start_time
            logger.info(
                f"Query processed in {execution_time:.2f}s",
                extra={
                    "session_id": session_id,
                    "request_id": request_id,
                    "execution_time": execution_time
                }
            )
            
            return response
            
        except Exception as e:
            logger.error(
                f"Error processing query: {str(e)}",
                extra={"session_id": session_id, "request_id": request_id},
                exc_info=True
            )
            
            # Return fallback response
            return AgentResponse(
                message="Xin lỗi, tôi không thể xử lý yêu cầu của bạn lúc này. Vui lòng thử lại sau.",
                type="text"
            )
    
    async def generate_response(
        self,
        message: str,
        intent: Dict[str, Any],
        tool_results: Dict[str, Any],
        conversation_history: List[Dict[str, Any]],
        user_id: Optional[str] = None
    ) -> AgentResponse:
        """
        Tạo phản hồi dựa trên intent, tool results và lịch sử hội thoại.
        
        Parameters:
        -----------
        message : str
            Tin nhắn từ người dùng
        intent : Dict[str, Any]
            Intent đã được phân tích
        tool_results : Dict[str, Any]
            Kết quả từ các tool
        conversation_history : List[Dict[str, Any]]
            Lịch sử hội thoại
        user_id : str, optional
            ID của người dùng
            
        Returns:
        --------
        AgentResponse
            Phản hồi của agent
        """
        intent_type = intent.get("type")
        
        if intent_type == "product_search":
            # Format product search response
            products = tool_results.get("products", {})
            return self.response_generator.format_product_response(
                products=products, 
                keywords=intent.get("keywords", [])
            )
            
        elif intent_type == "order_status":
            # Format order status response
            order_info = tool_results.get("order", {})
            return self.response_generator.format_order_response(order_info)
            
        elif intent_type == "customer_support":
            # Generate support response using LLM
            support_info = tool_results.get("support_info", {})
            support_response = await self.llm_orchestrator.generate_support_response(
                query=message,
                support_info=support_info
            )
            return AgentResponse(
                message=support_response,
                type="text"
            )
            
        else:
            # General queries - use LLM to generate response
            llm_response = await self.llm_orchestrator.generate_response(
                query=message,
                conversation_history=conversation_history
            )
            return AgentResponse(
                message=llm_response,
                type="text"
            )