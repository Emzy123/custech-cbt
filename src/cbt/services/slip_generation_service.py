"""
Slip generation service for creating PDF exam slips.
"""

from typing import List, Dict, Any, Optional
import io
from datetime import datetime

try:
    from reportlab.lib.pagesizes import A4
    from reportlab.platypus import SimpleDocTemplate, Paragraph, Spacer, Table, TableStyle
    from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
    from reportlab.lib import colors
    from reportlab.lib.units import inch
except ImportError:
    pass

from ..models.exam import Examination
from ..models.venue import Venue, ExamVenueAssignment
from ..models.student import Student
from ..core.database import get_db

class SlipGenerationService:
    """Service to generate PDF examination slips."""
    
    def __init__(self, db: Any):
        self.db = db
        
    async def generate_slips(self, examination_id: str, student_ids: Optional[List[str]] = None) -> bytes:
        """Generate PDF slips for the given exam. If student_ids is None, generate for all assigned students."""
        
        # Fetch examination
        exam = await Examination.get(examination_id)
        if not exam:
            raise ValueError("Examination not found")
            
        # Fetch assignments
        query = {"examination_id": examination_id}
        if student_ids:
            query["student_id"] = {"$in": student_ids}
            
        assignments = await ExamVenueAssignment.find(query).to_list()
        
        if not assignments:
            raise ValueError("No venue assignments found for this examination")
            
        # Group by student
        buffer = io.BytesIO()
        doc = SimpleDocTemplate(buffer, pagesize=A4, rightMargin=30, leftMargin=30, topMargin=30, bottomMargin=18)
        
        elements = []
        styles = getSampleStyleSheet()
        
        title_style = styles['Heading1']
        title_style.alignment = 1 # Center
        
        normal_style = styles['Normal']
        
        for i, assignment in enumerate(assignments):
            # Fetch student
            student = await Student.get(assignment.student_id)
            if not student:
                continue
                
            # Fetch venue
            venue = await Venue.get(assignment.venue_id)
            venue_name = venue.name if venue else "Unknown Venue"
            
            # Header
            elements.append(Paragraph("CUSTECH CBT SYSTEM", title_style))
            elements.append(Paragraph("EXAMINATION SLIP", styles['Heading2']))
            elements.append(Spacer(1, 0.25 * inch))
            
            # Student Details
            data = [
                ["Student Name:", f"{student.first_name} {student.last_name}", "Matric Number:", student.matric_number],
                ["Department:", student.department_id, "Level:", str(student.current_level)],
                ["Course:", exam.course_id, "Exam Number:", assignment.exam_number],
                ["Exam Title:", exam.title, "Date:", exam.exam_date.strftime("%Y-%m-%d") if isinstance(exam.exam_date, datetime) else str(exam.exam_date)],
                ["Start Time:", exam.start_time.strftime("%H:%M") if isinstance(exam.start_time, datetime) else str(exam.start_time), "Duration:", f"{exam.duration_minutes} minutes"],
                ["Venue:", venue_name, "Seat:", assignment.seat_label]
            ]
            
            table = Table(data, colWidths=[1.2*inch, 2.3*inch, 1.2*inch, 2.3*inch])
            table.setStyle(TableStyle([
                ('BACKGROUND', (0, 0), (-1, -1), colors.white),
                ('TEXTCOLOR', (0, 0), (-1, -1), colors.black),
                ('ALIGN', (0, 0), (-1, -1), 'LEFT'),
                ('FONTNAME', (0, 0), (-1, -1), 'Helvetica'),
                ('FONTSIZE', (0, 0), (-1, -1), 10),
                ('BOTTOMPADDING', (0, 0), (-1, -1), 6),
                ('GRID', (0, 0), (-1, -1), 1, colors.black),
                ('FONTNAME', (0, 0), (0, -1), 'Helvetica-Bold'),
                ('FONTNAME', (2, 0), (2, -1), 'Helvetica-Bold'),
            ]))
            
            elements.append(table)
            elements.append(Spacer(1, 0.5 * inch))
            
            # Instructions
            elements.append(Paragraph("Instructions:", styles['Heading3']))
            instructions = [
                "1. Arrive at the venue at least 30 minutes before the start time.",
                "2. Present this slip and your valid ID card for biometric verification.",
                "3. Mobile phones and unauthorized materials are strictly prohibited.",
                "4. Any form of examination malpractice will lead to severe disciplinary actions."
            ]
            for instr in instructions:
                elements.append(Paragraph(instr, normal_style))
                elements.append(Spacer(1, 0.1 * inch))
                
            if i < len(assignments) - 1:
                from reportlab.platypus import PageBreak
                elements.append(PageBreak())
                
        doc.build(elements)
        buffer.seek(0)
        return buffer.read()
