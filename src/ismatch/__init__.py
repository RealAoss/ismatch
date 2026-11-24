"""ismatch - match Arabic names across spellings and scripts.

>>> import ismatch
>>> ismatch.is_match("محمد عبد الرحمن", "Mohamed Abdelrahman")
True
>>> ismatch.is_match("Hassan", "Hussein")
False
"""

from .index import NameIndex, dedupe
from .match import DEFAULT_THRESHOLD, Match, compare, is_match, keys, score
from .parse import parse_name

__version__ = "0.1.0"
__all__ = [
    "compare", "score", "is_match", "keys", "parse_name",
    "Match", "NameIndex", "dedupe", "DEFAULT_THRESHOLD", "__version__",
]
