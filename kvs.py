import time


class KVS(object):
    # timeout sec
    TIMEOUT = 600
    _instance = None
    context = {}
    # 'dummy_id': {
    #     'context': 'some_value',
    #     'time': 'some_time'
    # }

    def __new__(cls, *args, **kwargs):
        if not cls._instance:
            cls._instance = super(KVS, cls).__new__(cls, *args, **kwargs)
        return cls._instance

    def __init__(self, *args, **kwargs):
        pass

    def set_value(self, key, value):
        # check key in context
        if key not in self.context:
            self.context.update({
                    key: {
                        'context': value,
                        'time': time.time()
                    }
                })
        else:
            self.context[key]['context'] = value
            self.context[key]['time'] = time.time()

    def get_value(self, key):
        # check key in context
        ret = self.context.get(key, None)
        if ret is None:
            return None

        # check TIMEOUT in key
        if time.time() - ret['time'] > self.TIMEOUT:
            del self.context[key]
            return None
        else:
            return ret['context']
