#!/usr/bin/env python3
# -*- coding: utf-8 -*-

"""
Security Utility Module cho Mega Market AI Agent.

Module này cung cấp các chức năng bảo mật cần thiết cho hệ thống,
bao gồm xác thực, mã hóa, và kiểm tra quyền truy cập.
"""

import os
import time
import hmac
import hashlib
import jwt
from typing import Dict, Any, Optional

from fastapi import Depends, HTTPException, Header, status
from fastapi.security import APIKeyHeader

from utils.logging import setup_logger
from config import APIConfig

# Setup logging
logger = setup_logger("security")

# Load configuration
config = APIConfig()

# API Key security scheme
api_key_header = APIKeyHeader(name="X-Api-Key", auto_error=False)


def verify_api_key(api_key: str) -> bool:
    """
    Xác thực API key.
    
    Parameters:
    -----------
    api_key : str
        API key cần kiểm tra
        
    Returns:
    --------
    bool
        True nếu API key hợp lệ, False nếu không
    """
    # If no API keys are configured, always return True
    if not config.API_KEYS or config.API_KEYS == ['']:
        return True
    
    # Check if API key matches any of the configured keys
    return api_key in config.API_KEYS


async def get_api_key_dependency(api_key: str = Depends(api_key_header)) -> str:
    """
    FastAPI dependency for API key authentication.
    
    Parameters:
    -----------
    api_key : str
        API key từ request header
        
    Returns:
    --------
    str
        API key đã được xác thực
        
    Raises:
    -------
    HTTPException
        Nếu API key không hợp lệ hoặc không được cung cấp
    """
    if not api_key:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="API key is required"
        )
    
    if not verify_api_key(api_key):
        logger.warning(f"Invalid API key attempt: {api_key[:5]}...")
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid API key"
        )
    
    return api_key


async def get_current_user(
    authorization: Optional[str] = Header(None)
) -> Optional[Dict[str, Any]]:
    """
    Lấy thông tin user hiện tại từ token JWT.
    
    Parameters:
    -----------
    authorization : str, optional
        Authorization header từ request
        
    Returns:
    --------
    Dict[str, Any] or None
        Thông tin user nếu token hợp lệ, None nếu không
    """
    if not authorization:
        return None
    
    try:
        # Extract token from header
        scheme, token = authorization.split()
        if scheme.lower() != "bearer":
            return None
        
        # Decode token
        decoded_token = jwt.decode(
            token,
            os.getenv("JWT_SECRET_KEY", "secret"),
            algorithms=["HS256"]
        )
        
        # Check if token is expired
        if decoded_token["exp"] < time.time():
            logger.warning("Expired JWT token")
            return None
        
        return decoded_token["user"]
        
    except Exception as e:
        logger.error(f"Error authenticating user: {str(e)}")
        return None


def generate_hmac(data: str, secret: Optional[str] = None) -> str:
    """
    Tạo HMAC cho một chuỗi dữ liệu.
    
    Parameters:
    -----------
    data : str
        Dữ liệu cần tạo HMAC
    secret : str, optional
        Secret key
        
    Returns:
    --------
    str
        HMAC dưới dạng hex string
    """
    secret_key = secret or os.getenv("HMAC_SECRET", "megamarket_secret")
    h = hmac.new(
        secret_key.encode(),
        data.encode(),
        hashlib.sha256
    )
    return h.hexdigest()


def verify_hmac(data: str, signature: str, secret: Optional[str] = None) -> bool:
    """
    Xác thực HMAC cho một chuỗi dữ liệu.
    
    Parameters:
    -----------
    data : str
        Dữ liệu cần kiểm tra
    signature : str
        Chữ ký HMAC cần xác thực
    secret : str, optional
        Secret key
        
    Returns:
    --------
    bool
        True nếu HMAC hợp lệ, False nếu không
    """
    expected = generate_hmac(data, secret)
    return hmac.compare_digest(expected, signature)


def sanitize_input(text: str) -> str:
    """
    Làm sạch input từ người dùng để tránh injection attacks.
    
    Parameters:
    -----------
    text : str
        Input cần làm sạch
        
    Returns:
    --------
    str
        Input đã được làm sạch
    """
    # Basic sanitization - remove common injection patterns
    replacements = {
        "'": "",
        '"': "",
        ";": "",
        "\\": "",
        "<script>": "",
        "</script>": ""
    }
    
    result = text
    for char, replacement in replacements.items():
        result = result.replace(char, replacement)
    
    return result