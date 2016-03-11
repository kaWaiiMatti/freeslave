import logging

from time import time

logger = logging.getLogger(__name__)


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
            self.result = ''
            self.process_id = None
            self.last_active = None
            self.assigned_ip = None
            self.assigned_port = None

    def __eq__(self, other):
        equals = True

        # Make sure the objects are same type
        if type(self) != type(other):
            equals = False
        elif self.type != other.type:
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
