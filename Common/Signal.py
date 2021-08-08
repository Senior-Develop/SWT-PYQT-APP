class Signal:
    def __init__(self, SignalId=0
                 , Symbol=""
                 , CreatedDate=None
                 , CandleDate=None
                 , CurrentPrice=0
                 , StrategyName=""
                 , BacktestId=0

                 ):

        self.SignalId = int(SignalId)
        self.Symbol = Symbol
        self.CreatedDate = CreatedDate
        self.CandleDate = CandleDate
        self.CurrentPrice = CurrentPrice
        self.StrategyName = StrategyName
        self.BacktestId = BacktestId

    def __str__(self):
        return str(self.__dict__)

    def __repr__(self):
        return self.__str__()
