"""
Academics administration API — CRUD for sessions, semesters,
departments, courses and course-department links.
"""

from typing import Any, List, Optional
from datetime import datetime

from fastapi import APIRouter, Depends, HTTPException, Query, status
from pydantic import BaseModel, Field

from ..models.academic import (
    AcademicSession, Semester, Department, Course,
    CourseDepartment, SemesterType, CourseLevel,
)
from ..core.database import get_db
from .deps import get_current_active_user, require_permission

router = APIRouter(prefix="/academics", tags=["academics"])


# ──────────────────────────── Schemas (inline, small) ────────────────────────

class SessionCreate(BaseModel):
    session_code: str = Field(..., json_schema_extra={"example": "2025/2026"})
    start_date: datetime
    end_date: datetime
    is_current: bool = False

class SessionUpdate(BaseModel):
    session_code: Optional[str] = None
    start_date: Optional[datetime] = None
    end_date: Optional[datetime] = None
    is_current: Optional[bool] = None

class SemesterCreate(BaseModel):
    academic_session_id: str
    semester_type: SemesterType
    start_date: datetime
    end_date: datetime
    is_current: bool = False

class SemesterUpdate(BaseModel):
    start_date: Optional[datetime] = None
    end_date: Optional[datetime] = None
    is_current: Optional[bool] = None

class DepartmentCreate(BaseModel):
    code: str = Field(..., json_schema_extra={"example": "CSC"})
    name: str = Field(..., json_schema_extra={"example": "Computer Science"})
    faculty_code: Optional[str] = None

class DepartmentUpdate(BaseModel):
    name: Optional[str] = None
    faculty_code: Optional[str] = None

class CourseCreate(BaseModel):
    code: str = Field(..., json_schema_extra={"example": "GST101"})
    title: str = Field(..., json_schema_extra={"example": "Communication in English"})
    description: Optional[str] = None
    credit_units: int = Field(..., ge=1, le=6)
    level: CourseLevel
    semester_type: SemesterType

class CourseUpdate(BaseModel):
    title: Optional[str] = None
    description: Optional[str] = None
    credit_units: Optional[int] = None

class CourseDepartmentLink(BaseModel):
    course_id: str
    department_id: str
    is_mandatory: bool = False


# ──────────────────────────── Academic Sessions ───────────────────────────────

@router.get("/sessions", dependencies=[Depends(require_permission("academic.read"))])
async def list_sessions(
    current_user=Depends(get_current_active_user),
    db: Any = Depends(get_db),
) -> List[dict]:
    sessions = await AcademicSession.find_all().sort("-created_at").to_list()
    return [_doc(s) for s in sessions]


@router.post("/sessions", status_code=status.HTTP_201_CREATED,
             dependencies=[Depends(require_permission("academic.create"))])
async def create_session(
    data: SessionCreate,
    current_user=Depends(get_current_active_user),
    db: Any = Depends(get_db),
) -> dict:
    if data.is_current:
        # unset any existing current
        await AcademicSession.find({"is_current": True}).update({"$set": {"is_current": False}})
    obj = AcademicSession(**data.model_dump())
    await obj.insert()
    return _doc(obj)


@router.patch("/sessions/{session_id}",
              dependencies=[Depends(require_permission("academic.update"))])
async def update_session(
    session_id: str,
    data: SessionUpdate,
    current_user=Depends(get_current_active_user),
    db: Any = Depends(get_db),
) -> dict:
    obj = await AcademicSession.get(session_id)
    if not obj:
        raise HTTPException(status_code=404, detail="Session not found")
    updates = data.model_dump(exclude_unset=True)
    if updates.get("is_current"):
        await AcademicSession.find({"is_current": True}).update({"$set": {"is_current": False}})
    if updates:
        await obj.set(updates)
    return _doc(obj)


@router.delete("/sessions/{session_id}", status_code=status.HTTP_204_NO_CONTENT,
               dependencies=[Depends(require_permission("academic.delete"))])
