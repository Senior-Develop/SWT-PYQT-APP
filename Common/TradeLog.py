class TradeLog:
    def __init__(self
                 , TradeLogId=0
                 , TradeId=0
                 , Symbol=""
                 , CandleDate=None
                 , CreatedDate=None
                 , StrategyName=""
                 , TradeType=""
                 , Action=""
                 , Comment=""
                 , Amount=0
                 , QuoteAmount=0
                 , EntryPrice=0
                 , CurrentPrice=0
                 , StopLoss=0
                 , PLAmount=0
                 , PLPercentage=0
                 , Commission=0
                 , Balance=0
                 , TargetPrice=0
                 , BacktestId=0

                 ):

        self.TradeLogId = int(TradeLogId)
        self.TradeId = TradeId
        self.Symbol = Symbol
        self.CandleDate = CandleDate
        self.CreatedDate = CreatedDate
        self.StrategyName = StrategyName
        self.TradeType = TradeType
        self.Action = Action
        self.Comment = Comment
        self.Amount = Amount
        self.QuoteAmount = QuoteAmount
        self.EntryPrice = EntryPrice
        self.CurrentPrice = CurrentPrice
        self.StopLoss = StopLoss
        self.PLAmount = PLAmount
        self.PLPercentage = PLPercentage
        self.Commission = Commission
        self.Balance = Balance
        self.TargetPrice = TargetPrice
        self.BacktestId = BacktestId


    def __str__(self):
        return str(self.__dict__)

    def __repr__(self):
        return self.__str__()

