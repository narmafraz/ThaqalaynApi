from typing import Dict, List

from data.models.enums import PartType


class Crumb():
	titles: Dict[str, str]
	indexed_titles: Dict[str, str]
	path: str
