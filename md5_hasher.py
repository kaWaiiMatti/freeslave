class Md5Hasher:
    def __init__(self, target, startString = ''):
        self._target = target
        self._startString = startString
        self._allowedCharacters = 'abcdefghijklmnopqrstuvwxyzABCDEFGHIJKLMNOPQRSTUVWXYZ0123456789'
        self._maxLength = 4

    def getResults(self):
        for value in Md5Hasher.yieldCharCombinations(self._maxLength, allowed_characters=self._allowedCharacters):
            if self._startString + value == self._target:
                return self._startString + value
        return None

    @staticmethod
    def yieldCharCombinations(max_length, existing = '', include_not_max_length = False, allowed_characters = 'abcdefghijklmnopqrstuvwxyzABCDEFGHIJKLMNOPQRSTUVWXYZ0123456789'):
        for char in allowed_characters:
            new = existing + char
            if len(new) < max_length:
                for item in  Md5Hasher.yieldCharCombinations(max_length, new, include_not_max_length, allowed_characters):
                    yield item
            if len(new) == max_length or include_not_max_length:
                yield new

    @staticmethod
    def splitTask(max_length):
        pass

class Md5HasherPackage:
    def __init__(self, startString, ip, port):
        self.result = ''
        self.startString = startString
        self.assignerIp = ip
        self.assignerPort = port