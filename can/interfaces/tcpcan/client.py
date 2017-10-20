import logging
import socket
import select
import can
from can.interfaces.tcpcan import events
from can.interfaces.tcpcan import connection


logger = logging.getLogger(__name__)


def create_connection(address):
    address = address.split(':')
    if len(address) >= 2:
        address = (address[0], int(address[1]))
    else:
        address = (address[0], can.interfaces.remote.DEFAULT_PORT)
    return socket.create_connection(address)


class TcpcanBus(can.bus.BusABC):
    """CAN bus over a network connection bridge."""

    def __init__(self, channel, can_filters=None, **config):
        """
        :param str channel:
            Address of server as host:port (port may be omitted).

        :param list can_filters:
            A list of dictionaries each containing a "can_id" and a "can_mask".

            >>> [{"can_id": 0x11, "can_mask": 0x21}]

            The filters are handed to the actual CAN interface on the server.

        :param int bitrate:
            Bitrate in bits/s to use on CAN bus. May be ignored by the interface.

        Any other backend specific configuration will be silently ignored.
        """
        self.conn = connection.Connection()
        #: Socket connection to the server
        self.socket = create_connection(channel)
        # Disable Nagle algorithm for better real-time performance
        self.socket.setsockopt(socket.IPPROTO_TCP, socket.TCP_NODELAY, 1)

        self.channel = channel

    def _next_event(self, timeout=None):
        """Block until a new event has been received.

        :param float timeout: Max time in seconds to wait.
        :return: Next event received from socket (or None if timeout)
        """
        event = self.conn.next_event()
        while event is None:
            if timeout is not None and not select.select([self.socket], [], [], timeout)[0]:
                return None
            data = self.socket.recv(13)
            self.conn.receive_data(data)
            event = self.conn.next_event()
        return event

    def recv(self, timeout=None):
        """Block waiting for a message from the Bus.

        :param float timeout: Seconds to wait for a message.

        :return:
            None on timeout or a Message object.
        :rtype: can.Message
        """
        event = self._next_event(timeout)
        if isinstance(event, events.CanMessage):
            return event.msg
        elif isinstance(event, events.RemoteException):
            raise event.exc
        elif isinstance(event, events.ConnectionClosed):
            raise CanRemoteError("Server closed connection unexpectedly")
        return None

    def send(self, msg, timeout=None):
        """Transmit a message to CAN bus.

        :param can.Message msg: A Message object.
        :raises can.interfaces.remote.CanRemoteError:
            On failed transmission to socket.
        """
        self.send_event(events.CanMessage(msg))

    def send_event(self, event):
        self.conn.add_send_data(event)
        try:
            self.socket.sendall(self.conn.next_data())
        except OSError as e:
            raise CanRemoteError(str(e))

    def send_periodic(self, message, period, duration=None):
        return CyclicSendTask(self, message, period, duration)

    def shutdown(self):
        """Close socket connection."""
        # Give threads a chance to finish up
        logger.debug('Closing connection to server')
        self.socket.shutdown(socket.SHUT_WR)
        while not isinstance(self._next_event(1), events.ConnectionClosed):
            pass
        self.socket.close()
        logger.debug('Network connection closed')

class CanRemoteError(can.CanError):
    """An error occurred on socket connection or on the remote end."""
