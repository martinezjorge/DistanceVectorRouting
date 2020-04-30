from threading import Thread
import socket
import argparse
import selectors
import types
import json
from helper import read_topology_file
import time
import pandas as pd
import numpy as np

class Router:
    _args = ""
    _available_commands = ['help',
                           'myip',
                           'myport',
                           # 'connect',
                           # 'list',
                           'terminate',
                           'disable', # calls terminate
                           # 'send',
                           'exit',
                           'crash', # calls exit + neighbors must set link costs to infinity

                           'update', # modifies the local routing table
                           'step', # send routing table to all neighbors
                           'packet', # show number of routing tables received since last 'packet' command input
                           'display',
                           'server',
                           ]
    _input = None
    connections = []
    is_running = True
    update_interval = float('inf')
    sockets = {}
    timeout = 2
    send_request = False
    packet_count = 0

    def __init__(self, id, port):
        """ Initialize Things"""
        self.id = id
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
                if hasattr(self, 't0') and (time.time() - self.t0 > self.update_interval):
                    # periodic send
                    self.func_step()
                    self.t0 = time.time()

                # elif self.send_request:
                #     # when another server requests for the routing table
                #     self.send_table_to_neighbor()

                else:
                    # handle user input
                    self._input = input("{}>> ".format(self.id if hasattr(self, 'id') else ''))
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
        print("myip\t\t\t\t\tPrints your computer's ip address.")
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

    def func_server(self):
        self.filepath = "{}/topology{}.json".format(self._args[2], self.id)
        self.update_interval = float(self._args[4])
        self.id, self.routing_table, self.neighbors, data = read_topology_file(self.filepath)
        self.num_servers = data['num_servers']

        print("Read table:\n{}".format(self.routing_table))
        for ip, port in zip(self.routing_table['ip'], self.routing_table['port']):
            self.connect(ip, port)
        self.t0 = time.time()

    def connect(self, ip, port):
        '''Connect to single server'''
        sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        sock.setblocking(False)
        sock.connect_ex((ip, int(port)))
        self.set_socket(ip, port, sock)

    def get_socket(self, ip, port):
        _addr = ":".join([ip, str(port)])
        if _addr not in self.sockets:
            print("Socket not created")
            return None
        return self.sockets[_addr]

    def set_socket(self, ip, port, socket):
        _addr = ":".join([ip, port])
        self.sockets[_addr] = socket

    def get_server_ix(self, ip, port):
        return self.routing_table.query("ip == @ip & port == @port").index[0]

    def func_display(self):
        print(self.routing_table)

    def terminate(self, ip, port):
        s = self.get_socket(ip, port)
        if s is not None:
            s.close()
        self.set_socket(ip, port, None)

    def func_disable(self):
        server_ix = self._args[1]
        if server_ix in self.neighbors:
            ip = self.routing_table.at[server_ix, 'ip']
            port = self.routing_table.at[server_ix, 'port']
            self.terminate(ip, port)
        else:
            print("{} is not a neighbors".format(server_ix))

    def func_exit(self):
        """ Close all the connections and then exit. """
        # close all the sockets
        for s in self.sockets:
            # s.send(f"{self.my_ip} has terminated their connection!".encode())
            s.close()
        # self.is_running = False
        # exit(0)
        print("after exit(0) in exit function")

    def func_crash(self):
        self.func_exit()

    def func_update(self):
        server_from, server_to, cost = self._args[1], self._args[2], float(self._args[3])
        self.routing_table.at[server_from, server_to] = cost

    def func_step(self):
        print("Step function")
        # Send routing table to all neighbors
        for server_ix in self.neighbors:
            ip = self.routing_table.at[server_ix, 'ip']
            port = self.routing_table.at[server_ix, 'port']
            self.send_table(ip, port)

    def send_table(self, ip, port):
        socket = self.get_socket(ip, port)
        if socket is not None:
            message = {
                'type': 'table',
                'id': self.id,
                'data': self.routing_table.to_json()
            }
            message = json.dumps(message)
            print("Sending to {}".format(self.get_server_ix(ip, port)))
            socket.send(message.encode())
        else:
            print("Trying to send message to unexisting socket {}:{}".format(ip, port))

        # """ Send a message to the specified connection. """
        # try:
        #     idx = int(self._args[1])
        # except IndexError:
        #     print("You're missing some arguments for the send command. Type help to see what arguments it requires.")
        # except ValueError:
        #     print("Don't forget to put an integer specifying who you are sending the message to!")
        # else:
        #     message = " ".join(self._args[2:])
        #     try:
        #         self.sockets[idx].send(message.encode())
        #     except IndexError:
        #         print(f"Index {idx} is not available. Type list to see what connections are available.")

    def func_packets(self):
        print("Received {} packets".format(self.packet_count))
        self.packet_count = 0

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
            try:
                recv_data = sock.recv(1024)  # Should be ready to read
            except ConnectionResetError:
                recv_data = False

            if recv_data:
                data.outb += recv_data
            else:
                '''exit, update local df with infinity'''
                _ip, _port = data.addr[0], data.addr[1]
                print("closing connection to {}:{}".format(_ip, _port))
                server_ix = self.routing_table.query('ip == @_ip & recv_port == @_port')
                self.routing_table.at[self.id, server_ix] = float('inf')

                self.server_sel.unregister(sock)
                sock.close()
        if mask & selectors.EVENT_WRITE:
            if data.outb:
                # print(f"Message received from {data.addr[0]}")
                # print(f"Sender's Port: {data.addr[1]}")
                message = json.loads(data.outb.decode())

                server_ix = int(message['id'])
                self.routing_table.at[server_ix, 'recv_port'] = data.addr[1]

                if message['type'] == 'table':
                    # receiving a table
                    new_table = pd.read_json(message['data'])
                    new_table.fillna(float('inf'), inplace=True)
                    print("Received from Server {}".format(message['id']))
                    self.update(server_ix, new_table)
                    self.packet_count += 1

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

    # Update functions

    def _dist(self, target):
        new_dist = []
        for n in range(self.num_servers):
            cost = self.routing_table.at[self.id, n]
            dist_to = self.routing_table.at[n, target]
            new_dist.append(cost + dist_to)
        return min(new_dist)

    def update(self, inc_node, new_table):
        # set current info to incoming
        # print("Local\n{}\nReceived from {}\n{}".format(self.routing_table, inc_node, new_table))
        for i in range(self.num_servers):
            self.routing_table.at[inc_node, i] = new_table.at[inc_node, str(i)]
        # update info
        for c in range(self.num_servers):
            self.routing_table.at[self.id, c] = self._dist(c)
        print("After update we have:\n{}".format(self.routing_table))

if __name__ == "__main__":
    parser = argparse.ArgumentParser()
    parser.add_argument("id", nargs=1)
    parser.add_argument("port", nargs=1)
    args = parser.parse_args()

    Router(args.id[0], args.port[0])
