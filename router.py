from threading import Thread
import socket
import argparse
import selectors
import types


class Peer:
    _args = ""
    _available_commands = ['help', 'myip', 'myport', 'connect', 'list', 'terminate', 'send', 'exit']
    _input = None
    connections = []
    is_running = True
    sockets = []
    timeout = 2

    def __init__(self, port):
        """ Initialize Things"""
        self.server_sel = selectors.DefaultSelector()

        # Used to get the real ip address of this machine
        s = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
        s.connect(('8.8.8.8', 12000))
        self.my_ip = s.getsockname()[0]
        s.close()

        self.my_port = port
        # Run the server
        t = Thread(None, self.check_inbox)
        t.start()
        # Run the client
        self.run()
        exit(0)

    def run(self):
        try:
            while self.is_running:
                # events = self.client_sel.select(timeout=1)
                self._input = input(">> ")
                self._args = self._input.split(' ')
                if self._args[0] not in self._available_commands:
                    print("Invalid command '{}' - type 'help' to get the available commands".format(self._input))
                else:
                    getattr(self, 'func_' + self._args[0])()
        except KeyboardInterrupt:
            print("caught keyboard interrupt, exiting")

    def func_help(self):
        print("Command\t\t\t\t\tDescription")
        print("help\t\t\t\t\tPulls this up.")
        print("myyp\t\t\t\t\tPrints your computer's ip address.")
        print("myport\t\t\t\t\tPrints the port this program is communicating through.")
        print("connect<destination><port>\t\tCreates new connection to specified destination at the specified port.")
        print("list\t\t\t\t\tDisplays a numbered list of connections.")
        print("terminate<connection id>\t\tTerminates connection specified by id in numbered list of connections.")
        print("send<connection_id><message>\t\tSends message to specified peer by id in numbered list of connections.")
        print("exit\t\t\t\t\tCloses all connections and terminates this process.")

    def func_myip(self):
        print(f"My IP is {self.my_ip}")

    def func_myport(self):
        print(f"My Port is {self.my_port}")

    def func_connect(self):
        try:
            addr = (self._args[1], int(self._args[2]))
        except IndexError:
            print("You're missing some arguments for the connect command. Type help to see what arguments it requires.")
        else:
            if addr in self.connections:
                print("You are already connected to that peer. No duplicates allowed!")
                """ Comment this out if testing multiple user functionality on the same machine! """
            # elif addr[0] == self.my_ip:
            #     print("Self-connections are not allowed!")
            else:
                sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
                sock.setblocking(False)
                sock.connect_ex(addr)
                self.sockets.append(sock)
                self.connections.append(addr)

    def func_list(self):
        """ Print all active connections """
        print("ID\tIP Address\tPort No.")
        for i, conn in enumerate(self.connections):
            print(f"{i}:\t{conn[0]}\t{conn[1]}")

    def func_terminate(self):
        """ Close a connection specified by the connection id """
        try:
            idx = int(self._args[1])
        except IndexError:
            print("You're missing some arguments for the terminate command. Type help to see what arguments it requires.")
        else:
            try:
                self.sockets[idx].send(f"{self.my_ip} has terminated their connection!".encode())
                self.sockets[idx].close()
                self.sockets.pop(idx)
                self.connections.pop(idx)
                print(f"Terminated {self._args}")
            except IndexError:
                print(f"Index {idx} is not available. Type list to see what connections are available.")

    def func_send(self):
        """ Send a message to the specified connection. """
        try:
            idx = int(self._args[1])
        except IndexError:
            print("You're missing some arguments for the send command. Type help to see what arguments it requires.")
        else:
            message = " ".join(self._args[2:])
            try:
                self.sockets[idx].send(message.encode())
            except IndexError:
                print(f"Index {idx} is not available. Type list to see what connections are available.")

    def func_exit(self):
        """ Close all the connections and then exit. """
        # close all the sockets
        for s in self.sockets:
            s.send(f"{self.my_ip} has terminated their connection!".encode())
            s.close()
        self.is_running = False
        exit(0)
        print("after exit(0) in exit function")

    def accept_wrapper(self, sock):
        """ Helper function for the server. Accepts connections from peers. """
        conn, addr = sock.accept()  # Should be ready to read
        print('accepted connection from', addr)
        conn.setblocking(False)
        data = types.SimpleNamespace(addr=addr, inb=b'', outb=b'')
        events = selectors.EVENT_READ | selectors.EVENT_WRITE
        self.server_sel.register(conn, events, data=data)

    def service_server_connection(self, key, mask):
        """ Helps manage multiple connections at the same time """
        sock = key.fileobj
        data = key.data
        if mask & selectors.EVENT_READ:
            recv_data = sock.recv(1024)  # Should be ready to read
            if recv_data:
                data.outb += recv_data
            else:
                print("closing connection to", data.addr)
                self.server_sel.unregister(sock)
                sock.close()
        if mask & selectors.EVENT_WRITE:
            if data.outb:
                print(f"Message received from {data.addr[0]}")
                print(f"Sender's Port: {data.addr[1]}")
                print(f"{data.outb.decode()}")
                # print("echoing", repr(data.outb), "to", data.addr)
                try:
                    sent = sock.send(data.outb)  # Should be ready to write
                    data.outb = data.outb[sent:]

                    """ The following exceptions catch errors when a remote peer closes their connection.  """
                except ConnectionResetError:
                    pass
                except OSError:
                    pass

    def check_inbox(self):
        """ Where the server is hosted"""
        lsock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        # Avoid bind() exception: OSError: [Errno 48] Address already in use
        lsock.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
        lsock.bind(('0.0.0.0', int(self.my_port)))
        lsock.listen()
        lsock.setblocking(False)
        self.server_sel.register(lsock, selectors.EVENT_READ, data=None)
        try:
            while self.is_running:
                events = self.server_sel.select(timeout=1)
                for key, mask in events:
                    if key.data is None:
                        self.accept_wrapper(key.fileobj)
                    else:
                        self.service_server_connection(key, mask)
        except KeyboardInterrupt:
            print("caught keyboard interrupt, exiting")
        finally:
            self.server_sel.close()
        exit(0)


if __name__ == "__main__":
    parser = argparse.ArgumentParser()
    parser.add_argument("port", nargs=1)
    args = parser.parse_args()

    Peer(args.port[0])
