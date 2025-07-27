"""Admin API endpoints."""
import logging
from typing import List, Optional

from fastapi import APIRouter, HTTPException, Depends, status
from fastapi.security import HTTPBearer, HTTPAuthorizationCredentials

from app.config import settings
from app.schemas.user import UserResponse, UserStats
from app.schemas.product import ProductResponse, ProductStats
from app.schemas.order import OrderResponse, OrderStats
from app.services.user_service import UserService
from app.services.product_service import ProductService
from app.services.order_service import OrderService

logger = logging.getLogger(__name__)

router = APIRouter(tags=["admin"])
security = HTTPBearer()


async def verify_admin_token(credentials: HTTPAuthorizationCredentials = Depends(security)) -> bool:
    """Verify admin API token."""
    # In production, implement proper token verification
    # For now, we'll use a simple check
    if not settings.is_production:
        return True
    
    # TODO: Implement proper token verification
    if credentials.credentials != "admin-token":
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid authentication token"
        )
    return True


@router.get("/stats/users", response_model=UserStats)
async def get_user_stats(admin: bool = Depends(verify_admin_token)) -> UserStats:
    """Get user statistics."""
    try:
        return await UserService.get_user_stats()
    except Exception as e:
        logger.error(f"Error getting user stats: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to get user statistics"
        )


@router.get("/stats/products", response_model=ProductStats)
async def get_product_stats(admin: bool = Depends(verify_admin_token)) -> ProductStats:
    """Get product statistics."""
    try:
        return await ProductService.get_product_stats()
    except Exception as e:
        logger.error(f"Error getting product stats: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to get product statistics"
        )


@router.get("/stats/orders", response_model=OrderStats)
async def get_order_stats(admin: bool = Depends(verify_admin_token)) -> OrderStats:
    """Get order statistics."""
    try:
        return await OrderService.get_order_stats()
    except Exception as e:
        logger.error(f"Error getting order stats: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to get order statistics"
        )


@router.get("/users/{telegram_id}", response_model=UserResponse)
async def get_user(telegram_id: int, admin: bool = Depends(verify_admin_token)) -> UserResponse:
    """Get user by Telegram ID."""
    try:
        user = await UserService.get_by_telegram_id(telegram_id)
        if not user:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="User not found"
            )
        return UserResponse.model_validate(user)
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error getting user: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to get user"
        )


@router.post("/users/{telegram_id}/ban")
async def ban_user(telegram_id: int, admin: bool = Depends(verify_admin_token)) -> dict:
    """Ban a user."""
    try:
        user = await UserService.get_by_telegram_id(telegram_id)
        if not user:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="User not found"
            )
        
        success = await UserService.ban_user(user.id, ban=True)
        if success:
            return {"status": "success", "message": f"User {telegram_id} banned"}
        else:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Failed to ban user"
            )
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error banning user: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to ban user"
        )


@router.delete("/users/{telegram_id}/ban")
async def unban_user(telegram_id: int, admin: bool = Depends(verify_admin_token)) -> dict:
    """Unban a user."""
    try:
        user = await UserService.get_by_telegram_id(telegram_id)
        if not user:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="User not found"
            )
        
        success = await UserService.ban_user(user.id, ban=False)
        if success:
            return {"status": "success", "message": f"User {telegram_id} unbanned"}
        else:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Failed to unban user"
            )
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error unbanning user: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to unban user"
        )


@router.get("/products", response_model=List[ProductResponse])
async def get_products(
    category: Optional[str] = None,
    is_active: Optional[bool] = None,
    limit: Optional[int] = 50,
    offset: int = 0,
    admin: bool = Depends(verify_admin_token)
) -> List[ProductResponse]:
    """Get products list."""
    try:
        products = await ProductService.get_all_products(
            category=category,
            is_active=is_active,
            limit=limit,
            offset=offset
        )
        return [ProductResponse.model_validate(product) for product in products]
    except Exception as e:
        logger.error(f"Error getting products: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to get products"
        )


@router.get("/orders", response_model=List[OrderResponse])
async def get_orders(
    status: Optional[str] = None,
    limit: Optional[int] = 50,
    offset: int = 0,
    admin: bool = Depends(verify_admin_token)
) -> List[OrderResponse]:
    """Get orders list."""
    try:
        orders = await OrderService.get_all_orders(
            status=status,
            limit=limit,
            offset=offset
        )
        return [OrderResponse.model_validate(order) for order in orders]
    except Exception as e:
        logger.error(f"Error getting orders: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to get orders"
        )


@router.post("/orders/cleanup")
async def cleanup_orders(admin: bool = Depends(verify_admin_token)) -> dict:
    """Cleanup expired orders."""
    try:
        expired_count = await OrderService.expire_pending_orders()
        return {
            "status": "success",
            "expired_orders": expired_count,
            "message": f"Cleaned up {expired_count} expired orders"
        }
    except Exception as e:
        logger.error(f"Error cleaning up orders: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to cleanup orders"
        )


@router.post("/products/load")
async def load_products(admin: bool = Depends(verify_admin_token)) -> dict:
    """Load products from JSON file."""
    try:
        loaded_count = await ProductService.load_products_from_json()
        return {
            "status": "success",
            "loaded_products": loaded_count,
            "message": f"Loaded {loaded_count} products from JSON"
        }
    except Exception as e:
        logger.error(f"Error loading products: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to load products"
        )


@router.post("/products/export")
async def export_products(admin: bool = Depends(verify_admin_token)) -> dict:
    """Export products to JSON file."""
    try:
        success = await ProductService.export_products_to_json()
        if success:
            return {
                "status": "success",
                "message": "Products exported successfully"
            }
        else:
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail="Failed to export products"
            )
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error exporting products: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to export products"
        )