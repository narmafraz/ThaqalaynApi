from typing import List

from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session

from app import crud
from app.api.utils.db import get_db
from app.api.utils.security import get_current_active_user
from app.models.user import User as DBUser
from app.schemas.book_part import BookPart, BookPartCreate, BookPartUpdate

router = APIRouter()


@router.get("/", response_model=List[BookPart])
def read_book_parts(
    db: Session = Depends(get_db),
    skip: int = 0,
    limit: int = 100,
    kind: str = None
):
    """
    Retrieve book_parts.
    """
    book_parts = crud.book_part.get_multi_filter(db, skip=skip, limit=limit, kind=kind)
    return book_parts


@router.post("/", response_model=BookPart)
def create_book_part(
    *,
    db: Session = Depends(get_db),
    book_part_in: BookPartCreate,
    current_user: DBUser = Depends(get_current_active_user),
):
    """
    Create new book_part.
    """
    book_part = crud.book_part.create_by_user(
        db_session=db, obj_in=book_part_in, user_id=current_user.id
    )
    return book_part


@router.put("/{index}", response_model=BookPart)
def update_book_part(
    *,
    db: Session = Depends(get_db),
    index: str,
    book_part_in: BookPartUpdate,
    current_user: DBUser = Depends(get_current_active_user),
):
    """
    Update an book_part.
    """
    book_part = crud.book_part.get_by_index(db_session=db, index=index)
    if not book_part:
        raise HTTPException(status_code=404, detail="BookPart not found")
    book_part = crud.book_part.update(db_session=db, db_obj=book_part, obj_in=book_part_in)
    return book_part


@router.get("/{index}", response_model=BookPart)
def read_book_part(
    *,
    db: Session = Depends(get_db),
    index: str,
):
    """
    Get book_part by ID.
    """
    book_part = crud.book_part.get_by_index(db_session=db, index=index)
    if not book_part:
        raise HTTPException(status_code=404, detail="BookPart not found")
    return book_part


@router.delete("/{index}", response_model=BookPart)
def delete_book_part(
    *,
    db: Session = Depends(get_db),
    index: str,
    current_user: DBUser = Depends(get_current_active_user),
):
    """
    Delete an book_part.
    """
    book_part = crud.book_part.get_by_index(db_session=db, index=index)
    if not book_part:
        raise HTTPException(status_code=404, detail="BookPart not found")
    if not crud.user.is_superuser(current_user) and (book_part.owner_id != current_user.id):
        raise HTTPException(status_code=400, detail="Not enough permissions")
    book_part = crud.book_part.remove(db_session=db, id=book_part.id)
    return book_part
