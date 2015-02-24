import socket
import sys
import struct
from lxml import etree
from time import sleep


class body(object):

    def __init__(self):
        self.id = 0
        self.name = ''
        self.linear_x = []
        self.linear_y = []
        self.linear_z = []
        self.angular_x = []
        self.angular_y = []
        self.angular_z = []

    def setAll(self, attitude_list):
        if len(attitude_list) != 6:
            print 'setAll(): Size of array should be 6.'
            return
        self.linear_x, self.linear_y, self.linear_z,\
            self.angular_x, self.angular_y, self.angular_z = attitude_list

    def getAll(self):
        return self.__dict__


class QTMClient(object):

    """A Client For Qualisys Track Manager.

    Banana banana banana

    Example:
        with QTMClient() as qt:
            qt.connect()
            qt.getPacket()
            qt.sendCommand('Version 1.1')
            qt.getPacket()

    Attributes:
        sock (socket.socket)

    Public Methods:
        connect([string ip_address])
        getPacket()
        sendCommand(string command)
        getAttitude()
    """

    def __enter__(self):
        # Create a TCP/IP socket
        self.sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        self.bodies = []
        self.control=[]
        return self

    def __exit__(self, exc_type, exc_value, traceback):
        print 'Closing The Connection To QTM RT.'
        self.sock.close()
        if exc_type is not None:
            print exc_type, exc_value, traceback
            # return False # uncomment to pass exception through

    def getAttitude(self):
        self.getPacket()
        self.sendCommand('GetCurrentFrame 6DEuler')

    def setup(self):
        self.connect()
        self.sendCommand('Version 1.1')
        self.sendCommand('getparameters 6D')
        if not self.bodies:
            sys.exit('setup(): No defined bodies were introduced by QTM')

    def connect(self, ip_address='192.168.0.21'):
        # Connect the socket to the port where the server is listening
        server_address = (ip_address, 22223)
        print >>sys.stderr, 'Connecting To %s Port %s' % server_address
        self.sock.connect(server_address)
        self.sock.settimeout(3)
        response = self.sock.recv(1024)
        if 'QTM RT Interface connected' in response:
            print 'Connetction Established'
        else:
            sys.exit('Could not connect to Qualisys')

    def __getHeader(self):
        try:
            data = self.sock.recv(8)
            packet_length = struct.unpack('<I', data[:4])[0]
            packet_type = struct.unpack('<I', data[4:])[0]
            # print 'Packet Length:', packet_length
            # print 'Packet Type:', packet_type
            return packet_length - 8, packet_type
        except socket.timeout:
            print 'Connection Timed Out: No Buffer To Read'
            return None, None
        except Exception, e:
            print '!!!!!!!!! Hey! Fix This ->', e
            sys.exit(e)

    def sendCommand(self, command):
        packet_length = 8 + len(command)
        packet_type = 1
        buf = struct.pack('<I', packet_length) + \
            struct.pack('<I', packet_type) + command
        self.sock.sendall(buf)
        self.getPacket()

    def getPacket(self):
        data_length, packet_type = self.__getHeader()
        self.control=data_length
        if data_length is None:
            return
        if packet_type == 0:
            self.__displayData(data_length)
        elif packet_type == 1:
            self.__displayData(data_length)
        elif packet_type == 2:
            self.__parseXML(data_length)
        elif packet_type == 3:
            print data_length,'Control var:',self.control
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


    def __parseXML(self, data_length):
        sleep(1)
        response = ''
        chunck_limit = 1024
        while data_length > chunck_limit:
            response += self.sock.recv(chunck_limit)
            data_length -= chunck_limit
        if data_length > 0:
            response += self.sock.recv(data_length)
        else:
            print '!!!!!!!!! fix parseXML in qtm shitforbrains.gif'
        parser = etree.XMLParser(recover=True)
        root = etree.fromstring(response, parser=parser)
        number_of_bodies = root[0][0].text
        number_of_bodies = int(root.find('The_6D').find('Bodies').text)
        self.bodies = [body() for temp in range(number_of_bodies)]
        print 'Bodies Defined In QTM Project:',
        for i in range(number_of_bodies):
            self.bodies[i].id = i
            self.bodies[i].name = root.find(
                'The_6D').findall('Body')[i].find('Name').text
            print self.bodies[i].name,
        print

    def __parseData(self, data_length):
        # print 'Data Packet Length:', data_length
        data = self.sock.recv(data_length)
        # time_stamp = struct.unpack('<Q', data[:8])[0]
        # frame_number = struct.unpack('<I', data[8:12])[0]
        component_count = struct.unpack('<I', data[12:16])[0]
        # print 'Time Stamp Is:', time_stamp
        # print 'Frame Count Is:', frame_number
        print 'Number Of Components In Data Packet:', component_count
        self.control -=24
        bytes_parsed = 16
        for i in range(component_count):
            size_data = data[bytes_parsed:bytes_parsed + 4]
            component_size = struct.unpack('<I', size_data)[0]
            print "comp size",component_size, 'control var 345',self.control
            type_data = data[bytes_parsed + 4:bytes_parsed + 8]
            component_type = struct.unpack('<I', type_data)[0]
            print "component_type",component_type
            component_data = data[
                bytes_parsed + 8:bytes_parsed + component_size]
            # print 'Component Size:', component_size
            # print 'Component Type:', component_type
            if component_type == 6:
                self.__sixDofEulerParser(component_data)
            else:
                print '!!!!!!!!!!!!!!!!!!!!!!!!! fix this fucker'
            bytes_parsed += component_size

    def __sixDofEulerParser(self, data):
        body_count = struct.unpack('<I', data[:4])[0]
        self.control -=16
        # drop_rate = struct.unpack('<H', data[4:6])[0]
        # unsync_rate = struct.unpack('<H', data[6:8])[0]
        print 'Body Count:', body_count
        # print '2D Drop Rate:', drop_rate
        # print '2D Out Of Sync Rate:', unsync_rate
        bytes_parsed = 8
        for i in range(body_count):
            self.control-=24
            position_x = struct.unpack(
                '<f', data[bytes_parsed:bytes_parsed + 4])[0]
            position_y = struct.unpack(
                '<f', data[bytes_parsed + 4:bytes_parsed + 8])[0]
            position_z = struct.unpack(
                '<f', data[bytes_parsed + 8:bytes_parsed + 12])[0]
            euler_x = struct.unpack(
                '<f', data[bytes_parsed + 12:bytes_parsed + 16])[0]
            euler_y = struct.unpack(
                '<f', data[bytes_parsed + 16:bytes_parsed + 20])[0]
            euler_z = struct.unpack(
                '<f', data[bytes_parsed + 20:bytes_parsed + 24])[0]
            bytes_parsed += 24
            attitude_list = position_x, position_y, position_z, euler_x, euler_y, euler_z
            self.bodies[i].setAll(attitude_list)
            print(self.bodies[i].getAll()['linear_x'])
            print 'CV',self.control,'parsed',bytes_parsed
        print data[bytes_parsed:]

    def __displayData(self, data_length):
        response = self.sock.recv(data_length)
        print response

    def __parseNoData(self):
        print 'No Data Available In QTM'

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
        print 'Event #' + str(event_number) + ':', event_list[event_number]
