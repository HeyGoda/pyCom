import serialimport structimport osimport timeimport loggingimport sys
def crc16_compute(buf, length):    crc = 0xffff    for i in range(length):        c = buf[i] & 0x00ff        crc = crc ^ c;        for j in range(8):             if (crc & 0x0001) > 0:                crc = crc >> 1                crc = crc ^ 0xA001             else:                crc = crc >> 1    crc = (crc>>8) + (crc<<8)    return crc&0xffff
def ser_init(port):    ser = serial.Serial()    ser.baudrate = 115200    ser.port=
