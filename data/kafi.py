import glob
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

BOOK_INDEX = "al-kafi-ha"
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

VOLUME_HEADING_PATTERN = re.compile("^AL-KAFI VOLUME")
TABLE_OF_CONTENTS_PATTERN = re.compile("^TABLE OF CONTENTS")
WHITESPACE_PATTERN = re.compile("^\\s*$")
END_OF_HADITH_PATTERN = re.compile("<sup>\[\d+\]</sup>\s*$")

def we_dont_care(heading):
	if heading is None:
		return True
	
	htext = heading.get_text(strip=True).upper()
	if VOLUME_HEADING_PATTERN.match(htext):
		return True
	
	return False

def table_of_contents(heading):
	htext = heading.get_text(strip=True).upper()
	return TABLE_OF_CONTENTS_PATTERN.match(htext)

def get_contents(element):
	return "".join([str(x) for x in element.contents])

def join_texts(texts: List[str]) -> str:
	return "\n".join([text for text in texts])

def is_arabic_tag(element: Tag) -> bool:
	return element.has_attr('dir') and element['dir'] == 'rtl'

def is_book_title(element: Tag) -> bool:
	return element.has_attr('style') and "font-size: x-large; font-weight: bold; text-align: center; text-decoration: underline" in element['style']

def is_chapter_title(element: Tag) -> bool:
	return element.has_attr('style') and "font-weight: bold; text-align: justify; text-decoration: underline" in element['style']

def is_newline(element) -> bool:
	return isinstance(element, NavigableString) and WHITESPACE_PATTERN.match(element)

def add_hadith(chapter: Chapter, hadith_ar: List[str], hadith_en: List[str]):
	hadith = Verse()
	hadith.part_type = PartType.Hadith
	hadith.text = join_texts(hadith_ar)
	
	translation = Translation()
	translation.name = "hubeali"
	translation.lang = Language.EN.value
	translation.text = join_texts(hadith_en)
	hadith.translations = [translation]
	
	chapter.verses.append(hadith)

def build_hubeali_books(dirname) -> List[Chapter]:
	books: List[Chapter] = []
	logger.info("Adding Al-Kafi dir %s", dirname)

	cfiles = glob.glob(dirname + "c*.xhtml")


	book = None
	chapter = None
	book_title = None
	chapter_title = None
	for cfile in cfiles:
		logger.info("Processing file %s", cfile)

		with open(cfile, 'r', encoding='utf8') as qfile:
			file_html = qfile.read()
			soup = BeautifulSoup(file_html, 'html.parser')

			heading = soup.body.h1
			if we_dont_care(heading):
				continue

			if table_of_contents(heading):
				book_title = get_contents(soup.body.contents[-2])
				continue

			heading_en = get_contents(heading.a)

			if book_title:
				book = Chapter()
				book.part_type = PartType.Book
				book.titles = {}
				# Arabic title comes from previous file
				book.titles[Language.AR.value] = book_title
				book.titles[Language.EN.value] = heading_en
				book_title = None
				book.chapters = []

				books.append(book)
			elif chapter_title or not chapter:
				chapter = Chapter()
				chapter.part_type = PartType.Chapter
				chapter.titles = {}
				chapter.titles[Language.AR.value] = chapter_title
				chapter.titles[Language.EN.value] = heading_en
				chapter_title = None
				chapter.verses = []

				book.chapters.append(chapter)


			last_element = soup.find('p', 'first-in-chapter')

			hadith_ar = []
			hadith_en = []

			while last_element:
				if is_newline(last_element):
					last_element = last_element.next_sibling
					continue

				is_tag = isinstance(last_element, Tag)
				is_arabic = is_arabic_tag(last_element)

				element_content = get_contents(last_element)
				is_end_of_hadith = END_OF_HADITH_PATTERN.search(element_content)

				if is_book_title(last_element):
					book_title = element_content
				elif is_chapter_title(last_element):
					chapter_title = element_content
				elif is_arabic:
					hadith_ar.append(element_content)
				else:
					hadith_en.append(element_content)
				
				if is_end_of_hadith:
					add_hadith(chapter, hadith_ar, hadith_en)

					hadith_ar = []
					hadith_en = []

				last_element = last_element.next_sibling

			if hadith_ar and hadith_en:
				add_hadith(chapter, hadith_ar, hadith_en)


	return books

def build_volume(file, title_en: str, title_ar: str, description: str) -> Chapter:
	volume = Chapter()
	volume.titles = {
		Language.EN.value: title_en,
		Language.AR.value: title_ar
	}
	volume.descriptions = {
			Language.EN.value: description
	}
	volume.chapters = build_hubeali_books(file)
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

	kafi.chapters.append(build_volume(
		get_path("hubeali_com\\Al-Kafi-Volume-1\\"),
		"Volume 1",
		"جلد اول",
		"First volume of Al-Kafi"))

	# kafi.chapters.append(build_volume(
	# 	get_path("alhassanain_org\\hubeali_com_usul_kafi_v_01_ed_html\\usul_kafi_v_01_ed.htm"),
	# 	"Volume 1",
	# 	"جلد اول",
	# 	"First volume of Al-Kafi"))

	# kafi.chapters.append(build_volume(
	# 	get_path("alhassanain_org\\hubeali_com_usul_kafi_v_02_ed_html\\usul_kafi_v_02_ed.htm"),
	# 	"Volume 2",
	# 	"جلد 2",
	# 	"Second volume of Al-Kafi"))

	# kafi.chapters.append(build_volume(
	# 	get_path("alhassanain_org\\hubeali_com_usul_kafi_v_03_ed_html\\usul_kafi_v_03_ed.htm"),
	# 	"Volume 3",
	# 	"جلد 3",
	# 	"Third volume of Al-Kafi"))

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
