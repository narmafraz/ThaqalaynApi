from __future__ import annotations

from typing import Dict, List

from data.models.translation import Language, Translation


class Verse():
	index: int
	path: str
	text: str
	chain_text: str
	sajda_type: str
	translations: List[Translation]

class Chapter():
	verses: List[Verse]
	chapters: List[Chapter]
	index: str
	path: str
	verse_count: int
	verse_start_index: int
	titles: Dict[str, str]
	descriptions: Dict[str, str]
	type: str
	order: int
	rukus: int
	sajda_type: str = None

class Quran():
	chapters: List[Chapter]
