import json


class AttrDict(dict):
    def __init__(self, *args, **kwargs):
        super(AttrDict, self).__init__(*args, **kwargs)
        self.__dict__ = self

        def to_attrdict(obj):
            if type(obj) is list:
                return [to_attrdict(v) for v in obj]
            elif type(obj) is dict:
                return AttrDict({k: to_attrdict(v) for k, v in obj.items()})
            return obj

        for k, v in self.items():
            self[k] = to_attrdict(v)

    def __getattr__(self, name):
        try:
            return self[name]
        except KeyError:
            raise AttributeError(name)

    def from_file(filename):
        with open(filename, "r") as f:
            return AttrDict(json.load(f))

    def dict(self):
        def to_dict(obj):
            if type(obj) is AttrDict:
                return obj.dict()
            elif type(obj) is list:
                return [to_dict(v) for v in obj]

            return obj

        d = {}
        for k, v in self.items():
            d[k] = to_dict(v)

        return d
