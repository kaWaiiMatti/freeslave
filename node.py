from time import time


class Node:
    def __init__(self, data):
        self.ip = data['ip']
        self.port = data['port']
        self.last_active = data['last_active'] if 'last_active' in data.keys() else int(time())

    def __str__(self):
        return 'node {}:{}'.format(self.ip, self.port)

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
        return True