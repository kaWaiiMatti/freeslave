from time import time
import hashlib

ALLOWED_CHARS = 'abcdefghijklmnopqrstuvwxyz' \
                'ABCDEFGHIJKLMNOPQRSTUVWXYZ0123456789'


class MD5HashTask:
    package_size = 4

    def __init__(self, ip, port, target_hash, task_id,
                 max_length=6, create_packages=True):
        self.type = 'md5hashtask'
        self.target_hash = target_hash
        self.result = ''
        self.max_length = max_length
        self.task_id = task_id
        self.packages = []

        if create_packages:
            self.packages.append(MD5HashPackage(
                {
                    'assigner_ip': ip,
                    'assigner_port': port,
                    'target_hash': target_hash,
                    'start_string': '',
                    'task_id': task_id
                })
            )
            if int(max_length) > MD5HashTask.package_size:
                for start_string in MD5HashTask.yield_char_combinations(
                        (self.max_length - MD5HashTask.package_size),
                        include_not_max_length=True):
                    self.packages.append(MD5HashPackage(
                        {
                            'assigner_ip': ip,
                            'assigner_port': port,
                            'target_hash': target_hash,
                            'start_string': start_string,
                            'task_id': task_id
                        })
                    )

    def __str__(self):
        return 'task_id:{}, target_hash:{} ' \
               'and max_length:{}'.format(
                self.task_id,
                self.target_hash,
                self.max_length
                )

    def get_dict(self, include_packages=False):
        if include_packages:
            packages = []
            for package in self.packages:
                packages.append(package.get_dict())
            return {
                "target_hash": self.target_hash,
                "result": self.result,
                "max_length": self.max_length,
                "task_id": self.task_id,
                "packages": packages
            }
        return {
            "target_hash": self.target_hash,
            "result": self.result,
            "max_length": self.max_length,
            "task_id": self.task_id
        }

    def add_result(self, identifier, data):
        for package in self.packages:
            if package.start_string == identifier:
                print('correct package found!')  # TODO: implement this
                return True
        return False

    @staticmethod
    def validate_md5hashtask_data(data):
        if type(data) is not dict:
            return False
        if 'max_length' not in data.keys():
            return False
        if type(data['max_length']) is not int:
            return False
        if data['max_length'] < 1:
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


class MD5HashPackage:
    def __init__(self, data):
        self.type = 'md5hashpackage'
        self.target_hash = data['target_hash']
        self.result = ''
        self.start_string = data['start_string']
        self.assigner_ip = data['assigner_ip']
        self.assigner_port = data['assigner_port']
        self.task_id = data['task_id']
        self.process_id = None
        self.last_active = None
        self.assigned_ip = None
        self.assigned_port = None

    def __str__(self):
        return 'Package - assigner:{}:{}, task_id:{}, start_string:{}, ' \
               'pid:{}'.format(
                self.assigner_ip,
                self.assigner_port,
                self.task_id,
                self.start_string,
                self.process_id
                )

    def get_dict(self):
        return {
            "target_hash": self.target_hash,
            "start_string": self.start_string,
            "assigner_ip": self.assigner_ip,
            "assigner_port": self.assigner_port,
            "type": "md5hashpackage",
            "task_id": self.task_id
        }

    def get_result(self):
        if self.start_string == '':
            include_not_max_length = True
        else:
            include_not_max_length = False
        for value in MD5HashTask.yield_char_combinations(
                MD5HashTask.package_size,
                include_not_max_length=include_not_max_length):
            h = hashlib.md5()
            h.update(str.encode(self.start_string + value))
            if h.hexdigest() == self.target_hash:
                self.result = self.start_string + value
                return self.result

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

    @staticmethod
    def validate_md5hashpackage_result(data):
        if type(data) is not dict:
            print('not dict')
            return False
        if 'target_hash' not in data.keys():
            print('no target_hash')
            return False
        if type(data['target_hash']) is not str:
            print('target_hash not str')
            return False
        if len(data['target_hash']) != 32:
            print('wrong target_hash length')
            return False
        if 'assigner_ip' not in data.keys():
            print('no assinger_ip')
            return False
        if type(data['assigner_ip']) is not str:
            print('assigner_ip not str')
            return False
        if len(data['assigner_ip']) < 5:
            print('too short assigner_ip')
            return False
        if 'assigner_port' not in data.keys():
            print('no assigner_port')
            return False
        if type(data['assigner_port']) is not int:
            return False
        if 'task_id' not in data.keys():
            return False
        if type(data['task_id']) is not int:
            return False
        if 'start_string' not in data.keys():
            return False
        if type(data['start_string']) is not str:
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
        if 'start_string' not in data.keys():
            return False
        if type(data['start_string']) is not str:
            return False
        if 'type' not in data.keys():
            return False
        if type(data['type']) is not str:
            return False
        if data['type'] != 'md5hashpackage':
            return False
        return True
