from Common.OptimizationRun import OptimizationRun
from DAL.DNBase import DNBase
import traceback


class DNOptimizationRun(DNBase):
    def getOptimizationRun(self, optimizationRun_id):
        optimizationRun = None
        try:
            sql = "SELECT * FROM OptimizationRun WHERE OptimizationRunId = %s"
            values = (optimizationRun_id,)
            self.cursor.execute(sql, values)
            result = self.cursor.fetchone()
            if result:
                optimizationRun = OptimizationRun(*result)
        except:
            print(traceback.format_exc())
        return optimizationRun

    def getOptimizationRunBySymbol(self, symbol):
        optimizationRun = None
        try:
            sql = "SELECT * FROM OptimizationRun WHERE Symbol = %s"
            values = (symbol,)
            self.cursor.execute(sql, values)
            result = self.cursor.fetchone()
            if result:
                optimizationRun = OptimizationRun(*result)
        except:
            print(traceback.format_exc())
        return optimizationRun

    def listOptimizationRun(self, limit=100):
        optimizationRuns = []
        try:
            if limit == 0:
                sql = "SELECT * FROM OptimizationRun ORDER BY OptimizationRunId desc"
            else:
                sql = "SELECT * FROM OptimizationRun ORDER BY OptimizationRunId desc LIMIT " + str(limit)

            self.cursor.execute(sql)
            results = self.cursor.fetchall()
            if results:
                optimizationRuns = [OptimizationRun(*result) for result in results]
        except:
            print(traceback.format_exc())
        return optimizationRuns

    def listOptimizationRunByOptimizationId(self, optimizationId):
        optimizationRuns = []
        try:
            sql = "SELECT * FROM OptimizationRun WHERE OptimizationId = %s ORDER BY OptimizationRunId desc"
            values = (optimizationId,)
            self.cursor.execute(sql,values)
            results = self.cursor.fetchall()
            if results:
                optimizationRuns = [OptimizationRun(*result) for result in results]
        except:
            print(traceback.format_exc())
        return optimizationRuns

    def insertOptimizationRun(self, optimizationRun):
        optimizationRunId = -1

        try:
            sql = "INSERT INTO OptimizationRun ("
            sql = sql + "OptimizationId, Symbol, Timeframe, CreatedDate, StartDate, EndDate, CombinationCount, DurationInMinutes, BestSpId, BestBacktestId, PLPercentage, State"
            sql = sql + ") "
            sql = sql + "VALUES (%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s)"

            values = (
            optimizationRun.OptimizationId, optimizationRun.Symbol, optimizationRun.Timeframe, optimizationRun.CreatedDate, optimizationRun.StartDate, optimizationRun.EndDate, optimizationRun.CombinationCount, optimizationRun.DurationInMinutes,
            optimizationRun.BestSpId, optimizationRun.BestBacktestId, optimizationRun.PLPercentage, optimizationRun.State
            )

            self.cursor.execute(sql, values)
            optimizationRunId = self.cursor.lastrowid
            self.db.commit()

        except:
            print(traceback.format_exc())

        return optimizationRunId

    def updateOptimizationRun(self, optimizationRun):
        try:
            sql = "UPDATE OptimizationRun SET "
            sql = sql + "OptimizationId = %s, Symbol = %s, Timeframe = %s, CreatedDate = %s, StartDate = %s, EndDate = %s, CombinationCount = %s, DurationInMinutes = %s, BestSpId = %s, BestBacktestId = %s, PLPercentage = %s, State = %s"

            sql = sql + " WHERE OptimizationRunId = %s"

            values = (
            optimizationRun.OptimizationId, optimizationRun.Symbol, optimizationRun.Timeframe, optimizationRun.CreatedDate, optimizationRun.StartDate, optimizationRun.EndDate, optimizationRun.CombinationCount, optimizationRun.DurationInMinutes,
            optimizationRun.BestSpId, optimizationRun.BestBacktestId, optimizationRun.PLPercentage, optimizationRun.State, optimizationRun.OptimizationRunId
            )

            self.cursor.execute(sql, values)
            self.db.commit()

        except:
            print(traceback.format_exc())


    def deleteOptimizationRun(self, optimizationRun_id):
        try:
            sql = "DELETE FROM OptimizationRun WHERE OptimizationRunId = %s"
            values = (optimizationRun_id,)
            self.cursor.execute(sql, values)
            self.db.commit()
        except:
            print(traceback.format_exc())
