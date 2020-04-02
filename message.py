# Jorge Martinez


class Message:
    """

        Work in progress

        Message that routers will use to update their routing tables.

    """

    def __init__(self,
                 update_fields,
                 server_port,
                 server_ip,
                 server_ip_address_n,
                 server_port_n,
                 server_id_n,
                 cost_n):

        self._update_fields = update_fields
        self._server_port = server_port
        self._server_ip = server_ip
        self._server_ip_address_n = server_ip_address_n
        self._server_port_n = server_port_n
        self._server_id_n = server_id_n
        self._cost_n = cost_n

    @property
    def server_port(self):
        return self._server_port

    @server_port.setter
    def server_port(self, value):
        if value < 0:
            raise ValueError("Negative Port Numbers are not allowed!")
        elif value < 1200:
            raise ValueError("Port numbers less than 1200 are reserved ports!")
        self._server_port = value

    @property
    def server_ip(self):
        return self._server_ip

    @server_ip.setter
    def server_ip(self, value):
        self._server_ip = value

    @property
    def server_ip_address_n(self):
        return self._server_ip_address_n

    @server_ip_address_n.setter
    def server_ip_address_n(self, value):
        self._server_ip_address_n = value

    @property
    def server_port_n(self):
        return self._server_port_n

    @server_port_n.setter
    def server_port_n(self, value):
        self._server_port_n = value

    @property
    def server_id_n(self):
        return self._server_id_n

    @server_id_n.setter
    def server_id_n(self, value):
        self._server_id_n = value

    @property
    def cost_n(self):
        return self._cost_n

    @cost_n.setter
    def cost_n(self, value):
        self._cost_n = value
