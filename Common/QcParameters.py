class QcParameters:
    def __init__(self,

                 qcRangeId=0
                 , asset=""

                 , minVolume1=0
                 , maxVolume1=0
                 , perc1=0
                 , minVolume2=0
                 , maxVolume2=0
                 , perc2=0
                 , minVolume3=0
                 , maxVolume3=0
                 , perc3=0
                 , minVolume4=0
                 , maxVolume4=0
                 , perc4=0
                 , minVolume5=0
                 , maxVolume5=0
                 , perc5=0
                 , minVolume6=0
                 , maxVolume6=0
                 , perc6=0
                 , dailySpendPerc=0
                 , tradeEnabled=0
                 , rebuyTriggerAmount=0
                 , rebuyAmount=0

                 ):

        self.qcRangeId = int(qcRangeId)
        self.asset = asset

        self.minVolume1 = minVolume1
        self.maxVolume1 = maxVolume1
        self.perc1 = perc1
        self.minVolume2 = minVolume2
        self.maxVolume2 = maxVolume2
        self.perc2 = perc2
        self.minVolume3 = minVolume3
        self.maxVolume3 = maxVolume3
        self.perc3 = perc3
        self.minVolume4 = minVolume4
        self.maxVolume4 = maxVolume4
        self.perc4 = perc4
        self.minVolume5 = minVolume5
        self.maxVolume5 = maxVolume5
        self.perc5 = perc5
        self.minVolume6 = minVolume6
        self.maxVolume6 = maxVolume6
        self.perc6 = perc6
        self.dailySpendPerc = dailySpendPerc
        self.tradeEnabled = tradeEnabled
        self.rebuyTriggerAmount = rebuyTriggerAmount
        self.rebuyAmount = rebuyAmount


    def __str__(self):
        return str(self.__dict__)

    def __repr__(self):
        return self.__str__()
