"""
Venue allocation service to assign students to seats for examinations.
"""

from typing import List, Dict, Any, Optional
from datetime import datetime
import random

from ..models.exam import Examination
from ..models.venue import Venue, ExamVenueAssignment
from ..models.student import Student, StudentCourse
from ..core.database import get_db

class VenueAllocationService:
    """Service to allocate venues and seats for an examination."""
    
    def __init__(self, db: Any):
        self.db = db
        
    async def allocate_venues(self, examination_id: str, venue_ids: List[str], current_user_id: str) -> Dict[str, Any]:
        """Allocate students registered for the course to the provided venues."""
        # Get Examination
        exam = await Examination.get(examination_id)
        if not exam:
            raise ValueError("Examination not found")
            
        # Get active venues
        venues = []
        for v_id in venue_ids:
            venue = await Venue.get(v_id)
            if venue and venue.is_active:
                venues.append(venue)
                
        if not venues:
            raise ValueError("No active venues found from the provided list")
            
        # Get all registered students for this course and session
        student_courses = await StudentCourse.find(
            {"course_id": exam.course_id, "academic_session_id": exam.academic_session_id, "status": "REGISTERED"}
        ).to_list()
        
        student_ids = [sc.student_id for sc in student_courses]
        
        if not student_ids:
            raise ValueError("No registered students found for this examination")
            
        total_capacity = sum([v.capacity for v in venues])
        if total_capacity < len(student_ids):
            raise ValueError(f"Insufficient venue capacity. Need {len(student_ids)}, but venues only hold {total_capacity}")
            
        # Randomize students
        random.shuffle(student_ids)
        
        # Clear previous assignments for this exam
        await ExamVenueAssignment.find({"examination_id": examination_id}).delete()
        
        assignments = []
        student_idx = 0
        
        for venue in venues:
            rows = venue.rows or (venue.capacity // 10) or 1
            cols = venue.columns or 10
            
            for row in range(1, rows + 1):
                for col in range(1, cols + 1):
                    if student_idx >= len(student_ids):
                        break
                        
                    # Calculate Seat Label (e.g., A1, B2)
                    row_char = chr(64 + row) if row <= 26 else f"R{row}"
                    seat_label = f"{row_char}{col}"
                    
                    student_id = student_ids[student_idx]
                    
                    # Generate a unique exam number
                    exam_number = f"{exam.course_id.split('-')[0].upper()}-{random.randint(10000, 99999)}"
                    
                    assignment = ExamVenueAssignment(
                        examination_id=examination_id,
                        venue_id=str(venue.id),
                        student_id=student_id,
                        seat_row=row,
                        seat_column=col,
                        seat_label=seat_label,
                        exam_number=exam_number,
                        assigned_by=current_user_id
                    )
                    assignments.append(assignment)
                    student_idx += 1
                    
                if student_idx >= len(student_ids):
                    break
            
            if student_idx >= len(student_ids):
                break
                
        # Bulk insert assignments
        if assignments:
            await ExamVenueAssignment.insert_many(assignments)
            
        return {
            "examination_id": examination_id,
            "total_students_allocated": len(assignments),
            "venues_used": len(venues),
            "assignments": [
                {
                    "student_id": a.student_id,
                    "venue_id": a.venue_id,
                    "seat_label": a.seat_label,
                    "exam_number": a.exam_number
                }
                for a in assignments
            ]
        }
