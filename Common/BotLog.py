class BotLog:
    def __init__(self
                 , BotLogId=0
                 , Symbol=""
                 , ShortLog=""
                 , LongLog=False
                 , CreatedDate=None

                 ):
        self.BotLogId = int(BotLogId)
        self.Symbol = Symbol
        self.ShortLog = ShortLog
        self.LongLog = LongLog
        self.CreatedDate = CreatedDate

    def __str__(self):
        return str(self.__dict__)

    def __repr__(self):
        return self.__str__()

