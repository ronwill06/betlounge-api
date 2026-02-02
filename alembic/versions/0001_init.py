from alembic import op
import sqlalchemy as sa

revision = "0001_init"
down_revision = None
branch_labels = None
depends_on = None

def upgrade():
    op.create_table(
        "prop_offers",
        sa.Column("id", sa.Integer(), primary_key=True),
        sa.Column("sport", sa.String(length=16), nullable=False),
        sa.Column("market_group", sa.String(length=32), nullable=False),
        sa.Column("player_name", sa.String(length=64), nullable=False),
        sa.Column("book", sa.String(length=32), nullable=False),
        sa.Column("line", sa.Float(), nullable=False),
        sa.Column("game_id", sa.String(length=64), nullable=True),
        sa.Column("start_time", sa.DateTime(timezone=True), nullable=True),
        sa.Column("updated_at", sa.DateTime(timezone=True), server_default=sa.text("now()"), nullable=False),
    )
    op.create_index("ix_offer_lookup", "prop_offers", ["sport", "market_group", "player_name"])

    op.create_table(
        "prop_projections",
        sa.Column("id", sa.Integer(), primary_key=True),
        sa.Column("sport", sa.String(length=16), nullable=False),
        sa.Column("market_group", sa.String(length=32), nullable=False),
        sa.Column("player_name", sa.String(length=64), nullable=False),
        sa.Column("projection", sa.Float(), nullable=False),
        sa.Column("confidence", sa.Integer(), nullable=False),
        sa.Column("updated_at", sa.DateTime(timezone=True), server_default=sa.text("now()"), nullable=False),
    )
    op.create_index("ix_proj_lookup", "prop_projections", ["sport", "market_group", "player_name"])

def downgrade():
    op.drop_index("ix_proj_lookup", table_name="prop_projections")
    op.drop_table("prop_projections")
    op.drop_index("ix_offer_lookup", table_name="prop_offers")
    op.drop_table("prop_offers")