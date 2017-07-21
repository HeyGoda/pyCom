import serial
import struct
import os
import time
import logging
import sys

def crc16_compute(buf, length):
    crc = 0xffff
    for i in range(length):
        c = buf[i] & 0x00ff
        crc = crc ^ c;
        for j in range(8):
            if (crc & 0x0001) > 0:
                crc = crc >> 1
                crc = crc ^ 0xA001
            else:
                crc = crc >> 1
    crc = (crc>>8) + (crc<<8)
    return crc&0xffff

class myClass(object):
    def __init__(self, port):
        self.ser = serial.Serial()
        self.ser.baudrate = 115200
        self.ser.port=port
        self.ser.timeout = 2

    def download(self, filename):
        ser = self.ser
        try:
            ser.open()
        except serial.SerialException as e:
            logging.error("Could not open serial port {}: {}".format(ser.name, e))
            sys.exit(1)
        
        try:
            fo = open(filename, 'rb')
        except IOError as e:
            logging.error("Could not open file {}: {}".format(filename, e))
            sys.exit(1)
        filesize = os.path.getsize(filename)
        file_cnt = filesize/2048
        if filesize%2048 > 0:
            file_cnt = file_cnt + 1
        
        ps_index = 0
        while True:
            ps = fo.read(512)
            if len(ps) > 0:
                ps_index = ps_index + 1
                pack = []
                pack.append((file_cnt >> 8) & 0xff)
                pack.append(file_cnt & 0xff)
                pack.append((ps_index >> 8) & 0xff)
                pack.append(ps_index & 0xff)
                pack.append((len(ps) >> 8) & 0xff)
                pack.append(len(ps) & 0xff)
                for i in ps:
                    b = struct.unpack('B', i)
                    pack.append(b[0])
                
                checksum = crc16_compute(pack, len(pack))
                pack.append(checksum & 0xff)
                pack.append((checksum >> 8) & 0xff)
                
                while True:
                    #send packet to MCU
                    for i in pack:
                        b = struct.pack('B', i)
                        ser.write(b)
                        
                    #wait ack packet
                    packack = ser.read(7)
                    if len(packack) > 0:
                        b = []
                        for i in packack:
                            b.append(struct.unpack('B', i))
                        if b[4][0] == 0x11:
                            break #success ack
                    #time.sleep(0.2)
            else:
                fo.close()
                ser.close()

if __name__ == '__main__':
    up = myClass(sys.argv[1])
    up.download_bin(sys.argv[2])
    exit(0)
