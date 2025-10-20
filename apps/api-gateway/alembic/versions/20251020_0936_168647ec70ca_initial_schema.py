"""initial schema

Revision ID: 168647ec70ca
Revises: 
Create Date: 2025-10-20 09:36:25.859114+00:00

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import postgresql

# revision identifiers, used by Alembic.
revision: str = '168647ec70ca'
down_revision: Union[str, Sequence[str], None] = None
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    """Upgrade schema."""
    # Create contracts table
    op.create_table(
        'contracts',
        sa.Column('id', sa.String(36), primary_key=True),
        sa.Column('name', sa.String(255), nullable=False),
        sa.Column('source_code', sa.Text(), nullable=False),
        sa.Column('compiler_version', sa.String(50)),
        sa.Column('optimization_runs', sa.Integer()),
        sa.Column('bytecode', sa.Text()),
        sa.Column('abi', postgresql.JSON()),
        sa.Column('created_at', sa.DateTime(), server_default=sa.text('now()')),
        sa.Column('updated_at', sa.DateTime(), server_default=sa.text('now()'), onupdate=sa.text('now()'))
    )
    
    # Create analysis_jobs table
    op.create_table(
        'analysis_jobs',
        sa.Column('id', sa.String(36), primary_key=True),
        sa.Column('contract_id', sa.String(36), sa.ForeignKey('contracts.id'), nullable=False),
        sa.Column('status', sa.Enum('pending', 'queued', 'running', 'completed', 'failed', 'cancelled', name='jobstatus'), nullable=False, server_default='pending'),
        sa.Column('priority', sa.Integer(), server_default='5'),
        sa.Column('phases', postgresql.JSON()),
        sa.Column('current_phase', sa.String(50)),
        sa.Column('progress', sa.Float(), server_default='0.0'),
        sa.Column('error_message', sa.Text()),
        sa.Column('started_at', sa.DateTime()),
        sa.Column('completed_at', sa.DateTime()),
        sa.Column('created_at', sa.DateTime(), server_default=sa.text('now()')),
        sa.Column('updated_at', sa.DateTime(), server_default=sa.text('now()'), onupdate=sa.text('now()'))
    )
    
    # Create indexes for analysis_jobs
    op.create_index('idx_analysis_jobs_status', 'analysis_jobs', ['status'])
    op.create_index('idx_analysis_jobs_contract_id', 'analysis_jobs', ['contract_id'])
    
    # Create vulnerabilities table
    op.create_table(
        'vulnerabilities',
        sa.Column('id', sa.String(36), primary_key=True),
        sa.Column('job_id', sa.String(36), sa.ForeignKey('analysis_jobs.id'), nullable=False),
        sa.Column('check_name', sa.String(255), nullable=False),
        sa.Column('severity', sa.Enum('critical', 'high', 'medium', 'low', 'informational', name='vulnerabilityseverity'), nullable=False),
        sa.Column('confidence', sa.String(50)),
        sa.Column('title', sa.String(500), nullable=False),
        sa.Column('description', sa.Text(), nullable=False),
        sa.Column('location', postgresql.JSON()),
        sa.Column('code_snippet', sa.Text()),
        sa.Column('remediation', sa.Text()),
        sa.Column('references', postgresql.JSON()),
        sa.Column('extra_data', postgresql.JSON()),
        sa.Column('source_engine', sa.String(100)),
        sa.Column('created_at', sa.DateTime(), server_default=sa.text('now()'))
    )
    
    # Create indexes for vulnerabilities
    op.create_index('idx_vulnerabilities_job_id', 'vulnerabilities', ['job_id'])
    op.create_index('idx_vulnerabilities_severity', 'vulnerabilities', ['severity'])
    
    # Create reports table
    op.create_table(
        'reports',
        sa.Column('id', sa.String(36), primary_key=True),
        sa.Column('job_id', sa.String(36), sa.ForeignKey('analysis_jobs.id'), nullable=False),
        sa.Column('format', sa.String(50), nullable=False),
        sa.Column('content', sa.Text()),
        sa.Column('file_path', sa.String(500)),
        sa.Column('generated_at', sa.DateTime(), server_default=sa.text('now()'))
    )
    
    # Create test_cases table
    op.create_table(
        'test_cases',
        sa.Column('id', sa.String(36), primary_key=True),
        sa.Column('job_id', sa.String(36), sa.ForeignKey('analysis_jobs.id'), nullable=False),
        sa.Column('name', sa.String(255), nullable=False),
        sa.Column('type', sa.String(50)),
        sa.Column('code', sa.Text(), nullable=False),
        sa.Column('vulnerability_id', sa.String(36), sa.ForeignKey('vulnerabilities.id')),
        sa.Column('passed', sa.Boolean()),
        sa.Column('execution_time', sa.Float()),
        sa.Column('created_at', sa.DateTime(), server_default=sa.text('now()'))
    )


def downgrade() -> None:
    """Downgrade schema."""
    op.drop_table('test_cases')
    op.drop_table('reports')
    op.drop_index('idx_vulnerabilities_severity', 'vulnerabilities')
    op.drop_index('idx_vulnerabilities_job_id', 'vulnerabilities')
    op.drop_table('vulnerabilities')
    op.drop_index('idx_analysis_jobs_contract_id', 'analysis_jobs')
    op.drop_index('idx_analysis_jobs_status', 'analysis_jobs')
    op.drop_table('analysis_jobs')
    op.drop_table('contracts')
    
    # Drop enums
    sa.Enum(name='jobstatus').drop(op.get_bind())
    sa.Enum(name='vulnerabilityseverity').drop(op.get_bind())

