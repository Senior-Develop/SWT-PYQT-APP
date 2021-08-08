class Backtest:
    def __init__(self, BacktestId=0
                 , Symbol=""
                 , Timeframe=""
                 , OptimizationRunId=0
                 , CreatedDate=None
                 , StartDate=None
                 , EndDate=None
                 , TickCount=0
                 , DurationInMinutes=0
                 , Params=""
                 , SpId=0
                 , SpCount=0
                 , SpIndex=0
                 , TotalTrades=0
                 , TotalTradesPerHour=0
                 , PLPercentage=0
                 , PLAmount=0
                 , PLAmountPerHour=0
                 , PLUsd=0
                 , AvgPLTrade=0
                 , AvgPLPercentage=0
                 , AvgTradeAmount=0
                 , AvgTimeInTradeInMinutes=0




                 ):

        self.BacktestId = int(BacktestId)
        self.Symbol = Symbol
        self.Timeframe = Timeframe
        self.OptimizationRunId = OptimizationRunId
        self.CreatedDate = CreatedDate
        self.StartDate = StartDate
        self.EndDate = EndDate
        self.TickCount = TickCount
        self.DurationInMinutes = DurationInMinutes
        self.Params = Params
        self.SpId = SpId
        self.SpCount = SpCount
        self.SpIndex = SpIndex
        self.TotalTrades = TotalTrades
        self.TotalTradesPerHour = TotalTradesPerHour
        self.PLPercentage = PLPercentage
        self.PLAmount = PLAmount
        self.PLAmountPerHour = PLAmountPerHour
        self.PLUsd = PLUsd
        self.AvgPLTrade = AvgPLTrade
        self.AvgPLPercentage = AvgPLPercentage
        self.AvgTradeAmount = AvgTradeAmount
        self.AvgTimeInTradeInMinutes = AvgTimeInTradeInMinutes

    def __str__(self):
        return str(self.__dict__)

    def __repr__(self):
        return self.__str__()
