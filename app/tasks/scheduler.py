"""Background task scheduler."""
import logging
from datetime import datetime
from typing import Optional

from apscheduler.schedulers.asyncio import AsyncIOScheduler
from apscheduler.triggers.interval import IntervalTrigger
from apscheduler.triggers.cron import CronTrigger

from app.services.order_service import OrderService
from app.config import settings

logger = logging.getLogger(__name__)

# Global scheduler instance
scheduler: Optional[AsyncIOScheduler] = None


async def cleanup_expired_orders() -> None:
    """Background task to cleanup expired orders."""
    try:
        expired_count = await OrderService.expire_pending_orders()
        if expired_count > 0:
            logger.info(f"Cleaned up {expired_count} expired orders")
    except Exception as e:
        logger.error(f"Error in cleanup_expired_orders task: {e}")


async def log_system_stats() -> None:
    """Background task to log system statistics."""
    try:
        from app.services.user_service import UserService
        from app.services.product_service import ProductService
        
        user_stats = await UserService.get_user_stats()
        product_stats = await ProductService.get_product_stats()
        order_stats = await OrderService.get_order_stats()
        
        logger.info(
            f"System Stats - Users: {user_stats.total_users}, "
            f"Products: {product_stats.active_products}, "
            f"Orders Today: {order_stats.pending_orders + order_stats.completed_orders}, "
            f"Revenue Today: {order_stats.revenue_today}"
        )
    except Exception as e:
        logger.error(f"Error in log_system_stats task: {e}")


async def process_referral_rewards() -> None:
    """Background task to process pending referral rewards."""
    try:
        # This would need additional implementation
        # For now, just log that the task ran
        logger.debug("Processing referral rewards...")
        
        # TODO: Implement referral reward processing
        # 1. Find completed orders with referral codes
        # 2. Calculate rewards for referrers
        # 3. Apply rewards (days, products, etc.)
        # 4. Send notifications
        
    except Exception as e:
        logger.error(f"Error in process_referral_rewards task: {e}")


async def backup_database() -> None:
    """Background task to backup database."""
    try:
        import shutil
        from pathlib import Path
        
        # Create backup directory if it doesn't exist
        backup_dir = settings.data_dir / "backups"
        backup_dir.mkdir(exist_ok=True)
        
        # Create timestamped backup
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        db_file = settings.data_dir / "store.db"
        backup_file = backup_dir / f"store_backup_{timestamp}.db"
        
        if db_file.exists():
            shutil.copy2(db_file, backup_file)
            logger.info(f"Database backed up to: {backup_file}")
            
            # Keep only last 7 backups
            backups = sorted(backup_dir.glob("store_backup_*.db"))
            if len(backups) > 7:
                for old_backup in backups[:-7]:
                    old_backup.unlink()
                    logger.info(f"Removed old backup: {old_backup}")
        else:
            logger.warning("Database file not found for backup")
            
    except Exception as e:
        logger.error(f"Error in backup_database task: {e}")


async def start_scheduler() -> None:
    """Start the background task scheduler."""
    global scheduler
    
    if scheduler is not None:
        logger.warning("Scheduler is already running")
        return
    
    scheduler = AsyncIOScheduler()
    
    # Add jobs
    scheduler.add_job(
        cleanup_expired_orders,
        trigger=IntervalTrigger(minutes=15),
        id="cleanup_expired_orders",
        name="Cleanup Expired Orders",
        max_instances=1,
        replace_existing=True
    )
    
    scheduler.add_job(
        log_system_stats,
        trigger=CronTrigger(hour=0, minute=0),  # Daily at midnight
        id="log_system_stats",
        name="Log System Statistics",
        max_instances=1,
        replace_existing=True
    )
    
    scheduler.add_job(
        process_referral_rewards,
        trigger=IntervalTrigger(hours=1),
        id="process_referral_rewards",
        name="Process Referral Rewards",
        max_instances=1,
        replace_existing=True
    )
    
    scheduler.add_job(
        backup_database,
        trigger=CronTrigger(hour=2, minute=0),  # Daily at 2 AM
        id="backup_database",
        name="Backup Database",
        max_instances=1,
        replace_existing=True
    )
    
    # Start scheduler
    scheduler.start()
    logger.info("Background task scheduler started")
    
    # Log scheduled jobs
    for job in scheduler.get_jobs():
        logger.info(f"Scheduled job: {job.name} ({job.id}) - Next run: {job.next_run_time}")


async def stop_scheduler() -> None:
    """Stop the background task scheduler."""
    global scheduler
    
    if scheduler is None:
        logger.warning("Scheduler is not running")
        return
    
    scheduler.shutdown(wait=True)
    scheduler = None
    logger.info("Background task scheduler stopped")


def get_scheduler_status() -> dict:
    """Get scheduler status and job information."""
    global scheduler
    
    if scheduler is None:
        return {"status": "stopped", "jobs": []}
    
    jobs = []
    for job in scheduler.get_jobs():
        jobs.append({
            "id": job.id,
            "name": job.name,
            "next_run_time": job.next_run_time.isoformat() if job.next_run_time else None,
            "trigger": str(job.trigger)
        })
    
    return {
        "status": "running" if scheduler.running else "stopped",
        "jobs": jobs
    }


async def run_job_now(job_id: str) -> bool:
    """Run a specific job immediately."""
    global scheduler
    
    if scheduler is None:
        logger.error("Scheduler is not running")
        return False
    
    try:
        job = scheduler.get_job(job_id)
        if job is None:
            logger.error(f"Job not found: {job_id}")
            return False
        
        # Get the job function
        job_func = job.func
        
        # Run the job
        await job_func()
        logger.info(f"Job {job_id} executed successfully")
        return True
        
    except Exception as e:
        logger.error(f"Error running job {job_id}: {e}")
        return False