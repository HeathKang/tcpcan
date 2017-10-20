"""
can is an object-orient Controller Area Network interface module.
"""
from __future__ import absolute_import

import logging

__version__ = "2.0.0-beta.1"

log = logging.getLogger('can')

rc = dict()


class CanError(IOError):
    pass


from can.util import set_logging_level

from can.message import Message
from can.bus import BusABC
from can.interfaces import VALID_INTERFACES
from . import interface

