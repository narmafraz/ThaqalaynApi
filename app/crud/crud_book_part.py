from typing import List, Optional

from fastapi.encoders import jsonable_encoder
from sqlalchemy.orm import Session

from app.crud.base import CRUDBase
from app.models.book_part import BookPart
from app.schemas.book_part import BookPartCreate, BookPartUpdate


class CRUDBookPart(CRUDBase[BookPart, BookPartCreate, BookPartUpdate]):
    def create_by_user(
        self, db_session: Session, *, obj_in: BookPartCreate, user_id: int
    ) -> BookPart:
        obj_in_data = jsonable_encoder(obj_in)
        db_obj = self.model(**obj_in_data, last_updated_id=user_id)
        db_session.add(db_obj)
        db_session.commit()
        db_session.refresh(db_obj)
        return db_obj

    def get_by_index(self, db_session: Session, index: str) -> Optional[BookPart]:
        return db_session.query(self.model).filter(self.model.index == index).first()

    def get_multi_filter(
        self, db_session: Session, *, kind: str, skip=0, limit=100
    ) -> List[BookPart]:
        q = db_session.query(self.model)
        
        if not(kind is None):
            q = q.filter(BookPart.kind == kind)

        return (
            q.offset(skip)
            .limit(limit)
            .all()
        )

    def get_multi_by_index(
        self, db_session: Session, *, indexes: List[str], skip=0, limit=100
    ) -> List[BookPart]:
        return (
            db_session.query(self.model)
            .filter(BookPart.index in indexes)
            .offset(skip)
            .limit(limit)
            .all()
        )


book_part = CRUDBookPart(BookPart)
