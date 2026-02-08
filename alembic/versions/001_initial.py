"""Initial migration

Revision ID: 001_initial
Revises:
Create Date: 2025-02-06

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import sqlite

# revision identifiers, used by Alembic.
revision: str = '001_initial'
down_revision: Union[str, None] = None
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    # 创建 sessions 表
    op.create_table(
        'sessions',
        sa.Column('id', sa.Integer(), autoincrement=True, nullable=False),
        sa.Column('session_id', sa.VARCHAR(36), nullable=False),
        sa.Column('project_id', sa.VARCHAR(36), nullable=True),
        sa.Column('title', sa.String(length=200), nullable=True),
        sa.Column('status', sa.Enum('active', 'archived', 'deleted', name='sessionstatus'), nullable=False),
        sa.Column('metadata', sa.JSON(), nullable=False),
        sa.Column('created_at', sa.DateTime(timezone=True), nullable=False),
        sa.Column('updated_at', sa.DateTime(timezone=True), nullable=False),
        sa.ForeignKeyConstraint(['project_id'], ['projects.project_id'], ),
        sa.PrimaryKeyConstraint('id')
    )
    op.create_index('ix_sessions_session_id', 'sessions', ['session_id'], unique=True)

    # 创建 messages 表
    op.create_table(
        'messages',
        sa.Column('id', sa.Integer(), autoincrement=True, nullable=False),
        sa.Column('session_id', sa.Integer(), nullable=False),
        sa.Column('role', sa.Enum('user', 'assistant', 'system', name='messagerole'), nullable=False),
        sa.Column('content', sa.Text(), nullable=False),
        sa.Column('metadata', sa.JSON(), nullable=False),
        sa.Column('created_at', sa.DateTime(timezone=True), nullable=False),
        sa.Column('updated_at', sa.DateTime(timezone=True), nullable=False),
        sa.ForeignKeyConstraint(['session_id'], ['sessions.id'], ),
        sa.PrimaryKeyConstraint('id')
    )
    op.create_index('ix_messages_session_created', 'messages', ['session_id', 'created_at'])
    op.create_index('ix_messages_session_id', 'messages', ['session_id'])

    # 创建 projects 表
    op.create_table(
        'projects',
        sa.Column('id', sa.Integer(), autoincrement=True, nullable=False),
        sa.Column('project_id', sa.VARCHAR(36), nullable=False),
        sa.Column('title', sa.String(length=200), nullable=False),
        sa.Column('description', sa.Text(), nullable=True),
        sa.Column('genre', sa.String(length=100), nullable=True),
        sa.Column('status', sa.Enum('draft', 'in_progress', 'completed', 'on_hold', name='projectstatus'), nullable=False),
        sa.Column('settings', sa.JSON(), nullable=False),
        sa.Column('word_count', sa.Integer(), nullable=False),
        sa.Column('chapter_count', sa.Integer(), nullable=False),
        sa.Column('created_at', sa.DateTime(timezone=True), nullable=False),
        sa.Column('updated_at', sa.DateTime(timezone=True), nullable=False),
        sa.PrimaryKeyConstraint('id')
    )
    op.create_index('ix_projects_project_id', 'projects', ['project_id'], unique=True)

    # 创建 chapters 表
    op.create_table(
        'chapters',
        sa.Column('id', sa.Integer(), autoincrement=True, nullable=False),
        sa.Column('chapter_id', sa.VARCHAR(36), nullable=False),
        sa.Column('project_id', sa.Integer(), nullable=False),
        sa.Column('title', sa.String(length=200), nullable=False),
        sa.Column('content', sa.Text(), nullable=False),
        sa.Column('order_index', sa.Integer(), nullable=False),
        sa.Column('word_count', sa.Integer(), nullable=False),
        sa.Column('summary', sa.Text(), nullable=True),
        sa.Column('notes', sa.Text(), nullable=True),
        sa.Column('created_at', sa.DateTime(timezone=True), nullable=False),
        sa.Column('updated_at', sa.DateTime(timezone=True), nullable=False),
        sa.ForeignKeyConstraint(['project_id'], ['projects.id'], ),
        sa.PrimaryKeyConstraint('id')
    )
    op.create_index('ix_chapters_chapter_id', 'chapters', ['chapter_id'], unique=True)
    op.create_index('ix_chapters_project_order', 'chapters', ['project_id', 'order_index'])
    op.create_index('ix_chapters_project_id', 'chapters', ['project_id'])

    # 创建 chapter_versions 表
    op.create_table(
        'chapter_versions',
        sa.Column('id', sa.Integer(), autoincrement=True, nullable=False),
        sa.Column('chapter_id', sa.Integer(), nullable=False),
        sa.Column('content', sa.Text(), nullable=False),
        sa.Column('change_description', sa.String(length=500), nullable=True),
        sa.Column('version_number', sa.Integer(), nullable=False),
        sa.Column('created_at', sa.DateTime(timezone=True), nullable=False),
        sa.Column('updated_at', sa.DateTime(timezone=True), nullable=False),
        sa.ForeignKeyConstraint(['chapter_id'], ['chapters.id'], ),
        sa.PrimaryKeyConstraint('id')
    )
    op.create_index('ix_chapter_versions_chapter_version', 'chapter_versions', ['chapter_id', 'version_number'])
    op.create_index('ix_chapter_versions_chapter_id', 'chapter_versions', ['chapter_id'])

    # 创建 generation_tasks 表
    op.create_table(
        'generation_tasks',
        sa.Column('id', sa.Integer(), autoincrement=True, nullable=False),
        sa.Column('task_id', sa.VARCHAR(36), nullable=False),
        sa.Column('project_id', sa.Integer(), nullable=False),
        sa.Column('status', sa.Enum('pending', 'running', 'completed', 'failed', 'cancelled', name='taskstatus'), nullable=False),
        sa.Column('mode', sa.Enum('full', 'continue', 'expand', 'rewrite', 'outline', name='generationmode'), nullable=False),
        sa.Column('chapter_id', sa.VARCHAR(36), nullable=True),
        sa.Column('prompt', sa.Text(), nullable=True),
        sa.Column('result', sa.JSON(), nullable=False),
        sa.Column('error_message', sa.Text(), nullable=True),
        sa.Column('started_at', sa.DateTime(timezone=True), nullable=True),
        sa.Column('completed_at', sa.DateTime(timezone=True), nullable=True),
        sa.Column('created_at', sa.DateTime(timezone=True), nullable=False),
        sa.Column('updated_at', sa.DateTime(timezone=True), nullable=False),
        sa.ForeignKeyConstraint(['project_id'], ['projects.id'], ),
        sa.PrimaryKeyConstraint('id')
    )
    op.create_index('ix_generation_tasks_project_id', 'generation_tasks', ['project_id'])
    op.create_index('ix_generation_tasks_task_id', 'generation_tasks', ['task_id'], unique=True)


def downgrade() -> None:
    op.drop_index('ix_generation_tasks_task_id', table_name='generation_tasks')
    op.drop_index('ix_generation_tasks_project_id', table_name='generation_tasks')
    op.drop_table('generation_tasks')

    op.drop_index('ix_chapter_versions_chapter_id', table_name='chapter_versions')
    op.drop_index('ix_chapter_versions_chapter_version', table_name='chapter_versions')
    op.drop_table('chapter_versions')

    op.drop_index('ix_chapters_project_id', table_name='chapters')
    op.drop_index('ix_chapters_project_order', table_name='chapters')
    op.drop_index('ix_chapters_chapter_id', table_name='chapters')
    op.drop_table('chapters')

    op.drop_index('ix_projects_project_id', table_name='projects')
    op.drop_table('projects')

    op.drop_index('ix_messages_session_id', table_name='messages')
    op.drop_index('ix_messages_session_created', table_name='messages')
    op.drop_table('messages')

    op.drop_index('ix_sessions_session_id', table_name='sessions')
    op.drop_table('sessions')
