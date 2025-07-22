import uuid
from sqlalchemy import Column, String, Integer, ForeignKey, TIMESTAMP
from sqlalchemy.dialects.postgresql import UUID
from pgvector.sqlalchemy import Vector
from .db import Base

# Import all models from the models package for backward compatibility
from app.models import *
