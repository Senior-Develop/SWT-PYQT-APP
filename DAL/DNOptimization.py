from Common.Optimization import Optimization
from DAL.DNBase import DNBase
import traceback
from datetime import datetime, timedelta


class DNOptimization(DNBase):
    def getOptimization(self, optimization_id):
        optimization = None
        try:
            sql = "SELECT * FROM Optimization WHERE OptimizationId = %s"
            values = (optimization_id,)
            self.cursor.execute(sql, values)
            result = self.cursor.fetchone()
            if result:
                optimization = Optimization(*result)
        except:
            print(traceback.format_exc())
        return optimization

    def getOptimizationBySymbol(self, symbol):
        optimization = None
        try:
            sql = "SELECT * FROM Optimization WHERE Symbol = %s"
            values = (symbol,)
            self.cursor.execute(sql, values)
            result = self.cursor.fetchone()
            if result:
                optimization = Optimization(*result)
        except:
            print(traceback.format_exc())
        return optimization

    def listOptimization(self):
        optimizations = []
        try:
            sql = "SELECT * FROM Optimization ORDER BY OptimizationId desc LIMIT 20"
            self.cursor.execute(sql)
            results = self.cursor.fetchall()
            if results:
                optimizations = [Optimization(*result) for result in results]
        except:
            print(traceback.format_exc())
        return optimizations


    def insertOptimization(self, optimization):
        optimizationId = -1
        try:
            sql = "INSERT INTO Optimization ("
            sql = sql + "Symbol, Timeframe, CreatedDate, StartDate, EndDate, CombinationCount, DurationInMinutes, BestSpId, BestBacktestId"
            sql = sql + ") "
            sql = sql + "VALUES (%s,%s,%s,%s,%s,%s,%s,%s,%s)"

            values = (
            optimization.Symbol, optimization.Timeframe, optimization.CreatedDate, optimization.StartDate, optimization.EndDate, optimization.CombinationCount, optimization.DurationInMinutes,
            optimization.BestSpId, optimization.BestBacktestId
            )

            self.cursor.execute(sql, values)
            optimizationId = self.cursor.lastrowid
            self.db.commit()

        except:
            print(traceback.format_exc())

        return optimizationId

    def updateOptimization(self, optimization):
        try:
            sql = "UPDATE Optimization SET "
            sql = sql + "Symbol = %s, Timeframe = %s, CreatedDate = %s, StartDate = %s, EndDate = %s, CombinationCount = %s, DurationInMinutes = %s, BestSpId = %s, BestBacktestId = %s"

            sql = sql + " WHERE OptimizationId = %s"

            values = (
            optimization.Symbol, optimization.Timeframe, optimization.CreatedDate, optimization.StartDate, optimization.EndDate, optimization.CombinationCount, optimization.DurationInMinutes,
            optimization.BestSpId, optimization.BestBacktestId, optimization.OptimizationId
            )

            self.cursor.execute(sql, values)
            self.db.commit()

        except:
            print(traceback.format_exc())


    def deleteOptimization(self, optimization_id):
        try:
            sql = "DELETE FROM Optimization WHERE OptimizationId = %s"
            values = (optimization_id,)
            self.cursor.execute(sql, values)
            self.db.commit()
        except:
            print(traceback.format_exc())
