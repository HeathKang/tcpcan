## tcpcan
### Description
tcpcan is a library to transmit or send messages via TCP method.
Forked by [python-can](https://github.com/hardbyte/python-can).So
 if you want to use more interfaces such as USBcan, Socketcan, you can
 see [python-can](https://github.com/hardbyte/python-can)



### Usage
```python
import tcpcan


bus = tcpcan.interface.Bus(bustype='tcpcan', channel="192.168.1.10:4001")
msg = tcpcan.Message(arbitration_id=id,
                      data=data,
                      extended_id=False,
                      is_remote_frame=False,
                      )
# send a meassage
bus.send(msg)

# receive a meassage
recv_msg = bus.recv()

