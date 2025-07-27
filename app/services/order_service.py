"""Order service for managing orders and purchases."""
import logging
import secrets
import string
from datetime import datetime, timedelta
from decimal import Decimal
from typing import List, Optional

from sqlalchemy import func, select
from sqlalchemy.ext.asyncio import AsyncSession

from app.database import get_session
from app.models.order import Order, OrderStatus
from app.models.product import Product
from app.models.user import User
from app.schemas.order import OrderCreate, OrderUpdate, OrderResponse, OrderStats
from app.services.product_service import ProductService
from app.config import settings

logger = logging.getLogger(__name__)


class OrderService:
    """Service for order management."""
    
    @staticmethod
    async def get_by_id(order_id: int) -> Optional[Order]:
        """Get order by ID."""
        async with get_session() as session:
            return await session.get(Order, order_id)
    
    @staticmethod
    async def get_by_order_number(order_number: str) -> Optional[Order]:
        """Get order by order number."""
        async with get_session() as session:
            query = select(Order).where(Order.order_number == order_number)
            result = await session.execute(query)
            return result.scalar_one_or_none()
    
    @staticmethod
    async def get_user_orders(
        user_id: int,
        status: Optional[str] = None,
        limit: Optional[int] = None,
        offset: int = 0
    ) -> List[Order]:
        """Get orders for a specific user."""
        async with get_session() as session:
            query = select(Order).where(Order.user_id == user_id)
            
            if status:
                query = query.where(Order.status == status)
            
            query = query.order_by(Order.created_at.desc())
            
            if limit:
                query = query.limit(limit)
            if offset:
                query = query.offset(offset)
            
            result = await session.execute(query)
            return list(result.scalars().all())
    
    @staticmethod
    async def get_all_orders(
        status: Optional[str] = None,
        limit: Optional[int] = None,
        offset: int = 0
    ) -> List[Order]:
        """Get all orders with optional filters."""
        async with get_session() as session:
            query = select(Order).order_by(Order.created_at.desc())
            
            if status:
                query = query.where(Order.status == status)
                
            if limit:
                query = query.limit(limit)
            if offset:
                query = query.offset(offset)
            
            result = await session.execute(query)
            return list(result.scalars().all())
    
    @staticmethod
    async def create_order(user_id: int, order_data: OrderCreate) -> Optional[Order]:
        """Create a new order."""
        async with get_session() as session:
            # Get product
            product = await session.get(Product, order_data.product_id)
            if not product or not product.is_available:
                logger.warning(f"Product {order_data.product_id} not available for order")
                return None
            
            # Check stock
            if not product.is_in_stock:
                logger.warning(f"Product {product.name} is out of stock")
                return None
            
            # Generate unique order number
            order_number = OrderService._generate_order_number()
            while await OrderService.get_by_order_number(order_number):
                order_number = OrderService._generate_order_number()
            
            # Calculate prices
            unit_price = product.price
            total_price = unit_price * order_data.quantity
            
            # Set expiration (15 minutes for pending orders)
            expires_at = datetime.now() + timedelta(minutes=15)
            
            # Create order
            order = Order(
                order_number=order_number,
                user_id=user_id,
                product_id=order_data.product_id,
                quantity=order_data.quantity,
                unit_price=unit_price,
                total_price=total_price,
                currency=product.currency,
                status=OrderStatus.PENDING.value,
                payment_gateway=order_data.payment_gateway,
                is_trial=order_data.is_trial,
                referral_code=order_data.referral_code,
                expires_at=expires_at
            )
            
            session.add(order)
            await session.commit()
            await session.refresh(order)
            
            logger.info(f"Created order: {order.order_number} for user {user_id}")
            return order
    
    @staticmethod
    async def update_order(order_id: int, order_data: OrderUpdate) -> Optional[Order]:
        """Update order information."""
        async with get_session() as session:
            order = await session.get(Order, order_id)
            if not order:
                return None
            
            update_data = order_data.model_dump(exclude_unset=True)
            for field, value in update_data.items():
                setattr(order, field, value)
            
            await session.commit()
            await session.refresh(order)
            
            logger.info(f"Updated order: {order.order_number}")
            return order
    
    @staticmethod
    async def complete_order(order_id: int, delivery_data: Optional[dict] = None) -> bool:
        """Complete an order and handle delivery."""
        async with get_session() as session:
            order = await session.get(Order, order_id)
            if not order or order.status != OrderStatus.PENDING.value:
                return False
            
            # Update product stock
            success = await ProductService.decrease_stock(order.product_id, order.quantity)
            if not success:
                logger.error(f"Failed to decrease stock for order {order.order_number}")
                return False
            
            # Mark order as completed
            order.mark_as_completed()
            if delivery_data:
                order.delivery_data = delivery_data
            
            await session.commit()
            
            logger.info(f"Completed order: {order.order_number}")
            return True
    
    @staticmethod
    async def cancel_order(order_id: int, reason: Optional[str] = None) -> bool:
        """Cancel an order."""
        async with get_session() as session:
            order = await session.get(Order, order_id)
            if not order or order.status not in [OrderStatus.PENDING.value, OrderStatus.PROCESSING.value]:
                return False
            
            order.mark_as_cancelled()
            await session.commit()
            
            logger.info(f"Cancelled order: {order.order_number} - {reason}")
            return True
    
    @staticmethod
    async def expire_pending_orders() -> int:
        """Expire old pending orders."""
        async with get_session() as session:
            now = datetime.now()
            
            # Find expired pending orders
            query = select(Order).where(
                Order.status == OrderStatus.PENDING.value,
                Order.expires_at < now
            )
            result = await session.execute(query)
            expired_orders = list(result.scalars().all())
            
            # Cancel expired orders
            cancelled_count = 0
            for order in expired_orders:
                order.mark_as_cancelled()
                cancelled_count += 1
            
            if cancelled_count > 0:
                await session.commit()
                logger.info(f"Expired {cancelled_count} pending orders")
            
            return cancelled_count
    
    @staticmethod
    async def get_order_stats() -> OrderStats:
        """Get order statistics."""
        async with get_session() as session:
            # Total orders
            total_query = select(func.count(Order.id))
            total_result = await session.execute(total_query)
            total_orders = total_result.scalar() or 0
            
            # Pending orders
            pending_query = select(func.count(Order.id)).where(
                Order.status == OrderStatus.PENDING.value
            )
            pending_result = await session.execute(pending_query)
            pending_orders = pending_result.scalar() or 0
            
            # Completed orders
            completed_query = select(func.count(Order.id)).where(
                Order.status == OrderStatus.COMPLETED.value
            )
            completed_result = await session.execute(completed_query)
            completed_orders = completed_result.scalar() or 0
            
            # Cancelled orders
            cancelled_query = select(func.count(Order.id)).where(
                Order.status == OrderStatus.CANCELLED.value
            )
            cancelled_result = await session.execute(cancelled_query)
            cancelled_orders = cancelled_result.scalar() or 0
            
            # Revenue today
            today = datetime.now().date()
            revenue_today_query = select(func.sum(Order.total_price)).where(
                Order.status == OrderStatus.COMPLETED.value,
                func.date(Order.created_at) == today
            )
            revenue_today_result = await session.execute(revenue_today_query)
            revenue_today = Decimal(str(revenue_today_result.scalar() or 0))
            
            # Total revenue
            revenue_total_query = select(func.sum(Order.total_price)).where(
                Order.status == OrderStatus.COMPLETED.value
            )
            revenue_total_result = await session.execute(revenue_total_query)
            revenue_total = Decimal(str(revenue_total_result.scalar() or 0))
            
            return OrderStats(
                total_orders=total_orders,
                pending_orders=pending_orders,
                completed_orders=completed_orders,
                cancelled_orders=cancelled_orders,
                revenue_today=revenue_today,
                revenue_total=revenue_total
            )
    
    @staticmethod
    async def generate_delivery_message(order: Order) -> Optional[str]:
        """Generate delivery message for completed order."""
        async with get_session() as session:
            # Get product with delivery config
            product = await session.get(Product, order.product_id)
            if not product or not product.delivery_config:
                return None
            
            delivery_config = product.delivery_config
            template = delivery_config.get('template', '')
            
            if not template:
                return f"✅ Your order #{order.order_number} has been completed!"
            
            # Replace variables in template
            variables = {
                'order_number': order.order_number,
                'product_name': product.name,
                'quantity': order.quantity,
                'user_id': order.user_id
            }
            
            # Add delivery data variables if available
            if order.delivery_data:
                variables.update(order.delivery_data)
            
            try:
                message = template.format(**variables)
                return message
            except KeyError as e:
                logger.error(f"Missing variable in delivery template: {e}")
                return f"✅ Your order #{order.order_number} has been completed!"
    
    @staticmethod
    async def get_user_order_stats(user_id: int) -> dict:
        """Get order statistics for a specific user."""
        async with get_session() as session:
            # Total orders for user
            total_query = select(func.count(Order.id)).where(Order.user_id == user_id)
            total_result = await session.execute(total_query)
            total_orders = total_result.scalar() or 0
            
            # Completed orders
            completed_query = select(func.count(Order.id)).where(
                Order.user_id == user_id,
                Order.status == OrderStatus.COMPLETED.value
            )
            completed_result = await session.execute(completed_query)
            completed_orders = completed_result.scalar() or 0
            
            # Pending orders
            pending_query = select(func.count(Order.id)).where(
                Order.user_id == user_id,
                Order.status == OrderStatus.PENDING.value
            )
            pending_result = await session.execute(pending_query)
            pending_orders = pending_result.scalar() or 0
            
            # Total spent (completed orders only)
            spent_query = select(func.sum(Order.total_price)).where(
                Order.user_id == user_id,
                Order.status == OrderStatus.COMPLETED.value
            )
            spent_result = await session.execute(spent_query)
            total_spent = float(spent_result.scalar() or 0)
            
            return {
                'total_orders': total_orders,
                'completed_orders': completed_orders,
                'pending_orders': pending_orders,
                'total_spent': total_spent
            }
    
    @staticmethod
    def _generate_order_number(length: int = 8) -> str:
        """Generate a random order number."""
        chars = string.ascii_uppercase + string.digits
        return ''.join(secrets.choice(chars) for _ in range(length))