document.addEventListener("DOMContentLoaded", function () {
    // DOM Elements
    const chatInput = document.getElementById("chat-input");
    const sendButton = document.getElementById("send-button");
    const chatWindow = document.getElementById("chat-window");
    const clearInput = document.getElementById("clear-input");
    const productContainer = document.getElementById("product-container");
    const orderContainer = document.getElementById("order-container");
    const typingIndicator = document.getElementById("typing-indicator");

    // Configuration
    const API_URL = "http://localhost:5000/chat";
    let sessionId = generateSessionId();
    let userId = null; // Will be set after authentication
    
    // State variables
    let isTyping = false;
    let conversationHistory = [];

    // Initialize quick action buttons
    initializeQuickActions();
    
    // Check connection status
    checkAPIConnection();

    // Event Listeners
    sendButton.addEventListener("click", handleUserMessage);
    chatInput.addEventListener("keydown", function(e) {
        if (e.key === "Enter" && !e.shiftKey) {
            e.preventDefault();
            handleUserMessage();
        }
    });
    
    clearInput.addEventListener("click", function() {
        chatInput.value = "";
        updateSendButtonState();
    });
    
    chatInput.addEventListener("input", updateSendButtonState);

    // Check if API is available
    async function checkAPIConnection() {
        const statusIndicator = document.querySelector(".connection-status");
        
        try {
            const response = await fetch(API_URL, {
                method: "HEAD"
            });
            
            if (response.ok) {
                statusIndicator.classList.remove("offline");
                statusIndicator.classList.add("online");
                statusIndicator.querySelector(".status-text").textContent = "Đang hoạt động";
            } else {
                setOfflineStatus(statusIndicator);
            }
        } catch (error) {
            setOfflineStatus(statusIndicator);
        }
    }
    
    function setOfflineStatus(indicator) {
        indicator.classList.remove("online");
        indicator.classList.add("offline");
        indicator.querySelector(".status-text").textContent = "Ngoại tuyến";
        
        // Add an offline message
        addBotMessageToChat("Xin lỗi, dịch vụ hiện đang ngoại tuyến. Vui lòng thử lại sau hoặc liên hệ bộ phận hỗ trợ.");
    }

    // Initialize quick action buttons
    function initializeQuickActions() {
        document.querySelectorAll(".quick-action-btn").forEach(button => {
            button.addEventListener("click", function() {
                const action = this.getAttribute("data-action");
                chatInput.value = action;
                handleUserMessage();
            });
        });
    }

    // Update send button state based on input
    function updateSendButtonState() {
        if (chatInput.value.trim() === "") {
            sendButton.disabled = true;
        } else {
            sendButton.disabled = false;
        }
    }
    
    // Initialize send button state
    updateSendButtonState();

    // Handle user message
    async function handleUserMessage() {
        const userMessage = chatInput.value.trim();
        if (!userMessage || isTyping) return;
        
        // Clear input
        chatInput.value = "";
        updateSendButtonState();
        
        // Add user message to chat
        addUserMessageToChat(userMessage);
        
        // Save to conversation history
        conversationHistory.push({
            role: "user",
            message: userMessage
        });
        
        // Show typing indicator
        setTypingState(true);
        
        try {
            // Send to API and get response
            const botResponse = await sendUserMessage(userMessage);
            
            // Hide typing indicator
            setTypingState(false);
            
            // Process the response
            processResponse(botResponse);
            
            // Save to conversation history
            conversationHistory.push({
                role: "bot",
                message: botResponse.message,
                type: botResponse.type,
                data: botResponse.data
            });
            
        } catch (error) {
            // Hide typing indicator
            setTypingState(false);
            
            // Show error message
            addBotMessageToChat("Xin lỗi, tôi không thể xử lý yêu cầu của bạn lúc này. Vui lòng thử lại sau.");
            console.error("API Error:", error);
        }
    }

    // Show/hide typing indicator
    function setTypingState(typing) {
        isTyping = typing;
        if (typing) {
            typingIndicator.classList.add("active");
        } else {
            typingIndicator.classList.remove("active");
        }
    }

    // Send message to API
    async function sendUserMessage(userMessage) {
        const response = await fetch(API_URL, {
            method: "POST",
            headers: { "Content-Type": "application/json" },
            body: JSON.stringify({ 
                message: userMessage,
                session_id: sessionId,
                user_id: userId
            })
        });

        if (!response.ok) {
            throw new Error(`HTTP error! Status: ${response.status}`);
        }
        
        return await response.json();
    }

    // Process the bot response
    function processResponse(response) {
        hideAllResponseContainers();
        
        // Add the text message to chat
        addBotMessageToChat(response.message);
        
        // Process different response types
        if (response.type === "product" && response.data) {
            renderProductResponse(response.data);
        } else if (response.type === "order" && response.data) {
            renderOrderResponse(response.data);
        }
    }

    // Hide all response containers
    function hideAllResponseContainers() {
        productContainer.classList.remove("active");
        orderContainer.classList.remove("active");
        productContainer.innerHTML = "";
        orderContainer.innerHTML = "";
    }

    // Add user message to chat
    function addUserMessageToChat(text) {
        const messageElement = document.createElement("div");
        messageElement.classList.add("user-message");
        
        messageElement.innerHTML = `
            <div class="message-content">
                <div class="message-text">${text}</div>
            </div>
            <div class="message-avatar">
                <i class="fas fa-user"></i>
            </div>
        `;
        
        chatWindow.appendChild(messageElement);
        scrollToBottom();
    }

    // Add bot message to chat
    function addBotMessageToChat(text, includeQuickActions = false) {
        const messageElement = document.createElement("div");
        messageElement.classList.add("bot-message");
        
        let quickActionsHTML = '';
        if (includeQuickActions) {
            quickActionsHTML = `
                <div class="quick-actions">
                    <button class="quick-action-btn" data-action="Tìm sản phẩm">Tìm sản phẩm</button>
                    <button class="quick-action-btn" data-action="Kiểm tra đơn hàng">Kiểm tra đơn hàng</button>
                    <button class="quick-action-btn" data-action="Hỗ trợ">Cần hỗ trợ</button>
                </div>
            `;
        }
        
        messageElement.innerHTML = `
            <div class="message-avatar">
                <i class="fas fa-robot"></i>
            </div>
            <div class="message-content">
                <div class="message-text">${text}</div>
                ${quickActionsHTML}
            </div>
        `;
        
        chatWindow.appendChild(messageElement);
        scrollToBottom();
        
        // Initialize any quick action buttons in this message
        if (includeQuickActions) {
            messageElement.querySelectorAll(".quick-action-btn").forEach(button => {
                button.addEventListener("click", function() {
                    const action = this.getAttribute("data-action");
                    chatInput.value = action;
                    handleUserMessage();
                });
            });
        }
    }

    // Render product response
    function renderProductResponse(data) {
        productContainer.classList.add("active");
        
        let html = '<h4>Kết quả tìm kiếm sản phẩm:</h4>';
        
        // For each keyword
        for (const keyword in data.results) {
            const result = data.results[keyword];
            
            if (result.error) {
                html += `<div class="error-message">Lỗi khi tìm kiếm "${keyword}": ${result.error}</div>`;
                continue;
            }
            
            if (result.total_count === 0) {
                html += `<div class="no-results">Không tìm thấy sản phẩm nào cho "${keyword}"</div>`;
                continue;
            }
            
            html += `
                <div class="product-section">
                    <h5 class="product-section-title">Kết quả cho "${keyword}" (${result.total_count} sản phẩm)</h5>
                    <div class="product-carousel">
            `;
            
            result.products.forEach(product => {
                const price = product.price_range?.minimum_price?.regular_price;
                const formattedPrice = price ? `${formatPrice(price.value)} ${price.currency}` : "Liên hệ";
                
                html += `
                    <div class="product-card">
                        <img class="product-thumbnail" src="${product.small_image?.url || 'placeholder-image.png'}" alt="${product.name}" onerror="this.src='https://via.placeholder.com/200x150?text=No+Image'">
                        <div class="product-info">
                            <h5 class="product-name">${product.name}</h5>
                            <p class="product-sku">SKU: ${product.sku}</p>
                            <p class="product-price">${formattedPrice}</p>
                            <div class="product-action">
                                <button class="add-to-cart-btn" data-sku="${product.sku}">Thêm vào giỏ</button>
                            </div>
                        </div>
                    </div>
                `;
            });
            
            html += `
                    </div>
                </div>
            `;
        }
        
        productContainer.innerHTML = html;
        
        // Add event listeners for "Add to cart" buttons
        productContainer.querySelectorAll(".add-to-cart-btn").forEach(button => {
            button.addEventListener("click", function() {
                const sku = this.getAttribute("data-sku");
                handleAddToCart(sku);
            });
        });
    }

    // Handle add to cart
    function handleAddToCart(sku) {
        // This would connect to your cart API
        console.log(`Adding product with SKU ${sku} to cart`);
        
        // Show confirmation in chat
        addBotMessageToChat(`Đã thêm sản phẩm có mã <strong>${sku}</strong> vào giỏ hàng của bạn!`);
        
        // You would typically make an API call here to actually add the item to the cart
    }

    // Render order response
    function renderOrderResponse(data) {
        orderContainer.classList.add("active");
        
        let itemsHTML = '';
        let total = 0;
        
        if (data.items && data.items.length > 0) {
            data.items.forEach(item => {
                const itemTotal = item.price * item.quantity;
                total += itemTotal;
                
                itemsHTML += `
                    <div class="order-item">
                        <div>${item.name} (x${item.quantity})</div>
                        <div>${formatPrice(itemTotal)} ${typeof data.currency !== 'undefined' ? data.currency : 'VND'}</div>
                    </div>
                `;
            });
        }
        
        const orderHTML = `
            <div class="order-info">
                <h4>Thông tin đơn hàng #${data.order_id}</h4>
                
                <div class="order-detail">
                    <div>Trạng thái:</div>
                    <div><span class="order-status ${data.status}">${translateOrderStatus(data.status)}</span></div>
                </div>
                
                <div class="order-detail">
                    <div>Ngày đặt hàng:</div>
                    <div>${data.order_date || 'N/A'}</div>
                </div>
                
                <h5>Chi tiết sản phẩm:</h5>
                <div class="order-items">
                    ${itemsHTML}
                    <div class="order-item order-total">
                        <div>Tổng cộng:</div>
                        <div>${formatPrice(data.total || total)} ${typeof data.currency !== 'undefined' ? data.currency : 'VND'}</div>
                    </div>
                </div>
                
                <div class="order-actions">
                    <button class="order-action-btn" data-action="track">Theo dõi đơn hàng</button>
                    <button class="order-action-btn" data-action="cancel">Hủy đơn hàng</button>
                </div>
            </div>
        `;
        
        orderContainer.innerHTML = orderHTML;
        
        // Add event listeners to order action buttons
        orderContainer.querySelectorAll(".order-action-btn").forEach(button => {
            button.addEventListener("click", function() {
                const action = this.getAttribute("data-action");
                handleOrderAction(action, data.order_id);
            });
        });
    }

    // Handle order action (track, cancel, etc.)
    function handleOrderAction(action, orderId) {
        if (action === "track") {
            // This would connect to your tracking API
            addBotMessageToChat(`Đơn hàng #${orderId} đang trong quá trình vận chuyển. Dự kiến giao hàng trong 3-5 ngày làm việc.`);
        } else if (action === "cancel") {
            // This would connect to your order cancellation API
            addBotMessageToChat(`Yêu cầu hủy đơn hàng #${orderId} đã được ghi nhận. Bộ phận CSKH sẽ liên hệ với bạn trong thời gian sớm nhất.`);
        }
    }

    // Helper Functions
    function scrollToBottom() {
        chatWindow.scrollTop = chatWindow.scrollHeight;
    }

    function formatPrice(price) {
        return new Intl.NumberFormat('vi-VN').format(price);
    }

    function translateOrderStatus(status) {
        const statusMap = {
            'processing': 'Đang xử lý',
            'pending': 'Chờ xác nhận',
            'pending_payment': 'Chờ thanh toán',
            'on_hold': 'Tạm giữ',
            'completed': 'Hoàn thành',
            'canceled': 'Đã hủy',
            'refunded': 'Đã hoàn tiền',
            'failed': 'Thất bại',
            'shipped': 'Đang giao hàng'
        };
        
        return statusMap[status] || status;
    }

    function generateSessionId() {
        return 'xxxx-xxxx-xxxx-xxxx'.replace(/[x]/g, function(c) {
            const r = Math.random() * 16 | 0;
            return r.toString(16);
        });
    }
});