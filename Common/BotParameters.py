class BotParameters:
    def __init__(self,
                 botParametersId=0
                 , apiKey=""
                 , secretKey=""
                 , maxConcurrentTradeNumber=0
                 , minPrice=0
                 , minDailyVolume=0
                 , bankingPercentage=0
                 , runOnSelectedMarkets=False
                 , marketUpdateDate=0
                 , optimizationMode=0
                 , optStartDate=None
                 , optEndDate=None
                 , optTimeframe=""
                 , optSymbol=""
                 , optUpdateStrategyParameters=False


                 ):

        self.botParametersId = int(botParametersId)
        self.apiKey = apiKey
        self.secretKey = secretKey
        self.maxConcurrentTradeNumber = maxConcurrentTradeNumber
        self.minPrice = minPrice
        self.minDailyVolume = minDailyVolume
        self.bankingPercentage = bankingPercentage

        self.runOnSelectedMarkets = runOnSelectedMarkets
        self.marketUpdateDate = marketUpdateDate
        self.optimizationMode = optimizationMode

        self.optStartDate = optStartDate
        self.optEndDate = optEndDate
        self.optTimeframe = optTimeframe
        self.optSymbol = optSymbol
        self.optUpdateStrategyParameters = optUpdateStrategyParameters



    def __str__(self):
        return str(self.__dict__)

    def __repr__(self):
        return self.__str__()
