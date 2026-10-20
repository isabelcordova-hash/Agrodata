"""Initial agricultural schema and user accounts."""
from alembic import op
import sqlalchemy as sa
revision = "001"
down_revision = None
branch_labels = None
depends_on = None
def upgrade():
    op.create_table("observations", sa.Column("id",sa.Integer,primary_key=True),sa.Column("kind",sa.String(20),nullable=False),sa.Column("year",sa.Integer,nullable=False),sa.Column("crop",sa.String(100),nullable=False),sa.Column("department",sa.String(100),nullable=False),sa.Column("yield_value",sa.Float,nullable=False),sa.Column("production",sa.Float,nullable=False),sa.Column("records",sa.Integer,nullable=False),sa.UniqueConstraint("kind","year","crop","department"))
    op.create_table("districts",sa.Column("id",sa.Integer,primary_key=True),sa.Column("crop",sa.String(100),nullable=False),sa.Column("department",sa.String(100),nullable=False),sa.Column("name",sa.String(100),nullable=False),sa.Column("yield_value",sa.Float,nullable=False),sa.Column("score_raw",sa.Float,nullable=False),sa.Column("score",sa.Float,nullable=False),sa.Column("stability",sa.Float,nullable=False),sa.Column("records",sa.Integer,nullable=False),sa.UniqueConstraint("crop","department","name"))
    op.create_table("users",sa.Column("id",sa.Integer,primary_key=True),sa.Column("email",sa.String(254),unique=True,nullable=False),sa.Column("name",sa.String(100),nullable=False),sa.Column("password_hash",sa.String(255)),sa.Column("google_sub",sa.String(255),unique=True))
    op.create_index("ix_observation_filter","observations",["crop","department","kind","year"])
    op.create_index("ix_district_filter","districts",["crop","department","score"])
def downgrade():
    op.drop_table("users")
    op.drop_table("districts")
    op.drop_table("observations")