async def delete_session(
    session_id: str,
    current_user=Depends(get_current_active_user),
    db: Any = Depends(get_db),
):
    obj = await AcademicSession.get(session_id)
    if not obj:
        raise HTTPException(status_code=404, detail="Session not found")
    await obj.delete()


# ──────────────────────────── Semesters ──────────────────────────────────────

@router.get("/semesters", dependencies=[Depends(require_permission("academic.read"))])
async def list_semesters(
    session_id: Optional[str] = Query(None),
    current_user=Depends(get_current_active_user),
    db: Any = Depends(get_db),
) -> List[dict]:
    f = {"academic_session_id": session_id} if session_id else {}
    sems = await Semester.find(f).sort("-created_at").to_list()
    return [_doc(s) for s in sems]


@router.post("/semesters", status_code=status.HTTP_201_CREATED,
             dependencies=[Depends(require_permission("academic.create"))])
async def create_semester(
    data: SemesterCreate,
    current_user=Depends(get_current_active_user),
    db: Any = Depends(get_db),
) -> dict:
    obj = Semester(**data.model_dump())
    await obj.insert()
    return _doc(obj)


@router.patch("/semesters/{semester_id}",
              dependencies=[Depends(require_permission("academic.update"))])
async def update_semester(
    semester_id: str,
    data: SemesterUpdate,
    current_user=Depends(get_current_active_user),
    db: Any = Depends(get_db),
) -> dict:
    obj = await Semester.get(semester_id)
    if not obj:
        raise HTTPException(status_code=404, detail="Semester not found")
    updates = data.model_dump(exclude_unset=True)
    if updates:
        await obj.set(updates)
    return _doc(obj)


@router.delete("/semesters/{semester_id}", status_code=status.HTTP_204_NO_CONTENT,
               dependencies=[Depends(require_permission("academic.delete"))])
async def delete_semester(
    semester_id: str,
    current_user=Depends(get_current_active_user),
    db: Any = Depends(get_db),
):
    obj = await Semester.get(semester_id)
    if not obj:
        raise HTTPException(status_code=404, detail="Semester not found")
    await obj.delete()


# ──────────────────────────── Departments ────────────────────────────────────

@router.get("/departments", dependencies=[Depends(require_permission("academic.read"))])
async def list_departments(
    current_user=Depends(get_current_active_user),
    db: Any = Depends(get_db),
) -> List[dict]:
    depts = await Department.find_all().sort("code").to_list()
    return [_doc(d) for d in depts]


@router.post("/departments", status_code=status.HTTP_201_CREATED,
             dependencies=[Depends(require_permission("academic.create"))])
async def create_department(
    data: DepartmentCreate,
    current_user=Depends(get_current_active_user),
    db: Any = Depends(get_db),
) -> dict:
    existing = await Department.find_one({"code": data.code})
    if existing:
        raise HTTPException(status_code=409, detail=f"Department '{data.code}' already exists")
    obj = Department(**data.model_dump(), created_by=str(current_user.id))
    await obj.insert()
    return _doc(obj)


@router.patch("/departments/{department_id}",
              dependencies=[Depends(require_permission("academic.update"))])
async def update_department(
    department_id: str,
    data: DepartmentUpdate,
    current_user=Depends(get_current_active_user),
    db: Any = Depends(get_db),
) -> dict:
    obj = await Department.get(department_id)
    if not obj:
        raise HTTPException(status_code=404, detail="Department not found")
    updates = data.model_dump(exclude_unset=True)
    if updates:
        await obj.set(updates)
    return _doc(obj)


@router.delete("/departments/{department_id}", status_code=status.HTTP_204_NO_CONTENT,
               dependencies=[Depends(require_permission("academic.delete"))])
