"""Add Scene, FXPlan, Asset, and Render models

Revision ID: 0001
Revises: 
Create Date: 2024-01-01 00:00:00.000000

"""
from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import postgresql

# revision identifiers, used by Alembic.
revision = '0001'
down_revision = None
branch_labels = None
depends_on = None


def upgrade() -> None:
    # Create scenes table
    op.create_table('scenes',
        sa.Column('id', sa.Integer(), nullable=False),
        sa.Column('name', sa.String(length=255), nullable=False),
        sa.Column('description', sa.Text(), nullable=True),
        sa.Column('scene_number', sa.Integer(), nullable=True),
        sa.Column('duration', sa.Float(), nullable=True),
        sa.Column('location', sa.String(length=255), nullable=True),
        sa.Column('time_of_day', sa.String(length=50), nullable=True),
        sa.Column('mood', sa.String(length=100), nullable=True),
        sa.Column('timeline_json', sa.JSON(), nullable=True),
        sa.Column('created_at', sa.DateTime(timezone=True), server_default=sa.text('now()'), nullable=True),
        sa.Column('updated_at', sa.DateTime(timezone=True), nullable=True),
        sa.Column('project_id', sa.Integer(), nullable=False),
        sa.ForeignKeyConstraint(['project_id'], ['projects.id'], ),
        sa.PrimaryKeyConstraint('id')
    )
    op.create_index(op.f('ix_scenes_id'), 'scenes', ['id'], unique=False)
    op.create_index(op.f('ix_scenes_name'), 'scenes', ['name'], unique=False)
    op.create_index(op.f('ix_scenes_project_id'), 'scenes', ['project_id'], unique=False)

    # Create fx_plans table
    op.create_table('fx_plans',
        sa.Column('id', sa.Integer(), nullable=False),
        sa.Column('name', sa.String(length=255), nullable=False),
        sa.Column('description', sa.Text(), nullable=True),
        sa.Column('status', sa.String(length=20), nullable=True),
        sa.Column('effects_config', sa.JSON(), nullable=True),
        sa.Column('priority', sa.Integer(), nullable=True),
        sa.Column('estimated_duration', sa.Float(), nullable=True),
        sa.Column('progress', sa.Float(), nullable=True),
        sa.Column('current_step', sa.String(length=100), nullable=True),
        sa.Column('error_message', sa.Text(), nullable=True),
        sa.Column('created_at', sa.DateTime(timezone=True), server_default=sa.text('now()'), nullable=True),
        sa.Column('started_at', sa.DateTime(timezone=True), nullable=True),
        sa.Column('completed_at', sa.DateTime(timezone=True), nullable=True),
        sa.Column('scene_id', sa.Integer(), nullable=False),
        sa.Column('project_id', sa.Integer(), nullable=False),
        sa.ForeignKeyConstraint(['project_id'], ['projects.id'], ),
        sa.ForeignKeyConstraint(['scene_id'], ['scenes.id'], ),
        sa.PrimaryKeyConstraint('id')
    )
    op.create_index(op.f('ix_fx_plans_id'), 'fx_plans', ['id'], unique=False)
    op.create_index(op.f('ix_fx_plans_name'), 'fx_plans', ['name'], unique=False)
    op.create_index(op.f('ix_fx_plans_scene_id'), 'fx_plans', ['scene_id'], unique=False)
    op.create_index(op.f('ix_fx_plans_project_id'), 'fx_plans', ['project_id'], unique=False)
    op.create_index(op.f('ix_fx_plans_status'), 'fx_plans', ['status'], unique=False)

    # Create assets table
    op.create_table('assets',
        sa.Column('id', sa.Integer(), nullable=False),
        sa.Column('name', sa.String(length=255), nullable=False),
        sa.Column('description', sa.Text(), nullable=True),
        sa.Column('asset_type', sa.String(length=50), nullable=False),
        sa.Column('file_path', sa.String(length=500), nullable=False),
        sa.Column('original_filename', sa.String(length=255), nullable=False),
        sa.Column('file_size', sa.Integer(), nullable=False),
        sa.Column('duration', sa.Float(), nullable=True),
        sa.Column('format', sa.String(length=10), nullable=False),
        sa.Column('sample_rate', sa.Integer(), nullable=True),
        sa.Column('channels', sa.Integer(), nullable=True),
        sa.Column('bit_rate', sa.Integer(), nullable=True),
        sa.Column('volume', sa.Float(), nullable=True),
        sa.Column('pan', sa.Float(), nullable=True),
        sa.Column('loop', sa.Boolean(), nullable=True),
        sa.Column('fade_in', sa.Float(), nullable=True),
        sa.Column('fade_out', sa.Float(), nullable=True),
        sa.Column('start_time', sa.Float(), nullable=True),
        sa.Column('end_time', sa.Float(), nullable=True),
        sa.Column('metadata', sa.JSON(), nullable=True),
        sa.Column('created_at', sa.DateTime(timezone=True), server_default=sa.text('now()'), nullable=True),
        sa.Column('updated_at', sa.DateTime(timezone=True), nullable=True),
        sa.Column('scene_id', sa.Integer(), nullable=False),
        sa.Column('project_id', sa.Integer(), nullable=False),
        sa.ForeignKeyConstraint(['project_id'], ['projects.id'], ),
        sa.ForeignKeyConstraint(['scene_id'], ['scenes.id'], ),
        sa.PrimaryKeyConstraint('id')
    )
    op.create_index(op.f('ix_assets_id'), 'assets', ['id'], unique=False)
    op.create_index(op.f('ix_assets_name'), 'assets', ['name'], unique=False)
    op.create_index(op.f('ix_assets_scene_id'), 'assets', ['scene_id'], unique=False)
    op.create_index(op.f('ix_assets_project_id'), 'assets', ['project_id'], unique=False)

    # Create renders table
    op.create_table('renders',
        sa.Column('id', sa.Integer(), nullable=False),
        sa.Column('name', sa.String(length=255), nullable=False),
        sa.Column('description', sa.Text(), nullable=True),
        sa.Column('render_type', sa.String(length=50), nullable=False),
        sa.Column('output_format', sa.String(length=10), nullable=True),
        sa.Column('sample_rate', sa.Integer(), nullable=True),
        sa.Column('bit_depth', sa.Integer(), nullable=True),
        sa.Column('channels', sa.Integer(), nullable=True),
        sa.Column('status', sa.String(length=20), nullable=True),
        sa.Column('output_path', sa.String(length=500), nullable=True),
        sa.Column('file_size', sa.Integer(), nullable=True),
        sa.Column('duration', sa.Float(), nullable=True),
        sa.Column('progress', sa.Float(), nullable=True),
        sa.Column('current_step', sa.String(length=100), nullable=True),
        sa.Column('error_message', sa.Text(), nullable=True),
        sa.Column('render_settings', sa.JSON(), nullable=True),
        sa.Column('created_at', sa.DateTime(timezone=True), server_default=sa.text('now()'), nullable=True),
        sa.Column('started_at', sa.DateTime(timezone=True), nullable=True),
        sa.Column('completed_at', sa.DateTime(timezone=True), nullable=True),
        sa.Column('scene_id', sa.Integer(), nullable=False),
        sa.Column('fx_plan_id', sa.Integer(), nullable=True),
        sa.Column('project_id', sa.Integer(), nullable=False),
        sa.ForeignKeyConstraint(['fx_plan_id'], ['fx_plans.id'], ),
        sa.ForeignKeyConstraint(['project_id'], ['projects.id'], ),
        sa.ForeignKeyConstraint(['scene_id'], ['scenes.id'], ),
        sa.PrimaryKeyConstraint('id')
    )
    op.create_index(op.f('ix_renders_id'), 'renders', ['id'], unique=False)
    op.create_index(op.f('ix_renders_name'), 'renders', ['name'], unique=False)
    op.create_index(op.f('ix_renders_scene_id'), 'renders', ['scene_id'], unique=False)
    op.create_index(op.f('ix_renders_fx_plan_id'), 'renders', ['fx_plan_id'], unique=False)
    op.create_index(op.f('ix_renders_project_id'), 'renders', ['project_id'], unique=False)
    op.create_index(op.f('ix_renders_status'), 'renders', ['status'], unique=False)


