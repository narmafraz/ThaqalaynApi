from sqlalchemy import Column, ForeignKey, Integer, String
from sqlalchemy.orm import relationship

from app.db.base_class import Base


class Book(Base):
    id = Column(Integer, primary_key=True, index=True)
    index = Column(String, index=True)
    title = Column(String, index=True)
    description = Column(String, index=True)
    last_updated_id = Column(Integer, ForeignKey("user.id"))
    last_updated = relationship("User")
