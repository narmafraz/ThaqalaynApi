from fastapi import APIRouter

from app.api.api_v1.endpoints import (book_parts, books, items, login, users,
                                      utils)

api_router = APIRouter()
api_router.include_router(login.router, tags=["login"])
api_router.include_router(users.router, prefix="/users", tags=["users"])
api_router.include_router(utils.router, prefix="/utils", tags=["utils"])
api_router.include_router(items.router, prefix="/items", tags=["items"])
api_router.include_router(books.router, prefix="/books", tags=["books"])
api_router.include_router(book_parts.router, prefix="/bookparts", tags=["bookparts"])
