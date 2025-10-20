"""
RUKH API Gateway
Main FastAPI application for smart contract audit platform

Author: Volodymyr Stetsenko (Zero2Auditor)
"""

import os
import uuid
import hashlib
import logging
from datetime import datetime
from typing import List, Optional
from contextlib import asynccontextmanager

from fastapi import FastAPI, HTTPException, Depends, UploadFile, File, BackgroundTasks, WebSocket, WebSocketDisconnect
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse
from sqlalchemy.orm import Session
from sqlalchemy import desc

# Local imports
from models import (
    Contract, AnalysisJob, Vulnerability, Report,
    JobStatus, VulnerabilitySeverity,
    ContractCreate, ContractResponse, JobCreate, JobResponse,
    VulnerabilityResponse, JobDetailResponse
)
from database import get_db, init_db, check_db_connection
from nats_client import get_nats_client, NATSClient
from cache import get_cache, RedisCache

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)


# Lifespan context manager for startup/shutdown
@asynccontextmanager
async def lifespan(app: FastAPI):
    """Handle startup and shutdown events"""
    # Startup
    logger.info("[*] Starting RUKH API Gateway...")
    
    # Initialize database
    init_db()
    
    # Check database connection
    if not check_db_connection():
        logger.error("[!] Database connection failed!")
    
    # Connect to NATS
    nats = await get_nats_client()
    if not nats.nc or not nats.nc.is_connected:
        logger.error("[!] NATS connection failed!")
    
    # Connect to Redis
    redis = await get_cache()
    if not redis.client:
        logger.error("[!] Redis connection failed!")
    
    logger.info("[+] RUKH API Gateway started successfully")
    
    yield
    
    # Shutdown
    logger.info("[*] Shutting down RUKH API Gateway...")
    await nats.close()
    await redis.close()
    logger.info("[+] Shutdown complete")


# Create FastAPI app
app = FastAPI(
    title="RUKH API Gateway",
    description="AI-Powered Smart Contract Audit Platform",
    version="1.0.0",
    lifespan=lifespan
)

# CORS middleware
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # Configure properly in production
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


# WebSocket connection manager
class ConnectionManager:
    """Manage WebSocket connections for real-time updates"""
    
    def __init__(self):
        self.active_connections: dict[str, WebSocket] = {}
    
    async def connect(self, job_id: str, websocket: WebSocket):
        await websocket.accept()
        self.active_connections[job_id] = websocket
        logger.info(f"[+] WebSocket connected for job {job_id}")
    
    def disconnect(self, job_id: str):
        if job_id in self.active_connections:
            del self.active_connections[job_id]
            logger.info(f"[-] WebSocket disconnected for job {job_id}")
    
    async def send_update(self, job_id: str, message: dict):
        if job_id in self.active_connections:
            try:
                await self.active_connections[job_id].send_json(message)
            except Exception as e:
                logger.error(f"[!] Failed to send WebSocket update: {e}")
                self.disconnect(job_id)


manager = ConnectionManager()


# Health check endpoint
@app.get("/health")
async def health_check():
    """Health check endpoint"""
    db_status = check_db_connection()
    
    # Check NATS
    nats = await get_nats_client()
    nats_status = nats.nc and nats.nc.is_connected
    
    # Check Redis
    redis = await get_cache()
    redis_status = redis.client is not None
    
    status = "healthy" if (db_status and nats_status and redis_status) else "unhealthy"
    
    return {
        "status": status,
        "timestamp": datetime.utcnow().isoformat(),
        "services": {
            "database": "up" if db_status else "down",
            "nats": "up" if nats_status else "down",
            "redis": "up" if redis_status else "down"
        }
    }


