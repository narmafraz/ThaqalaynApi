from typing import Dict, List

from data.models import Chapter, Language, Quran, Translation, Verse


def has_chapters(book: Chapter) -> bool:
	return hasattr(book, 'chapters') and book.chapters is not None

def has_verses(book: Chapter) -> bool:
	return hasattr(book, 'verses') and book.verses is not None

def set_index(chapter: Chapter, indexes: List[int], depth: int) -> List[int]:
	if len(indexes) < depth + 1:
		indexes.append(0)

	if has_verses(chapter):
		verse_local_index = 0
		for verse in chapter.verses:
			indexes[depth] = indexes[depth] + 1
			verse.index = indexes[depth]
			verse_local_index = verse_local_index + 1
			verse.local_index = verse_local_index
			verse.path = chapter.path + ":" + str(verse_local_index)
		chapter.verse_count = indexes[depth] - chapter.verse_start_index
	
	if has_chapters(chapter):
		chapter_local_index = 0
		for subchapter in chapter.chapters:
			indexes[depth] = indexes[depth] + 1
			subchapter.index = indexes[depth]
			chapter_local_index = chapter_local_index + 1
			subchapter.local_index = chapter_local_index
			subchapter.path = chapter.path + ":" + str(chapter_local_index)
			subchapter.verse_start_index = indexes[-1]
			indexes = set_index(subchapter, indexes, depth + 1)
		chapter.verse_count = indexes[-1] - chapter.verse_start_index

	return indexes


def post_processor(book: Chapter):
	volume_index = 0
	kitab_index = 0
	chapter_index = 0
	verse_index = 0

	for volume in book.chapters:
		volume_index = volume_index + 1
		volume.index = volume_index
		volume.local_index = volume_index
		volume.path = "BOOK_PATH" + ":" + str(volume_index)
		volume.verse_start_index = verse_index

		kitab_local_index = 0
		for kitab in volume.chapters:
			kitab_index = kitab_index + 1
			kitab.index = kitab_index
			kitab_local_index = kitab_local_index + 1
			kitab.local_index = kitab_local_index
			kitab.path = volume.path + ":" + str(kitab_index)
			kitab.verse_start_index = verse_index

			chapter_local_index = 0
			for chapter in kitab.chapters:
				chapter_index = chapter_index + 1
				chapter.index = chapter_index
				chapter_local_index = chapter_local_index + 1
				chapter.local_index = chapter_local_index
				chapter.path = kitab.path + ":" + str(chapter_index)
				chapter.verse_start_index = verse_index

				verse_local_index = 0
				for verse in chapter.verses:
					verse_index = verse_index + 1
					verse.index = verse_index
					verse_local_index = verse_local_index + 1
					verse.local_index = verse_local_index
					verse.path = chapter.path + ":" + str(verse_index)
				chapter.verse_count = verse_index - chapter.verse_start_index
			kitab.verse_count = verse_index - kitab.verse_start_index
		volume.verse_count = verse_index - volume.verse_start_index
