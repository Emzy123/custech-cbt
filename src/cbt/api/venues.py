"""
Venues API — CRUD for physical examination venues and seat assignments.
"""

from typing import Any, List, Optional
from fastapi import APIRouter, Depends, HTTPException, Query, status
from pydantic import BaseModel, Field

from ..models.venue import Venue, ExamVenueAssignment
from ..core.database import get_db
from .deps import get_current_active_user, require_permission

router = APIRouter(prefix="/venues", tags=["venues"])

# ──────────────────────────── Schemas ────────────────────────

class VenueCreate(BaseModel):
    name: str = Field(..., json_schema_extra={"example": "Main Hall A"})
    code: str = Field(..., json_schema_extra={"example": "MH-A"})
    capacity: int = Field(..., gt=0)
    rows: Optional[int] = None
    columns: Optional[int] = None
    building: Optional[str] = None
    floor: Optional[str] = None
    notes: Optional[str] = None
    is_active: bool = True

class VenueUpdate(BaseModel):
    name: Optional[str] = None
    code: Optional[str] = None
    capacity: Optional[int] = Field(None, gt=0)
    rows: Optional[int] = None
    columns: Optional[int] = None
    building: Optional[str] = None
    floor: Optional[str] = None
    notes: Optional[str] = None
    is_active: Optional[bool] = None

class ExamVenueAssignmentCreate(BaseModel):
    examination_id: str
    venue_id: str
    student_id: str
    seat_row: Optional[int] = None
    seat_column: Optional[int] = None
    seat_label: Optional[str] = None
    exam_number: Optional[str] = None

# ──────────────────────────── Venues ───────────────────────────────

@router.get("", dependencies=[Depends(require_permission("venue.read"))])
async def list_venues(
    is_active: Optional[bool] = Query(None),
    current_user=Depends(get_current_active_user),
    db: Any = Depends(get_db),
) -> List[dict]:
    f = {"is_active": is_active} if is_active is not None else {}
    venues = await Venue.find(f).sort("name").to_list()
    return [_doc(v) for v in venues]

@router.post("", status_code=status.HTTP_201_CREATED,
             dependencies=[Depends(require_permission("venue.create"))])
async def create_venue(
    data: VenueCreate,
    current_user=Depends(get_current_active_user),
    db: Any = Depends(get_db),
) -> dict:
    existing = await Venue.find_one({"code": data.code})
    if existing:
        raise HTTPException(status_code=409, detail=f"Venue '{data.code}' already exists")
    obj = Venue(**data.model_dump(), created_by=str(current_user.id))
    await obj.insert()
    return _doc(obj)

@router.get("/{venue_id}", dependencies=[Depends(require_permission("venue.read"))])
async def get_venue(
    venue_id: str,
    current_user=Depends(get_current_active_user),
    db: Any = Depends(get_db),
) -> dict:
    obj = await Venue.get(venue_id)
    if not obj:
        raise HTTPException(status_code=404, detail="Venue not found")
    return _doc(obj)

@router.patch("/{venue_id}", dependencies=[Depends(require_permission("venue.update"))])
async def update_venue(
    venue_id: str,
    data: VenueUpdate,
    current_user=Depends(get_current_active_user),
    db: Any = Depends(get_db),
) -> dict:
    obj = await Venue.get(venue_id)
    if not obj:
        raise HTTPException(status_code=404, detail="Venue not found")
    updates = data.model_dump(exclude_unset=True)
    if updates:
        await obj.set(updates)
    return _doc(obj)

@router.delete("/{venue_id}", status_code=status.HTTP_204_NO_CONTENT,
               dependencies=[Depends(require_permission("venue.delete"))])
async def delete_venue(
    venue_id: str,
    current_user=Depends(get_current_active_user),
    db: Any = Depends(get_db),
):
    obj = await Venue.get(venue_id)
    if not obj:
        raise HTTPException(status_code=404, detail="Venue not found")
    await obj.delete()

# ──────────────────────────── Assignments ────────────────────────────

@router.get("/{venue_id}/assignments", dependencies=[Depends(require_permission("venue.read"))])
async def list_assignments(
    venue_id: str,
    examination_id: Optional[str] = Query(None),
    current_user=Depends(get_current_active_user),
    db: Any = Depends(get_db),
) -> List[dict]:
    f: dict = {"venue_id": venue_id}
    if examination_id:
        f["examination_id"] = examination_id
    assignments = await ExamVenueAssignment.find(f).to_list()
    return [_doc(a) for a in assignments]

@router.post("/{venue_id}/assignments", status_code=status.HTTP_201_CREATED,
             dependencies=[Depends(require_permission("venue.update"))])
async def create_assignment(
    venue_id: str,
    data: ExamVenueAssignmentCreate,
    current_user=Depends(get_current_active_user),
    db: Any = Depends(get_db),
) -> dict:
    if data.venue_id != venue_id:
        raise HTTPException(status_code=400, detail="Venue ID mismatch")
        
    venue = await Venue.get(venue_id)
    if not venue:
        raise HTTPException(status_code=404, detail="Venue not found")
        
    existing = await ExamVenueAssignment.find_one({
        "examination_id": data.examination_id,
        "student_id": data.student_id
    })
    if existing:
        raise HTTPException(status_code=409, detail="Student already assigned for this examination")
        
    obj = ExamVenueAssignment(**data.model_dump(), assigned_by=str(current_user.id))
    await obj.insert()
    return _doc(obj)

@router.delete("/{venue_id}/assignments/{assignment_id}", status_code=status.HTTP_204_NO_CONTENT,
               dependencies=[Depends(require_permission("venue.update"))])
async def delete_assignment(
    venue_id: str,
    assignment_id: str,
    current_user=Depends(get_current_active_user),
    db: Any = Depends(get_db),
):
    obj = await ExamVenueAssignment.get(assignment_id)
    if not obj:
        raise HTTPException(status_code=404, detail="Assignment not found")
    if obj.venue_id != venue_id:
        raise HTTPException(status_code=400, detail="Assignment does not belong to this venue")
    await obj.delete()

# ──────────────────────────── Helper ─────────────────────────────────

def _doc(obj) -> dict:
    """Serialise a Beanie document to a plain dict."""
    d = obj.model_dump()
    d["id"] = str(obj.id)
    d.pop("_id", None)
    return d
