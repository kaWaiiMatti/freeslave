import logging

from time import time

logger = logging.getLogger(__name__)


class Task:
    logging.basicConfig(
        level=logging.DEBUG,
        format="%(asctime)s [%(levelname)s] %(name)s: %(message)s"
    )

    def __init__(self, task_id, max_length=6):
        self.type = "basetask"
        self.max_length = max_length
        self.task_id = task_id
        self.packages = []
        self.result = ""

    def __str__(self):
        return "task_id: {}, max_length: {}".format(
            self.task_id,
            self.max_length
            )

    def get_dict(self, include_packages=False):
        response = {
            "task_id": self.task_id,
            "result": self.result,
            "max_length": self.max_length,
        }

        if include_packages:
            response["packages"] = [p.get_dict() for p in self.packages]

        return response

    def add_result(self, identifier, data):
        for package in self.packages:
            if package.package_id == identifier:
                logger.debug('correct package found!')  # TODO: implement this
                return True
        return False

    @staticmethod
    def validate_input(data):
        if type(data) is not dict:
            return False
        if 'max_length' not in data.keys():
            return False
        if type(data['max_length']) is not int:
            return False
        if data['max_length'] < 1:
            return False
        return True


class TaskPackage:
    def __init__(self, data):
        try:
            self.package_id = data["package_id"]
            self.assigner_ip = data["assigner_ip"]
            self.assigner_port = data["assigner_port"]
            self.task_id = data["task_id"]
            self.type = data["type"]
        except KeyError:
            logger.critical("Malformed initialization data, could not "
                            "initialize TaskPackage!")
            logger.debug(data)

        self.result = ''
        self.process_id = None
        self.last_active = None
        self.assigned_ip = None
        self.assigned_port = None

    def __eq__(self, other):
        equals = True

        # Make sure the objects are same type
        #if type(self) != type(other):
        #    equals = False
        if self.type != other.type:
            equals = False
        elif self.assigner_ip != other.assigner_ip:
            equals = False
        elif self.assigner_port != other.assigner_port:
            equals = False
        elif self.task_id != other.task_id:
            equals = False
        elif self.package_id != other.package_id:
            equals = False

        return equals

    def __ne__(self, other):
        return not self.__eq__(other)

    def __str__(self):
        return 'Package - assigner: {}:{}, task_id: {}, package_id: {}, ' \
               'pid: {}'.format(
                self.assigner_ip,
                self.assigner_port,
                self.task_id,
                self.package_id,
                self.process_id
                )

    def get_dict(self):
        return {
            "task_id": self.task_id,
            "package_id": self.package_id,
            "assigner_ip": self.assigner_ip,
            "assigner_port": self.assigner_port,
            "type": self.type
        }

    def set_process_id(self, process_id):
        self.process_id = process_id

    def update_last_active(self):
        self.last_active = time()

    def assign_to(self, node):
        self.assigned_ip = node.ip
        self.assigned_port = node.port

    def release(self):
        self.assigned_ip = None
        self.assigned_port = None
