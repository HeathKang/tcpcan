import struct
import logging
from can.interfaces.tcpcan import events


log = logging.getLogger(__name__)


class Connection(object):
    """A connection handles buffering of raw data received from e.g. a socket
    and converts the data stream to a stream of events.

    Received events can be iterated over using this class.
    """
    def __init__(self):
        self._send_buf = bytearray()
        self._recv_buf = bytearray()
        #: Indicates if the sender has closed the connection
        self.closed = False
        self.HEART_BEAT = bytes([0xaa,0x00, 0xff, 0x00, 0x00,0x00, 0x00, 0x00, 0x00, 0x00,0x00, 0x00, 0x55])

    def receive_data(self, buf):
        """Feed data received from source.

        :param buf:
            A bytes-like object. If empty, the connection is considered closed.
        """
        if not buf:
            self.closed = True
        else:
            if buf!= self.HEART_BEAT:
                self._recv_buf += buf
            else:
                log.debug('Tcp CAN eceived heart beat data!')

    def add_send_data(self, event):
        """Convert event to data that can be transmitted as bytes.

        :param event:
            Event to be sent
        """
        data = event.encode()
        self._send_buf += data

    def next_data(self):
        """Get next set of data to be transmitted.

        The internal send buffer will be cleared.

        :return:
            A bytes-like object.
        """
        data = self._send_buf
        self._send_buf = bytearray()
        return data

    def next_event(self):
        """Get next event, if any.

        :return:
            An event object or None if not enough data exists.
        """
        if not self._recv_buf:
            if self.closed:
                return events.ConnectionClosed()
            return None

        #event_id = self._recv_buf[0]
        # if any recv data
        if self._recv_buf:

            try:
                # process data through right cls
                Event = events.CanMessage
            except Exception as e:
                raise e
            try:
                # cls convert data to msg method
                event = Event.from_buffer(self._recv_buf[0:])
            except events.NeedMoreDataError:
                return None

        # Remove processed data from buffer
        del self._recv_buf[:1+len(event)]
        return event

    def data_ready(self):
        """Check if there is data to transmit.

        :rtype: bool
        """
        return len(self._send_buf) > 0

    def __iter__(self):
        """Allow iteration on events in the buffer.

            >>> for event in conn:
            ...     print(event)

        :yields: Event objects.
        """
        while True:
            event = self.next_event()
            if event is None:
                break
            yield event


