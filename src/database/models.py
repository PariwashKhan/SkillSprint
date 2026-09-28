from sqlalchemy import create_engine, Column, Integer, String, Text, Boolean, Float, DateTime, ForeignKey, JSON
from sqlalchemy.orm import declarative_base, sessionmaker
from datetime import datetime
from config.settings import settings

Base = declarative_base()
engine = create_engine(settings.DATABASE_URL, echo=False)
SessionLocal = sessionmaker(bind=engine)


class Document(Base):
    __tablename__ = "documents"
    id = Column(Integer, primary_key=True)
    document_id = Column(String(64), unique=True, index=True)
    filename = Column(String(255))
    file_type = Column(String(10))
    version = Column(String(20), default="1.0")
    full_text = Column(Text)
    chunk_count = Column(Integer, default=0)
    created_at = Column(DateTime, default=datetime.utcnow)


class Employee(Base):
    __tablename__ = "employees"
    id = Column(Integer, primary_key=True)
    employee_id = Column(String(32), unique=True)
    name = Column(String(100))
    role = Column(String(100))
    department = Column(String(100))
    experience_level = Column(String(50), default="Beginner")
    joining_date = Column(String(20))
    status = Column(String(30), default="Active")


class OnboardingPlanRecord(Base):
    __tablename__ = "onboarding_plans"
    id = Column(Integer, primary_key=True)
    plan_id = Column(String(64), unique=True)
    employee_id = Column(String(32))
    role = Column(String(100))
    plan_json = Column(JSON)
    coverage_score = Column(Float, default=0)
    traceability_score = Column(Float, default=0)
    validation_status = Column(String(50))
    created_at = Column(DateTime, default=datetime.utcnow)
    prompt_version = Column(String(20))
    model_used = Column(String(50))


class AuditLog(Base):
    __tablename__ = "audit_logs"
    id = Column(Integer, primary_key=True)
    action = Column(String(100))
    entity_type = Column(String(50))
    entity_id = Column(String(64))
    old_value = Column(Text, nullable=True)
    new_value = Column(Text, nullable=True)
    user = Column(String(50))
    timestamp = Column(DateTime, default=datetime.utcnow)


def init_db():
    Base.metadata.create_all(bind=engine)