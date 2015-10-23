import socket
import sys
import threading
import qtm
import struct
import errno
import inspect
import logging

logging.basicConfig(filename='send_to_agents.log', format=50 * '=' +
                    '\n%(asctime)s %(message)s', level=logging.DEBUG)


def lineno():
    return inspect.currentframe().f_back.f_lineno


class get6D(threading.Thread):

    def __init__(self, qtm_obj):
        threading.Thread.__init__(self)
        # self.condition = condition
        self.qt = qtm_obj
        self.count = len(self.qt.bodies)

    def run(self):
        while True:
            try:
                self.qt.getAttitude()
            except socket.error, e:
                logging.exception(e)
                if e[0] == errno.EBADF:
                    print 'Qualisys Getting Thread Terminated.'
                sys.exit(socket.error)
            except Exception, e:
                logging.exception(e)
                print 'Line @', lineno(), 'Error in get6D:', e
                raise
                sys.exit(e)
            # print '--------------------'
            pose_data_buffer = struct.pack('<B', 2)
            for i in range(self.count):
                pose_data_buffer += struct.pack('<f',
                                                self.qt.bodies[i].linear_x)
                pose_data_buffer += struct.pack('<f',
                                                self.qt.bodies[i].linear_y)
                pose_data_buffer += struct.pack('<f',
                                                self.qt.bodies[i].linear_z)
                pose_data_buffer += struct.pack('<f',
                                                self.qt.bodies[i].angular_x)
                pose_data_buffer += struct.pack('<f',
                                                self.qt.bodies[i].angular_y)
                pose_data_buffer += struct.pack('<f',
                                                self.qt.bodies[i].angular_z)
            for i in range(self.count):
                conditions.acquire()
                if not messages[i]:
                    messages[i] = pose_data_buffer
                # if self.qt.bodies[i].linear_x!=struct.unpack('<f', pose_data_buffer[1:5])[0]:
                #     print ' found one'
                # print i, self.qt.bodies[i].angular_x, self.qt.bodies[i].angular_z
                conditions.notify()
                conditions.release()


class sendToAgent(threading.Thread):

    def __init__(self, index):
        threading.Thread.__init__(self)
        # self.connection = connection
        self.index = index
        # messages = msg
        # self.conditions = conditions
        self.peername = connections_list[index].getpeername()
        connections_list[index].setsockopt(socket.IPPROTO_TCP, socket.TCP_NODELAY, 1)

    def run(self):
        try:
            while True:
                conditions.acquire()
                while True:
                    if messages[self.index]:
                        msg = messages[self.index]
                        messages[self.index] = []
                        print self.index, struct.unpack('<f', msg[1:5])[0]
                        break
                    conditions.wait()

                conditions.release()
                connections_list[self.index].sendall(msg)
        except socket.error, e:
            if e[0] == errno.EPIPE:
                print 'Connection Terminated From Host:', self.peername
            elif e[0] == errno.ECONNRESET:
                print 'Connection reset by peer:', self.peername
            else:
                print 'something new happened'
                logging.exception(e)
        except IOError, e:
            if e[0] == errno.EPIPE:
                print 'The socket has been closed by client.'
        except Exception, e:
            logging.exception(e)
            print 'Error in sendToAgent():', e
            raise
        else:
            logging.exception(Exception)


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
    conditions = threading.Condition()
    messages = [[]] * 4
    reciever = get6D(qt)
    reciever.daemon = True
    reciever.start()

    # Initialization for connection threads
    sock.listen(4)
    threads_list = []
    connections_list = [[]] * 4
    while True:
        try:
            # Accepting connections from agents
            print 'Waiting For Connection.'

            connection, address = sock.accept()
            agent_id = int(connection.getpeername()[0][8]) - 1
            print connection.getpeername(), 'ID:', agent_id + 1, 'connected'

            # agent_id = 0 # SHOULD BE REMOVED LATER
            # print 'number of bodies sent by qualisys: ', len(messages)

            print 'agent id:', agent_id, 'connections list:', connections_list
            connections_list[agent_id] = connection

            # Starting a new thread for each new connection
            threads_list.append(sendToAgent(agent_id))
            threads_list[-1].daemon = True
            threads_list[-1].start()

        except KeyboardInterrupt, e:
            print '\nProgram Terminated by User.'
            break
            sys.exit(0)

        except Exception, e:
            logging.exception(e)
            raise
            sys.exit(e)

    sock.close()
    sys.exit(0)
