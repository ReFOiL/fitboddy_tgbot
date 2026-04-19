"""add gender_id FK to user and remove system fields

Revision ID: add_system_fields_to_user
Revises: 04346ee508d5
Create Date: 2026-02-13 12:00:00.000000

"""
from alembic import op
import sqlalchemy as sa


revision = 'add_system_fields_to_user'
down_revision = '04346ee508d5'
branch_labels = None
depends_on = None


def upgrade() -> None:
    # Добавляем FK на Gender (нормализованная связь)
    op.add_column('users', sa.Column('gender_id', sa.Integer(), nullable=True))
    op.create_foreign_key(
        'fk_users_gender_id',
        'users', 'genders',
        ['gender_id'], ['id'],
        ondelete='SET NULL'
    )
    op.create_index('ix_users_gender_id', 'users', ['gender_id'])


def downgrade() -> None:
    # Удаляем FK на Gender
    op.drop_index('ix_users_gender_id', table_name='users')
    op.drop_constraint('fk_users_gender_id', 'users', type_='foreignkey')
    op.drop_column('users', 'gender_id')
