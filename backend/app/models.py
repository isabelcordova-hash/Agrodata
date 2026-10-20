from sqlalchemy import String, Float, Integer, UniqueConstraint
from sqlalchemy.orm import Mapped, mapped_column
from .db import Base
class Observation(Base):
    __tablename__ = "observations"
    __table_args__ = (UniqueConstraint("kind", "year", "crop", "department"),)
    id: Mapped[int] = mapped_column(primary_key=True)
    kind: Mapped[str] = mapped_column(String(20), index=True)
    year: Mapped[int] = mapped_column(index=True)
    crop: Mapped[str] = mapped_column(String(100), index=True)
    department: Mapped[str] = mapped_column(String(100), default="", index=True)
    yield_value: Mapped[float] = mapped_column(Float)
    production: Mapped[float] = mapped_column(Float)
    records: Mapped[int] = mapped_column(Integer)
class District(Base):
    __tablename__ = "districts"
    __table_args__ = (UniqueConstraint("crop", "department", "name"),)
    id: Mapped[int] = mapped_column(primary_key=True)
    crop: Mapped[str] = mapped_column(String(100), index=True)
    department: Mapped[str] = mapped_column(String(100), index=True)
    name: Mapped[str] = mapped_column(String(100))
    yield_value: Mapped[float] = mapped_column(Float)
    score_raw: Mapped[float] = mapped_column(Float)
    score: Mapped[float] = mapped_column(Float, index=True)
    stability: Mapped[float] = mapped_column(Float)
    records: Mapped[int] = mapped_column(Integer)
class User(Base):
    __tablename__ = "users"
    id: Mapped[int] = mapped_column(primary_key=True)
    email: Mapped[str] = mapped_column(String(254), unique=True)
    name: Mapped[str] = mapped_column(String(100))
    password_hash: Mapped[str | None] = mapped_column(String(255), nullable=True)
    google_sub: Mapped[str | None] = mapped_column(String(255), unique=True, nullable=True)
