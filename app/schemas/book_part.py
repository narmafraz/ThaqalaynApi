from pydantic import BaseModel

from .user import User


# Shared properties
class BookPartBase(BaseModel):
    kind: str = None
    index: str = None
    data: dict = None


# Properties to receive on book_part creation
class BookPartCreate(BookPartBase):
    kind: str
    index: str
    data: dict


# Properties to receive on book_part update
class BookPartUpdate(BookPartBase):
    pass


# Properties shared by models stored in DB
class BookPartInDBBase(BookPartBase):
    id: int
    index: str
    data: dict
    last_updated_id: int

    class Config:
        orm_mode = True


# Properties to return to client
class BookPart(BookPartInDBBase):
    pass


# Properties properties stored in DB
class BookPartInDB(BookPartInDBBase):
    pass