async def delete_department(
    department_id: str,
    current_user=Depends(get_current_active_user),
    db: Any = Depends(get_db),
):
    obj = await Department.get(department_id)
    if not obj:
        raise HTTPException(status_code=404, detail="Department not found")
    await obj.delete()


# ──────────────────────────── Courses ────────────────────────────────────────

@router.get("/courses", dependencies=[Depends(require_permission("course.read"))])
async def list_courses(
    department_id: Optional[str] = Query(None),
    level: Optional[int] = Query(None),
    current_user=Depends(get_current_active_user),
    db: Any = Depends(get_db),
) -> List[dict]:
    if department_id:
        links = await CourseDepartment.find({"department_id": department_id}).to_list()
        course_ids = [lk.course_id for lk in links]
        f: dict = {"_id": {"$in": course_ids}}
    else:
        f = {}
    if level:
        f["level"] = level
    courses = await Course.find(f).sort("code").to_list()
    return [_doc(c) for c in courses]


@router.post("/courses", status_code=status.HTTP_201_CREATED,
             dependencies=[Depends(require_permission("course.create"))])
async def create_course(
    data: CourseCreate,
    current_user=Depends(get_current_active_user),
    db: Any = Depends(get_db),
) -> dict:
    existing = await Course.find_one({"code": data.code})
    if existing:
        raise HTTPException(status_code=409, detail=f"Course '{data.code}' already exists")
    obj = Course(**data.model_dump(), created_by=str(current_user.id))
    await obj.insert()
    return _doc(obj)


@router.patch("/courses/{course_id}",
              dependencies=[Depends(require_permission("course.update"))])
async def update_course(
    course_id: str,
    data: CourseUpdate,
    current_user=Depends(get_current_active_user),
    db: Any = Depends(get_db),
) -> dict:
    obj = await Course.get(course_id)
    if not obj:
        raise HTTPException(status_code=404, detail="Course not found")
    updates = data.model_dump(exclude_unset=True)
    if updates:
        await obj.set(updates)
    return _doc(obj)


@router.delete("/courses/{course_id}", status_code=status.HTTP_204_NO_CONTENT,
               dependencies=[Depends(require_permission("course.delete"))])
async def delete_course(
    course_id: str,
    current_user=Depends(get_current_active_user),
    db: Any = Depends(get_db),
):
    obj = await Course.get(course_id)
    if not obj:
        raise HTTPException(status_code=404, detail="Course not found")
    await obj.delete()


# ──────────────────────────── Course ↔ Department links ───────────────────────

@router.post("/courses/{course_id}/departments", status_code=status.HTTP_201_CREATED,
             dependencies=[Depends(require_permission("course.update"))])
async def link_course_department(
    course_id: str,
    data: CourseDepartmentLink,
    current_user=Depends(get_current_active_user),
    db: Any = Depends(get_db),
) -> dict:
    existing = await CourseDepartment.find_one({"course_id": course_id, "department_id": data.department_id})
    if existing:
        raise HTTPException(status_code=409, detail="Link already exists")
    obj = CourseDepartment(course_id=course_id, department_id=data.department_id, is_mandatory=data.is_mandatory)
    await obj.insert()
    return _doc(obj)


@router.delete("/courses/{course_id}/departments/{department_id}",
               status_code=status.HTTP_204_NO_CONTENT,
               dependencies=[Depends(require_permission("course.update"))])
async def unlink_course_department(
    course_id: str,
    department_id: str,
    current_user=Depends(get_current_active_user),
    db: Any = Depends(get_db),
):
    obj = await CourseDepartment.find_one({"course_id": course_id, "department_id": department_id})
    if not obj:
        raise HTTPException(status_code=404, detail="Link not found")
    await obj.delete()


# ──────────────────────────── Helper ─────────────────────────────────────────

def _doc(obj) -> dict:
    """Serialise a Beanie document to a plain dict."""
    d = obj.model_dump()
    d["id"] = str(obj.id)
    d.pop("_id", None)
    return d
