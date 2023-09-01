"""
qingque.hylab
~~~~~~~~~~~~~
The Hoyo API wrapper in Python.

Mostly based on the genshin.py library, everything is rewritten
to be more suitable for this project since the genshin.py library
is too bloated for my taste.

:copyright: (c) 2023-present naoTimesdev, (c) 2021-present sadru (genshin.py)
:license: MIT, see LICENSE for more details.
"""

from . import models
from .client import *
from .constants import *
from .ds import *
