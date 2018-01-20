#!/usr/bin/python
#coding=utf-8

import struct
import os
import time
import logging
import sys
import threading
import Queue
import serial
import serial.tools.list_ports  

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

def ser_download_bin(port, filename):
    ser = serial.Serial()
    ser.baudrate = 115200
    ser.port=port
    ser.timeout = 2
    try:
        ser.open()
    except serial.SerialException as e:
        logging.error("Error: Could not open serial port {}: {}".format(ser.name, e))
        sys.exit(1)
    
    try:
        fo = open(filename, 'rb')
    except IOError as e:
        logging.error("Error: Could not open file {}: {}".format(filename, e))
        sys.exit(1)
    filesize = os.path.getsize(filename)
    file_cnt = filesize/2048
    if filesize%2048 > 0:
        file_cnt = file_cnt + 1
    
    ps_index = 0
    while True:
        ps = fo.read(2048)
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
                        print "\n\t%s Downloading......%d/%d"%(ser.name, ps_index, file_cnt),
                        break #success ack
                #time.sleep(0.2)
        else:
            print "\n\t%s Downloading......Done."%(threading.current_thread().name)
            fo.close()
            ser.close()
            break

def parse_com(com_arr):
    if isinstance(com_arr, list) == False:
        return []

    #列出系统可用的串口
    port_list = list(serial.tools.list_ports.comports())  
    port_arr = []
    for port_list_e in port_list:
        port_list_i =list(port_list_e)  
        port_arr.append(port_list_i[0])

    #找出传入参数中可用的串口号
    ret_arr = []
    for com_arr_e in com_arr:
        com_up = com_arr_e.upper()
        if com_up in port_arr and com_up not in ret_arr:
            ret_arr.append(com_up)
    return ret_arr

def parse_file(file_arr):
    ret_file = None
    #找出参数列表中第一个存在的文件名
    if isinstance(file_arr, list):
        for file_arr_e in file_arr:
            if os.path.isfile(file_arr_e):
                ret_file = file_arr_e
    
    return ret_file

def usage(pro):
    print "Usage:\n\t%s [serial COM port] [.bin file]"%pro
    
if __name__ == '__main__':
    comLists = parse_com(sys.argv)
    downFile = parse_file(sys.argv)
    if comLists == None or downFile == None:
        usage(sys.argv[0])
        exit(0)

    logging.basicConfig(filename='./pymhs335.log', filemode='w')
    
    th_lists = []
    for com in comLists:
        th_lists.append(threading.Thread(target=ser_download_bin, name=com, args=(com, downFile,)))
    for th in th_lists:
        th.start()
    for th in th_lists:
        th.join()
        
    exit(0)
