class OptimizationRun:
    def __init__(self, OptimizationRunId=0
                 , OptimizationId=""
                 , Symbol=""
                 , Timeframe=""
                 , CreatedDate=None
                 , StartDate=None
                 , EndDate=None
                 , CombinationCount=0
                 , DurationInMinutes=0
                 , BestSpId=0
                 , BestBacktestId=0
                 , PLPercentage=0
                 , State=""


                 ):

        self.OptimizationRunId = int(OptimizationRunId)
        self.OptimizationId = OptimizationId
        self.Symbol = Symbol
        self.Timeframe = Timeframe
        self.CreatedDate = CreatedDate
        self.StartDate = StartDate
        self.EndDate = EndDate
        self.CombinationCount = CombinationCount
        self.DurationInMinutes = DurationInMinutes
        self.BestSpId = BestSpId
        self.BestBacktestId = BestBacktestId
        self.PLPercentage = PLPercentage
        self.State = State




    def __str__(self):
        return str(self.__dict__)

    def __repr__(self):
        return self.__str__()
