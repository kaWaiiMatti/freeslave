class Md5HashTask:
    def __init__(self, ip, port, target_hash, max_length = 6):
        self.target_hash = target_hash
        self.result = ''
        self.max_length = max_length
        self.packages = []
        for start_string in Md5HashTask.yieldCharCombinations((self.max_length - 4 if (self.max_length - 4) > 0 else 1), include_not_max_length=True):
            self.packages.append(Md5HashTask(ip, port, target_hash, start_string))
        print('Number of packages {}'.format(len(self.packages)))

    @staticmethod
    def validateMd5HashTaskData(data):
        if type(data) is not dict:
            return False
        if 'ip' not in data.keys():
            return False
        if type(data['port']) is not str:
            return False
        if 'port' not in data.keys():
            return False
        if type(data['port']) is not int:
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

    def getResults(self):
        for value in Md5HashTask.yieldCharCombinations(4, include_not_max_length = True if self.start_string == '' else False):
            '''
            h = hashlib.md5()
            h.update(str.encode(char))
            print(h.hexdigest())
            '''
            if self.start_string + value == self.target_hash:
                return self.start_string + value
        return ''