"""
RUKH Analysis Planner Service
Orchestrates analysis workflow and distributes tasks to specialized engines

Author: Volodymyr Stetsenko (Zero2Auditor)
"""

import os
import json
import asyncio
import logging
from datetime import datetime
from typing import Dict, List, Any, Optional
from enum import Enum

import nats
from nats.js.api import StreamConfig, RetentionPolicy

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

# Configuration
NATS_URL = os.getenv("NATS_URL", "nats://nats:4222")

# Subjects
SUBJECT_ANALYSIS_JOBS = "rukh.analysis.jobs"
SUBJECT_STATIC_INTEL = "rukh.static.tasks"
SUBJECT_BYTECODE_INTEL = "rukh.bytecode.tasks"
SUBJECT_FUZZ_RUNNER = "rukh.fuzz.tasks"
SUBJECT_SYMBOLIC_RUNNER = "rukh.symbolic.tasks"
SUBJECT_ATTACK_GRAPH = "rukh.attack.tasks"
SUBJECT_TEST_SYNTH = "rukh.test.tasks"
SUBJECT_REPORTER = "rukh.reporter.tasks"
SUBJECT_RESULTS = "rukh.analysis.results"
SUBJECT_PROGRESS = "rukh.analysis.progress"


class AnalysisPhase(str, Enum):
    """Analysis phases"""
    STATIC = "static"
    BYTECODE = "bytecode"
    FUZZ = "fuzz"
    SYMBOLIC = "symbolic"
    ATTACK_GRAPH = "attack_graph"
    TEST_SYNTHESIS = "test_synthesis"
    REPORTING = "reporting"


class JobStatus(str, Enum):
    """Job status"""
    PENDING = "pending"
    RUNNING = "running"
    COMPLETED = "completed"
    FAILED = "failed"


