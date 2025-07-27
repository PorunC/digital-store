"""Product service for managing products and catalog."""
import json
import logging
from decimal import Decimal
from pathlib import Path
from typing import List, Optional

from sqlalchemy import func, select
from sqlalchemy.ext.asyncio import AsyncSession

from app.database import get_session
from app.models.product import Product, ProductCategory
from app.schemas.product import ProductCreate, ProductUpdate, ProductResponse, ProductStats
from app.config import settings

logger = logging.getLogger(__name__)


class ProductService:
    """Service for product management."""
    
    @staticmethod
    async def get_by_id(product_id: int) -> Optional[Product]:
        """Get product by ID."""
        async with get_session() as session:
            return await session.get(Product, product_id)
    
    @staticmethod
    async def get_by_slug(slug: str) -> Optional[Product]:
        """Get product by slug."""
        async with get_session() as session:
            query = select(Product).where(Product.slug == slug)
            result = await session.execute(query)
            return result.scalar_one_or_none()
    
    @staticmethod
    async def get_all_products(
        category: Optional[str] = None,
        is_active: Optional[bool] = None,
        is_featured: Optional[bool] = None,
        limit: Optional[int] = None,
        offset: int = 0
    ) -> List[Product]:
        """Get all products with optional filters."""
        async with get_session() as session:
            query = select(Product).order_by(Product.sort_order, Product.created_at)
            
            if category:
                query = query.where(Product.category == category)
            if is_active is not None:
                query = query.where(Product.is_active == is_active)
            if is_featured is not None:
                query = query.where(Product.is_featured == is_featured)
                
            if limit:
                query = query.limit(limit)
            if offset:
                query = query.offset(offset)
            
            result = await session.execute(query)
            return list(result.scalars().all())
    
    @staticmethod
    async def get_available_products(category: Optional[str] = None) -> List[Product]:
        """Get available products (active and in stock)."""
        async with get_session() as session:
            query = select(Product).where(Product.is_active == True)
            
            if category:
                query = query.where(Product.category == category)
            
            query = query.order_by(Product.sort_order, Product.created_at)
            result = await session.execute(query)
            products = list(result.scalars().all())
            
            # Filter by stock availability
            return [p for p in products if p.is_in_stock]
    
    @staticmethod
    async def get_featured_products() -> List[Product]:
        """Get all featured products."""
        return await ProductService.get_all_products(is_featured=True, is_active=True)
    
    @staticmethod
    async def get_categories() -> List[str]:
        """Get all product categories."""
        async with get_session() as session:
            query = select(Product.category).distinct().where(Product.is_active == True)
            result = await session.execute(query)
            return list(result.scalars().all())
    
    @staticmethod
    async def create_product(product_data: ProductCreate) -> Product:
        """Create a new product."""
        async with get_session() as session:
            product = Product(**product_data.model_dump())
            session.add(product)
            await session.commit()
            await session.refresh(product)
            
            logger.info(f"Created product: {product.name} (ID: {product.id})")
            return product
    
    @staticmethod
    async def update_product(product_id: int, product_data: ProductUpdate) -> Optional[Product]:
        """Update product information."""
        async with get_session() as session:
            product = await session.get(Product, product_id)
            if not product:
                return None
            
            update_data = product_data.model_dump(exclude_unset=True)
            for field, value in update_data.items():
                setattr(product, field, value)
            
            await session.commit()
            await session.refresh(product)
            
            logger.info(f"Updated product: {product.name}")
            return product
    
    @staticmethod
    async def delete_product(product_id: int) -> bool:
        """Delete a product (soft delete by setting inactive)."""
        async with get_session() as session:
            product = await session.get(Product, product_id)
            if not product:
                return False
            
            product.is_active = False
            await session.commit()
            
            logger.info(f"Deleted product: {product.name}")
            return True
    
    @staticmethod
    async def decrease_stock(product_id: int, quantity: int = 1) -> bool:
        """Decrease product stock."""
        async with get_session() as session:
            product = await session.get(Product, product_id)
            if not product:
                return False
            
            if product.decrease_stock(quantity):
                await session.commit()
                logger.info(f"Decreased stock for {product.name}: -{quantity}")
                return True
            
            return False
    
    @staticmethod
    async def get_product_stats() -> ProductStats:
        """Get product statistics."""
        async with get_session() as session:
            # Total products
            total_query = select(func.count(Product.id))
            total_result = await session.execute(total_query)
            total_products = total_result.scalar() or 0
            
            # Active products
            active_query = select(func.count(Product.id)).where(Product.is_active == True)
            active_result = await session.execute(active_query)
            active_products = active_result.scalar() or 0
            
            # Out of stock products
            stock_query = select(func.count(Product.id)).where(
                Product.stock_count.is_not(None),
                Product.stock_count <= 0,
                Product.is_active == True
            )
            stock_result = await session.execute(stock_query)
            out_of_stock = stock_result.scalar() or 0
            
            # Total sales
            sales_query = select(func.sum(Product.sold_count))
            sales_result = await session.execute(sales_query)
            total_sales = sales_result.scalar() or 0
            
            # Revenue calculation would need order data
            # For now, we'll calculate from product prices * sold_count
            revenue_query = select(func.sum(Product.price * Product.sold_count))
            revenue_result = await session.execute(revenue_query)
            revenue_today = Decimal(str(revenue_result.scalar() or 0))
            
            return ProductStats(
                total_products=total_products,
                active_products=active_products,
                out_of_stock=out_of_stock,
                total_sales=total_sales,
                revenue_today=revenue_today
            )
    
    @staticmethod
    async def load_products_from_json(file_path: Optional[Path] = None) -> int:
        """Load products from JSON file."""
        if not file_path:
            file_path = settings.products_file
        
        if not file_path.exists():
            logger.warning(f"Products file not found: {file_path}")
            return 0
        
        try:
            with open(file_path, 'r', encoding='utf-8') as f:
                data = json.load(f)
            
            products_data = data.get('products', [])
            loaded_count = 0
            
            for product_data in products_data:
                # Check if product already exists
                existing = await ProductService.get_by_slug(product_data.get('slug'))
                if existing:
                    continue
                
                # Create product
                product_create = ProductCreate(**product_data)
                await ProductService.create_product(product_create)
                loaded_count += 1
            
            logger.info(f"Loaded {loaded_count} products from {file_path}")
            return loaded_count
            
        except Exception as e:
            logger.error(f"Failed to load products from {file_path}: {e}")
            return 0
    
    @staticmethod
    async def export_products_to_json(file_path: Optional[Path] = None) -> bool:
        """Export products to JSON file."""
        if not file_path:
            file_path = settings.data_dir / "products_export.json"
        
        try:
            products = await ProductService.get_all_products(is_active=True)
            
            export_data = {
                "categories": [category.value for category in ProductCategory],
                "products": []
            }
            
            for product in products:
                product_data = {
                    "name": product.name,
                    "description": product.description,
                    "category": product.category,
                    "price": float(product.price),
                    "currency": product.currency,
                    "delivery_type": product.delivery_type,
                    "duration_days": product.duration_days,
                    "stock_count": product.stock_count,
                    "delivery_config": product.delivery_config,
                    "is_featured": product.is_featured,
                    "slug": product.slug,
                    "image_url": product.image_url,
                    "sort_order": product.sort_order
                }
                export_data["products"].append(product_data)
            
            with open(file_path, 'w', encoding='utf-8') as f:
                json.dump(export_data, f, indent=2, ensure_ascii=False)
            
            logger.info(f"Exported {len(products)} products to {file_path}")
            return True
            
        except Exception as e:
            logger.error(f"Failed to export products to {file_path}: {e}")
            return False