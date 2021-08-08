class Balance:
    def __init__(self, asset=None, free=0.0, locked=0.0):
        self.asset = asset
        self.free = float(free)
        self.locked = float(locked)

    def __str__(self):
        return str(self.__dict__)

    def __repr__(self):
        return self.__str__()