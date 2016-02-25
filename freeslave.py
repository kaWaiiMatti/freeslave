from node import Node
from task_md5 import Md5HashTask
import json


class FreeSlave:
    def __init__(self, ip, port):
        self.ip = ip
        self.port = port

        self.nodes = []
        self.nodes.append(Node({'ip':self.ip, 'port':self.port}))

        self.last_task_id = 0
        self.tasks = []

        self._packages = []
        self._max_packages = 10 #TODO: determine value for this

    def write_tasks(self):
        f = open('tasks.dat', 'w')
        tasks = []
        for task in self.tasks:
            tasks.append(task.getDict(include_packages=True))
        f.write(json.dumps(tasks))
        f.close()

    def getOwnNodeData(self):
        return {'ip': self.ip, 'port': self.port}

    def getTaskId(self):
        self.last_task_id = self.last_task_id + 1
        return self.last_task_id

    def addNode(self, data):
        for node in self.nodes:
            if node.ip == data['ip'] and node.port == data['port']:
                print('Node already exists!')
                return False
        self.nodes.append(Node(data))
        return True

    def addTask(self, task):
        #TODO: check if task already exists
        self.tasks.append(task)
        self.write_tasks()
        print('There are {} tasks in queue.'.format(len(self.tasks)))
        return True

    def addResult(self, data):
        #TODO: check if task id and others match and add result
        #TODO: remove not found result from task from the beginning
        self.write_tasks()
        return True

    def addPackage(self, package):
        self._packages.append(package)
        return True

    def getOtherNodes(self):
        other_nodes = []
        for node in self.nodes:
            if node.ip != self.ip and node.port != self.port:
                other_nodes.append(node)
        return other_nodes

    def getPackageBufferLeft(self):
        return self._max_packages - len(self._packages) if len(self._packages) < self._max_packages else 0

    # TEST METHODS
    def printNodes(self):
        for node in self.nodes:
            print(node)

