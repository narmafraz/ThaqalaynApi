import json
import logging
import os
import sqlite3
import xml.etree.ElementTree
from sqlite3 import Error
from typing import Dict, List

from sqlalchemy.orm import Session

from app import crud
from app.core import config
# make sure all SQL Alchemy models are imported before initializing DB
# otherwise, SQL Alchemy might fail to initialize relationships properly
# for more details: https://github.com/tiangolo/full-stack-fastapi-postgresql/issues/28
from app.db import base
from app.db.base import Base
from app.db.session import engine
from app.schemas.book_part import BookPartCreate
from data.models import Language
from data.quran import BOOK_INDEX as QURAN_INDEX

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

BOOK_INDEX = "books"

def init_books(db_session: Session):
	data_root = {
		"title": "books",
		"chapters": [
			{
				"index": QURAN_INDEX,
				"names": {
					Language.EN: "The Noble Quran",
					Language.AR: "القرآن الكريم"
				}
			}
		]
	}

	data_json = json.dumps(data_root)
	obj_in = BookPartCreate (
		index = BOOK_INDEX,
		kind = "chapter_list",
		data = data_json
	)
	book = crud.book_part.create(db_session, obj_in=obj_in)
	logger.info("Inserted books list into book_part ID %i with index %s", book.id, book.index)
