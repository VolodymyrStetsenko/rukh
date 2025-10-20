"""
NATS Client for Job Distribution
Author: Volodymyr Stetsenko (Zero2Auditor)
"""

import os
import json
import asyncio
from typing import Dict, Any, Optional, Callable
from nats.aio.client import Client as NATS
from nats.js.api import StreamConfig, RetentionPolicy
import logging

logger = logging.getLogger(__name__)

# NATS configuration
NATS_URL = os.getenv("NATS_URL", "nats://nats:4222")

# Subject names
SUBJECT_ANALYSIS_JOBS = "rukh.analysis.jobs"
SUBJECT_ANALYSIS_RESULTS = "rukh.analysis.results"
SUBJECT_ANALYSIS_PROGRESS = "rukh.analysis.progress"


class NATSClient:
    """NATS client for pub/sub messaging"""
    
    def __init__(self):
        self.nc: Optional[NATS] = None
        self.js = None
        
    async def connect(self):
        """Connect to NATS server"""
        try:
            self.nc = NATS()
            await self.nc.connect(NATS_URL)
            self.js = self.nc.jetstream()
            
            # Create streams if they don't exist
            await self._setup_streams()
            
            logger.info(f"[+] Connected to NATS at {NATS_URL}")
            return True
        except Exception as e:
            logger.error(f"[!] Failed to connect to NATS: {e}")
            return False
    
    async def _setup_streams(self):
        """Setup JetStream streams"""
        try:
            # Analysis jobs stream
            await self.js.add_stream(
                StreamConfig(
                    name="ANALYSIS_JOBS",
                    subjects=[f"{SUBJECT_ANALYSIS_JOBS}.>"],
                    retention=RetentionPolicy.WORK_QUEUE,
                    max_age=86400,  # 24 hours
                )
            )
            
            # Analysis results stream
            await self.js.add_stream(
                StreamConfig(
                    name="ANALYSIS_RESULTS",
                    subjects=[f"{SUBJECT_ANALYSIS_RESULTS}.>"],
                    retention=RetentionPolicy.LIMITS,
                    max_age=604800,  # 7 days
                )
            )
            
            # Progress updates stream
            await self.js.add_stream(
                StreamConfig(
                    name="ANALYSIS_PROGRESS",
                    subjects=[f"{SUBJECT_ANALYSIS_PROGRESS}.>"],
                    retention=RetentionPolicy.LIMITS,
                    max_age=86400,  # 24 hours
                )
            )
            
            logger.info("[+] NATS streams configured")
        except Exception as e:
            # Streams might already exist
            logger.debug(f"Stream setup: {e}")
    
    async def publish_job(self, job_id: str, job_data: Dict[str, Any]) -> bool:
        """
        Publish analysis job to queue
        
        Args:
            job_id: Unique job identifier
            job_data: Job configuration and contract data
            
        Returns:
            True if published successfully
        """
        try:
            subject = f"{SUBJECT_ANALYSIS_JOBS}.{job_id}"
            message = json.dumps(job_data).encode()
            
            await self.js.publish(subject, message)
            logger.info(f"[+] Published job {job_id} to NATS")
            return True
        except Exception as e:
            logger.error(f"[!] Failed to publish job {job_id}: {e}")
            return False
    
    async def subscribe_results(self, callback: Callable):
        """
        Subscribe to analysis results
        
        Args:
            callback: Async function to handle results
        """
        try:
            async def message_handler(msg):
                try:
                    data = json.loads(msg.data.decode())
                    await callback(data)
                    await msg.ack()
                except Exception as e:
                    logger.error(f"[!] Error processing result: {e}")
                    await msg.nak()
            
            await self.js.subscribe(
                f"{SUBJECT_ANALYSIS_RESULTS}.>",
                cb=message_handler,
                durable="api-gateway-results"
            )
            
            logger.info("[+] Subscribed to analysis results")
        except Exception as e:
            logger.error(f"[!] Failed to subscribe to results: {e}")
    
    async def subscribe_progress(self, callback: Callable):
        """
        Subscribe to progress updates
        
        Args:
            callback: Async function to handle progress updates
        """
        try:
            async def message_handler(msg):
                try:
                    data = json.loads(msg.data.decode())
                    await callback(data)
                    await msg.ack()
                except Exception as e:
                    logger.error(f"[!] Error processing progress: {e}")
                    await msg.nak()
            
            await self.js.subscribe(
                f"{SUBJECT_ANALYSIS_PROGRESS}.>",
                cb=message_handler,
                durable="api-gateway-progress"
            )
            
            logger.info("[+] Subscribed to progress updates")
        except Exception as e:
            logger.error(f"[!] Failed to subscribe to progress: {e}")
    
    async def publish_progress(self, job_id: str, progress_data: Dict[str, Any]) -> bool:
        """
        Publish progress update
        
        Args:
            job_id: Job identifier
            progress_data: Progress information
            
        Returns:
            True if published successfully
        """
        try:
            subject = f"{SUBJECT_ANALYSIS_PROGRESS}.{job_id}"
            message = json.dumps(progress_data).encode()
            
            await self.nc.publish(subject, message)
            return True
        except Exception as e:
            logger.error(f"[!] Failed to publish progress: {e}")
            return False
    
    async def close(self):
        """Close NATS connection"""
        if self.nc:
            await self.nc.close()
            logger.info("[+] NATS connection closed")


# Global NATS client instance
nats_client = NATSClient()


async def get_nats_client() -> NATSClient:
    """Get NATS client instance"""
    if not nats_client.nc or not nats_client.nc.is_connected:
        await nats_client.connect()
    return nats_client

