from typing import List

from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session

from app import crud
from app.api.utils.db import get_db
from app.api.utils.security import get_current_active_user
from app.models.user import User as DBUser
from app.schemas.book import Book, BookCreate, BookUpdate

router = APIRouter()


@router.get("/", response_model=List[Book])
def read_books(
    db: Session = Depends(get_db),
    skip: int = 0,
    limit: int = 100,
    type: str = None
):
    """
    Retrieve books.
    """
    books = crud.book.get_multi_filter(db, skip=skip, limit=limit, type=type)
    return books


@router.post("/", response_model=Book)
def create_book(
    *,
    db: Session = Depends(get_db),
    book_in: BookCreate,
    current_user: DBUser = Depends(get_current_active_user),
):
    """
    Create new book.
    """
    book = crud.book.create_by_user(
        db_session=db, obj_in=book_in, user_id=current_user.id
    )
    return book


@router.put("/{index}", response_model=Book)
def update_book(
    *,
    db: Session = Depends(get_db),
    index: str,
    book_in: BookUpdate,
    current_user: DBUser = Depends(get_current_active_user),
):
    """
    Update an book.
    """
    book = crud.book.get_by_index(db_session=db, index=index)
    if not book:
        raise HTTPException(status_code=404, detail="Book not found")
    book = crud.book.update(db_session=db, db_obj=book, obj_in=book_in)
    return book


@router.get("/{index}", response_model=Book)
def read_book(
    *,
    db: Session = Depends(get_db),
    index: str,
):
    """
    Get book by ID.
    """
    book = crud.book.get_by_index(db_session=db, index=index)
    if not book:
        raise HTTPException(status_code=404, detail="Book not found")
    return book


@router.delete("/{index}", response_model=Book)
def delete_book(
    *,
    db: Session = Depends(get_db),
    index: str,
    current_user: DBUser = Depends(get_current_active_user),
):
    """
    Delete an book.
    """
    book = crud.book.get_by_index(db_session=db, index=index)
    if not book:
        raise HTTPException(status_code=404, detail="Book not found")
    if not crud.user.is_superuser(current_user) and (book.owner_id != current_user.id):
        raise HTTPException(status_code=400, detail="Not enough permissions")
    book = crud.book.remove(db_session=db, id=book.id)
    return book
