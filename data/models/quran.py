from typing import Dict, List

from data.models.translation import Language, Translation


class Verse():
	index: int
	text: str
	sajda_type: str
	translations: List[Translation]

class Chapter():
	verses: List[Verse]
	index: int
	verseCount: int
	verseStartIndex: int
	names: Dict[str, str]
	type: str
	order: int
	rukus: int
	sajda_type: str = None

class Quran():
	chapters: List[Chapter]
