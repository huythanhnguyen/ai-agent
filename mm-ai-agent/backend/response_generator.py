#!/usr/bin/env python3
# -*- coding: utf-8 -*-

"""
Response Generator Module cho Mega Market AI Agent.

Module này chịu trách nhiệm tạo và định dạng các phản hồi cuối cùng
của AI Agent gửi lại cho người dùng, bao gồm định dạng kết quả sản phẩm,
thông tin đơn hàng, v.v.
"""

from typing import Dict, Any, List, Optional

from pydantic import BaseModel

from utils.logging import setup_logger

# Setup logging
logger = setup_logger("response_generator")


class AgentResponse(BaseModel):
    """Model cho response từ AI Agent."""
    message: str
    data: Optional[Dict[str, Any]] = None
    type: str  # 'text', 'product', 'order', etc.


class ResponseGenerator:
    """
    Tạo và định dạng các phản hồi của AI Agent.
    
    Chịu trách nhiệm:
    1. Định dạng kết quả tìm kiếm sản phẩm
    2. Định dạng thông tin đơn hàng
    3. Tạo câu trả lời dựa trên context
    """
    
    def __init__(self):
        """Khởi tạo Response Generator."""
        logger.info("Response Generator initialized")
    
    def format_product_response(
        self,
        products: Dict[str, Any],
        keywords: List[str]
    ) -> AgentResponse:
        """
        Định dạng kết quả tìm kiếm sản phẩm.
        
        Parameters:
        -----------
        products : Dict[str, Any]
            Kết quả tìm kiếm sản phẩm từ Tool Manager
        keywords : List[str]
            Các từ khóa đã tìm kiếm
            
        Returns:
        --------
        AgentResponse
            Response đã được định dạng
        """
        # Initialize response data
        formatted_data = {
            "keywords": keywords,
            "results": {}
        }
        
        all_products_count = 0
        error_count = 0
        
        # Process each keyword result
        for keyword, result in products.items():
            if "error" in result:
                formatted_data["results"][keyword] = {
                    "error": result["error"],
                    "products": []
                }
                error_count += 1
            else:
                # Extract product data
                try:
                    product_items = result.get("data", {}).get("products", {}).get("items", [])
                    total_count = result.get("data", {}).get("products", {}).get("total_count", 0)
                    
                    formatted_data["results"][keyword] = {
                        "total_count": total_count,
                        "products": product_items
                    }
                    
                    all_products_count += total_count
                except Exception as e:
                    logger.error(f"Error formatting products for {keyword}: {e}")
                    formatted_data["results"][keyword] = {
                        "error": f"Data formatting error: {str(e)}",
                        "products": []
                    }
                    error_count += 1
        
        # Generate response message
        if all_products_count > 0:
            message = f"Tìm thấy {all_products_count} sản phẩm liên quan đến từ khóa: {', '.join(keywords)}"
        elif error_count == len(keywords):
            message = "Xin lỗi, có lỗi khi tìm kiếm sản phẩm. Vui lòng thử lại sau."
        else:
            message = f"Không tìm thấy sản phẩm nào cho từ khóa: {', '.join(keywords)}"
        
        return AgentResponse(
            message=message,
            data=formatted_data,
            type="product"
        )
    
    def format_order_response(self, order_info: Dict[str, Any]) -> AgentResponse:
        """
        Định dạng thông tin đơn hàng.
        
        Parameters:
        -----------
        order_info : Dict[str, Any]
            Thông tin đơn hàng từ Tool Manager
            
        Returns:
        --------
        AgentResponse
            Response đã được định dạng
        """
        if "error" in order_info:
            return AgentResponse(
                message=f"Xin lỗi, không thể lấy thông tin đơn hàng: {order_info['error']}",
                type="text"
            )
        
        # Extract order details
        order_id = order_info.get("order_id", "N/A")
        status = order_info.get("status", "N/A")
        
        # Format status message for Vietnamese
        status_map = {
            "processing": "đang xử lý",
            "pending": "chờ xác nhận",
            "pending_payment": "chờ thanh toán",
            "on_hold": "tạm giữ",
            "completed": "đã hoàn thành",
            "shipped": "đang giao hàng",
            "canceled": "đã hủy",
            "refunded": "đã hoàn tiền"
        }
        
        status_vi = status_map.get(status.lower(), status)
        
        # Generate message
        message = f"Đơn hàng #{order_id} đang trong trạng thái {status_vi}."
        
        # Add estimated delivery if available
        if "estimated_delivery" in order_info:
            message += f" Dự kiến giao hàng vào ngày {order_info['estimated_delivery']}."
        
        return AgentResponse(
            message=message,
            data=order_info,
            type="order"
        )
    
    def format_customer_profile_response(
        self,
        customer_info: Dict[str, Any],
        cdp_info: Optional[Dict[str, Any]] = None
    ) -> AgentResponse:
        """
        Định dạng thông tin hồ sơ khách hàng với dữ liệu từ Magento và CDP.
        
        Parameters:
        -----------
        customer_info : Dict[str, Any]
            Thông tin khách hàng từ Magento
        cdp_info : Dict[str, Any], optional
            Thông tin khách hàng từ CDP Platform
            
        Returns:
        --------
        AgentResponse
            Response đã được định dạng
        """
        if "error" in customer_info:
            return AgentResponse(
                message=f"Xin lỗi, không thể lấy thông tin khách hàng: {customer_info['error']}",
                type="text"
            )
        
        # Extract basic customer details
        customer_name = customer_info.get("firstname", "") + " " + customer_info.get("lastname", "")
        customer_email = customer_info.get("email", "N/A")
        
        # Generate message
        message = f"Xin chào {customer_name}! "
        
        # Add loyalty info if available
        if cdp_info and "loyalty" in cdp_info:
            loyalty = cdp_info["loyalty"]
            tier = loyalty.get("tier", "")
            points = loyalty.get("points", 0)
            
            if tier and points:
                message += f"Bạn đang ở hạng {tier} với {points} điểm tích lũy. "
        
        # Add purchase history if available
        if cdp_info and "purchase_history" in cdp_info:
            purchase_count = cdp_info["purchase_history"].get("total_orders", 0)
            if purchase_count > 0:
                message += f"Bạn đã thực hiện {purchase_count} đơn hàng với Mega Market. "
        
        # Add recommendations if available
        if cdp_info and "recommendations" in cdp_info and cdp_info["recommendations"]:
            message += "Dựa trên lịch sử mua hàng, chúng tôi có một số đề xuất sản phẩm dành cho bạn."
        
        # Combine data
        combined_data = {
            "basic_info": customer_info,
        }
        
        if cdp_info:
            combined_data["cdp_info"] = cdp_info
        
        return AgentResponse(
            message=message,
            data=combined_data,
            type="customer_profile"
        )
    
    def format_search_suggestions(self, products: List[Dict[str, Any]]) -> AgentResponse:
        """
        Định dạng gợi ý tìm kiếm sản phẩm tương tự.
        
        Parameters:
        -----------
        products : List[Dict[str, Any]]
            Danh sách sản phẩm gợi ý
            
        Returns:
        --------
        AgentResponse
            Response đã được định dạng
        """
        if not products:
            return AgentResponse(
                message="Không có gợi ý sản phẩm nào.",
                type="text"
            )
        
        # Generate message with suggestions
        message = "Bạn có thể quan tâm đến các sản phẩm sau:"
        
        # Prepare data
        formatted_data = {
            "suggestions": products,
            "total_count": len(products)
        }
        
        return AgentResponse(
            message=message,
            data=formatted_data,
            type="suggestion"
        )
    
    def format_category_response(self, category_info: Dict[str, Any]) -> AgentResponse:
        """
        Định dạng thông tin danh mục sản phẩm.
        
        Parameters:
        -----------
        category_info : Dict[str, Any]
            Thông tin danh mục
            
        Returns:
        --------
        AgentResponse
            Response đã được định dạng
        """
        if "error" in category_info:
            return AgentResponse(
                message=f"Xin lỗi, không thể lấy thông tin danh mục: {category_info['error']}",
                type="text"
            )
        
        # Extract category details
        category_name = category_info.get("name", "")
        
        # Generate message
        message = f"Thông tin về danh mục {category_name}:"
        
        if "subcategories" in category_info:
            subcats = ", ".join(category_info["subcategories"])
            message += f"\nDanh mục con: {subcats}"
        
        if "popular_brands" in category_info:
            brands = ", ".join(category_info["popular_brands"])
            message += f"\nThương hiệu nổi bật: {brands}"
        
        if "promotion" in category_info:
            message += f"\nKhuyến mãi hiện tại: {category_info['promotion']}"
        
        return AgentResponse(
            message=message,
            data=category_info,
            type="category"
        )
    
    def format_error_response(self, error_message: str) -> AgentResponse:
        """
        Định dạng thông báo lỗi.
        
        Parameters:
        -----------
        error_message : str
            Thông điệp lỗi
            
        Returns:
        --------
        AgentResponse
            Response đã được định dạng
        """
        return AgentResponse(
            message=f"Xin lỗi, đã có lỗi xảy ra: {error_message}. Vui lòng thử lại sau hoặc liên hệ tổng đài 1900 1234 để được hỗ trợ.",
            type="error"
        )
    
    def format_fallback_response(self) -> AgentResponse:
        """
        Định dạng phản hồi dự phòng.
        
        Returns:
        --------
        AgentResponse
            Response đã được định dạng
        """
        return AgentResponse(
            message="Xin lỗi, tôi không hiểu yêu cầu của bạn. Bạn có thể hỏi về sản phẩm, đơn hàng, hoặc các dịch vụ của Mega Market.",
            type="text"
        )