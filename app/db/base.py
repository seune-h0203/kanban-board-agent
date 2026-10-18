"""Shared SQLAlchemy registry for the unchanged Assignment 5 model."""
from sqlalchemy.orm import DeclarativeBase


class Base(DeclarativeBase):
    """Register the pre-existing six-table Kanban schema."""
