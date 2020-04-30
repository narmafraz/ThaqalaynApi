from enum import Enum, auto


class AutoName(Enum):
    def _generate_next_value_(name: str, start, count, last_values):
        return name.lower()

class Language(AutoName):
    AR = auto()
    EN = auto()
    ENT = auto()
    FA = auto()