class AnalysisPlanner:
    """
    Analysis Planner Service
    
    Responsibilities:
    1. Receive analysis jobs from API Gateway
    2. Determine analysis strategy based on contract
    3. Orchestrate execution of analysis phases
    4. Collect results from engines
    5. Update job status and progress
    """
    
    def __init__(self):
        self.nc: Optional[nats.NATS] = None
        self.js = None
        self.active_jobs: Dict[str, Dict[str, Any]] = {}
        
    async def connect(self):
        """Connect to NATS"""
        try:
            self.nc = await nats.connect(NATS_URL)
            self.js = self.nc.jetstream()
            
            logger.info(f"[+] Connected to NATS at {NATS_URL}")
            
            # Setup streams
            await self._setup_streams()
            
            return True
        except Exception as e:
            logger.error(f"[!] Failed to connect to NATS: {e}")
            return False
    
    async def _setup_streams(self):
        """Setup JetStream streams"""
        try:
            # Task streams for each engine
            task_subjects = [
                SUBJECT_STATIC_INTEL,
                SUBJECT_BYTECODE_INTEL,
                SUBJECT_FUZZ_RUNNER,
                SUBJECT_SYMBOLIC_RUNNER,
                SUBJECT_ATTACK_GRAPH,
                SUBJECT_TEST_SYNTH,
                SUBJECT_REPORTER
            ]
            
            for subject in task_subjects:
                stream_name = subject.replace("rukh.", "").replace(".", "_").upper()
                try:
                    await self.js.add_stream(
                        StreamConfig(
                            name=stream_name,
                            subjects=[f"{subject}.>"],
                            retention=RetentionPolicy.WORK_QUEUE,
                            max_age=86400,  # 24 hours
                        )
                    )
                except Exception:
                    pass  # Stream might already exist
            
            logger.info("[+] NATS streams configured")
        except Exception as e:
            logger.error(f"[!] Stream setup error: {e}")
    
    async def subscribe_to_jobs(self):
        """Subscribe to incoming analysis jobs"""
        try:
            await self.js.subscribe(
                f"{SUBJECT_ANALYSIS_JOBS}.>",
                cb=self._handle_job,
                durable="analysis-planner"
            )
            
            logger.info(f"[+] Subscribed to {SUBJECT_ANALYSIS_JOBS}")
        except Exception as e:
            logger.error(f"[!] Failed to subscribe to jobs: {e}")
    
    async def _handle_job(self, msg):
        """
        Handle incoming analysis job
        
        Args:
            msg: NATS message with job data
        """
        try:
            data = json.loads(msg.data.decode())
            job_id = data.get("job_id")
            
            logger.info(f"[*] Received job {job_id}")
            
            # Store job info
            self.active_jobs[job_id] = {
                "data": data,
                "status": JobStatus.RUNNING,
                "current_phase": None,
                "phases_completed": [],
                "results": {}
            }
            
            # Acknowledge message
            await msg.ack()
            
            # Start analysis workflow
            await self._execute_analysis(job_id, data)
            
        except Exception as e:
            logger.error(f"[!] Error handling job: {e}")
            await msg.nak()
    
    async def _execute_analysis(self, job_id: str, job_data: Dict[str, Any]):
        """
        Execute analysis workflow
        
        Args:
            job_id: Job identifier
            job_data: Job configuration and contract data
        """
        try:
            phases = job_data.get("phases", [
                AnalysisPhase.STATIC,
                AnalysisPhase.BYTECODE,
                AnalysisPhase.FUZZ,
                AnalysisPhase.SYMBOLIC,
                AnalysisPhase.ATTACK_GRAPH,
                AnalysisPhase.TEST_SYNTHESIS,
                AnalysisPhase.REPORTING
            ])
            
            total_phases = len(phases)
            
            for idx, phase in enumerate(phases):
                logger.info(f"[*] Job {job_id}: Starting phase {phase}")
                
                # Update progress
                progress = (idx / total_phases) * 100
                await self._publish_progress(job_id, phase, progress)
                
                # Update job state
                self.active_jobs[job_id]["current_phase"] = phase
                
                # Execute phase
                result = await self._execute_phase(job_id, phase, job_data)
                
                # Store result
                self.active_jobs[job_id]["results"][phase] = result
                self.active_jobs[job_id]["phases_completed"].append(phase)
                
                logger.info(f"[+] Job {job_id}: Completed phase {phase}")
            
            # Mark job as completed
            self.active_jobs[job_id]["status"] = JobStatus.COMPLETED
            
            # Publish final results
            await self._publish_results(job_id)
            
            # Update progress to 100%
            await self._publish_progress(job_id, "completed", 100.0)
            
            logger.info(f"[+] Job {job_id}: Analysis completed")
            
        except Exception as e:
            logger.error(f"[!] Job {job_id} failed: {e}")
            self.active_jobs[job_id]["status"] = JobStatus.FAILED
            self.active_jobs[job_id]["error"] = str(e)
            await self._publish_progress(job_id, "failed", 0.0, error=str(e))
    
    async def _execute_phase(self, job_id: str, phase: str, job_data: Dict[str, Any]) -> Dict[str, Any]:
        """
        Execute a single analysis phase
        
        Args:
            job_id: Job identifier
            phase: Phase to execute
            job_data: Job data
            
        Returns:
            Phase results
        """
        # Map phase to subject
        phase_subjects = {
            AnalysisPhase.STATIC: SUBJECT_STATIC_INTEL,
            AnalysisPhase.BYTECODE: SUBJECT_BYTECODE_INTEL,
            AnalysisPhase.FUZZ: SUBJECT_FUZZ_RUNNER,
            AnalysisPhase.SYMBOLIC: SUBJECT_SYMBOLIC_RUNNER,
            AnalysisPhase.ATTACK_GRAPH: SUBJECT_ATTACK_GRAPH,
            AnalysisPhase.TEST_SYNTHESIS: SUBJECT_TEST_SYNTH,
            AnalysisPhase.REPORTING: SUBJECT_REPORTER
        }
        
        subject = phase_subjects.get(phase)
        
        if not subject:
            logger.warning(f"[!] Unknown phase: {phase}")
            return {"status": "skipped", "reason": "unknown phase"}
        
        # Prepare task data
        task_data = {
            "job_id": job_id,
            "phase": phase,
            "contract_id": job_data.get("contract_id"),
            "contract_name": job_data.get("contract_name"),
            "source_code": job_data.get("source_code"),
            "compiler_version": job_data.get("compiler_version"),
            "previous_results": self.active_jobs[job_id]["results"],
            "timestamp": datetime.utcnow().isoformat()
        }
        
        # Publish task
        task_subject = f"{subject}.{job_id}"
        await self.js.publish(task_subject, json.dumps(task_data).encode())
        
        logger.info(f"[+] Published task for phase {phase} to {task_subject}")
        
        # For now, return success
        # In production, would wait for result from engine
        return {
            "status": "completed",
            "phase": phase,
            "timestamp": datetime.utcnow().isoformat()
        }
    
    async def _publish_progress(self, job_id: str, phase: str, progress: float, error: Optional[str] = None):
        """
        Publish progress update
        
        Args:
            job_id: Job identifier
            phase: Current phase
            progress: Progress percentage (0-100)
            error: Error message if failed
        """
        try:
            progress_data = {
                "job_id": job_id,
                "phase": phase,
                "progress": progress,
                "timestamp": datetime.utcnow().isoformat()
            }
            
            if error:
                progress_data["error"] = error
            
            subject = f"{SUBJECT_PROGRESS}.{job_id}"
            await self.nc.publish(subject, json.dumps(progress_data).encode())
            
        except Exception as e:
            logger.error(f"[!] Failed to publish progress: {e}")
    
    async def _publish_results(self, job_id: str):
        """
        Publish final analysis results
        
        Args:
            job_id: Job identifier
        """
        try:
            job_info = self.active_jobs.get(job_id)
            
            if not job_info:
                logger.error(f"[!] Job {job_id} not found")
                return
            
            results_data = {
                "job_id": job_id,
                "status": job_info["status"],
                "phases_completed": job_info["phases_completed"],
                "results": job_info["results"],
                "timestamp": datetime.utcnow().isoformat()
            }
            
            subject = f"{SUBJECT_RESULTS}.{job_id}"
            await self.js.publish(subject, json.dumps(results_data).encode())
            
            logger.info(f"[+] Published results for job {job_id}")
            
        except Exception as e:
            logger.error(f"[!] Failed to publish results: {e}")
    
    async def run(self):
        """Run the analysis planner service"""
        logger.info("[*] Starting Analysis Planner Service...")
        
        # Connect to NATS
        if not await self.connect():
            logger.error("[!] Failed to connect to NATS, exiting...")
            return
        
        # Subscribe to jobs
        await self.subscribe_to_jobs()
        
        logger.info("[+] Analysis Planner Service is running")
        
        # Keep running
        try:
            while True:
                await asyncio.sleep(1)
        except KeyboardInterrupt:
            logger.info("[*] Shutting down...")
            await self.nc.close()


async def main():
    """Main entry point"""
    planner = AnalysisPlanner()
    await planner.run()


if __name__ == "__main__":
    asyncio.run(main())

