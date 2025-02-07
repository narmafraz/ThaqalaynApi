from typing import Any

from pydantic import BaseModel

from .user import User


# Shared properties
class BookPartBase(BaseModel):
    kind: str = None
    index: str = None
    data: Any = None


# Properties to receive on book_part creation
class BookPartCreate(BookPartBase):
    kind: str
    index: str
    data: Any
    last_updated_id: int


# Properties to receive on book_part update
class BookPartUpdate(BookPartBase):
    kind: str
    data: Any
    last_updated_id: int
    pass


# Properties shared by models stored in DB
class BookPartInDBBase(BookPartBase):
    id: int
    index: str
    data: Any
    last_updated_id: int

    class Config:
        orm_mode = True


# Properties to return to client
class BookPart(BookPartInDBBase):
    pass


# Properties properties stored in DB
class BookPartInDB(BookPartInDBBase):
    pass
