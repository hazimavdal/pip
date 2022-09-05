import json


class AttrDict(dict):
    def __init__(self, *args, **kwargs):
        super(AttrDict, self).__init__(*args, **kwargs)
        self.__dict__ = self

        for k, v in self.items():
            if type(v) is dict:
                self[k] = AttrDict(v)
            elif type(v) is list:
                self[k] = [AttrDict(vv) for vv in v if type(vv) in (list, dict)]

    def __getattr__(self, name):
        try:
            return self[name]
        except KeyError:
            raise AttributeError(name)

    def from_file(filename):
        with open(filename, "r") as f:
            return AttrDict(json.load(f))

    def dict(self):
        d = {}
        for k, v in self.items():
            if type(v) is AttrDict:
                d[k] = v.dict()
            elif type(v) is list:
                d[k] = [vv.dict() if type(vv) is AttrDict else vv for vv in v]
            else:
                d[k] = v

        return d


AttrDict({
    "location": ["**/.git", "._*"]
})
