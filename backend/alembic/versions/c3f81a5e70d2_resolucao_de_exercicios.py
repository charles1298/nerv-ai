"""resolucao de exercicios com explicacao

Revision ID: c3f81a5e70d2
Revises: b7c4e91a2d38
Create Date: 2026-09-21 14:10:00.000000
"""

from alembic import op
import sqlalchemy as sa
from sqlalchemy import Text
from sqlalchemy.dialects import postgresql

revision = 'c3f81a5e70d2'
down_revision = 'b7c4e91a2d38'
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.create_table(
        'exercise_solutions',
        sa.Column('id', sa.Uuid(), nullable=False),
        sa.Column('student_id', sa.Uuid(), nullable=False),
        # De onde veio o exercicio: digitado pelo aluno ou fotografado
        sa.Column('origem', sa.String(length=10), nullable=False),
        sa.Column('enunciado', sa.Text(), nullable=False),
        sa.Column('imagem_key', sa.Text(), nullable=True),
        # O que o sistema entendeu — separado do enunciado porque na foto pode divergir
        sa.Column('enunciado_interpretado', sa.Text(), nullable=False),
        sa.Column('materia', sa.String(length=100), nullable=False),
        sa.Column('topico', sa.String(length=200), nullable=False),
        sa.Column('passos', postgresql.JSONB(astext_type=Text()).with_variant(sa.JSON(), 'sqlite'), nullable=False),
        sa.Column('resposta_final', sa.Text(), nullable=False),
        sa.Column('conceito', sa.Text(), nullable=False),
        sa.Column('erros_comuns', postgresql.JSONB(astext_type=Text()).with_variant(sa.JSON(), 'sqlite'), nullable=False),
        sa.Column('como_conferir', sa.Text(), nullable=False),
        sa.Column('exercicio_parecido', sa.Text(), nullable=False),
        sa.Column('confianca', sa.String(length=10), nullable=False),
        sa.Column('created_at', sa.DateTime(timezone=True), server_default=sa.text('(CURRENT_TIMESTAMP)'), nullable=False),
        sa.ForeignKeyConstraint(['student_id'], ['users.id'], ),
        sa.PrimaryKeyConstraint('id'),
    )
    # A listagem do aluno filtra por student_id e ordena por data.
    op.create_index(
        'ix_exercise_solutions_student_created',
        'exercise_solutions',
        ['student_id', 'created_at'],
    )


def downgrade() -> None:
    op.drop_index('ix_exercise_solutions_student_created', table_name='exercise_solutions')
    op.drop_table('exercise_solutions')
