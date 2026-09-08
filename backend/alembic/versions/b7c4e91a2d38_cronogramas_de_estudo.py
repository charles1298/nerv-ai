"""cronogramas de estudo personalizados

Revision ID: b7c4e91a2d38
Revises: 21b21d8dbda6
Create Date: 2026-09-08 19:20:00.000000
"""

from alembic import op
import sqlalchemy as sa
from sqlalchemy import Text
from sqlalchemy.dialects import postgresql

revision = 'b7c4e91a2d38'
down_revision = '21b21d8dbda6'
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.create_table(
        'study_plans',
        sa.Column('id', sa.Uuid(), nullable=False),
        sa.Column('student_id', sa.Uuid(), nullable=False),
        # Restricoes informadas pelo aluno no formulario
        sa.Column('objetivo', sa.Text(), nullable=False),
        sa.Column('semanas_total', sa.Integer(), nullable=False),
        sa.Column('dias_por_semana', sa.Integer(), nullable=False),
        sa.Column('minutos_por_dia', sa.Integer(), nullable=False),
        sa.Column('materias_foco', postgresql.JSONB(astext_type=Text()).with_variant(sa.JSON(), 'sqlite'), nullable=False),
        # Plano gerado
        sa.Column('resumo', sa.Text(), nullable=False),
        sa.Column('estrategia', sa.Text(), nullable=False),
        sa.Column('semanas', postgresql.JSONB(astext_type=Text()).with_variant(sa.JSON(), 'sqlite'), nullable=False),
        sa.Column('dicas', postgresql.JSONB(astext_type=Text()).with_variant(sa.JSON(), 'sqlite'), nullable=False),
        sa.Column('created_at', sa.DateTime(timezone=True), server_default=sa.text('(CURRENT_TIMESTAMP)'), nullable=False),
        sa.ForeignKeyConstraint(['student_id'], ['users.id'], ),
        sa.PrimaryKeyConstraint('id'),
    )
    # A listagem do aluno sempre filtra por student_id e ordena por data.
    op.create_index('ix_study_plans_student_created', 'study_plans', ['student_id', 'created_at'])


def downgrade() -> None:
    op.drop_index('ix_study_plans_student_created', table_name='study_plans')
    op.drop_table('study_plans')
