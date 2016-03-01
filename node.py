from time import time


class Node:
    def __init__(self, data):
        self.ip = data['ip']
        self.port = data['port']
        self.last_active = data['last_active'] if 'last_active' in data.keys() else int(time())

    def __str__(self):
        return 'node {}:{}'.format(self.ip, self.port)

    def __eq__(self, other):
        return self.ip == other.ip and self.port == other.port

    def updateLastActive(self):
        self.last_active = int(time())
        return True

    def getSinceLastActive(self):
        return int(time()) - self.last_active

    def getDict(self):
        return {'ip':self.ip, 'port':self.port, 'last_active':int(self.last_active)}

    @staticmethod
    def validateNodeData(data):
        if type(data) is not dict:
            return False
        if 'ip' not in data.keys():
            return False
        if type(data['ip']) is not str:
            return False
        if(len(data['ip']) < 5):
            return False
        if 'port' not in data.keys():
            return False
        if type(data['port']) is not int:
            return False
        if 'nodes' not in data.keys():
            return False
        if type(data['nodes']) is not list:
            return False
        for node in data['nodes']:
            if type(node) is not dict:
                return False
            if 'ip' not in node.keys():
                return False
            if type(node['ip']) is not str:
                return False
            if(len(node['ip']) < 5):
                return False
            if 'port' not in node.keys():
                return False
            if type(node['port']) is not int:
                return False
        return True