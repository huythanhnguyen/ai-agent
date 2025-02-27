#!/usr/bin/env python3
# -*- coding: utf-8 -*-

"""
API Gateway Module cho Mega Market AI Agent.

Module này đóng vai trò là điểm vào cho tất cả các request đến hệ thống, chịu trách nhiệm
xử lý CORS, authentication, request validation, rate limiting và routing.
"""

import os
import time
import uuid
from typing import Dict, Any, Optional

from fastapi import FastAPI, Request, HTTPException, Depends, Header, status
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse
from pydantic import BaseModel, Field
from starlette.middleware.base import BaseHTTPMiddleware

# Import các module khác
from agent_orchestrator import AgentOrchestrator
from config import APIConfig
from utils.logging import setup_logger
from utils.security import verify_api_key, get_current_user


# Setup logging
logger = setup_logger("api_gateway")

# Load configuration
config = APIConfig()

# Initialize FastAPI app
app = FastAPI(
    title="Mega Market AI Agent API",
    description="Backend API for Mega Market AI Assistant",
    version="1.0.0"
)

# CORS middleware
app.add_middleware(
    CORSMiddleware,
    allow_origins=config.CORS_ORIGINS,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


# Rate limiting middleware
class RateLimitMiddleware(BaseHTTPMiddleware):
    def __init__(self, app, rate_limit_per_minute=60):
        super().__init__(app)
        self.rate_limit = rate_limit_per_minute
        self.clients = {}
    
    async def dispatch(self, request: Request, call_next):
        client_ip = request.client.host
        current_time = time.time()
        
        # Clean up old entries
        self.clients = {ip: data for ip, data in self.clients.items() 
                        if current_time - data["last_request"] < 60}
        
        if client_ip in self.clients:
            client_data = self.clients[client_ip]
            if current_time - client_data["last_request"] < 60:
                if client_data["requests"] >= self.rate_limit:
                    return JSONResponse(
                        status_code=status.HTTP_429_TOO_MANY_REQUESTS,
                        content={"detail": "Too many requests"}
                    )
                client_data["requests"] += 1
            else:
                client_data["requests"] = 1
            client_data["last_request"] = current_time
        else:
            self.clients[client_ip] = {
                "requests": 1,
                "last_request": current_time
            }
        
        response = await call_next(request)
        return response


# Add rate limiting middleware
app.add_middleware(RateLimitMiddleware, rate_limit_per_minute=config.RATE_LIMIT)


# Request models
class UserQuery(BaseModel):
    """Model cho user query request."""
    message: str = Field(..., description="User message")
    session_id: Optional[str] = Field(None, description="Session identifier")
    user_id: Optional[str] = Field(None, description="User identifier")
    context: Optional[Dict[str, Any]] = Field(None, description="Additional context")


class HealthCheckResponse(BaseModel):
    """Model cho health check response."""
    status: str
    version: str
    timestamp: float


# Response models
class AgentResponse(BaseModel):
    """Model cho response từ AI Agent."""
    message: str = Field(..., description="Response message")
    data: Optional[Dict[str, Any]] = Field(None, description="Additional data")
    type: str = Field(..., description="Response type")


# Initialize Agent Orchestrator
agent_orchestrator = AgentOrchestrator()


@app.get("/health", response_model=HealthCheckResponse)
async def health_check():
    """Health check endpoint."""
    return {
        "status": "ok",
        "version": config.VERSION,
        "timestamp": time.time()
    }


@app.post("/chat", response_model=AgentResponse)
async def chat_endpoint(
    query: UserQuery,
    request: Request,
    x_api_key: Optional[str] = Header(None)
):
    """
    Endpoint chính để xử lý các chat request.
    
    Parameters:
    - query: UserQuery object
    - x_api_key: Optional API key for authentication
    
    Returns:
    - AgentResponse object
    """
    try:
        # Validate API key if required
        if config.REQUIRE_API_KEY:
            if not x_api_key or not verify_api_key(x_api_key):
                raise HTTPException(
                    status_code=status.HTTP_401_UNAUTHORIZED,
                    detail="Invalid or missing API key"
                )
        
        # Generate request ID for tracking
        request_id = str(uuid.uuid4())
        
        # Log the incoming request
        client_ip = request.client.host
        logger.info(f"Request {request_id} received from {client_ip}",
                   extra={"request_id": request_id, "client_ip": client_ip})
        
        # Get or generate session ID
        session_id = query.session_id or str(uuid.uuid4())
        
        # Process query through orchestrator
        start_time = time.time()
        response = await agent_orchestrator.process_query(
            query.message,
            session_id=session_id,
            user_id=query.user_id,
            context=query.context,
            request_id=request_id
        )
        
        # Log processing time
        processing_time = time.time() - start_time
        logger.info(f"Request {request_id} processed in {processing_time:.2f}s",
                   extra={"request_id": request_id, "processing_time": processing_time})
        
        return response
        
    except Exception as e:
        logger.error(f"Error processing request: {str(e)}", exc_info=True)
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="An error occurred processing your request"
        )


@app.post("/feedback")
async def feedback_endpoint(
    feedback_data: Dict[str, Any],
    x_api_key: Optional[str] = Header(None)
):
    """
    Endpoint để nhận feedback từ người dùng.
    
    Parameters:
    - feedback_data: Feedback data
    - x_api_key: Optional API key for authentication
    
    Returns:
    - Acknowledgment
    """
    # Validate API key if required
    if config.REQUIRE_API_KEY:
        if not x_api_key or not verify_api_key(x_api_key):
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="Invalid or missing API key"
            )
    
    # Log feedback
    logger.info(f"Received feedback: {feedback_data}")
    
    # Store feedback in database
    # TODO: Implement feedback storage
    
    return {"status": "success", "message": "Feedback received"}


if __name__ == "__main__":
    import uvicorn
    uvicorn.run(
        "api_gateway:app",
        host=config.HOST,
        port=config.PORT,
        reload=config.DEBUG
    )