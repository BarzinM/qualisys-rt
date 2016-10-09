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


def getIP():
    # Get the IP address of the computer executing this file
    temp_sock = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
    temp_sock.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
    temp_sock.connect(('192.168.0.1', 0))
    ip_address = temp_sock.getsockname()[0]
    temp_sock.close()
    return ip_address


class QualisysLocalizer(object):

    def __init__(self, number_of_bodies):
        self.qt = qtm.QTMClient()
        self.qt.setup()
        self.number_of_bodies = number_of_bodies
        self.messages = [qtm.body()] * number_of_bodies
        self.conditions = [threading.Condition()] * number_of_bodies
        pass

    def run(self):
        # Setting up server
        sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        sock.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
        sock.setsockopt(socket.IPPROTO_TCP, socket.TCP_NODELAY, 1)
        server_address = (getIP(), 1895)
        print >>sys.stderr, 'starting up on %s port %s' % server_address
        sock.bind(server_address)
        sock.listen(self.number_of_bodies)
        print 'Ready for agents.'

        # start receiving location of bodies from qualisys camera system
        reciever = threading.Thread(name='reciever', target=self.recieveLocations)
        reciever.daemon = True
        reciever.start()
        while True:
            try:
                print '------------------------------------------------'
                print 'Waiting For Connection.'
                connection, address = sock.accept()
                print connection.getpeername(), 'connected'

                # setup a new thread for sending to a new agent
                thrd = threading.Thread(target=self.sendLocation, args=(connection,))
                thrd.daemon = True
                thrd.start()
                print 'Number of running threads:', threading.activeCount()

            except KeyboardInterrupt, e:
                print '\nProgram Terminated by User.'
                break

            except Exception, e:
                logging.exception(e)
                raise

    def recieveLocations(self):
        while True:
            try:
                self.qt.getAttitude()
            except socket.error, e:
                logging.exception(e)
                if e[0] == errno.EBADF:
                    print 'Qualisys Getting Thread Terminated.'
                raise
            except Exception, e:
                logging.exception(e)
                raise
            for i in range(self.number_of_bodies):
                with self.conditions[i]:
                    self.messages[i] = self.qt.bodies[i]
                    self.conditions[i].notifyAll()

    def sendLocation(self, connection):
        # connection configuration
        self.peername = connection.getpeername()
        connection.setsockopt(socket.IPPROTO_TCP, socket.TCP_NODELAY, 1)
        try:
            while True:
                # recieve the body_id that is requested by agent
                body_id = int(connection.recv(1))

                # send the state of the body with ID specified in body_id
                with self.conditions[body_id]:
                    self.conditions[body_id].wait()
                    msg = self.messages[body_id].pack()
                connection.sendall(msg)
        except ValueError, e:
            print 'Connection terminated by', self.peername
            sys.exit()
        except Exception, e:
            logging.exception(e)
            print 'Error in sendToAgent():', e
            raise


def lineno():
    return inspect.currentframe().f_back.f_lineno


class get6D(threading.Thread):

    def __init__(self, qtm_obj):
        threading.Thread.__init__(self)
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
                conditions.notify()
                conditions.release()


class sendToAgent(threading.Thread):

    def __init__(self, index):
        threading.Thread.__init__(self)
        self.index = index
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

if __name__ == '__main__':
    nav = QualisysLocalizer(5)
    nav.run()


# with qtm.QTMClient() as qt:
#     qt.setup()
#     number_of_bodies = len(qt.bodies)

# Setting up server
#     sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
#     sock.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
#     sock.setsockopt(socket.IPPROTO_TCP, socket.TCP_NODELAY, 1)
#     server_address = (getIP(), 1895)
#     print >>sys.stderr, 'starting up on %s port %s' % server_address
#     sock.bind(server_address)

# Setting up recieving thread
#     conditions = threading.Condition()
#     messages = [[]] * 4
#     reciever = get6D(qt)
#     reciever.daemon = True
#     reciever.start()

# Initialization for connection threads
#     sock.listen(4)
#     threads_list = []
#     connections_list = [[]] * 4
#     while True:
#         try:
# Accepting connections from agents
#             print 'Waiting For Connection.'

#             connection, address = sock.accept()
#             agent_id = int(connection.getpeername()[0][8]) - 1
#             print connection.getpeername(), 'ID:', agent_id + 1, 'connected'

#             print 'agent id:', agent_id, 'connections list:', connections_list
#             connections_list[agent_id] = connection

# Starting a new thread for each new connection
#             threads_list.append(sendToAgent(agent_id))
#             threads_list[-1].daemon = True
#             threads_list[-1].start()

#         except KeyboardInterrupt, e:
#             print '\nProgram Terminated by User.'
#             break
#             sys.exit(0)

#         except Exception, e:
#             logging.exception(e)
#             raise
#             sys.exit(e)

#     sock.close()
#     sys.exit(0)
