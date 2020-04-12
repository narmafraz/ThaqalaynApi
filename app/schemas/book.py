from pydantic import BaseModel

from .user import User


# Shared properties
class BookBase(BaseModel):
    kind: str = None
    index: str = None
    data: dict = None


# Properties to receive on book creation
class BookCreate(BookBase):
    kind: str
    index: str
    data: dict


# Properties to receive on book update
class BookUpdate(BookBase):
    pass


# Properties shared by models stored in DB
class BookInDBBase(BookBase):
    id: int
    index: str
    data: str
    last_updated_id: int

    class Config:
        orm_mode = True


# Properties to return to client
class Book(BookInDBBase):
    pass


# Properties properties stored in DB
class BookInDB(BookInDBBase):
    pass
