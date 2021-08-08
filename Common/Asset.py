class Asset:
    def __init__(self
                 , AssetId=0
                 , AssetName=""
                 , BalanceFree=""
                 , BalanceLocked=0
                 , ModifiedDate=None
                 ):
        self.AssetId = int(AssetId)
        self.AssetName = AssetName
        self.BalanceFree = BalanceFree
        self.BalanceLocked = BalanceLocked
        self.ModifiedDate = ModifiedDate

    def __str__(self):
        return str(self.__dict__)

    def __repr__(self):
        return self.__str__()

