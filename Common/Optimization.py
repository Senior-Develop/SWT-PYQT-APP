class Optimization:
    def __init__(self, OptimizationId=0
                 , Symbol=""
                 , Timeframe=""
                 , CreatedDate=None
                 , StartDate=None
                 , EndDate=None
                 , CombinationCount=0
                 , DurationInMinutes=0
                 , BestSpId=0
                 , BestBacktestId=0

                 ):

        self.OptimizationId = int(OptimizationId)
        self.Symbol = Symbol
        self.Timeframe = Timeframe
        self.CreatedDate = CreatedDate
        self.StartDate = StartDate
        self.EndDate = EndDate
        self.CombinationCount = CombinationCount
        self.DurationInMinutes = DurationInMinutes
        self.BestSpId = BestSpId
        self.BestBacktestId = BestBacktestId




    def __str__(self):
        return str(self.__dict__)

    def __repr__(self):
        return self.__str__()
