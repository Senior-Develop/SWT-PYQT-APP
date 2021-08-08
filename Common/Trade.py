class Trade:
    def __init__(self
                 , TradeId=0
                 , Symbol=""
                 , StrategyName=""
                 , IsOpen=False
                 , TradeType=""
                 , Amount=0
                 , QuoteAmount=0
                 , EntryPrice=0
                 , ExitPrice=0
                 , StopLoss=0
                 , EntryDate=None
                 , ExitDate=None
                 , EntryCandleDate=None
                 , TimerInSeconds=0
                 , EntryTriggerPrice=0
                 , ExitTriggerPrice=0
                 , ModifiedDate=None
                 , CurrentPrice=0
                 , PLAmount=0
                 , PLPercentage=0
                 , EntryCommission=0
                 , ExitCommission=0
                 , TargetPrice=0
                 , ReEntryNumber=0
                 , IsTslActivated=0
                 , BacktestId=0


                 ):
        self.TradeId = int(TradeId)
        self.Symbol = Symbol
        self.StrategyName = StrategyName
        self.IsOpen = IsOpen
        self.TradeType = TradeType
        self.Amount = Amount
        self.QuoteAmount = QuoteAmount
        self.EntryPrice = EntryPrice
        self.ExitPrice = ExitPrice
        self.StopLoss = StopLoss
        self.EntryDate = EntryDate
        self.ExitDate = ExitDate
        self.EntryCandleDate = EntryCandleDate
        self.TimerInSeconds = TimerInSeconds
        self.EntryTriggerPrice = EntryTriggerPrice
        self.ExitTriggerPrice = ExitTriggerPrice
        self.ModifiedDate = ModifiedDate
        self.CurrentPrice = CurrentPrice
        self.PLAmount = PLAmount
        self.PLPercentage = PLPercentage
        self.EntryCommission = EntryCommission
        self.ExitCommission = ExitCommission
        self.TargetPrice = TargetPrice
        self.ReEntryNumber = ReEntryNumber
        self.IsTslActivated = IsTslActivated
        self.BacktestId = BacktestId






    def __str__(self):
        return str(self.__dict__)

    def __repr__(self):
        return self.__str__()

