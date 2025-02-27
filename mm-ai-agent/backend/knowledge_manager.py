# Delete conversation history
            history_key = f"conversation:{session_id}"
            await self.redis.delete(history_key)
            
            logger.info(f"Cleared session data for session: {session_id}")
            return True
            
        except Exception as e:
            logger.error(f"Error clearing session data: {str(e)}")
            return False
    
    async def get_personalized_recommendations(
        self, 
        user_id: str, 
        limit: int = 5,
        context: Optional[Dict[str, Any]] = None
    ) -> List[Dict[str, Any]]:
        """
        Lấy đề xuất sản phẩm cá nhân hóa từ CDP.
        
        Parameters:
        -----------
        user_id : str
            ID của người dùng
        limit : int
            Số lượng sản phẩm đề xuất tối đa
        context : Dict[str, Any], optional
            Context bổ sung cho đề xuất
            
        Returns:
        --------
        List[Dict[str, Any]]
            Danh sách sản phẩm đề xuất
        """
        try:
            # Check cache first
            cache_key = f"recommendations:{user_id}"
            cached = await self.redis.get(cache_key)
            
            if cached:
                logger.info(f"Recommendations cache hit for user: {user_id}")
                return json.loads(cached)
            
            # In a real system, this would call the CDP API
            # For now, we use dummy recommendations
            recommendations = self._get_dummy_recommendations(user_id, limit, context)
            
            # Cache the result
            await self.redis.set(
                cache_key,
                json.dumps(recommendations),
                ex=cache_config.CDP_CACHE_TTL
            )
            
            return recommendations
            
        except Exception as e:
            logger.error(f"Error getting personalized recommendations: {str(e)}")
            return []
    
    def _get_dummy_recommendations(
        self, 
        user_id: str, 
        limit: int,
        context: Optional[Dict[str, Any]] = None
    ) -> List[Dict[str, Any]]:
        """
        Generate dummy personalized recommendations.
        In a real system, this would call the CDP API.
        """
        # This is just placeholder data
        categories = ["Điện tử", "Gia dụng", "Thời trang", "Thực phẩm"]
        
        # Use context if available
        if context and "interests" in context:
            categories = context["interests"]
        
        recommendations = []
        for i in range(1, limit + 1):
            category = categories[i % len(categories)]
            recommendations.append({
                "id": f"rec-{user_id}-{i}",
                "name": f"{category} Recommendation {i}",
                "price": 200000 + (i * 100000),
                "category": category,
                "image_url": f"https://example.com/products/rec-{i}.jpg",
                "url": f"https://megamarket.vn/products/rec-{i}",
                "reason": f"Dựa trên lịch sử mua hàng {category.lower()} của bạn"
            })
        
        return recommendations
    
    async def log_user_interaction(
        self, 
        session_id: str, 
        user_id: Optional[str],
        interaction_type: str,
        interaction_data: Dict[str, Any]
    ) -> bool:
        """
        Ghi lại tương tác của người dùng để phân tích sau này.
        
        Parameters:
        -----------
        session_id : str
            ID phiên làm việc
        user_id : str, optional
            ID của người dùng nếu đã xác thực
        interaction_type : str
            Loại tương tác (chat, product_view, order, etc.)
        interaction_data : Dict[str, Any]
            Dữ liệu tương tác
            
        Returns:
        --------
        bool
            True nếu ghi thành công, False nếu có lỗi
        """
        try:
            # Create interaction object
            interaction = {
                "session_id": session_id,
                "user_id": user_id,
                "interaction_type": interaction_type,
                "timestamp": time.time(),
                "date": datetime.now().isoformat(),
                "data": interaction_data
            }
            
            # In a real system, this would be sent to an analytics service
            # For now, we just log it
            logger.info(f"User interaction: {interaction_type} from session {session_id}")
            
            # We could also store this in Redis for short-term analysis
            interaction_key = f"interaction:{session_id}:{int(time.time())}"
            await self.redis.set(
                interaction_key,
                json.dumps(interaction),
                ex=cache_config.INTERACTION_TTL
            )
            
            return True
            
        except Exception as e:
            logger.error(f"Error logging user interaction: {str(e)}")
            return False
    
    async def get_product_details(self, product_id: str) -> Dict[str, Any]:
        """
        Lấy thông tin chi tiết về sản phẩm.
        
        Parameters:
        -----------
        product_id : str
            ID sản phẩm
            
        Returns:
        --------
        Dict[str, Any]
            Thông tin chi tiết sản phẩm
        """
        try:
            # Check cache first
            cache_key = f"product:detail:{product_id}"
            cached = await self.redis.get(cache_key)
            
            if cached:
                logger.info(f"Product details cache hit for: {product_id}")
                return json.loads(cached)
            
            # In a real system, this would query the database or API
            # For now, we use dummy data
            product = self._get_dummy_product_details(product_id)
            
            # Cache the result
            await self.redis.set(
                cache_key,
                json.dumps(product),
                ex=cache_config.PRODUCT_CACHE_TTL
            )
            
            return product
            
        except Exception as e:
            logger.error(f"Error retrieving product details: {str(e)}")
            return {"error": str(e)}
    
    def _get_dummy_product_details(self, product_id: str) -> Dict[str, Any]:
        """
        Generate dummy product details.
        In a real system, this would query the database or API.
        """
        # Generate consistent dummy data based on product_id
        hash_val = int(hashlib.md5(product_id.encode()).hexdigest(), 16) % 10000
        
        categories = ["Điện tử", "Gia dụng", "Thời trang", "Thực phẩm"]
        brands = ["Samsung", "LG", "Sony", "Apple", "Xiaomi", "Philips", "Sunhouse"]
        
        # Use hash_val to deterministically select category and brand
        category = categories[hash_val % len(categories)]
        brand = brands[(hash_val // 10) % len(brands)]
        
        return {
            "id": product_id,
            "name": f"{brand} {category} Product {hash_val}",
            "brand": brand,
            "category": category,
            "price": 100000 + (hash_val * 100),
            "discount_price": 100000 + (hash_val * 100) * 0.9 if hash_val % 3 == 0 else None,
            "stock": hash_val % 50,
            "rating": (hash_val % 50) / 10,
            "image_url": f"https://example.com/products/{product_id}.jpg",
            "description": f"Đây là sản phẩm {category.lower()} chất lượng cao từ {brand}. Sản phẩm có nhiều tính năng nổi bật và thiết kế hiện đại.",
            "specifications": {
                "Thương hiệu": brand,
                "Xuất xứ": "Việt Nam" if hash_val % 2 == 0 else "Nhập khẩu",
                "Bảo hành": f"{6 + (hash_val % 18)} tháng",
                "Kích thước": f"{20 + (hash_val % 30)}cm x {15 + (hash_val % 25)}cm x {5 + (hash_val % 10)}cm",
                "Trọng lượng": f"{500 + (hash_val % 1500)}g"
            },
            "url": f"https://megamarket.vn/products/{product_id}"
        }