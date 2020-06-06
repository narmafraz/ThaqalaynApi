import json
import logging
import math
import os
import re
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
from data.lib_db import insert_chapter
from data.lib_model import set_index
from data.models import (Chapter, Crumb, Language, PartType, Quran,
                         Translation, Verse)

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

BOOK_INDEX = "al-kafi"
BOOK_PATH = "/books/" + BOOK_INDEX

TITLE_NUMBERING = re.compile(r' \(\d+\)')

def extract_headings(headings):
	assert len(headings) > 0, "Did not find headings in " + str(headings)
	names = {}
	if len(headings) > 1:
		names[Language.AR.value] = headings[0].get_text(strip=True)
		names[Language.EN.value] = TITLE_NUMBERING.sub('', headings[1].get_text(strip=True))
	else:
		names[Language.EN.value] = TITLE_NUMBERING.sub('', headings[0].get_text(strip=True))
	return names


def build_alhassanain_baabs(file) -> List[Chapter]:
	baabs: List[Chapter] = []
	logger.info("Adding Al-Kafi file %s", file)

	with open(file, 'r', encoding='utf8') as qfile:
		inner_html = qfile.read()
		sections = inner_html.split("<br clear=all>")
		for section in sections:
			section_soup = BeautifulSoup(section, 'html.parser')
			
			headings = section_soup.select(".Heading1Center")
			if not headings:
				continue
			
			# process "the book of" chapter
			baab_titles = extract_headings(headings)
			
			en_title = baab_titles[Language.EN.value]
			
			baab = None
			for existing_baab in baabs:
				if existing_baab.titles[Language.EN.value] == en_title:
					baab = existing_baab
			
			if not baab:
				baab = Chapter()
				baab.part_type = PartType.Book
				baab.titles = baab_titles
				baab.chapters = []

				baabs.append(baab)

			# process chapters
			chapters = section_soup.select(".Heading2Center")
			chapters_len = len(chapters)
			for subchapter_index in range(math.ceil(chapters_len / 2)):
				subchapter_heading_index = subchapter_index * 2
				
				remaining_chapters = chapters[subchapter_heading_index:]
				if len(remaining_chapters) > 1:
					remaining_chapters = remaining_chapters[:2]
				chapter_titles = extract_headings(remaining_chapters)

				chapter = Chapter()
				chapter.part_type = PartType.Chapter
				chapter.titles = chapter_titles
				chapter.verses = []

				baab.chapters.append(chapter)

				last_element = remaining_chapters[-1]
				last_element = last_element.next_sibling

				verse: Verse = None
				while (last_element is not None
					and (isinstance(last_element, NavigableString) 
						or ( isinstance(last_element, Tag) and 'Heading2Center' not in last_element['class'])
						)
					):
					is_tag = isinstance(last_element, Tag)
					if is_tag and 'libAr' in last_element['class']:
						
						# push the last verse if its not the start of chapter
						if verse != None:
							chapter.verses.append(verse)
						
						verse = Verse()
						verse.part_type = PartType.Hadith
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

				if verse != None:
					chapter.verses.append(verse)

	
	return baabs
			
def build_alhassanain_volume(file, title_en: str, title_ar: str, description: str) -> Chapter:
	volume = Chapter()
	volume.titles = {
		Language.EN.value: title_en,
		Language.AR.value: title_ar
	}
	volume.descriptions = {
			Language.EN.value: description
	}
	volume.chapters = build_alhassanain_baabs(file)
	volume.part_type = PartType.Volume

	return volume

def get_path(file):
	return os.path.join(os.path.dirname(__file__), "raw\\" + file)


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

	kafi.chapters.append(build_alhassanain_volume(
		get_path("alhassanain_org\\hubeali_com_usul_kafi_v_01_ed_html\\usul_kafi_v_01_ed.htm"),
		"Volume 1",
		"جلد اول",
		"First volume of Al-Kafi"))

	kafi.chapters.append(build_alhassanain_volume(
		get_path("alhassanain_org\\hubeali_com_usul_kafi_v_02_ed_html\\usul_kafi_v_02_ed.htm"),
		"Volume 2",
		"جلد 2",
		"Second volume of Al-Kafi"))

	kafi.chapters.append(build_alhassanain_volume(
		get_path("alhassanain_org\\hubeali_com_usul_kafi_v_03_ed_html\\usul_kafi_v_03_ed.htm"),
		"Volume 3",
		"جلد 3",
		"Third volume of Al-Kafi"))

	# post_processor(kafi)
	kafi.verse_start_index = 0
	kafi.index = BOOK_INDEX
	kafi.path = BOOK_PATH
	
	crumb = Crumb()
	crumb.titles = kafi.titles
	crumb.indexed_titles = kafi.titles
	crumb.path = kafi.path
	kafi.crumbs = [crumb]

	set_index(kafi, [0, 0, 0, 0], 0)

	return kafi

def init_kafi(db_session: Session):
	book = build_kafi()
	insert_chapter(db_session, book)
