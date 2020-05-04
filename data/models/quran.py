from typing import Dict, List

from data.models.translation import Language, Translation


class Verse():
	index: int
	path: str
	text: str
	sajda_type: str
	translations: List[Translation]

class Chapter():
	verses: List[Verse]
	index: int
	path: str
	verse_count: int
	verse_start_index: int
	names: Dict[str, str]
	type: str
	order: int
	rukus: int
	sajda_type: str = None

class Quran():
	chapters: List[Chapter]
