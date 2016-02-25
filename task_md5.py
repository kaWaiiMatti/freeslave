import hashlib
import json


class Md5HashTask:
    package_size = 4

    def __init__(self, ip, port, target_hash, task_id, max_length = 6):
        self.target_hash = target_hash
        self.result = ''
        self.max_length = max_length
        self.task_id = task_id
        self.packages = []
        self.packages.append(Md5HashPackage({'assigner_ip':ip, 'assigner_port':port, 'target_hash':target_hash, 'start_string':'', 'task_id':task_id}))

        if int(max_length) > Md5HashTask.package_size:
            for start_string in Md5HashTask.yieldCharCombinations((self.max_length - Md5HashTask.package_size), include_not_max_length=True):
                self.packages.append(Md5HashPackage({'assigner_ip':ip, 'assigner_port':port, 'target_hash':target_hash, 'start_string':start_string, 'task_id':task_id}))

        print('Number of packages {}'.format(len(self.packages)))

    def __str__(self):
        return 'task_id:{}, target_hash:{} and max_length:{}'.format(self.task_id, self.target_hash, self.max_length)

    def getDict(self, include_packages = False):
        if include_packages:
            packages = []
            for package in self.packages:
                packages.append(package.getDict())
            return {"target_hash":self.target_hash, "result":self.result, "max_length":self.max_length, "task_id":self.task_id, "packages":packages}
        return {"target_hash":self.target_hash, "result":self.result, "max_length":self.max_length, "task_id":self.task_id}

    @staticmethod
    def validateMd5HashTaskData(data):
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
    def yieldCharCombinations(max_length, existing = '', include_not_max_length = False, allowed_characters = 'abcdefghijklmnopqrstuvwxyzABCDEFGHIJKLMNOPQRSTUVWXYZ0123456789'):
        for char in allowed_characters:
            new = existing + char
            if len(new) < max_length:
                for item in  Md5HashTask.yieldCharCombinations(max_length, new, include_not_max_length, allowed_characters):
                    yield item
            if len(new) == max_length or include_not_max_length:
                yield new


class Md5HashPackage:
    def __init__(self, data):
        self.target_hash = data['target_hash']
        self.result = ''
        self.start_string = data['start_string']
        self.assigner_ip = data['assigner_ip']
        self.assigner_port = data['assigner_port']
        self.related_task = data['task_id']

    def __str__(self):
        return json.dumps(self.getDict())

    def getDict(self):
        return {"target_hash":self.target_hash, "start_string":self.start_string, "assigner_ip":self.assigner_ip, "assigner_port":self.assigner_port, "type":"md5hashpackage"}

    def getResult(self):
        for value in Md5HashTask.yieldCharCombinations(Md5HashTask.package_size, include_not_max_length = True if self.start_string == '' else False):
            h = hashlib.md5()
            h.update(str.encode(self.start_string + value))
            if(h.hexdigest() == self.target_hash):
                self.result = self.start_string + value
                break

    @staticmethod
    def validate_md5hashpackage_data(data):
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
        if(data['type'] != 'md5hashpackage'):
            return False
        return True