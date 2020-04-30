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
from data.models import Chapter, Quran, Translation, Verse

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

BOOK_INDEX = "quran"

def get_sajda_data(quran):
	sajdas = {}
	group = quran.find("sajdas")
	for j in group.findall("sajda"):
		meta = j.attrib
		ttype = meta['type']
		sura = int(meta['sura'])
		aya = int(meta['aya'])

		sajdas[(sura, aya)] = ttype

	return sajdas

def build_chapters(file: str, verses: List[Verse]) -> List[Chapter]:
	chapters: List[Chapter] = []
	
	quran = xml.etree.ElementTree.parse(file).getroot()

	suras = quran.find('suras')
	for s in suras.findall('sura'):
		meta = s.attrib
		index=int(meta['index'])
		ayas=int(meta['ayas'])
		start=int(meta['start'])
		name=meta['name']
		tname=meta['tname']
		ename=meta['ename']
		type=meta['type']
		order=int(meta['order'])
		rukus=int(meta['rukus'])

		names = {
			'ar': name,
			'en': ename,
			'ent': tname
		}

		sura = Chapter()
		sura.index=index,
		sura.names=names,
		sura.verseCount=ayas,
		sura.verseStartIndex=start,
		sura.type=type,
		sura.order=order,
		sura.rukus=rukus,
		sura.verses=verses[start:ayas+start]

		chapters.append(sura)

	sajdas = get_sajda_data(quran)
	for k, v in sajdas.items():
		(sura_index, aya_index) = k
		sajda_chapter = chapters[sura_index - 1]
		sajda_chapter.sajda_type = v
		sajda_chapter.verses[aya_index - 1].sajda_type = v



	# add_group_data(quran, ayaindex, 'juzs', 'juz')
	# add_group_data(quran, ayaindex, 'hizbs', 'quarter')
	# add_group_data(quran, ayaindex, 'manzils', 'manzil')
	# add_group_data(quran, ayaindex, 'rukus', 'ruku')
	# add_group_data(quran, ayaindex, 'pages', 'page')



def build_verses(file):
	logger.info("Adding Quran file %s", file)

	index = 0
	verses = []
	with open(file, 'r', encoding='utf8') as qfile:
		for line in qfile.readlines():
			text = line.strip()
			if text and not text.startswith('#'):
				index=index+1
				verse = Verse()
				verse.index=index
				verse.text=text

				verses.append(verse)
	
	return verses

def insert_quran_translation(verses, file, key, lang, author, bio):
	logger.info("Adding Quran translation file %s", file)

	index = 0
	with open(file, 'r') as qfile:
		for line in qfile.readlines():
			text = line.strip()
			if text and not text.startswith('#'):
				qt = Translation()
				qt.lang = lang
				qt.name = author
				qt.text = text

				verses[index].translations.append(qt)
				index = index + 1

def get_path(file):
	return os.path.join(os.path.dirname(__file__), file)


