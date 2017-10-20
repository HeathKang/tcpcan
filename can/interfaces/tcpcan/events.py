"""
Different events can be sent and transmitted over the network connection.

Examples:
  * Messages
  * Exceptions
  * Transmit success
  * Transmit failure
  * ...
"""

import struct
import logging
import can

logger = logging.getLogger(__name__)

EXTENDED_BIT = 0x80000000


class BaseEvent(object):
    """Events should inherit this class."""

    def encode(self):
        """Convert event data to bytes.

        :return:
            Bytestring representing the event data.
        :rtype: bytes
        """
        return b''

    @classmethod
    def from_buffer(cls, buf):
        """Parse the data and return a new event.

        :param bytes buf:
            Bytestring representing the event data.

        :return:
            Event decoded from buffer.

        :raise can.interfaces.remote.events.NeedMoreDataError:
            If not enough data exists.
        """
        return cls()

    def __len__(self):
        return len(self.encode())

    # Useful for tests
    def __eq__(self, other):
        return (self.__class__ == other.__class__ and
                self.__dict__ == other.__dict__)


class CanMessage(BaseEvent):
    """CAN message being received or transmitted.

    +--------+-------+--------------------------------------------------------+
    | Byte   | Type  | Contents                                               |
    +========+=======+========================================================+
    | 0 - 7  | F64   | Timestamp                                              |
    +--------+-------+--------------------------------------------------------+
    | 8 - 11 | U32   | Arbitration ID                                         |
    +--------+-------+--------------------------------------------------------+
    | 12     | U8    | DLC                                                    |
    +--------+-------+--------------------------------------------------------+
    | 13     | U8    | Flags:                                                 |
    |        |       |  - Bit 0: Extended ID                                  |
    |        |       |  - Bit 1: Remote frame                                 |
    |        |       |  - Bit 2: Error frame                                  |
    +--------+-------+--------------------------------------------------------+
    | 14 - 21| U8    | Data padded to an 8 byte array                         |
    +--------+-------+--------------------------------------------------------+
    """

    #: Event ID
    EVENT_ID = 3

    _STRUCT = struct.Struct('>Bi8s')
    _EXT_FLAG = 0x80
    _REMOTE_FRAME_FLAG = 0x40
    _ERROR_FRAME_FLAG = 0x40

    def __init__(self, msg):
        """
        :param can.Message msg:
            A Message object.
        """
        #: A :class:`can.Message` instance.
        self.msg = msg

    def encode(self):
        """
        package data like this
        flags | id  | data
        --------------------
        1     | 4  |  8
        :return: 
        """

        flags = 0
        length = len(self.msg.data)
        if self.msg.id_type:
            flags |= self._EXT_FLAG
        if self.msg.is_remote_frame:
            flags |= self._REMOTE_FRAME_FLAG
        if self.msg.is_error_frame:
            flags |= self._ERROR_FRAME_FLAG

        flags |= length
        buf = self._STRUCT.pack(flags,
                                self.msg.arbitration_id,
                                bytes(self.msg.data))
        return buf

    @classmethod
    def from_buffer(cls, buf):
        try:
            flags, arb_id, data = cls._STRUCT.unpack_from(buf)
            dlc = flags & 0x0f
            timestamp = 0
        except struct.error:
            raise NeedMoreDataError()

        msg = can.Message(timestamp=timestamp,
                          arbitration_id=arb_id,
                          extended_id=bool(flags & cls._EXT_FLAG),
                          is_remote_frame=bool(flags & cls._REMOTE_FRAME_FLAG),
                          is_error_frame=bool(flags & cls._ERROR_FRAME_FLAG),
                          dlc=dlc,
                          data=data[:dlc])
        return cls(msg)

    def __len__(self):
        return self._STRUCT.size


class ConnectionClosed(BaseEvent):
    """Connection closed by peer.

    Will be automatically emitted if the socket is closed.
    """

    #: Event ID
    EVENT_ID = 255


class NeedMoreDataError(Exception):
    """There is not enough data yet."""
    pass
