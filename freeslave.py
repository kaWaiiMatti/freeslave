from http import client
from node import Node
from task_md5 import Md5HashTask, Md5HashPackage
from time import time, sleep
import os
import json


class FreeSlave:
    tasks_filename = 'tasks.dat'
    inactive_process_time_limit = 60
    known_package_types = [Md5HashPackage]

    def __init__(self, ip, port):
        self.ip = ip
        self.port = port

        self.nodes = []
        self.nodes.append(Node({'ip':self.ip, 'port':self.port}))

        self.last_task_id = 0
        self.tasks = []

        self._packages = []
        self._max_packages = 10 #TODO: determine value for this

        self._max_workers = 1

        self.load_tasks()

    def write_tasks(self):
        f = open(FreeSlave.tasks_filename, 'w')
        tasks = []
        for task in self.tasks:
            tasks.append(task.getDict(include_packages=True))
        f.write(json.dumps({'last_task_id':self.last_task_id, 'tasks':tasks}))
        f.close()

    def load_tasks(self):
        try:
            f = open(FreeSlave.tasks_filename, 'r')
            data = json.loads(f.read())
            f.close()
            self.last_task_id = data['last_task_id']
            for task in data['tasks']:
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

    def register_to_node(self, node):
        connection = client.HTTPConnection(node.ip, node.port)
        other_nodes = []
        for other_node in self.getOtherNodes():
            other_nodes.append(other_node.getDict())
        for i in range(3):
            connection.request("POST", "/api/nodes", json.dumps({'ip':self.ip, 'port':self.port, 'nodes':other_nodes}))
            response = connection.getresponse()
            if response.status == 200:
                received_nodes = bytes.decode(response.read())
                return True

    def addNode(self, data):
        for node in self.nodes:
            if node.ip == data['ip'] and node.port == data['port']:
                return False
        self.nodes.append(Node(data))
        print('Added new node {}:{}'.format(data['ip'], data['port']))
        return True

    def addTask(self, task):
        #TODO: make checking global, not specific to md5hashtask
        for item in self.tasks:
            if item.task_id == task.task_id:
                print('Task with id {} already exists!'.format(task.task_id))
                return False
            if item.target_hash == task.target_hash and item.max_length >= task.max_length:
                print('Task with same target_hash and same or greater max_length already exists!')
                return False
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

    def get_active_worker_count(self):
        current_time = int(time())
        count = 0

        for package in self._packages:
            if package.last_active == None:
                continue
            if (current_time - package.last_active) > FreeSlave.inactive_process_time_limit:
                package.last_active = None
                package.process_id = None
            if package.last_active is not None:
                count = count + 1

        return count

    def start_worker(self):
        if len(self._packages) == 0:
            print('Empty package list!')
            return False

        if self.get_active_worker_count() >= self._max_workers:
            print('Max number of workers running already!')
            return False

        print('Worker count:{}'.format(self.get_active_worker_count()))

        for package in self._packages:
            if package.last_active == None and package.process_id == None:
                if type(package) not in FreeSlave.known_package_types:
                    print('Unknown package type:{}'.format(type(package)))
                    continue

                package.update_last_active()

                newpid = os.fork()
                if newpid == 0:
                    #Worker process code
                    node = client.HTTPConnection(self.ip, self.port)
                    for i in range(3):
                        node.request("POST", "/api/processes", json.dumps({'process_id':os.getpid(), 'assigner_ip':package.assigner_ip, 'assigner_port':package.assigner_port, 'task_id':package.task_id, 'package_identifier':package.start_string}))
                        response = node.getresponse()
                        if response.status == 204:
                            result = package.getResult()
                            os._exit(0)

                    #TODO: package.getResult()
                    #TODO: post result to assigner
                    #TODO: unregister process

                    #End of worker process code

                return True
        print('Could not find packages to be started!')
        return False

    def delegate_packages(self):
        if len(self.tasks) == 0:
            print('No tasks to delegate!')
            return False
        packages = self.get_packages(lock_packages=False)
        if packages is None:
            print('No packages available!')
            return False
        for node in self.nodes:
            if node.ip == self.ip and node.port == self.port:
                buffer = self.getPackageBufferLeft()
                if buffer == 0:
                    continue
                packages = self.get_packages(max_count=buffer)
                self.set_assigned_to_packages(node=node, packages=packages)
                for package in packages:
                    self._packages.append(package)
                continue

            #TODO: finish this and test that it works!
            connection = client.HTTPConnection(node.ip, node.port)
            connection.request("GET", "/api/packages/{}/{}".format(self.ip, self.port))
            response = connection.getresponse()
            if response.status == 200:
                node.updateLastActive()
                data = json.loads(response.read())
            else:
                print('something went wong... :(')
            #node.request("POST", "/api/processes", json.dumps({'process_id':newpid, 'assigner_ip':package.assigner_ip, 'assigner_port':package.assigner_port, 'task_id':package.task_id, 'package_identifier':package.start_string}))

    def convert_to_dict(self, list):
        items = []
        for item in list:
            items.append(item.getDict())
        return items

    def set_assigned_to_packages(self, node, packages):
        for package in packages:
            found = False
            for task in self.tasks:
                for task_package in task.packages:
                    if task_package.assigner_ip == package.assigner_ip and task_package.assigner_port == package.assigner_port and task_package.task_id == package.task_id and task_package.start_string == package.start_string:
                        task_package.assign_to(node)
                        found = True
                    if found:
                        break
                if found:
                    break

    def get_packages(self, lock_packages = True, max_count = 10):
        packages = []
        for task in self.tasks:
            for package in task.packages:
                if package.assigned_ip == None:
                    if lock_packages:
                        package.assign_to(Node({'ip':'locked', 'port':'locked'}))
                    packages.append(package)
                    if len(packages) >= max_count:
                        return packages
            if len(packages) > 0:
                return packages
        return None

    @staticmethod
    def validate_package_get_request(data):
        if type(data) is not dict:
            return False
        if 'ip' not in data.keys():
            return False
        if type(data['ip']) is not str:
            return False
        if len(data['ip']) < 5:
            return False
        if 'port' not in data.keys():
            return False
        if type(data['port']) is not int:
            return False
        return True

    @staticmethod
    def validate_register_worker_data(data):
        if type(data) is not dict:
            return False
        if 'assigner_ip' not in data.keys():
            return False
        if type(data['assigner_ip']) is not str:
            return False
        if 'assigner_port' not in data.keys():
            return False
        if type(data['assigner_port']) is not int:
            return False
        if 'process_id' not in data.keys():
            return False
        if type(data['process_id']) is not int:
            return False
        if 'task_id' not in data.keys():
            return False
        if type(data['task_id']) is not int:
            return False
        if 'package_identifier' not in data.keys():
            return False
        if type(data['package_identifier']) is not str:
            return False
        return True

    # TEST METHODS
    def printNodes(self):
        for node in self.nodes:
            print(node)

