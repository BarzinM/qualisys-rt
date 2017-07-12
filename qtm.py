from __future__ import print_function
import socket
import sys
import struct
from lxml import etree
from numpy import pi
from bs4 import BeautifulSoup

degree_to_rad = pi / 180


class Body(object):

    def __init__(self, id=0, name=''):
        self.id = id
        self.name = name
        self.states = []
        self.linear_x = []
        self.linear_y = []
        self.linear_z = []
        self.angular_x = []
        self.angular_y = []
        self.angular_z = []

    def setAll(self, attitude_list):
        assert len(attitude_list)==6
        self.states = attitude_list

    def pack(self):
        packed_buffer = struct.pack('<B6f', self.id, *self.states)
        return packed_buffer

    def unpack(self, packed_buffer):
        self.states = struct.unpack('<6f', packed_buffer)

    def getAll(self):
        return self.__dict__


class QTMClient(object):

    """A Client For Qualisys Track Manager.

    Example:
        with QTMClient() as qt:
            qt.setup()
            qt.getAttitude()
            print(qt.getBody(0)['linear_x'])

    Attributes:
        bodies (list): An Array Of Body() Objects. Each Object Contain
            Information Recieved From Qualisys Addressing That Object.
        sock (socket.socket): Handling The Configurations Of The Connection
            With Qualisys Track Manager.
        control (int): A Variable To Check Complete Reception Of Packets.

    Public Methods:
        getAttitude()
        command(string command)
        setup([string ip_address])
    """

    def __init__(self, ip):
        self.sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        self.bodies = []
        self.control = []
        self.connect(ip)
        self.command('Version 1.9')
        self.command('getparameters 6D')
        if not self.bodies:
            sys.exit('setup(): No Defined Bodies Were Introduced By QTM')

    def __enter__(self, ip):
        # Create a TCP/IP socket
        self.sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        self.bodies = []
        self.control = []
        return self

    def close(self):
        print('Closing The Connection To QTM RT.')
        self.sock.close()
        print('QTM Connection Closed Successfully.')

    def __exit__(self, exc_type, exc_value, traceback):
        if exc_type is not None and exc_value[0] is not 0:
            print(exc_type, exc_value, traceback)
        self.close()

    def getBody(self, id):
        return self.bodies[id].getAll()

    def getAttitude(self):
        self.command('GetCurrentFrame 6DEuler')

    def connect(self, ip_address='192.168.0.21'):
        # Connect the socket to the port where the server is listening
        server_address = (ip_address, 22223)
        print('Connecting to QTM at %s on %s ... ' % server_address,end='')
        try:
            self.sock.connect(server_address)
            response = self.sock.recv(1024)
        except socket.error as e:
            print(e, '\nConnection Could Not Be Established. Check Qualisys Server.')
            sys.exit(0)
        self.sock.settimeout(3)
        if 'QTM RT Interface connected' in response:
            print('OK')
        else:
            sys.exit('Could Not Connect To Qualisys')

    def __getHeader(self):
        while True:
            try:
                data = self.sock.recv(8)
                packet_length = struct.unpack('<I', data[:4])[0]
                packet_type = struct.unpack('<I', data[4:])[0]
                return packet_length - 8, packet_type
            except socket.timeout:
                print('Connection Timed Out: No Buffer To Read')
                continue
            except Exception as e:
                print('!!!!!!!!! Hey! Fix This ->')
                raise
                sys.exit(e)
            break

    def command(self, command):
        packet_length = 8 + len(command)
        packet_type = 1
        buf = struct.pack('<I', packet_length) + \
            struct.pack('<I', packet_type) + command
        self.sock.sendall(buf)
        self.__getPacket()

    def __getPacket(self):
        data_length, packet_type = self.__getHeader()
        self.control = data_length
        if data_length is None:
            return
        if packet_type == 0:
            self.__displayData(data_length)
        elif packet_type == 1:
            self.__displayData(data_length)
        elif packet_type == 2:
            self.__parseXML()
        elif packet_type == 3:
            self.__parseData(data_length)
        elif packet_type == 4:
            self.__parseNoData()
        elif packet_type == 5:
            self.__displayData(data_length)
        elif packet_type == 6:
            self.__parseEvent()
        elif packet_type == 7:
            self.__displayData(data_length)
        elif packet_type == 8:
            self.parseFile(data_length)
        if self.control:
            print('Control Var:', self.control)
            sys.exit('Bad Packet Sizing')

    def __parseXML(self):
        response = ''
        while self.control > 0:
            recieved = self.sock.recv(1024)
            response += recieved
            self.control -= len(recieved)
        data = BeautifulSoup(response, "lxml")
        self.number_of_bodies = int(data.find('bodies').contents[0])
        names = [t.contents[0].encode("ascii") for t in data.find_all('name')]
        self.bodies = [Body(i, names[i]) for i in range(self.number_of_bodies)]

    def __parseData(self, data_length):
        data = self.sock.recv(data_length)
        component_count = struct.unpack('<I', data[12:16])[0]
        self.control -= 16
        bytes_parsed = 16
        for i in range(component_count):
            size_data = data[bytes_parsed:bytes_parsed + 4]
            component_size = struct.unpack('<I', size_data)[0]
            type_data = data[bytes_parsed + 4:bytes_parsed + 8]
            component_type = struct.unpack('<I', type_data)[0]
            component_data = data[
                bytes_parsed + 8:bytes_parsed + component_size]
            if component_type == 6:
                self.__sixDofEulerParser(component_data)
            else:
                print('!!!!!!!!!!!!!!!!!!!!!!!!! fix this fucker')
            bytes_parsed += component_size

    def __sixDofEulerParser(self, data):
        body_count = struct.unpack('<I', data[:4])[0]
        self.control -= 16
        bytes_parsed = 8
        for i in range(body_count):
            self.control -= 24
            position_x, position_y, position_z, euler_x, euler_y, euler_z = struct.unpack(
                '<6f', data[bytes_parsed:bytes_parsed + 24])
            bytes_parsed += 24
            attitude_list = position_x / 1000, position_y / 1000, position_z / 1000, euler_x * degree_to_rad,\
                euler_y * degree_to_rad, euler_z * degree_to_rad
            self.bodies[i].setAll(attitude_list)

    def __displayData(self, data_length):
        response = self.sock.recv(data_length)
        self.control -= len(response)
        print(response)

    def __parseNoData(self):
        print('No Data Available In QTM')

    def __parseEvent(self):
        event = self.sock.recv(1)
        event_list = {1: 'Connected',
                      2: 'Connection Closed',
                      3: 'Capture Started',
                      4: 'Capture Stopped',
                      6: 'Calibration Started',
                      7: 'Calibration Stopped',
                      8: 'RT From File Started',
                      9: 'RT From File Stopped',
                      10: 'Waiting For Trigger',
                      11: 'Camera Settings Changed',
                      12: 'QTM Shutting Down',
                      13: 'Capture Saved'}
        event_number = struct.unpack('B', event)[0]
        print('Event #' + str(event_number) + ':', event_list[event_number])
