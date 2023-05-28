import rospy
import serial
import struct
from std_msgs.msg import UInt8
from copy import deepcopy
import pdb
# ctypes is imported to create a string buffer
import ctypes
import numpy as np

SIZE = 5  # bytes after head 

## Steve says make a custom message to hold 2 named items: altitude, m (float) and SNR (UInt8)
# create blank msg to populate instead of the zeros list + deepcopies
# next interpret the msg as a struct (builtin package) 
# sensor is format string '>H'
# convert int from tuple to float through conversion to meters, stuff into msg


def decodePacket(packet):
    check = 0x00
    for item in packet[:-1]:
        check += item
    check &= 0xFF
    if check == packet[-1]:
        print(packet)
        # size = struct.calcsize('HHHH')
        # buff = ctypes.create_string_buffer(size)
        # buff = struct.pack_into('HHHH', buff, *packet)
        # tmp = struct.unpack('HHHH', packet)
        print(np.uint16(packet[2]) << 8)
        print(np.uint16(packet[1]))
        alt = (np.uint16(packet[2]) << 8) + np.uint16(packet[1])
        snr = packet[-2]
        print(alt, snr)
        if snr > 13:
            return (1, alt, snr)
        else: 
            error_msg = 'altimeter SNR below manufacturer-defined minimum threshold (13dB); packet dumped'
            rospy.loginfo(error_msg)
            return (0,)
    else:
        error_msg = 'decoding checksum failed; packet dumped'
        rospy.loginfo(error_msg)
        return (0,) 


def talker():
    pub = rospy.Publisher('chatter', UInt8, queue_size=10)
    rospy.init_node('ainstein_usd1', anonymous=True)
    rate = rospy.Rate(100) # 100hz

    port = rospy.get_param('port', '/dev/ttyUSB0')
    device = serial.Serial(port=port, baudrate=115200, timeout=0.5)

    blank_packet = [0 for _ in range(SIZE)]
    packet = deepcopy(blank_packet)
    # pdb.set_trace()
    head_flag = 0
    while not rospy.is_shutdown():
        val = device.read()  # figure out how this interacts with timeout
        if val == b'\xfe':
            # pdb.set_trace()
            # for i in range(SIZE):
            #     val = device.read()
            #     print(val)
            #     if val == b'\xfe':
            #         head_flag = 1
            #     elif val == b'\x02' and head_flag:
            #         error_msg = 'unexpected head character before we filled the buffer; packet dumped'
            #         rospy.loginfo(error_msg)
            #         head_flag = 0
            #         packet = deepcopy(blank_packet)
            #         break
            val = device.read(SIZE)
            packet = np.frombuffer(val, dtype=np.uint8)

            # decode the packet; pass to subroutine which calls struct 
            ret = decodePacket(packet)
            if ret[0]:
                pub.publish()
            rate.sleep()
        else:
            pass


if __name__ == '__main__':
    try:
        talker()
    except rospy.ROSInterruptException: pass