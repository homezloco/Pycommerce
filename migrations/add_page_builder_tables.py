
"""
Add page builder tables to the database.

This migration script adds tables for the page builder system, including pages,
sections, blocks, and templates.
"""

import uuid
from datetime import datetime
from sqlalchemy import (
    Column, String, Text, Boolean, DateTime, ForeignKey, JSON, Integer,
    Table, MetaData, create_engine
)
from sqlalchemy.dialects.postgresql import UUID

from pycommerce.core.config import settings

# Define metadata
metadata = MetaData()

# Define tables
pages = Table(
    'pages',
    metadata,
    Column('id', UUID(as_uuid=True), primary_key=True, default=uuid.uuid4),
    Column('tenant_id', UUID(as_uuid=True), ForeignKey("tenants.id", ondelete="CASCADE"), nullable=False),
    Column('title', String(255), nullable=False),
    Column('slug', String(255), nullable=False),
    Column('meta_title', String(255), nullable=True),
    Column('meta_description', Text, nullable=True),
    Column('is_published', Boolean, default=False),
    Column('layout_data', JSON, nullable=True),
    Column('created_at', DateTime, default=datetime.utcnow),
    Column('updated_at', DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
)

page_sections = Table(
    'page_sections',
    metadata,
    Column('id', UUID(as_uuid=True), primary_key=True, default=uuid.uuid4),
    Column('page_id', UUID(as_uuid=True), ForeignKey("pages.id", ondelete="CASCADE"), nullable=False),
    Column('section_type', String(50), nullable=False),
    Column('position', Integer, nullable=False, default=0),
    Column('settings', JSON, nullable=True),
    Column('created_at', DateTime, default=datetime.utcnow),
    Column('updated_at', DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
)

content_blocks = Table(
    'content_blocks',
    metadata,
    Column('id', UUID(as_uuid=True), primary_key=True, default=uuid.uuid4),
    Column('section_id', UUID(as_uuid=True), ForeignKey("page_sections.id", ondelete="CASCADE"), nullable=False),
    Column('block_type', String(50), nullable=False),
    Column('position', Integer, nullable=False, default=0),
    Column('content', JSON, nullable=True),
    Column('settings', JSON, nullable=True),
    Column('created_at', DateTime, default=datetime.utcnow),
    Column('updated_at', DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
)

page_templates = Table(
    'page_templates',
    metadata,
    Column('id', UUID(as_uuid=True), primary_key=True, default=uuid.uuid4),
    Column('name', String(255), nullable=False),
    Column('description', Text, nullable=True),
    Column('thumbnail_url', String(255), nullable=True),
    Column('is_system', Boolean, default=False),
    Column('template_data', JSON, nullable=False),
    Column('created_at', DateTime, default=datetime.utcnow),
    Column('updated_at', DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
)


from sqlalchemy import (
    Column, String, Text, Boolean, DateTime, ForeignKey, JSON, Integer,
    Table, MetaData, create_engine
)
from sqlalchemy.dialects.postgresql import UUID
from pycommerce.core.config import settings

# Define tables for page_sections and content_blocks
page_sections = Table(
    'page_sections',
    metadata,
    Column('id', UUID(as_uuid=True), primary_key=True, default=uuid.uuid4),
    Column('page_id', UUID(as_uuid=True), ForeignKey("pages.id", ondelete="CASCADE"), nullable=False),
    Column('section_type', String(50), nullable=False),
    Column('position', Integer, nullable=False, default=0),
    Column('settings', JSON, nullable=True),
    Column('created_at', DateTime, default=datetime.utcnow),
    Column('updated_at', DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
)

content_blocks = Table(
    'content_blocks',
    metadata,
    Column('id', UUID(as_uuid=True), primary_key=True, default=uuid.uuid4),
    Column('section_id', UUID(as_uuid=True), ForeignKey("page_sections.id", ondelete="CASCADE"), nullable=False),
    Column('block_type', String(50), nullable=False),
    Column('position', Integer, nullable=False, default=0),
    Column('content', JSON, nullable=True),
    Column('settings', JSON, nullable=True),
    Column('created_at', DateTime, default=datetime.utcnow),
    Column('updated_at', DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
)

def run_migration():
    """Run the migration."""
    # Create engine - get URI from settings or use environment variable
    db_uri = getattr(settings, 'SQLALCHEMY_DATABASE_URI', None)
    
    # Fallback to environment variable if attribute not found
    if not db_uri:
        import os
        db_uri = os.environ.get('DATABASE_URL', 'sqlite:///pycommerce.db')
        print(f"Using database URI from environment: {db_uri}")
    
    engine = create_engine(db_uri)
    
    # Create tables
    metadata.create_all(engine)
    
    print("Created page builder tables")


if __name__ == "__main__":
    run_migration()
