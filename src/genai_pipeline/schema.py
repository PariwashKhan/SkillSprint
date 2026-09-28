"""
Pydantic schemas for structured GenAI output
Free-form text is NEVER accepted as final output.
"""

from typing import List, Optional, Literal
from pydantic import BaseModel, Field, field_validator, model_validator


class LearningObjective(BaseModel):
    objective: str
    measurable: bool = True


class TaskItem(BaseModel):
    task_id: str = "T-UNKNOWN"
    description: str = ""
    expected_outcome: str = ""
    source_document_id: str = "UNKNOWN"
    source_section_id: str = "0.0"
    difficulty: Literal["Beginner", "Intermediate", "Advanced"] = "Beginner"
    due_stage: str = "Week 1"
    mandatory: bool = True


class ChecklistItem(BaseModel):
    item_id: str = "C-UNKNOWN"
    activity: str = ""
    mandatory: bool = True
    due_stage: str = "Day 1"
    source_document_id: str = "UNKNOWN"
    source_section_id: str = "0.0"
    responsible: Optional[str] = None


class QuizQuestion(BaseModel):
    # Accept both "question_id" and "quiz_id" from the model
    question_id: str = "Q-UNKNOWN"
    question: str = ""
    question_type: Literal["multiple_choice", "multiple_response", "true_false", "scenario"] = "multiple_choice"
    options: List[str] = []
    correct_answer: str = ""
    explanation: str = ""
    source_document_id: str = "UNKNOWN"
    source_section_id: str = "0.0"
    difficulty: Literal["Beginner", "Intermediate", "Advanced"] = "Beginner"

    @model_validator(mode="before")
    @classmethod
    def _accept_quiz_id(cls, data):
        """Accept 'quiz_id' as an alias for 'question_id'."""
        if isinstance(data, dict):
            if "quiz_id" in data and "question_id" not in data:
                data["question_id"] = data.pop("quiz_id")
            # also accept 'text' as 'question'
            if "text" in data and "question" not in data:
                data["question"] = data.pop("text")
        return data


class AssessmentRubric(BaseModel):
    criterion: str
    weight: float
    expected_performance: str
    pass_condition: str


class LearningModule(BaseModel):
    module_id: str = "M-UNKNOWN"
    module_title: str = "Untitled Module"
    purpose: str = ""
    learning_objectives: List[LearningObjective] = []
    key_concepts: List[str] = []
    required_source_documents: List[str] = []
    source_document_id: str = "UNKNOWN"
    source_section_id: str = "0.0"
    estimated_duration_minutes: int = 30
    learning_activities: List[str] = []
    tasks: List[TaskItem] = []
    checklist: List[ChecklistItem] = []
    quiz: List[QuizQuestion] = []
    assessment_rubric: List[AssessmentRubric] = []
    mandatory: bool = True
    priority: Literal["High", "Medium", "Low"] = "High"
    due_stage: str = "Week 1"
    prerequisites: List[str] = []


class OnboardingPlan(BaseModel):
    plan_id: str
    employee_id: str
    role: str
    department: str
    experience_level: str
    generated_at: str
    prompt_version: str
    model_used: str
    source_document_versions: List[str] = []
    
    stages: List[str] = ["Day 1", "Week 1", "Week 2", "First 30 Days", "First 60 Days", "First 90 Days"]
    modules: List[LearningModule]
    
    overall_mandatory_count: int = 0
    notes: Optional[str] = None

    @field_validator("modules")
    @classmethod
    def at_least_one_module(cls, v):
        if not v:
            raise ValueError("At least one learning module is required")
        return v
