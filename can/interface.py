from __future__ import absolute_import

import can
import importlib

from can.util import load_config

# interface_name => (module, classname)
BACKENDS = {
    'tcpcan':           ('can.interfaces.tcpcan', 'TcpcanBus'),
}


class Bus(object):
    """
    Instantiates a CAN Bus of the given `bustype`, falls back to reading a
    configuration file from default locations.
    """

    @classmethod
    def __new__(cls, other, channel=None, *args, **kwargs):
        """
        Takes the same arguments as :class:`can.BusABC` with the addition of:

        :param kwargs:
            Should contain a bustype key with a valid interface name.

        :raises:
            NotImplementedError if the bustype isn't recognized
        :raises:
            ValueError if the bustype or channel isn't either passed as an argument
            or set in the can.rc config.

        """
        config = load_config(config={
            'interface': kwargs.get('bustype'),
            'channel': channel
        })

        if 'bustype' in kwargs:
            # remove the bustype so it doesn't get passed to the backend
            del kwargs['bustype']
        interface = config['interface']
        channel = config['channel']

        # Import the correct Bus backend
        try:
            (module_name, class_name) = BACKENDS[interface]
        except KeyError:
            raise NotImplementedError("CAN interface '{}' not supported".format(interface))

        try:
            module = importlib.import_module(module_name)
        except Exception as e:
            raise ImportError(
                "Cannot import module {} for CAN interface '{}': {}".format(module_name, interface, e)
            )
        try:
            cls = getattr(module, class_name)
        except Exception as e:
            raise ImportError(
                "Cannot import class {} from module {} for CAN interface '{}': {}".format(
                    class_name, module_name, interface, e
                )
            )

        return cls(channel, **kwargs)

