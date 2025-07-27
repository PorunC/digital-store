"""Payment service for handling different payment gateways."""
import logging
from datetime import datetime
from typing import Dict, Optional

from app.models.order import Order, OrderStatus, PaymentGateway
from app.schemas.order import PaymentRequest, PaymentResponse
from app.services.order_service import OrderService
from app.config import settings

logger = logging.getLogger(__name__)


class PaymentService:
    """Service for payment processing."""
    
    @staticmethod
    async def create_payment(payment_request: PaymentRequest) -> Optional[PaymentResponse]:
        """Create payment for an order."""
        order = await OrderService.get_by_id(payment_request.order_id)
        if not order or not order.is_pending:
            logger.warning(f"Invalid order for payment: {payment_request.order_id}")
            return None
        
        gateway = payment_request.payment_gateway.lower()
        
        if gateway == PaymentGateway.TELEGRAM_STARS.value:
            return await PaymentService._create_telegram_stars_payment(order)
        elif gateway == PaymentGateway.CRYPTOMUS.value:
            return await PaymentService._create_cryptomus_payment(order)
        else:
            logger.error(f"Unsupported payment gateway: {gateway}")
            return None
    
    @staticmethod
    async def handle_payment_callback(
        gateway: str,
        payment_id: str,
        callback_data: Dict
    ) -> bool:
        """Handle payment callback from gateway."""
        if gateway == PaymentGateway.TELEGRAM_STARS.value:
            return await PaymentService._handle_telegram_stars_callback(payment_id, callback_data)
        elif gateway == PaymentGateway.CRYPTOMUS.value:
            return await PaymentService._handle_cryptomus_callback(payment_id, callback_data)
        else:
            logger.error(f"Unsupported gateway callback: {gateway}")
            return False
    
    @staticmethod
    async def _create_telegram_stars_payment(order: Order) -> Optional[PaymentResponse]:
        """Create Telegram Stars payment."""
        if not settings.telegram_stars_enabled:
            logger.warning("Telegram Stars payments are disabled")
            return None
        
        try:
            # For Telegram Stars, we don't need external API calls
            # The payment is handled directly through Telegram Bot API
            payment_id = f"stars_{order.order_number}"
            
            # Update order with payment info
            await OrderService.update_order(order.id, {
                "payment_gateway": PaymentGateway.TELEGRAM_STARS.value,
                "payment_id": payment_id,
                "status": OrderStatus.PROCESSING.value
            })
            
            return PaymentResponse(
                payment_id=payment_id,
                payment_url=None,  # Handled in bot
                qr_code=None,
                expires_at=order.expires_at
            )
            
        except Exception as e:
            logger.error(f"Failed to create Telegram Stars payment: {e}")
            return None
    
    @staticmethod
    async def _create_cryptomus_payment(order: Order) -> Optional[PaymentResponse]:
        """Create Cryptomus payment."""
        if not settings.cryptomus_enabled or not settings.cryptomus_api_key:
            logger.warning("Cryptomus payments are disabled or not configured")
            return None
        
        try:
            import httpx
            
            # Cryptomus API endpoint
            url = "https://api.cryptomus.com/v1/payment"
            
            # Prepare payment data
            payment_data = {
                "amount": str(order.total_price),
                "currency": order.currency,
                "order_id": order.order_number,
                "callback_url": f"https://{settings.bot_domain}/api/webhooks/cryptomus",
                "return_url": f"https://{settings.bot_domain}/payment/success",
                "cancel_url": f"https://{settings.bot_domain}/payment/cancel"
            }
            
            headers = {
                "merchant": settings.cryptomus_merchant_id,
                "sign": PaymentService._generate_cryptomus_signature(payment_data)
            }
            
            async with httpx.AsyncClient() as client:
                response = await client.post(url, json=payment_data, headers=headers)
                
                if response.status_code == 200:
                    result = response.json()
                    payment_id = result.get("uuid")
                    payment_url = result.get("url")
                    
                    # Update order with payment info
                    await OrderService.update_order(order.id, {
                        "payment_gateway": PaymentGateway.CRYPTOMUS.value,
                        "payment_id": payment_id,
                        "status": OrderStatus.PROCESSING.value,
                        "payment_data": result
                    })
                    
                    return PaymentResponse(
                        payment_id=payment_id,
                        payment_url=payment_url,
                        qr_code=result.get("qr_code"),
                        expires_at=order.expires_at
                    )
                else:
                    logger.error(f"Cryptomus API error: {response.status_code} - {response.text}")
                    return None
                    
        except Exception as e:
            logger.error(f"Failed to create Cryptomus payment: {e}")
            return None
    
    @staticmethod
    async def _handle_telegram_stars_callback(payment_id: str, callback_data: Dict) -> bool:
        """Handle Telegram Stars payment callback."""
        try:
            # Extract order number from payment_id
            order_number = payment_id.replace("stars_", "")
            order = await OrderService.get_by_order_number(order_number)
            
            if not order:
                logger.error(f"Order not found for Telegram Stars callback: {order_number}")
                return False
            
            # Check payment status
            if callback_data.get("successful_payment"):
                # Payment successful
                await OrderService.complete_order(order.id)
                logger.info(f"Telegram Stars payment completed: {payment_id}")
                return True
            else:
                # Payment failed
                await OrderService.cancel_order(order.id, "Payment failed")
                logger.info(f"Telegram Stars payment failed: {payment_id}")
                return False
                
        except Exception as e:
            logger.error(f"Error handling Telegram Stars callback: {e}")
            return False
    
    @staticmethod
    async def _handle_cryptomus_callback(payment_id: str, callback_data: Dict) -> bool:
        """Handle Cryptomus payment callback."""
        try:
            # Verify callback signature
            if not PaymentService._verify_cryptomus_callback(callback_data):
                logger.error("Invalid Cryptomus callback signature")
                return False
            
            # Find order by payment_id
            order = None
            orders = await OrderService.get_all_orders(status=OrderStatus.PROCESSING.value)
            for o in orders:
                if o.payment_id == payment_id:
                    order = o
                    break
            
            if not order:
                logger.error(f"Order not found for Cryptomus callback: {payment_id}")
                return False
            
            # Check payment status
            status = callback_data.get("status")
            if status == "paid":
                # Payment successful
                await OrderService.complete_order(order.id)
                logger.info(f"Cryptomus payment completed: {payment_id}")
                return True
            elif status in ["failed", "cancelled", "expired"]:
                # Payment failed
                await OrderService.cancel_order(order.id, f"Payment {status}")
                logger.info(f"Cryptomus payment {status}: {payment_id}")
                return False
            else:
                # Payment still processing
                logger.info(f"Cryptomus payment processing: {payment_id}")
                return True
                
        except Exception as e:
            logger.error(f"Error handling Cryptomus callback: {e}")
            return False
    
    @staticmethod
    def _generate_cryptomus_signature(data: Dict) -> str:
        """Generate signature for Cryptomus API request."""
        import hashlib
        import json
        
        # Sort data and create string
        sorted_data = json.dumps(data, sort_keys=True, separators=(',', ':'))
        
        # Create signature with API key
        signature_string = sorted_data + settings.cryptomus_api_key
        signature = hashlib.md5(signature_string.encode()).hexdigest()
        
        return signature
    
    @staticmethod
    def _verify_cryptomus_callback(callback_data: Dict) -> bool:
        """Verify Cryptomus callback signature."""
        try:
            import hashlib
            import json
            
            received_signature = callback_data.pop("sign", "")
            if not received_signature:
                return False
            
            # Generate expected signature
            sorted_data = json.dumps(callback_data, sort_keys=True, separators=(',', ':'))
            signature_string = sorted_data + settings.cryptomus_api_key
            expected_signature = hashlib.md5(signature_string.encode()).hexdigest()
            
            return received_signature == expected_signature
            
        except Exception as e:
            logger.error(f"Error verifying Cryptomus callback: {e}")
            return False