"""
Venue and exam seat assignment models using Beanie (MongoDB).
"""

from typing import Optional
from datetime import datetime
from beanie import Document
from pydantic import Field

from .base import BaseDocument


class Venue(BaseDocument):
    """Physical examination venue."""
    name: str
    code: str
    capacity: int
    rows: Optional[int] = None
    columns: Optional[int] = None
    building: Optional[str] = None
    floor: Optional[str] = None
    notes: Optional[str] = None
    is_active: bool = True
    created_by: Optional[str] = None

    @property
    def display_name(self) -> str:
        return f"{self.code} – {self.name} (cap. {self.capacity})"

    class Settings:
        name = "venues"


class ExamVenueAssignment(BaseDocument):
    """Links a student to a specific seat in a venue for an exam."""
    examination_id: str
    venue_id: str
    student_id: str
    seat_row: Optional[int] = None
    seat_column: Optional[int] = None
    seat_label: Optional[str] = None   # e.g. "A3"
    exam_number: Optional[str] = None  # printed on slip
    assigned_by: Optional[str] = None

    class Settings:
        name = "exam_venue_assignments"
