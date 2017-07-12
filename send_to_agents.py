from __future__ import print_function
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

    def __init__(self, ip, number_of_bodies):
        self.qt = qtm.QTMClient(ip)
        self.number_of_bodies = self.qt.number_of_bodies
        # self.messages = [qtm.Body()] * number_of_bodies
        # self.conditions = [threading.Lock()] * number_of_bodies

    def run(self):
        # Setting up server
        sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        sock.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
        sock.setsockopt(socket.IPPROTO_TCP, socket.TCP_NODELAY, 1)
        server_address = (getIP(), 1895)
        sock.bind(server_address)
        sock.listen(3)

        # start receiving location of bodies from qualisys camera system
        reciever = threading.Thread(
            name='receiver', target=self.recieveLocations)
        reciever.daemon = True
        reciever.start()
        print('Waiting for connection from agents ...')
        while True:
            try:
                connection, address = sock.accept()
                print('Connection #%i to %s.'%(threading.activeCount()-1,connection.getpeername()[0]))

                # setup a new thread for sending to a new agent
                thrd = threading.Thread(
                    target=self.sendLocation, args=(connection,))
                thrd.daemon = True
                thrd.start()

            except KeyboardInterrupt as e:
                print('\nProgram Terminated by User.')
                break

            except Exception as e:
                logging.exception(e)
                raise

    def recieveLocations(self):
        while True:
            try:
                self.qt.getAttitude()
            except socket.error as e:
                logging.exception(e)
                if e[0] == errno.EBADF:
                    print('Qualisys Getting Thread Terminated.')
                raise
            except Exception as e:
                logging.exception(e)
                raise
            # for i in range(self.number_of_bodies):
            #     with self.conditions[i]:
            #         self.messages[i] = self.qt.bodies[i]

    def sendLocation(self, connection):
        # connection configuration
        self.peername = connection.getpeername()
        connection.setsockopt(socket.IPPROTO_TCP, socket.TCP_NODELAY, 1)
        try:
            while True:
                # receive the body_id that is requested by agent
                body_id = int(connection.recv(1))

                # send the state of the body with ID specified in body_id
                msg = self.qt.bodies[body_id].pack()
                connection.sendall(msg)
        except ValueError as e:
            print('Connection to %s terminated!'% self.peername[0],end=' ')
        except Exception as e:
            logging.exception(e)
            if e[0] == errno.EHOSTUNREACH:
                print('Connection to %s interrupted!' % self.peername[0],end=' ')
            elif e[0] == errno.ECONNRESET:
                print('Connection to %s terminated!'% self.peername[0],end=' ')
            else:
                raise
        print("%i left."%(threading.active_count()-3))


def lineno():
    return inspect.currentframe().f_back.f_lineno


if __name__ == '__main__':
    try:
        nav = QualisysLocalizer('192.168.0.21', 4)
    except KeyboardInterrupt as e:
        print('\nInitialization Incomplete! Exiting ...')
        sys.exit(e)
    nav.run()
