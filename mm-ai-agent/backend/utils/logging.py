#!/usr/bin/env python3
# -*- coding: utf-8 -*-

"""
Logging Utility Module cho Mega Market AI Agent.

Module này cung cấp các chức năng logging cần thiết cho hệ thống,
cho phép ghi log có cấu trúc và dễ dàng tích hợp với các hệ thống giám sát.
"""

import os
import logging
import json
from datetime import datetime
from typing import Dict, Any, Optional


class StructuredLogFormatter(logging.Formatter):
    """
    Formatter tạo ra JSON có cấu trúc cho mỗi log message.
    Giúp dễ dàng phân tích và tìm kiếm log trong các hệ thống như 
    ELK Stack, Google Cloud Logging, etc.
    """
    
    def format(self, record):
        """Format log record thành JSON có cấu trúc."""
        log_data = {
            "timestamp": datetime.utcfromtimestamp(record.created).isoformat() + "Z",
            "level": record.levelname,
            "module": record.module,
            "message": record.getMessage(),
        }
        
        # Add exception info if any
        if record.exc_info:
            log_data["exception"] = self.formatException(record.exc_info)
        
        # Add any extra attributes
        for key, value in record.__dict__.items():
            if key not in {
                "args", "asctime", "created", "exc_info", "exc_text", "filename",
                "funcName", "id", "levelname", "levelno", "lineno", "module",
                "msecs", "message", "msg", "name", "pathname", "process",
                "processName", "relativeCreated", "stack_info", "thread", "threadName"
            }:
                log_data[key] = value
        
        return json.dumps(log_data)


def setup_logger(name: str) -> logging.Logger:
    """
    Thiết lập và trả về logger với formatter cấu trúc.
    
    Parameters:
    -----------
    name : str
        Tên của logger
        
    Returns:
    --------
    logging.Logger
        Logger đã được cấu hình
    """
    logger = logging.getLogger(name)
    
    # Set log level from environment or default to INFO
    log_level_str = os.getenv("LOG_LEVEL", "INFO").upper()
    log_level = getattr(logging, log_level_str, logging.INFO)
    logger.setLevel(log_level)
    
    # Check if handlers already exist to avoid duplicates
    if not logger.handlers:
        # Console handler
        console_handler = logging.StreamHandler()
        console_handler.setFormatter(StructuredLogFormatter())
        logger.addHandler(console_handler)
        
        # File handler if LOG_FILE is specified
        log_file = os.getenv("LOG_FILE")
        if log_file:
            file_handler = logging.FileHandler(log_file)
            file_handler.setFormatter(StructuredLogFormatter())
            logger.addHandler(file_handler)
    
    return logger


def log_method_call(logger):
    """
    Decorator để log method calls với parameters và return value.
    
    Ví dụ:
    ```
    @log_method_call(logger)
    def some_method(self, arg1, arg2):
        return result
    ```
    """
    def decorator(func):
        def wrapper(*args, **kwargs):
            # Extract method info
            class_name = args[0].__class__.__name__ if args else ""
            method_name = func.__name__
            
            # Log method call
            logger.debug(
                f"Calling {class_name}.{method_name}",
                extra={
                    "class": class_name,
                    "method": method_name,
                    "args": str(args[1:]),  # Skip self
                    "kwargs": str(kwargs)
                }
            )
            
            # Call the method
            try:
                result = func(*args, **kwargs)
                
                # Log success
                logger.debug(
                    f"{class_name}.{method_name} completed successfully",
                    extra={
                        "class": class_name,
                        "method": method_name,
                        "result_type": type(result).__name__
                    }
                )
                
                return result
                
            except Exception as e:
                # Log error
                logger.error(
                    f"Error in {class_name}.{method_name}: {str(e)}",
                    extra={
                        "class": class_name,
                        "method": method_name,
                        "error": str(e)
                    },
                    exc_info=True
                )
                raise
                
        return wrapper
    return decorator