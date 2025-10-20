"""
Database Models for RUKH Platform
Author: Volodymyr Stetsenko (Zero2Auditor)
"""

from datetime import datetime
from enum import Enum
from typing import Optional, List
from sqlalchemy import Column, String, Integer, DateTime, Text, JSON, ForeignKey, Enum as SQLEnum, Boolean, Float
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import relationship
from pydantic import BaseModel, Field

Base = declarative_base()


class JobStatus(str, Enum):
    """Job execution status"""
    PENDING = "pending"
    QUEUED = "queued"
    RUNNING = "running"
    COMPLETED = "completed"
    FAILED = "failed"
    CANCELLED = "cancelled"


class VulnerabilitySeverity(str, Enum):
    """Vulnerability severity levels"""
    CRITICAL = "critical"
    HIGH = "high"
    MEDIUM = "medium"
    LOW = "low"
    INFORMATIONAL = "informational"


class AnalysisPhase(str, Enum):
    """Analysis phase types"""
    STATIC = "static"
    BYTECODE = "bytecode"
    FUZZ = "fuzz"
    SYMBOLIC = "symbolic"
    ATTACK_GRAPH = "attack_graph"
    REPORTING = "reporting"


# Database Models

class Contract(Base):
    """Smart contract model"""
    __tablename__ = "contracts"

    id = Column(String(36), primary_key=True)
    name = Column(String(255), nullable=False)
    source_code = Column(Text, nullable=False)
    compiler_version = Column(String(50))
    optimization_runs = Column(Integer)
    bytecode = Column(Text)
    abi = Column(JSON)
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    
    # Relationships
    jobs = relationship("AnalysisJob", back_populates="contract", cascade="all, delete-orphan")


class AnalysisJob(Base):
    """Analysis job model"""
    __tablename__ = "analysis_jobs"

    id = Column(String(36), primary_key=True)
    contract_id = Column(String(36), ForeignKey("contracts.id"), nullable=False)
    status = Column(SQLEnum(JobStatus), default=JobStatus.PENDING, nullable=False)
    priority = Column(Integer, default=5)
    phases = Column(JSON)  # List of phases to execute
    current_phase = Column(String(50))
    progress = Column(Float, default=0.0)
    error_message = Column(Text)
    started_at = Column(DateTime)
    completed_at = Column(DateTime)
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    
    # Relationships
    contract = relationship("Contract", back_populates="jobs")
    vulnerabilities = relationship("Vulnerability", back_populates="job", cascade="all, delete-orphan")
    reports = relationship("Report", back_populates="job", cascade="all, delete-orphan")


class Vulnerability(Base):
    """Vulnerability finding model"""
    __tablename__ = "vulnerabilities"

    id = Column(String(36), primary_key=True)
    job_id = Column(String(36), ForeignKey("analysis_jobs.id"), nullable=False)
    check_name = Column(String(255), nullable=False)
    severity = Column(SQLEnum(VulnerabilitySeverity), nullable=False)
    confidence = Column(String(50))
    title = Column(String(500), nullable=False)
    description = Column(Text, nullable=False)
    location = Column(JSON)  # File, line, column
    code_snippet = Column(Text)
    remediation = Column(Text)
    references = Column(JSON)  # List of reference URLs
    metadata = Column(JSON)  # Additional data
    source_engine = Column(String(100))  # Which engine found it
    created_at = Column(DateTime, default=datetime.utcnow)
    
    # Relationships
    job = relationship("AnalysisJob", back_populates="vulnerabilities")


class Report(Base):
    """Analysis report model"""
    __tablename__ = "reports"

    id = Column(String(36), primary_key=True)
    job_id = Column(String(36), ForeignKey("analysis_jobs.id"), nullable=False)
    format = Column(String(50), nullable=False)  # markdown, pdf, html, json
    content = Column(Text)
    file_path = Column(String(500))  # S3/MinIO path
    generated_at = Column(DateTime, default=datetime.utcnow)
    
    # Relationships
    job = relationship("AnalysisJob", back_populates="reports")


class TestCase(Base):
    """Generated test case model"""
    __tablename__ = "test_cases"

    id = Column(String(36), primary_key=True)
    job_id = Column(String(36), ForeignKey("analysis_jobs.id"), nullable=False)
    name = Column(String(255), nullable=False)
    type = Column(String(50))  # unit, fuzz, invariant, exploit
    code = Column(Text, nullable=False)
    vulnerability_id = Column(String(36), ForeignKey("vulnerabilities.id"))
    passed = Column(Boolean)
    execution_time = Column(Float)
    created_at = Column(DateTime, default=datetime.utcnow)


# Pydantic Models for API

class ContractCreate(BaseModel):
    """Contract creation request"""
    name: str = Field(..., min_length=1, max_length=255)
    source_code: str = Field(..., min_length=1)
    compiler_version: Optional[str] = None
    optimization_runs: Optional[int] = None


class ContractResponse(BaseModel):
    """Contract response"""
    id: str
    name: str
    compiler_version: Optional[str]
    created_at: datetime
    
    class Config:
        from_attributes = True


class JobCreate(BaseModel):
    """Job creation request"""
    contract_id: str
    phases: Optional[List[str]] = None
    priority: int = Field(default=5, ge=1, le=10)


class JobResponse(BaseModel):
    """Job response"""
    id: str
    contract_id: str
    status: JobStatus
    progress: float
    current_phase: Optional[str]
    created_at: datetime
    started_at: Optional[datetime]
    completed_at: Optional[datetime]
    
    class Config:
        from_attributes = True


class VulnerabilityResponse(BaseModel):
    """Vulnerability response"""
    id: str
    check_name: str
    severity: VulnerabilitySeverity
    confidence: str
    title: str
    description: str
    location: Optional[dict]
    remediation: Optional[str]
    
    class Config:
        from_attributes = True


class ReportResponse(BaseModel):
    """Report response"""
    id: str
    job_id: str
    format: str
    file_path: Optional[str]
    generated_at: datetime
    
    class Config:
        from_attributes = True


class JobDetailResponse(BaseModel):
    """Detailed job response with vulnerabilities"""
    id: str
    contract_id: str
    status: JobStatus
    progress: float
    current_phase: Optional[str]
    vulnerabilities: List[VulnerabilityResponse]
    reports: List[ReportResponse]
    created_at: datetime
    completed_at: Optional[datetime]
    
    class Config:
        from_attributes = True

