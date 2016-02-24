import hashlib


class Md5HashTask:
    package_size = 4

    def __init__(self, ip, port, target_hash, task_id, max_length = 6):
        self.target_hash = target_hash
        self.result = ''
        self.max_length = max_length
        self.task_id = task_id
        self.packages = []
        self.packages.append(Md5HashPackage(ip, port, target_hash, ''))

        if int(max_length) > Md5HashTask.package_size:
            for start_string in Md5HashTask.yieldCharCombinations((self.max_length - Md5HashTask.package_size), include_not_max_length=True):
                self.packages.append(Md5HashPackage(ip, port, target_hash, start_string))

        print('Number of packages {}'.format(len(self.packages)))

    def __str__(self):
        return 'task_id:{}, target_hash:{} and max_length:{}'.format(self.task_id, self.target_hash, self.max_length)

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
    def __init__(self, ip, port, target_hash, start_string):
        self.target_hash = target_hash
        self.result = ''
        self.start_string = start_string
        self.assigner_ip = ip
        self.assigner_port = port

    def getResult(self):
        for value in Md5HashTask.yieldCharCombinations(Md5HashTask.package_size, include_not_max_length = True if self.start_string == '' else False):
            h = hashlib.md5()
            h.update(str.encode(self.start_string + value))
            if(h.hexdigest() == self.target_hash):
                self.result = self.start_string + value
                break