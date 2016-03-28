import hashlib
import logging

from base_task import Task, TaskPackage
from string import ascii_letters, digits

ALLOWED_CHARS = ascii_letters + digits

logger = logging.getLogger(__name__)


class MD5HashTask(Task):
    logging.basicConfig(
        level=logging.DEBUG,
        format="%(asctime)s [%(levelname)s] %(name)s: %(message)s"
    )

    package_size = 4

    def __init__(self, ip, port, target_hash, task_id,
                 max_length=6, result='', stop_at_first_result=True, create_packages=True):
        super().__init__(task_id, max_length, result, stop_at_first_result)
        self.type = "md5hashtask"
        self.target_hash = target_hash

        if create_packages:
            self._add_task_package("", ip, port, target_hash)
            if int(max_length) > MD5HashTask.package_size:
                for start_string in MD5HashTask.yield_char_combinations(
                        (self.max_length - MD5HashTask.package_size),
                        include_not_max_length=True):
                    self._add_task_package(start_string, ip, port, target_hash)

    def __str__(self):
        return str(super()) + " target_hash: {}".format(self.target_hash)

    def _add_task_package(self, package_id, ip, port, target_hash):
        self.packages.append(MD5HashPackage(
            {
                'assigner_ip': ip,
                'assigner_port': port,
                'target_hash': target_hash,
                'package_id': package_id,
                'task_id': self.task_id
            })
        )

    def get_dict(self, include_packages=False):
        superdict = super().get_dict(include_packages)
        superdict["target_hash"] = self.target_hash
        return superdict

    @staticmethod
    def validate_input(data):
        # Unbound Super in Python is funny:
        # http://stackoverflow.com/a/26807879/3529415
        if not super(MD5HashTask, MD5HashTask).validate_input(data):
            return False
        if 'target_hash' not in data.keys():
            return False
        if type(data['target_hash']) is not str:
            return False
        if len(data['target_hash']) != 32:
            return False
        return True

    @staticmethod
    def yield_char_combinations(max_length, existing='',
                                include_not_max_length=False,
                                allowed_characters=ALLOWED_CHARS):
        for char in allowed_characters:
            new = existing + char
            if len(new) < max_length:
                for item in MD5HashTask.yield_char_combinations(
                        max_length,
                        new,
                        include_not_max_length,
                        allowed_characters):
                    yield item
            if len(new) == max_length or include_not_max_length:
                yield new


class MD5HashPackage(TaskPackage):
    def __init__(self, data):
        data["type"] = "md5hashpackage"
        super().__init__(data)
        self.target_hash = data['target_hash']

    def get_dict(self):
        superdict = super().get_dict()
        superdict["target_hash"] = self.target_hash
        return superdict

    def get_result(self):
        if self.package_id == '':
            include_not_max_length = True
        else:
            include_not_max_length = False
        for value in MD5HashTask.yield_char_combinations(
                MD5HashTask.package_size,
                include_not_max_length=include_not_max_length):
            h = hashlib.md5()
            h.update(str.encode(self.package_id + value))
            if h.hexdigest() == self.target_hash:
                self.result = self.package_id + value
                return self.result

    @staticmethod
    def validate_md5hashpackage_result(data):
        if type(data) is not dict:
            logger.error('not dict')
            return False
        if 'target_hash' not in data.keys():
            logger.error('no target_hash')
            return False
        if type(data['target_hash']) is not str:
            logger.error('target_hash not str')
            return False
        if len(data['target_hash']) != 32:
            logger.error('wrong target_hash length')
            return False
        if 'assigner_ip' not in data.keys():
            logger.error('no assinger_ip')
            return False
        if type(data['assigner_ip']) is not str:
            logger.error('assigner_ip not str')
            return False
        if len(data['assigner_ip']) < 5:
            logger.error('too short assigner_ip')
            return False
        if 'assigner_port' not in data.keys():
            logger.error('no assigner_port')
            return False
        if type(data['assigner_port']) is not int:
            return False
        if 'task_id' not in data.keys():
            return False
        if type(data['task_id']) is not int:
            return False
        if 'package_id' not in data.keys():
            return False
        if type(data['package_id']) is not str:
            return False
        if 'type' not in data.keys():
            return False
        if type(data['type']) is not str:
            return False
        if data['type'] != 'md5hashpackage':
            return False
        return True

    @staticmethod
    def validate_md5hashpackage_data(data):
        if type(data) is not dict:
            return False
        if 'target_hash' not in data.keys():
            return False
        if type(data['target_hash']) is not str:
            return False
        if len(data['target_hash']) != 32:
            return False
        if 'assigner_ip' not in data.keys():
            return False
        if type(data['assigner_ip']) is not str:
            return False
        if len(data['assigner_ip']) < 5:
            return False
        if 'assigner_port' not in data.keys():
            return False
        if type(data['assigner_port']) is not int:
            return False
        if 'task_id' not in data.keys():
            return False
        if type(data['task_id']) is not int:
            return False
        if 'package_id' not in data.keys():
            return False
        if type(data['package_id']) is not str:
            return False
        if 'type' not in data.keys():
            return False
        if type(data['type']) is not str:
            return False
        if data['type'] != 'md5hashpackage':
            return False
        return True
