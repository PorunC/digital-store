"""Webhook handlers for payment gateways."""
import logging
from typing import Dict, Any

from fastapi import APIRouter, HTTPException, Request, status
from pydantic import BaseModel

from app.services.payment_service import PaymentService

logger = logging.getLogger(__name__)

router = APIRouter(tags=["webhooks"])


class CryptomusWebhook(BaseModel):
    """Cryptomus webhook payload model."""
    uuid: str
    order_id: str
    amount: str
    currency: str
    status: str
    sign: str
    # Add other fields as needed


@router.post("/cryptomus")
async def cryptomus_webhook(payload: CryptomusWebhook) -> Dict[str, Any]:
    """Handle Cryptomus payment webhook."""
    try:
        logger.info(f"Received Cryptomus webhook: {payload.uuid}")
        
        # Convert to dict for processing
        callback_data = payload.model_dump()
        
        # Process payment callback
        success = await PaymentService.handle_payment_callback(
            gateway="cryptomus",
            payment_id=payload.uuid,
            callback_data=callback_data
        )
        
        if success:
            logger.info(f"Cryptomus webhook processed successfully: {payload.uuid}")
            return {"status": "success"}
        else:
            logger.error(f"Failed to process Cryptomus webhook: {payload.uuid}")
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Failed to process webhook"
            )
            
    except Exception as e:
        logger.error(f"Error processing Cryptomus webhook: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Internal server error"
        )


@router.post("/telegram-stars")
async def telegram_stars_webhook(request: Request) -> Dict[str, Any]:
    """Handle Telegram Stars payment webhook."""
    try:
        payload = await request.json()
        logger.info(f"Received Telegram Stars webhook")
        
        # Extract payment information
        payment_id = payload.get("payment_id")
        if not payment_id:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Missing payment_id"
            )
        
        # Process payment callback
        success = await PaymentService.handle_payment_callback(
            gateway="telegram_stars",
            payment_id=payment_id,
            callback_data=payload
        )
        
        if success:
            logger.info(f"Telegram Stars webhook processed successfully: {payment_id}")
            return {"status": "success"}
        else:
            logger.error(f"Failed to process Telegram Stars webhook: {payment_id}")
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Failed to process webhook"
            )
            
    except Exception as e:
        logger.error(f"Error processing Telegram Stars webhook: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Internal server error"
        )


@router.get("/health")
async def health_check() -> Dict[str, str]:
    """Health check endpoint."""
    return {"status": "healthy", "service": "digital-store-webhooks"}