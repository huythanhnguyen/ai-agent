#!/usr/bin/env python3
# -*- coding: utf-8 -*-

"""
Tool Manager Module cho Mega Market AI Agent.

Module này quản lý tất cả các công cụ tương tác với dịch vụ bên ngoài như:
- Tìm kiếm sản phẩm trong Magento
- Kiểm tra thông tin đơn hàng
- Truy vấn thông tin khách hàng từ CDP
"""

import os
import json
import asyncio
import aiohttp
from typing import Dict, Any, List, Optional, Union

import redis.asyncio as redis

from utils.logging import setup_logger
from config import ToolsConfig, CacheConfig

# Setup logging
logger = setup_logger("tool_manager")

# Load configuration
tools_config = ToolsConfig()
cache_config = CacheConfig()


class ToolManager:
    """
    Quản lý các công cụ tương tác với hệ thống bên ngoài.
    
    Chịu trách nhiệm:
    1. Tìm kiếm sản phẩm
    2. Kiểm tra thông tin đơn hàng
    3. Truy vấn thông tin khách hàng
    """
    
    def __init__(self):
        """Khởi tạo Tool Manager và kết nối Redis cache."""
        # Setup Redis connection
        self.redis = redis.Redis(
            host=cache_config.REDIS_HOST,
            port=cache_config.REDIS_PORT,
            db=cache_config.REDIS_TOOL_DB,
            decode_responses=True
        )
        
        # Setup API configurations
        self.search_api_url = tools_config.SEARCH_API_URL
        self.order_api_url = tools_config.ORDER_API_URL
        self.customer_api_url = tools_config.CUSTOMER_API_URL
        self.cdp_api_url = tools_config.CDP_API_URL
        
        # API Headers
        self.headers = {
            "Content-Type": "application/json",
            "Store": tools_config.STORE_CODE,
            "Authorization": f"Bearer {tools_config.API_TOKEN}"
        }
        
        logger.info("Tool Manager initialized")
    
    async def search_products(self, keywords: List[str]) -> Dict[str, Any]:
        """
        Tìm kiếm sản phẩm dựa trên từ khóa.
        
        Parameters:
        -----------
        keywords : List[str]
            Danh sách các từ khóa tìm kiếm
            
        Returns:
        --------
        Dict[str, Any]
            Kết quả tìm kiếm sản phẩm
        """
        results = {}
        
        async with aiohttp.ClientSession() as session:
            tasks = []
            for keyword in keywords:
                # Check cache first
                cache_key = f"product:{keyword}"
                cached = await self.redis.get(cache_key)
                
                if cached:
                    logger.info(f"Product search cache hit for keyword: {keyword}")
                    results[keyword] = json.loads(cached)
                else:
                    # Create search task
                    task = self._fetch_product_data(session, keyword)
                    tasks.append(task)
            
            # Execute all search tasks concurrently
            if tasks:
                task_results = await asyncio.gather(*tasks, return_exceptions=True)
                
                for keyword, result in task_results:
                    if isinstance(result, Exception):
                        logger.error(f"Error searching for keyword {keyword}: {result}")
                        results[keyword] = {"error": str(result)}
                    else:
                        # Cache the result
                        await self.redis.set(
                            f"product:{keyword}", 
                            json.dumps(result), 
                            ex=cache_config.PRODUCT_CACHE_TTL
                        )
                        results[keyword] = result
        
        return results
    
    async def _fetch_product_data(self, session: aiohttp.ClientSession, keyword: str) -> tuple:
        """
        Fetch product data từ Magento API.
        
        Parameters:
        -----------
        session : aiohttp.ClientSession
            Session HTTP
        keyword : str
            Từ khóa tìm kiếm
            
        Returns:
        --------
        tuple
            (keyword, result)
        """
        try:
            # Prepare GraphQL query
            query = {
                "query": f"""
                query ProductSearch {{
                    products(search: "{keyword}", sort: {{ relevance: DESC }}) {{
                        items {{
                            id
                            sku
                            name
                            url_key
                            price_range {{
                                minimum_price {{
                                    regular_price {{
                                        value
                                        currency
                                    }}
                                }}
                            }}
                            small_image {{
                                url
                            }}
                        }}
                        total_count
                    }}
                }}"""
            }
            
            async with session.post(
                self.search_api_url, 
                headers=self.headers, 
                json=query,
                timeout=10
            ) as response:
                if response.status == 200:
                    result = await response.json()
                    logger.info(f"Successfully fetched data for keyword: {keyword}")
                    return keyword, result
                else:
                    error_text = await response.text()
                    logger.error(f"API error: {response.status}, {error_text}")
                    return keyword, {"error": f"API error: {response.status}"}
                    
        except asyncio.TimeoutError:
            logger.error(f"Timeout while searching for keyword: {keyword}")
            return keyword, {"error": "Request timeout"}
            
        except Exception as e:
            logger.error(f"Request error for keyword {keyword}: {e}")
            return keyword, {"error": str(e)}
    
    async def get_order_info(self, order_id: str, user_id: Optional[str] = None) -> Dict[str, Any]:
        """
        Lấy thông tin đơn hàng.
        
        Parameters:
        -----------
        order_id : str
            Mã đơn hàng
        user_id : str, optional
            ID của người dùng
            
        Returns:
        --------
        Dict[str, Any]
            Thông tin đơn hàng
        """
        # Check cache first
        cache_key = f"order:{order_id}"
        cached = await self.redis.get(cache_key)
        
        if cached:
            logger.info(f"Order cache hit for order_id: {order_id}")
            return json.loads(cached)
        
        try:
            # Prepare headers with authentication
            headers = self.headers.copy()
            if user_id:
                headers["Customer-ID"] = user_id
            
            # Fetch order data
            async with aiohttp.ClientSession() as session:
                async with session.get(
                    f"{self.order_api_url}/{order_id}", 
                    headers=headers,
                    timeout=10
                ) as response:
                    if response.status == 200:
                        result = await response.json()
                        
                        # Cache the result
                        await self.redis.set(
                            cache_key, 
                            json.dumps(result), 
                            ex=cache_config.ORDER_CACHE_TTL
                        )
                        
                        logger.info(f"Successfully fetched order info for order_id: {order_id}")
                        return result
                    else:
                        error_text = await response.text()
                        logger.error(f"Order API error: {response.status}, {error_text}")
                        return {"error": f"API error: {response.status}"}
                        
        except asyncio.TimeoutError:
            logger.error(f"Timeout while fetching order info: {order_id}")
            return {"error": "Request timeout"}
            
        except Exception as e:
            logger.error(f"Request error for order {order_id}: {e}")
            return {"error": str(e)}
    
    async def get_customer_info(self, user_id: str) -> Dict[str, Any]:
        """
        Lấy thông tin khách hàng từ Magento.
        
        Parameters:
        -----------
        user_id : str
            ID của người dùng
            
        Returns:
        --------
        Dict[str, Any]
            Thông tin khách hàng
        """
        # Check cache first
        cache_key = f"customer:{user_id}"
        cached = await self.redis.get(cache_key)
        
        if cached:
            logger.info(f"Customer cache hit for user_id: {user_id}")
            return json.loads(cached)
        
        try:
            # Fetch customer data
            async with aiohttp.ClientSession() as session:
                async with session.get(
                    f"{self.customer_api_url}/{user_id}", 
                    headers=self.headers,
                    timeout=10
                ) as response:
                    if response.status == 200:
                        result = await response.json()
                        
                        # Cache the result
                        await self.redis.set(
                            cache_key, 
                            json.dumps(result), 
                            ex=cache_config.CUSTOMER_CACHE_TTL
                        )
                        
                        logger.info(f"Successfully fetched customer info for user_id: {user_id}")
                        return result
                    else:
                        error_text = await response.text()
                        logger.error(f"Customer API error: {response.status}, {error_text}")
                        return {"error": f"API error: {response.status}"}
                        
        except asyncio.TimeoutError:
            logger.error(f"Timeout while fetching customer info: {user_id}")
            return {"error": "Request timeout"}
            
        except Exception as e:
            logger.error(f"Request error for customer {user_id}: {e}")
            return {"error": str(e)}
    
    async def get_cdp_info(self, user_id: str) -> Dict[str, Any]:
        """
        Lấy thông tin khách hàng từ CDP Platform.
        
        Parameters:
        -----------
        user_id : str
            ID của người dùng
            
        Returns:
        --------
        Dict[str, Any]
            Thông tin khách hàng từ CDP
        """
        # Check cache first
        cache_key = f"cdp:{user_id}"
        cached = await self.redis.get(cache_key)
        
        if cached:
            logger.info(f"CDP cache hit for user_id: {user_id}")
            return json.loads(cached)
        
        try:
            # Fetch CDP data
            async with aiohttp.ClientSession() as session:
                async with session.get(
                    f"{self.cdp_api_url}/customers/{user_id}/profile", 
                    headers={
                        "Content-Type": "application/json",
                        "x-api-key": tools_config.CDP_API_KEY
                    },
                    timeout=10
                ) as response:
                    if response.status == 200:
                        result = await response.json()
                        
                        # Cache the result
                        await self.redis.set(
                            cache_key, 
                            json.dumps(result), 
                            ex=cache_config.CDP_CACHE_TTL
                        )
                        
                        logger.info(f"Successfully fetched CDP info for user_id: {user_id}")
                        return result
                    else:
                        error_text = await response.text()
                        logger.error(f"CDP API error: {response.status}, {error_text}")
                        return {"error": f"API error: {response.status}"}
                        
        except asyncio.TimeoutError:
            logger.error(f"Timeout while fetching CDP info: {user_id}")
            return {"error": "Request timeout"}
            
        except Exception as e:
            logger.error(f"Request error for CDP profile {user_id}: {e}")
            return {"error": str(e)}
    
    async def create_order(self, user_id: str, order_data: Dict[str, Any]) -> Dict[str, Any]:
        """
        Tạo đơn hàng mới trong Magento.
        
        Parameters:
        -----------
        user_id : str
            ID của người dùng
        order_data : Dict[str, Any]
            Dữ liệu đơn hàng
            
        Returns:
        --------
        Dict[str, Any]
            Kết quả tạo đơn hàng
        """
        try:
            # Prepare headers with authentication
            headers = self.headers.copy()
            if user_id:
                headers["Customer-ID"] = user_id
                
            # Create order
            async with aiohttp.ClientSession() as session:
                async with session.post(
                    self.order_api_url,
                    headers=headers,
                    json=order_data,
                    timeout=15  # Order creation can take longer
                ) as response:
                    result = await response.json()
                    
                    if response.status in (200, 201):
                        logger.info(f"Successfully created order for user_id: {user_id}")
                        return result
                    else:
                        logger.error(f"Order creation API error: {response.status}, {result}")
                        return {"error": f"API error: {response.status}", "details": result}
                        
        except asyncio.TimeoutError:
            logger.error(f"Timeout while creating order for user_id: {user_id}")
            return {"error": "Request timeout"}
            
        except Exception as e:
            logger.error(f"Request error creating order for user {user_id}: {e}")
            return {"error": str(e)}