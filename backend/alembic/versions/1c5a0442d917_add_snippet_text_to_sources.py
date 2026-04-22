"""add snippet_text to sources

Revision ID: 1c5a0442d917
Revises: c3d4e5f6a1b2
Create Date: 2026-04-22 08:12:50.503886

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa
import sqlmodel


# revision identifiers, used by Alembic.
revision: str = '1c5a0442d917'
down_revision: Union[str, Sequence[str], None] = 'c3d4e5f6a1b2'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    op.add_column('sources', sa.Column('snippet_text', sa.Text(), nullable=True))
    op.create_unique_constraint('uq_sources_file_path', 'sources', ['file_path'])

def downgrade() -> None:
    op.drop_column('sources', 'snippet_text')
    op.drop_constraint('uq_sources_file_path', 'sources', type_='unique')
