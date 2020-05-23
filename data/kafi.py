import json
import logging
import math
import os
import sqlite3
import xml.etree.ElementTree
from sqlite3 import Error
from typing import Dict, List

from bs4 import BeautifulSoup, NavigableString, Tag
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
from data.models import Chapter, Language, Quran, Translation, Verse

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

BOOK_INDEX = "al-kafi"
BOOK_PATH = "/books/" + BOOK_INDEX

def extract_headings(headings):
	assert len(headings) > 0, "Did not find headings in " + str(headings)
	names = {}
	if len(headings) > 1:
		names[Language.AR.value] = headings[0].get_text(strip=True)
		names[Language.EN.value] = headings[1].get_text(strip=True)
	else:
		names[Language.EN.value] = headings[0].get_text(strip=True)
	return names


def build_alhassanain_baabs(file, index_suffix: str) -> List[Chapter]:
	baabs: List[Chapter] = []
	logger.info("Adding Al-Kafi file %s", file)

	with open(file, 'r', encoding='utf8') as qfile:
		#soup = BeautifulSoup(qfile, 'html.parser')
		#content_div = soup.find(id="bookContent")
		inner_html = qfile.read()
		sections = inner_html.split("<br clear=all>")
		index = 0
		for section in sections:
			section_soup = BeautifulSoup(section, 'html.parser')
			
			headings = section_soup.select(".Heading1Center")
			if not headings:
				continue
			
			# process "the book of" chapter
			baab_titles = extract_headings(headings)
			index = index + 1
			baab = Chapter()
			baab.index = BOOK_INDEX + index_suffix + ":" + str(index)
			baab.path = BOOK_PATH + index_suffix + ":" + str(index)
			baab.titles = baab_titles
			baab.chapters = []

			baabs.append(baab)

			# process chapters
			chapters = section_soup.select(".Heading2Center")
			chapters_len = len(chapters)
			chapter_index = 0
			for subchapter_index in range(math.ceil(chapters_len / 2)):
				subchapter_heading_index = subchapter_index * 2
				
				remaining_chapters = chapters[subchapter_heading_index:]
				if len(remaining_chapters) > 1:
					remaining_chapters = remaining_chapters[:2]
				chapter_titles = extract_headings(remaining_chapters)

				chapter_index = chapter_index + 1
				chapter = Chapter()
				chapter.index = baab.index + ":" + str(chapter_index)
				chapter.path = baab.path + ":" + str(chapter_index)
				chapter.titles = chapter_titles
				chapter.verses = []

				baab.chapters.append(chapter)

				last_element = remaining_chapters[-1]
				last_element = last_element.next_sibling

				verse: Verse = None
				verse_index = 0
				while last_element is not None and (isinstance(last_element, NavigableString) or not last_element.select('.Heading2Center')):
					is_tag = isinstance(last_element, Tag)
					if is_tag and 'libAr' in last_element['class']:
						
						# push the last verse if its not the start of chapter
						if verse != None:
							chapter.verses.append(verse)
						
						verse_index = verse_index + 1
						verse = Verse()
						verse.index = chapter.index + ":" + str(verse_index)
						verse.path = chapter.path + ":" + str(verse_index)
						translation = Translation()
						translation.name = "hubeali"
						translation.lang = Language.EN.value
						translation.text = None
						verse.translations = [translation]

						verse.text = last_element.get_text(strip=True)

					if is_tag and 'libNormal' in last_element['class']:
						if verse.translations[0].text:
							verse.translations[0].text = verse.translations[0].text + "\n" + last_element.get_text(strip=True)
						else:
							verse.translations[0].text = last_element.get_text(strip=True)

					last_element = last_element.next_sibling
				
				chapter.verse_count = verse_index

	
	return baabs
			
def build_alhassanain_volume(file, index_suffix: str, title_en: str, title_ar: str, description: str) -> Chapter:
	volume = Chapter()
	volume.index = BOOK_INDEX + index_suffix
	volume.path = BOOK_PATH + index_suffix
	volume.titles = {
		Language.EN.value: title_en,
		Language.AR.value: title_ar
	}
	volume.descriptions = {
			Language.EN.value: description
	}
	volume.chapters = build_alhassanain_baabs(file, index_suffix)

	return volume


def get_path(file):
	return os.path.join(os.path.dirname(__file__), file)


def build_kafi() -> Chapter:
	kafi = Chapter()
	kafi.index = BOOK_INDEX
	kafi.path = BOOK_PATH
	kafi.titles = {
		Language.EN.value: "Al-Kafi",
		Language.AR.value: "الكافي"
	}
	kafi.descriptions = {
			Language.EN.value: "Of the majestic narrator and the scholar, the jurist, the Sheykh Muhammad Bin Yaqoub Al-Kulayni Well known as ‘The trustworthy of Al-Islam Al-Kulayni’ Who died in the year 329 H"
	}
	kafi.chapters = []

	kafi.chapters.append(build_alhassanain_volume(get_path("usul_kafi_v_01_ed_html\\usul_kafi_v_01_ed.htm"), ":1", "Volume 1", "جلد اول", "First volume of Al-Kafi"))

	return kafi

def insert_chapter(db: Session, book: Chapter):
	if hasattr(book, 'chapters') and book.chapters is not None:
		insert_chapters_list(db, book)

	if hasattr(book, 'verses') and book.verses is not None:
		insert_chapter_content(db, book)

def insert_chapters_list(db: Session, book: Chapter):
	data_root = {
		"titles": book.titles,
		"chapters": []
	}

	if hasattr(book, 'descriptions'):
		data_root['descriptions'] = book.descriptions

	chapters = data_root["chapters"]

	for chapter in book.chapters:
		data_chapter = {
			"index": chapter.index,
			"path": chapter.path
		}

		if hasattr(chapter, "titles"):
			data_chapter["titles"] = chapter.titles

		if hasattr(chapter, "verse_count"):
			data_chapter["verse_count"] = chapter.verse_count

		if hasattr(chapter, "verse_start_index"):
			data_chapter["verse_start_index"] = chapter.verse_start_index

		chapters.append(data_chapter)

	obj_in = BookPartCreate (
		index = book.index,
		kind = "chapter_list",
		data = data_root,
		last_updated_id = 1
	)
	book_part = crud.book_part.upsert(db, obj_in=obj_in)
	logger.info("Inserted chapter list into book_part ID %i with index %s", book_part.id, book_part.index)

	for chapter in book.chapters:
		insert_chapter(db, chapter)

def insert_chapter_content(db: Session, chapter: Chapter):
	obj_in = BookPartCreate (
		index = chapter.index,
		kind = "verse_list",
		data = chapter,
		last_updated_id = 1
	)
	book = crud.book_part.upsert(db, obj_in=obj_in)
	logger.info("Inserted Quran chapter content into book_part ID %i with index %s", book.id, chapter.index)

def init_kafi(db_session: Session):
	book = build_kafi()
	insert_chapters_list(db_session, book)
