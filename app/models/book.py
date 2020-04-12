from sqlalchemy import JSON, Boolean, Column, ForeignKey, Integer, String
from sqlalchemy.orm import relationship

from app.db.base_class import Base


class Book(Base):
    id = Column(Integer, primary_key=True, index=True)
    index = Column(String, index=True, nullable=False, unique=True)
    kind = Column(String, index=True, nullable=False)
    data = Column(JSON)
    last_updated_id = Column(Integer, ForeignKey("user.id"))
    last_updated = relationship("User")
