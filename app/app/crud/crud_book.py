from typing import List, Optional

from fastapi.encoders import jsonable_encoder
from sqlalchemy.orm import Session

from app.crud.base import CRUDBase
from app.models.book import Book
from app.schemas.book import BookCreate, BookUpdate


class CRUDBook(CRUDBase[Book, BookCreate, BookUpdate]):
    def create_by_user(
        self, db_session: Session, *, obj_in: BookCreate, user_id: int
    ) -> Book:
        obj_in_data = jsonable_encoder(obj_in)
        db_obj = self.model(**obj_in_data, last_updated_id=user_id)
        db_session.add(db_obj)
        db_session.commit()
        db_session.refresh(db_obj)
        return db_obj

    def get_by_index(self, db_session: Session, index: str) -> Optional[Book]:
        return db_session.query(self.model).filter(self.model.index == index).first()

    def get_multi_filter(
        self, db_session: Session, *, kind: str, skip=0, limit=100
    ) -> List[Book]:
        q = db_session.query(self.model)
        
        if not(kind is None):
            q = q.filter(Book.kind == kind)

        return (
            q.offset(skip)
            .limit(limit)
            .all()
        )

    def get_multi_by_index(
        self, db_session: Session, *, indexes: List[str], skip=0, limit=100
    ) -> List[Book]:
        return (
            db_session.query(self.model)
            .filter(Book.index in indexes)
            .offset(skip)
            .limit(limit)
            .all()
        )


book = CRUDBook(Book)