def build_quran() -> Quran:
	verses = build_verses(get_path("quran_simple.txt"))

	insert_quran_translation(verses, get_path("trans/fa.ansarian.txt"), "ansarian", "fa", "Hussain Ansarian", "https://fa.wikipedia.org/wiki/%D8%AD%D8%B3%DB%8C%D9%86_%D8%A7%D9%86%D8%B5%D8%A7%D8%B1%DB%8C%D8%A7%D9%86")
	insert_quran_translation(verses, get_path("trans/fa.ayati.txt"), "ayati", "fa", "AbdolMohammad Ayati", "https://fa.wikipedia.org/wiki/%D8%B9%D8%A8%D8%AF%D8%A7%D9%84%D9%85%D8%AD%D9%85%D8%AF_%D8%A2%DB%8C%D8%AA%DB%8C")
	insert_quran_translation(verses, get_path("trans/fa.bahrampour.txt"), "bahrampour", "fa", "Abolfazl Bahrampour", "https://fa.wikipedia.org/wiki/%D8%A7%D8%A8%D9%88%D8%A7%D9%84%D9%81%D8%B6%D9%84_%D8%A8%D9%87%D8%B1%D8%A7%D9%85%E2%80%8C%D9%BE%D9%88%D8%B1")
	insert_quran_translation(verses, get_path("trans/fa.fooladvand.txt"), "fooladvand", "fa", "Mohammad Mahdi Fooladvand", "https://fa.wikipedia.org/wiki/%D9%85%D8%AD%D9%85%D8%AF%D9%85%D9%87%D8%AF%DB%8C_%D9%81%D9%88%D9%84%D8%A7%D8%AF%D9%88%D9%86%D8%AF")
	insert_quran_translation(verses, get_path("trans/fa.ghomshei.txt"), "ghomshei", "fa", "Mahdi Elahi Ghomshei", "https://fa.wikipedia.org/wiki/%D9%85%D9%87%D8%AF%DB%8C_%D8%A7%D9%84%D9%87%DB%8C_%D9%82%D9%85%D8%B4%D9%87%E2%80%8C%D8%A7%DB%8C")
	insert_quran_translation(verses, get_path("trans/fa.khorramdel.txt"), "khorramdel", "fa", "Mostafa Khorramdel", "https://rasekhoon.net/mashahir/Show-904328.aspx")
	insert_quran_translation(verses, get_path("trans/fa.khorramshahi.txt"), "khorramshahi", "fa", "Baha'oddin Khorramshahi", "https://fa.wikipedia.org/wiki/%D8%A8%D9%87%D8%A7%D8%A1%D8%A7%D9%84%D8%AF%DB%8C%D9%86_%D8%AE%D8%B1%D9%85%D8%B4%D8%A7%D9%87%DB%8C")
	insert_quran_translation(verses, get_path("trans/fa.makarem.txt"), "makarem", "fa", "Naser Makarem Shirazi", "https://en.wikipedia.org/wiki/Naser_Makarem_Shirazi")
	insert_quran_translation(verses, get_path("trans/fa.moezzi.txt"), "moezzi", "fa", "Mohammad Kazem Moezzi", "")
	insert_quran_translation(verses, get_path("trans/fa.mojtabavi.txt"), "mojtabavi", "fa", "Sayyed Jalaloddin Mojtabavi", "http://rasekhoon.net/mashahir/Show-118481.aspx")
	insert_quran_translation(verses, get_path("trans/fa.sadeqi.txt"), "sadeqi", "fa", "Mohammad Sadeqi Tehrani", "https://fa.wikipedia.org/wiki/%D9%85%D8%AD%D9%85%D8%AF_%D8%B5%D8%A7%D8%AF%D9%82%DB%8C_%D8%AA%D9%87%D8%B1%D8%A7%D9%86%DB%8C")

	insert_quran_translation(verses, get_path("trans/en.ahmedali.txt"), "ahmedali", "en", "Ahmed Ali", "https://en.wikipedia.org/wiki/Ahmed_Ali_(writer)")
	insert_quran_translation(verses, get_path("trans/en.ahmedraza.txt"), "ahmedraza", "en", "Ahmed Raza Khan", "https://en.wikipedia.org/wiki/Ahmed_Raza_Khan_Barelvi")
	insert_quran_translation(verses, get_path("trans/en.arberry.txt"), "arberry", "en", "A. J. Arberry", "https://en.wikipedia.org/wiki/Arthur_John_Arberry")
	insert_quran_translation(verses, get_path("trans/en.daryabadi.txt"), "daryabadi", "en", "Abdul Majid Daryabadi", "https://en.wikipedia.org/wiki/Abdul_Majid_Daryabadi")
	insert_quran_translation(verses, get_path("trans/en.hilali.txt"), "hilali", "en", "Muhammad Taqi-ud-Din al-Hilali and Muhammad Muhsin Khan", "https://en.wikipedia.org/wiki/Noble_Quran_(Hilali-Khan)")
	insert_quran_translation(verses, get_path("trans/en.itani.txt"), "itani", "en", "Talal Itani", "")
	insert_quran_translation(verses, get_path("trans/en.maududi.txt"), "maududi", "en", "Abul Ala Maududi", "https://en.wikipedia.org/wiki/Abul_A%27la_Maududi")
	insert_quran_translation(verses, get_path("trans/en.mubarakpuri.txt"), "mubarakpuri", "en", "Safi-ur-Rahman al-Mubarakpuri", "https://en.wikipedia.org/wiki/Safiur_Rahman_Mubarakpuri")
	insert_quran_translation(verses, get_path("trans/en.pickthall.txt"), "pickthall", "en", "Mohammed Marmaduke William Pickthall", "https://en.wikipedia.org/wiki/Marmaduke_Pickthall")
	insert_quran_translation(verses, get_path("trans/en.qarai.txt"), "qarai", "en", "Ali Quli Qarai", "")
	insert_quran_translation(verses, get_path("trans/en.qaribullah.txt"), "qaribullah", "en", "Hasan al-Fatih Qaribullah and Ahmad Darwish", "")
	insert_quran_translation(verses, get_path("trans/en.sahih.txt"), "sahih", "en", "Saheeh International", "http://www.saheehinternational.com/")
	insert_quran_translation(verses, get_path("trans/en.sarwar.txt"), "sarwar", "en", "Muhammad Sarwar", "https://en.wikipedia.org/wiki/Shaykh_Muhammad_Sarwar")
	insert_quran_translation(verses, get_path("trans/en.shakir.txt"), "shakir", "en", "Mohammad Habib Shakir", "https://en.wikipedia.org/wiki/Muhammad_Habib_Shakir")
	insert_quran_translation(verses, get_path("trans/en.transliteration.txt"), "transliteration", "en", "English Transliteration", "")
	insert_quran_translation(verses, get_path("trans/en.wahiduddin.txt"), "wahiduddin", "en", "Wahiduddin Khan", "https://en.wikipedia.org/wiki/Wahiduddin_Khan")
	insert_quran_translation(verses, get_path("trans/en.yusufali.txt"), "yusufali", "en", "Abdullah Yusuf Ali", "https://en.wikipedia.org/wiki/Abdullah_Yusuf_Ali")

	chapters = build_chapters(get_path("quran-data.xml"), verses)

	q = Quran()
	q.chapters=chapters

	return q

def insert_chapters_list(db: Session, quran: Quran):
	data_root = {
		"chapters": []
	}
	chapters = data_root["chapters"]

	for chapter in quran.chapters:
		data_chapter = {
			"index": BOOK_INDEX + ":" + chapter.index,
			"verseCount": chapter.verseCount,
			"verseStartIndex": chapter.verseStartIndex,
			"names": chapter.names,
			"verse_type": chapter.type,
			"order": chapter.order,
			"sajda_type": chapter.sajda_type,
			"rukus": chapter.rukus
		}
		chapters.append(data_chapter)

	data_json = json.dumps(data_root)
	obj_in = BookPartCreate (
		index = BOOK_INDEX,
		kind = "chapter_list",
		data = data_json
	)
	book = crud.book_part.create(db, obj_in=obj_in)
	logger.info("Inserted Quran chapter list into book_part ID %i with index %s", book.id, book.index)

def insert_chapter_content(db: Session, quran: Quran):
	pass

def insert_quran_content(db: Session, quran: Quran):
	pass

def init_quran(db_session: Session):
	quran = build_quran()
	insert_chapters_list(db_session, quran)
	insert_quran_content(db_session, quran)
