import socket
import sys
import threading
import qtm
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
                # receive the body_id that is requested by agent
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


if __name__ == '__main__':
    try:
        nav = QualisysLocalizer(5)
    except KeyboardInterrupt as e:
        print '\nInitialization Incomplete! Exiting ...'
        sys.exit(e)
    nav.run()
