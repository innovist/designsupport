"""spec_document: track selected generated design

Revision ID: c61d3b8e4a9f
Revises: b4a9c6e2f105
Create Date: 2026-05-11 02:39:00.000000
"""

from alembic import op
import sqlalchemy as sa


revision = "c61d3b8e4a9f"
down_revision = "b4a9c6e2f105"
branch_labels = None
depends_on = None


def upgrade() -> None:
    with op.batch_alter_table("spec_document") as batch_op:
        batch_op.add_column(sa.Column("selected_design_id", sa.UUID(), nullable=True))
        batch_op.create_foreign_key(
            "fk_spec_document_selected_design_id_generated_design",
            "generated_design",
            ["selected_design_id"],
            ["id"],
            ondelete="SET NULL",
        )


def downgrade() -> None:
    with op.batch_alter_table("spec_document") as batch_op:
        batch_op.drop_constraint(
            "fk_spec_document_selected_design_id_generated_design",
            type_="foreignkey",
        )
        batch_op.drop_column("selected_design_id")
