"""initial_supabase_schema

Revision ID: 672db3d458cd
Revises: 
Create Date: 2026-11-20 22:36:17.628808

"""
import os
import sys
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa

backend_dir = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
if backend_dir not in sys.path:
    sys.path.insert(0, backend_dir)

from app.database import Base
from app.models.models import *

# revision identifiers, used by Alembic.
revision: str = '672db3d458cd'
down_revision: Union[str, None] = None
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    bind = op.get_bind()
    Base.metadata.create_all(bind=bind, checkfirst=True)


def downgrade() -> None:
    # Never drop tables or delete production data automatically
    pass
