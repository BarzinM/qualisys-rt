import socket
import sys
import threading
import qtm
import struct
import errno
import inspect
import time


def lineno():
    return inspect.currentframe().f_back.f_lineno


class get6D(threading.Thread):

    def __init__(self, qtm_obj, messages,  condition):
        threading.Thread.__init__(self)
        self.condition = condition
        self.qt = qtm_obj
        self.count = len(self.qt.bodies)

    def run(self):
        while True:
            try:
                self.qt.getAttitude()
            except socket.error, e:
                if e[0] == errno.EBADF:
                    print 'Qualisys Getting Thread Terminated.'
                sys.exit(socket.error)
            except Exception, e:
                print 'Line @', lineno(), 'Error in get6D:', e
                raise e
                sys.exit(e)
            for i in range(self.count):
                pose_data_buffer = struct.pack('<B', 2)
                pose_data_buffer += struct.pack('<f',
                                                self.qt.bodies[i].linear_x)
                pose_data_buffer += struct.pack('<f',
                                                self.qt.bodies[i].linear_y)
                pose_data_buffer += struct.pack('<f',
                                                self.qt.bodies[i].angular_z)
                self.condition.acquire()
                if not messages[i]:
                    messages[i].append(pose_data_buffer)
                self.condition.notify()
                self.condition.release()


class sendToAgent(threading.Thread):

    def __init__(self, connection, msg, condition):
        threading.Thread.__init__(self)
        self.connection = connection
        self.msg = msg
        self.condition = condition
        self.peername = self.connection.getpeername()
        connection.setsockopt(socket.IPPROTO_TCP, socket.TCP_NODELAY, 1)

    def run(self):
        try:
            while True:
                self.condition.acquire()
                while True:
                    if self.msg:
                        msg = self.msg.pop()
                        break
                    self.condition.wait()

                self.condition.release()
                connection.sendall(msg)
        except socket.error, e:

            if e[0] == errno.EPIPE:
                print 'Connection Terminated From Host:', self.peername
            else:
                raise
        except Exception, e:
            print 'Error in sendToAgent():', e


def getIP():
    temp_sock = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
    temp_sock.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
    temp_sock.connect(('192.168.0.1', 0))
    ip_address = temp_sock.getsockname()[0]
    temp_sock.close()
    return ip_address


with qtm.QTMClient() as qt:
    qt.setup()
    number_of_bodies = len(qt.bodies)

    # Setting up server
    sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    sock.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
    sock.setsockopt(socket.IPPROTO_TCP, socket.TCP_NODELAY, 1)
    server_address = (getIP(), 1895)
    print >>sys.stderr, 'starting up on %s port %s' % server_address
    sock.bind(server_address)

    # Setting up recieving thread
    condition = threading.Condition()
    messages = [[] for i in range(number_of_bodies)]
    reciever = get6D(qt, messages, condition)
    reciever.daemon = True
    reciever.start()

    # Initialization for connection threads
    sock.listen(4)
    threads_list = []
    connections_list = []
    while True:
        try:
            # Accepting connections from agents
            print 'Waiting For Connection.'
            connection, address = sock.accept()
            agent_id = int(connection.getpeername()[0][8])
            print connection.getpeername(), 'ID:', agent_id, 'connected'
            connections_list.append(connection)

            # Starting a new thread for each new connection
            threads_list.append(
                sendToAgent(connection, messages[agent_id], condition))
            threads_list[-1].daemon = True
            threads_list[-1].start()

        except KeyboardInterrupt, e:
            print '\nProgram Terminated'
            break
            sys.exit(0)

        except Exception, e:
            raise
            sys.exit(e)

    sock.close()
    sys.exit(0)