# Contract endpoints
@app.post("/api/v1/contracts", response_model=ContractResponse, status_code=201)
async def create_contract(
    contract: ContractCreate,
    db: Session = Depends(get_db)
):
    """
    Upload a new smart contract for analysis
    
    Args:
        contract: Contract data (name, source code, compiler version)
        
    Returns:
        Created contract information
    """
    try:
        # Create contract record
        db_contract = Contract(
            id=str(uuid.uuid4()),
            name=contract.name,
            source_code=contract.source_code,
            compiler_version=contract.compiler_version,
            optimization_runs=contract.optimization_runs
        )
        
        db.add(db_contract)
        db.commit()
        db.refresh(db_contract)
        
        logger.info(f"[+] Contract created: {db_contract.id}")
        
        return ContractResponse(
            id=db_contract.id,
            name=db_contract.name,
            compiler_version=db_contract.compiler_version,
            created_at=db_contract.created_at
        )
    
    except Exception as e:
        db.rollback()
        logger.error(f"[!] Failed to create contract: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@app.get("/api/v1/contracts/{contract_id}", response_model=ContractResponse)
async def get_contract(
    contract_id: str,
    db: Session = Depends(get_db)
):
    """Get contract by ID"""
    contract = db.query(Contract).filter(Contract.id == contract_id).first()
    
    if not contract:
        raise HTTPException(status_code=404, detail="Contract not found")
    
    return ContractResponse(
        id=contract.id,
        name=contract.name,
        compiler_version=contract.compiler_version,
        created_at=contract.created_at
    )


@app.get("/api/v1/contracts", response_model=List[ContractResponse])
async def list_contracts(
    skip: int = 0,
    limit: int = 100,
    db: Session = Depends(get_db)
):
    """List all contracts"""
    contracts = db.query(Contract).order_by(desc(Contract.created_at)).offset(skip).limit(limit).all()
    
    return [
        ContractResponse(
            id=c.id,
            name=c.name,
            compiler_version=c.compiler_version,
            created_at=c.created_at
        )
        for c in contracts
    ]


# Job endpoints
async def process_analysis_job(job_id: str, contract_id: str, phases: List[str]):
    """
    Background task to process analysis job
    
    Args:
        job_id: Job identifier
        contract_id: Contract to analyze
        phases: Analysis phases to execute
    """
    try:
        logger.info(f"[*] Processing job {job_id}")
        
        # Get NATS client
        nats = await get_nats_client()
        
        # Get contract from database
        from database import get_db_session
        with get_db_session() as db:
            contract = db.query(Contract).filter(Contract.id == contract_id).first()
            
            if not contract:
                logger.error(f"[!] Contract {contract_id} not found")
                return
            
            # Prepare job data
            job_data = {
                "job_id": job_id,
                "contract_id": contract_id,
                "contract_name": contract.name,
                "source_code": contract.source_code,
                "compiler_version": contract.compiler_version,
                "phases": phases,
                "timestamp": datetime.utcnow().isoformat()
            }
            
            # Publish to NATS
            await nats.publish_job(job_id, job_data)
            
            # Update job status
            job = db.query(AnalysisJob).filter(AnalysisJob.id == job_id).first()
            if job:
                job.status = JobStatus.QUEUED
                job.started_at = datetime.utcnow()
                db.commit()
            
            logger.info(f"[+] Job {job_id} queued for processing")
    
    except Exception as e:
        logger.error(f"[!] Failed to process job {job_id}: {e}")


@app.post("/api/v1/jobs", response_model=JobResponse, status_code=201)
async def create_job(
    job: JobCreate,
    background_tasks: BackgroundTasks,
    db: Session = Depends(get_db)
):
    """
    Create a new analysis job
    
    Args:
        job: Job configuration
        
    Returns:
        Created job information
    """
    try:
        # Verify contract exists
        contract = db.query(Contract).filter(Contract.id == job.contract_id).first()
        if not contract:
            raise HTTPException(status_code=404, detail="Contract not found")
        
        # Default phases if not specified
        phases = job.phases or ["static", "bytecode", "fuzz", "symbolic", "attack_graph", "reporting"]
        
        # Create job record
        db_job = AnalysisJob(
            id=str(uuid.uuid4()),
            contract_id=job.contract_id,
            status=JobStatus.PENDING,
            priority=job.priority,
            phases=phases,
            progress=0.0
        )
        
        db.add(db_job)
        db.commit()
        db.refresh(db_job)
        
        # Queue job for processing
        background_tasks.add_task(process_analysis_job, db_job.id, job.contract_id, phases)
        
        logger.info(f"[+] Job created: {db_job.id}")
        
        return JobResponse(
            id=db_job.id,
            contract_id=db_job.contract_id,
            status=db_job.status,
            progress=db_job.progress,
            current_phase=db_job.current_phase,
            created_at=db_job.created_at,
            started_at=db_job.started_at,
            completed_at=db_job.completed_at
        )
    
    except HTTPException:
        raise
    except Exception as e:
        db.rollback()
        logger.error(f"[!] Failed to create job: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@app.get("/api/v1/jobs/{job_id}", response_model=JobDetailResponse)
async def get_job(
    job_id: str,
    db: Session = Depends(get_db),
    redis: RedisCache = Depends(get_cache)
):
    """Get job details with vulnerabilities and reports"""
    
    # Try cache first
    cached = await redis.get_job_status(job_id)
    if cached:
        return JSONResponse(content=cached)
    
    # Query database
    job = db.query(AnalysisJob).filter(AnalysisJob.id == job_id).first()
    
    if not job:
        raise HTTPException(status_code=404, detail="Job not found")
    
    # Get vulnerabilities
    vulnerabilities = db.query(Vulnerability).filter(Vulnerability.job_id == job_id).all()
    
    # Get reports
    reports = db.query(Report).filter(Report.job_id == job_id).all()
    
    response = JobDetailResponse(
        id=job.id,
        contract_id=job.contract_id,
        status=job.status,
        progress=job.progress,
        current_phase=job.current_phase,
        vulnerabilities=[
            VulnerabilityResponse(
                id=v.id,
                check_name=v.check_name,
                severity=v.severity,
                confidence=v.confidence,
                title=v.title,
                description=v.description,
                location=v.location,
                remediation=v.remediation
            )
            for v in vulnerabilities
        ],
        reports=[
            {"id": r.id, "format": r.format, "file_path": r.file_path, "generated_at": r.generated_at}
            for r in reports
        ],
        created_at=job.created_at,
        completed_at=job.completed_at
    )
    
    # Cache result
    if job.status in [JobStatus.COMPLETED, JobStatus.FAILED]:
        await redis.set_job_status(job_id, response.dict(), ttl=3600)
    
    return response


@app.get("/api/v1/jobs", response_model=List[JobResponse])
async def list_jobs(
    skip: int = 0,
    limit: int = 100,
    status: Optional[JobStatus] = None,
    db: Session = Depends(get_db)
):
    """List all jobs with optional status filter"""
    query = db.query(AnalysisJob)
    
    if status:
        query = query.filter(AnalysisJob.status == status)
    
    jobs = query.order_by(desc(AnalysisJob.created_at)).offset(skip).limit(limit).all()
    
    return [
        JobResponse(
            id=j.id,
            contract_id=j.contract_id,
            status=j.status,
            progress=j.progress,
            current_phase=j.current_phase,
            created_at=j.created_at,
            started_at=j.started_at,
            completed_at=j.completed_at
        )
        for j in jobs
    ]


# WebSocket endpoint for real-time updates
@app.websocket("/ws/jobs/{job_id}")
async def websocket_endpoint(websocket: WebSocket, job_id: str):
    """WebSocket endpoint for real-time job updates"""
    await manager.connect(job_id, websocket)
    
    try:
        while True:
            # Keep connection alive
            data = await websocket.receive_text()
            
            # Echo back for ping/pong
            await websocket.send_json({"type": "pong", "timestamp": datetime.utcnow().isoformat()})
    
    except WebSocketDisconnect:
        manager.disconnect(job_id)


# Statistics endpoint
@app.get("/api/v1/stats")
async def get_statistics(db: Session = Depends(get_db)):
    """Get platform statistics"""
    total_contracts = db.query(Contract).count()
    total_jobs = db.query(AnalysisJob).count()
    completed_jobs = db.query(AnalysisJob).filter(AnalysisJob.status == JobStatus.COMPLETED).count()
    total_vulnerabilities = db.query(Vulnerability).count()
    
    # Vulnerabilities by severity
    critical = db.query(Vulnerability).filter(Vulnerability.severity == VulnerabilitySeverity.CRITICAL).count()
    high = db.query(Vulnerability).filter(Vulnerability.severity == VulnerabilitySeverity.HIGH).count()
    medium = db.query(Vulnerability).filter(Vulnerability.severity == VulnerabilitySeverity.MEDIUM).count()
    low = db.query(Vulnerability).filter(Vulnerability.severity == VulnerabilitySeverity.LOW).count()
    
    return {
        "total_contracts": total_contracts,
        "total_jobs": total_jobs,
        "completed_jobs": completed_jobs,
        "total_vulnerabilities": total_vulnerabilities,
        "vulnerabilities_by_severity": {
            "critical": critical,
            "high": high,
            "medium": medium,
            "low": low
        }
    }


if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8000)

