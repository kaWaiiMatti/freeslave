from node import Node
from task_md5 import Md5HashTask, Md5HashPackage
import json


class FreeSlave:
    tasks_filename = 'tasks.dat'

    def __init__(self, ip, port):
        self.ip = ip
        self.port = port

        self.nodes = []
        self.nodes.append(Node({'ip':self.ip, 'port':self.port}))

        self.last_task_id = 0
        self.tasks = []

        self._packages = []
        self._max_packages = 10 #TODO: determine value for this

        self.load_tasks()

    def write_tasks(self):
        f = open(FreeSlave.tasks_filename, 'w')
        tasks = []
        for task in self.tasks:
            tasks.append(task.getDict(include_packages=True))
        f.write(json.dumps(tasks))
        f.close()

    def load_tasks(self):
        try:
            f = open(FreeSlave.tasks_filename, 'r')
            data = json.loads(f.read())
            f.close()
            for task in data:
                temp_task = Md5HashTask(ip=self.ip, port=self.port, target_hash=task['target_hash'], task_id=task['task_id'], max_length=task['max_length'], create_packages=False)
                for package in task['packages']:
                    temp_task.packages.append(Md5HashPackage(package)) #TODO: finish this
                self.addTask(temp_task)
        except FileNotFoundError:
            pass

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
        return True

    def removeTask(self, id):
        for task in self.tasks:
            if task.task_id == id:
                self.tasks.remove(task)
                self.write_tasks()
                for package in self._packages:
                    if package.related_task == id:
                        self._packages.remove(package)
                return True
        return False

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

