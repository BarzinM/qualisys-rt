import socket
import sys
import struct


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
    """

    def __init__(self):
        # Create a TCP/IP socket
        self.sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)

    def __enter__(self):
        # Create a TCP/IP socket
        self.sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        return self

    def __exit__(self, exc_type, exc_value, traceback):
        print 'Closing The Connection To QTM RT.'
        self.sock.close()
        if exc_type is not None:
            print exc_type, exc_value, traceback
            # return False # uncomment to pass exception through

    def connect(self, ip_address='192.168.0.21'):
        # Connect the socket to the port where the server is listening
        server_address = (ip_address, 22223)
        print >>sys.stderr, 'Connecting To %s Port %s' % server_address
        self.sock.connect(server_address)
        self.sock.settimeout(3)
        print 'Connetction Established'

    def __getHeader(self):
        try:
            data = self.sock.recv(8)
            packet_length = struct.unpack('<I', data[:4])[0]
            packet_type = struct.unpack('<I', data[4:])[0]
            print 'Packet Length:', packet_length
            print 'Packet Type:', packet_type
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

    def getPacket(self):
        data_length, packet_type = self.__getHeader()
        if data_length is None:
            return
        if packet_type == 0:
            self.__displayData(data_length),
        elif packet_type == 1:
            self.__displayData(data_length),
        elif packet_type == 2:
            self.__displayData(data_length),
        elif packet_type == 3:
            self.__parseData(data_length),
        elif packet_type == 4:
            self.__parseNoData(),
        elif packet_type == 5:
            self.__displayData(data_length),
        elif packet_type == 6:
            self.__parseEvent(),
        elif packet_type == 7:
            self.__displayData(data_length),
        elif packet_type == 8:
            self.parseFile(data_length)

    def __parseData(self, data_length):
        print 'Data Packet Length:', data_length
        data = self.sock.recv(data_length)
        time_stamp = struct.unpack('<Q', data[:8])[0]
        frame_number = struct.unpack('<I', data[8:12])[0]
        component_count = struct.unpack('<I', data[12:16])[0]
        print 'Time Stamp Is:', time_stamp
        print 'Frame Count Is:', frame_number
        print 'Number Of Components In Data Packet:', component_count
        bytes_parsed = 16
        for i in range(component_count):
            size_data = data[bytes_parsed:bytes_parsed + 4]
            component_size = struct.unpack('<I', size_data)[0]
            type_data = data[bytes_parsed + 4:bytes_parsed + 8]
            component_type = struct.unpack('<I', type_data)[0]
            component_data = data[
                bytes_parsed + 8:bytes_parsed + component_size]
            print 'Component Size:', component_size
            print 'Component Type:', component_type
            if component_type == 6:
                self.__sixDofEulerParser(component_data)
            bytes_parsed += component_size

    def __sixDofEulerParser(self, data):
        body_count = struct.unpack('<I', data[:4])[0]
        drop_rate = struct.unpack('<H', data[4:6])[0]
        unsync_rate = struct.unpack('<H', data[6:8])[0]
        print 'Body Count:', body_count
        print '2D Drop Rate:', drop_rate
        print '2D Out Of Sync Rate:', unsync_rate
        bytes_parsed = 8
        for i in range(body_count):
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
            print 'Body #' + str(i) + ':', position_x, position_y, position_z,\
                euler_x, euler_y, euler_z

    def __displayData(self, data_length):
        print '### Qualisys Says:', self.sock.recv(data_length)

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


with QTMClient() as qt:
    qt.connect()
    qt.getPacket()
    qt.sendCommand('Version 1.9')
    qt.getPacket()
    qt.sendCommand('GetState')
    qt.getPacket()
    qt.sendCommand('GetCurrentFrame 6DEuler')
    qt.getPacket()
    qt.getPacket()

print "Done"
