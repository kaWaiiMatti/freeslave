import os
import json
import logging
import requests

from node import Node
from task_md5 import MD5HashTask, MD5HashPackage
from time import time, sleep

CONN_STRING = "http://{}:{}{}"  # http://ip:port/route
logger = logging.getLogger(__name__)


class FreeSlave:
    logging.basicConfig(
        level=logging.DEBUG,
        format="%(asctime)s [%(levelname)s] %(name)s: %(message)s"
    )

    tasks_filename = 'tasks.dat'
    inactive_process_time_limit = 60
    known_package_types = [MD5HashPackage]

    def __init__(self, ip, port):
        self.ip = ip
        self.port = port

        self.nodes = []
        self.node = Node({'ip': self.ip, 'port': self.port})
        self.nodes.append(self.node)

        self.last_task_id = 0
        self.tasks = []

        self.packages = []
        self._max_packages = 10

        self._max_workers = 1

        self.results_since_delegate = 0
        self.delegate_packages_threshold = 3

        self.load_tasks()

    def write_tasks(self):
        tasks = []
        for task in self.tasks:
            tasks.append(task.get_dict(include_packages=True))
        with open(FreeSlave.tasks_filename, "w") as f:
            f.write(json.dumps(
                {'last_task_id': self.last_task_id, 'tasks': tasks}
            ))

    def load_tasks(self):
        try:
            f = open(FreeSlave.tasks_filename, 'r')
            data = json.loads(f.read())
            f.close()
            self.last_task_id = data['last_task_id']
            for task in data['tasks']:
                if task['type'] == 'md5hashtask':
                    temp_task = MD5HashTask(
                        ip=self.ip,
                        port=self.port,
                        target_hash=task['target_hash'],
                        task_id=task['task_id'],
                        max_length=task['max_length'],
                        result=task['result'],
                        create_packages=False
                    )
                    for package in task['packages']:
                        temp_task.packages.append(MD5HashPackage(package))
                    self.add_task(temp_task)
                # implement other task types here
                else:
                    logger.error("Trying to load invalid task type!")
                    continue
        except IOError:
            pass

    def get_own_node_data(self):
        return {'ip': self.ip, 'port': self.port}

    def get_task_id(self):
        self.last_task_id += 1
        return self.last_task_id

    def remove_working_packages(self, task_id):
        for package in self.packages:
            if package.assigner_ip == self.ip and package.assigner_port == self.port and package.task_id == task_id and package.process_id is None:
                self.packages.remove(package)

    def register_to_node(self, node):
        logger.debug('registering to: {}'.format(node))
        other_nodes = []
        for other_node in self.get_other_nodes():
            logger.debug('enter')
            other_nodes.append(other_node.get_dict())
        logger.debug('other nodes: {}'.format(other_nodes))
        uri = CONN_STRING.format(node.ip, node.port, "/api/nodes")
        payload = {
            'ip': self.ip,
            'port': self.port,
            'nodes': other_nodes
        }
        for i in range(3):
            try:
                response = requests.post(uri, json=payload)
            except (requests.ConnectionError, requests.HTTPError,
                    requests.Timeout) as e:
                logger.debug("Error while connecting to host: {}".format(e))
                self.remove_node(node)
                return False
            if response.status_code == 200:
                received_nodes = response.json()["nodes"]
                new_nodes = []
                for received_node in received_nodes:
                    if self.add_node(received_node):
                        new_nodes.append(Node(received_node))
                for new_node in new_nodes:
                    self.register_to_node(new_node)
                return True
        return False

    def add_node(self, data):
        new_node = Node(data)
        for node in self.nodes:
            if node == new_node:
                return False
        self.nodes.append(new_node)
        logger.debug(
            'Added new node {}:{}'.format(new_node.ip, new_node.port)
        )
        return True

    def remove_node(self, removable_node):
        return self.nodes.remove(removable_node)

    def add_task(self, task):
        # TODO: make checking global, not specific to md5hashtask
        for item in self.tasks:
            if item.task_id == task.task_id:
                logger.debug(
                    'Task with id {} already exists!'.format(task.task_id)
                )
                return False
            if item.target_hash == task.target_hash \
                    and item.max_length >= task.max_length:
                logger.debug(
                    'Task with same target_hash '
                    'and same or greater max_length already exists!'
                )
                return False
        self.tasks.append(task)
        self.write_tasks()
        return True

    def remove_task(self, task_id):
        for task in self.tasks:
            if task.task_id == task_id:
                self.tasks.remove(task)
                self.write_tasks()
                for package in self.packages:
                    if package.task_id == task_id and package.process_id is None:
                        self.packages.remove(package)
                return True
        return False

    def add_package(self, package):
        self.packages.append(package)
        return True

    def get_other_nodes(self):
        other_nodes = []
        logger.debug('own ip and port: {}:{}'.format(self.ip, self.port))
        for node in self.nodes:
            if node != self.node:
                logger.debug('enter: {}'.format(node))
                other_nodes.append(node)
        return other_nodes

    def get_package_buffer_left(self):
        if len(self.packages) < self._max_packages:
            buffer_len = self._max_packages - len(self.packages)
        else:
            buffer_len = 0
        return buffer_len

    def get_active_worker_count(self):
        current_time = int(time())
        count = 0

        for package in self.packages:
            if package.last_active is None:
                continue
            if (current_time - package.last_active) > \
                    FreeSlave.inactive_process_time_limit:
                package.last_active = None
                package.process_id = None
            if package.last_active is not None:
                count += 1

        return count

    def start_worker(self):
        if len(self.packages) == 0:
            logger.debug('Empty package list!')
            return 0

        if self.get_active_worker_count() >= self._max_workers:
            logger.debug('Max number of workers running already!')
            return 0

        logger.debug('Worker count: {}'.format(self.get_active_worker_count()))

        for package in self.packages:
            if package.last_active is None and package.process_id is None:
                if type(package) not in FreeSlave.known_package_types:
                    logger.debug(
                        'Unknown package type: {}'.format(type(package))
                    )
                    continue

                package.update_last_active()

                newpid = os.fork()
                if newpid == 0:
                    # Worker process code

                    # Register worker
                    uri = CONN_STRING.format(
                        package.assigner_ip,
                        package.assigner_port,
                        "/api/processes"
                    )
                    payload = {
                        'process_id': os.getpid(),
                        'assigner_ip': package.assigner_ip,
                        'assigner_port': package.assigner_port,
                        'task_id': package.task_id,
                        'package_id': package.package_id,
                        'type': package.type
                    }
                    for i in range(3):
                        try:
                            response = requests.post(uri, json=payload)
                        except (requests.ConnectionError, requests.HTTPError,
                                requests.Timeout) as e:
                            logger.debug(
                                "Error while connecting to host: {}".format(e)
                            )
                            if i == 2:
                                os._exit(0)
                            sleep(0.05)
                            continue
                        # Worker successfully registered
                        if response.status_code == 204:
                            # Calculate the result for package
                            result = package.get_result()

                            # Post result
                            uri = CONN_STRING.format(
                                package.assigner_ip,
                                package.assigner_port,
                                '/api/packages/result'
                            )
                            payload = package.get_dict()
                            payload['result'] = result

                            for i in range(3):
                                try:
                                    response = requests.post(uri, json=payload)
                                except (requests.ConnectionError, requests.HTTPError,
                                        requests.Timeout) as e:
                                    logger.debug("Error while connecting to host: {}".format(e))
                                    if i == 2:
                                        os._exit(0)
                                    continue
                                # Result successfully posted
                                if response.status_code == 200:
                                    uri = CONN_STRING.format(
                                        self.ip,
                                        self.port,
                                        '/api/processes/{}'.format(os.getpid())
                                    )
                                    # Unregister worker
                                    for i in range(3):
                                        try:
                                            response = requests.delete(uri)
                                        except (requests.ConnectionError, requests.HTTPError, requests.Timeout) as e:
                                            logger.debug("Error while connecting to host: {}".format(e))
                                            if i == 2:
                                                os._exit(0)
                                            continue
                                        os._exit(0)
                                elif response.status_code == 204 or response.status_code == 404:
                                    uri = CONN_STRING.format(
                                        self.ip,
                                        self.port,
                                        '/api/packages/{}/{}/{}'.format(package.assigner_ip, package.assigner_port, package.task_id)
                                    )
                                    # Remove working packages from queue because assigner does not have such task anymore
                                    for i in range(3):
                                        try:
                                            response = requests.delete(uri)
                                            if response.status_code == 204:
                                                break
                                        except (requests.ConnectionError, requests.HTTPError, requests.Timeout) as e:
                                            logger.debug("Error while connecting to host: {}".format(e))
                                            continue
                                    # Unregister worker
                                    uri = CONN_STRING.format(
                                        self.ip,
                                        self.port,
                                        '/api/processes/{}'.format(os.getpid())
                                    )
                                    for i in range(3):
                                        try:
                                            response = requests.delete(uri)
                                            if response.status_code == 204:
                                                break
                                        except (requests.ConnectionError, requests.HTTPError, requests.Timeout) as e:
                                            logger.debug("Error while connecting to host: {}".format(e))
                                    os._exit(0)
                    # End of worker process code

                return newpid
        logger.debug('Could not find packages to be started!')
        return 0

    def delegate_packages(self):
        logger.debug("Assigning packages.")
        # Reset results since delegate
        self.results_since_delegate = 0
        # Verify that we have existing tasks.
        if len(self.tasks) == 0:
            logger.debug('No tasks to delegate!')
            return False
        # Loop through all the nodes to delegate packages
        for node in self.nodes:
            # Verify that we have packages that can be delegated.
            packages = self.get_packages(lock_packages=False)
            if not packages:
                logger.debug('No packages available!')
                return False
            # Check if we can handle more packages ourselves
            if node == self.node:
                remaining_buffer = self.get_package_buffer_left()
                if not remaining_buffer:
                    continue
                packages = self.get_packages(max_count=remaining_buffer)
                self.set_assigned_to_packages(node, packages)
                for package in packages:
                    self.packages.append(package)
                logger.debug("Successfully assigned packages for self.")
                self.start_worker()
                continue

            # Check if someone else can handle more packages
            # TODO: finish this and test that it works!
            uri = CONN_STRING.format(
                node.ip, node.port, "/api/packages/{}/{}".format(
                    self.ip, self.port
                )
            )
            try:
                response = requests.get(uri)
            except (requests.ConnectionError, requests.HTTPError,
                    requests.Timeout) as e:
                logger.debug("Error while connecting to host: {}".format(e))
                return False
            if response.status_code == 200:
                node.update_last_active()
                data = response.json()
            else:
                # TODO: What should we do if server answers something else
                # than 200 OK?
                logger.debug('something went wong... :(')
                raise ValueError
            remaining_buffer = data["available_buffer"]
            packages = self.get_packages(max_count=remaining_buffer)

            uri = CONN_STRING.format(node.ip, node.port, "/api/packages")
            payload = {
                "packages": self.convert_to_dict(packages)
            }
            try:
                response = requests.post(uri, json=payload)
            except (requests.ConnectionError, requests.HTTPError,
                    requests.Timeout) as e:
                logger.debug("Error while connecting to host: {}".format(e))
                return False
            if response.status_code == 204:
                logger.debug(
                    "Packages assigned successfully "
                    "to remote node {}".format(node)
                )
                self.set_assigned_to_packages(node, packages)
                return True
            else:
                logger.debug(
                    "Unexpected status code: {}\n"
                    "Error message: {}".format(
                        response.status_code, response.text
                    )
                )
                logger.debug(
                    "Something went wrong when assigning packages "
                    "to remote node {}, releasing packages.".format(node)
                )
                for package in packages:
                    package.release()
                return False

    @staticmethod
    def convert_to_dict(convertable):
        items = []
        for item in convertable:
            items.append(item.get_dict())
        return items

    def set_assigned_to_packages(self, node, packages):
        for package in packages:
            found = False
            for task in self.tasks:
                for task_package in task.packages:
                    if task_package == package:
                        task_package.assign_to(node)
                        found = True
                    if found:
                        break
                if found:
                    break

    def get_packages(self, lock_packages=True, max_count=10):
        packages = []
        for task in self.tasks:
            for package in task.packages:
                if package.assigned_ip is None:
                    if lock_packages:
                        package.assign_to(
                            Node({'ip': 'locked', 'port': 'locked'})
                        )
                    packages.append(package)
                    if len(packages) >= max_count:
                        break
            if len(packages) > 0:
                break

        return packages

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
        if 'package_id' not in data.keys():
            return False
        if type(data['package_id']) is not str:
            return False
        return True

    # TEST METHODS
    def print_nodes(self):
        for node in self.nodes:
            logger.debug(node)
