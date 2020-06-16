import copy
from typing import Dict, List

from data.models import (Chapter, Crumb, Language, PartType, Quran,
                         Translation, Verse)


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
			if verse.part_type == PartType.Hadith:
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

			subchapter.crumbs = copy.copy(chapter.crumbs)
			crumb = Crumb()
			crumb.indexed_titles = {
				Language.EN.value: subchapter.part_type.name + ' ' + str(subchapter.local_index)
			}
			crumb.titles = subchapter.titles
			crumb.path = subchapter.path
			subchapter.crumbs.append(crumb)

			indexes = set_index(subchapter, indexes, depth + 1)
		chapter.verse_count = indexes[-1] - chapter.verse_start_index

	return indexes
