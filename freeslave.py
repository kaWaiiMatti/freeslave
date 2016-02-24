from node import Node

class FreeSlave:
    def __init__(self, ip, port):
        self.ip = ip
        self.port = port

        self.nodes = []
        self.nodes.append(Node({'ip':self.ip, 'port':self.port}))

        self._packages = []
        self._max_packages = 10 #TODO: determine value for this

    def getOwnNodeData(self):
        return {'ip': self.ip, 'port': self.port}

    def addNode(self, data):
        for node in self.nodes:
            if node.ip == data['ip'] and node.port == data['port']:
                print('Node already exists!')
                return False
        self.nodes.append(Node(data))
        return True

    def getOtherNodes(self):
        other_nodes = []
        for node in self.nodes:
            if node.ip != self.ip and node.port != self.port:
                other_nodes.append(node)
        return other_nodes

    def getPackageBufferLeft(self):
        return self._max_packages - len(self._packages)

    # TEST METHODS
    def printNodes(self):
        for node in self.nodes:
            print(node)