def downgrade() -> None:
    # Drop renders table
    op.drop_index(op.f('ix_renders_status'), table_name='renders')
    op.drop_index(op.f('ix_renders_project_id'), table_name='renders')
    op.drop_index(op.f('ix_renders_fx_plan_id'), table_name='renders')
    op.drop_index(op.f('ix_renders_scene_id'), table_name='renders')
    op.drop_index(op.f('ix_renders_name'), table_name='renders')
    op.drop_index(op.f('ix_renders_id'), table_name='renders')
    op.drop_table('renders')

    # Drop assets table
    op.drop_index(op.f('ix_assets_project_id'), table_name='assets')
    op.drop_index(op.f('ix_assets_scene_id'), table_name='assets')
    op.drop_index(op.f('ix_assets_name'), table_name='assets')
    op.drop_index(op.f('ix_assets_id'), table_name='assets')
    op.drop_table('assets')

    # Drop fx_plans table
    op.drop_index(op.f('ix_fx_plans_status'), table_name='fx_plans')
    op.drop_index(op.f('ix_fx_plans_project_id'), table_name='fx_plans')
    op.drop_index(op.f('ix_fx_plans_scene_id'), table_name='fx_plans')
    op.drop_index(op.f('ix_fx_plans_name'), table_name='fx_plans')
    op.drop_index(op.f('ix_fx_plans_id'), table_name='fx_plans')
    op.drop_table('fx_plans')

    # Drop scenes table
    op.drop_index(op.f('ix_scenes_project_id'), table_name='scenes')
    op.drop_index(op.f('ix_scenes_name'), table_name='scenes')
    op.drop_index(op.f('ix_scenes_id'), table_name='scenes')
    op.drop_table('scenes')
