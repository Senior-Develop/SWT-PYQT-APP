class TickData:
    def __init__(self
                 , TickDataId=0
                 , Symbol=""
                 , Timeframe=""
                 , Close=0
                 , Open=0
                 , High=0
                 , Low=0
                 , OpenTime=None
                 , CloseTime=None
                 , NumTrades=0
                 , Volume=0
                 , QuoteAssetVolume=0
                 , TakerBuyBaseAssetVolume=0
                 , TakerBuyQuoteAssetVolume=0
                 , CreatedDate=None
                 , EventTime=None
                 ):

        self.TickDataId = int(TickDataId)
        self.Symbol = Symbol
        self.Timeframe = Timeframe
        self.Close = Close
        self.Open = Open
        self.High = High
        self.Low = Low
        self.OpenTime = OpenTime
        self.CloseTime = CloseTime
        self.NumTrades = NumTrades
        self.Volume = Volume
        self.QuoteAssetVolume = QuoteAssetVolume
        self.TakerBuyBaseAssetVolume = TakerBuyBaseAssetVolume
        self.TakerBuyQuoteAssetVolume = TakerBuyQuoteAssetVolume
        self.CreatedDate = CreatedDate
        self.EventTime = EventTime


    def __str__(self):
        return str(self.__dict__)

    def __repr__(self):
        return self.__str__()


