from pydantic import BaseModel

from .user import User


# Shared properties
class BookBase(BaseModel):
    type: str = None
    index: str = None
    title: str = None
    description: str = None


# Properties to receive on book creation
class BookCreate(BookBase):
    type: str
    index: str
    title: str


# Properties to receive on book update
class BookUpdate(BookBase):
    pass


# Properties shared by models stored in DB
class BookInDBBase(BookBase):
    id: int
    index: str
    title: str
    last_updated_id: int

    class Config:
        orm_mode = True


# Properties to return to client
class Book(BookInDBBase):
    pass


# Properties properties stored in DB
class BookInDB(BookInDBBase):
    pass
