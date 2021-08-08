from Common.Backtest import Backtest
from DAL.DNBase import DNBase
import traceback
from datetime import datetime, timedelta


class DNBacktest(DNBase):
    def getBacktest(self, backtest_id):
        backtest = None
        try:
            sql = "SELECT * FROM Backtest WHERE BacktestId = %s"
            values = (backtest_id,)
            self.cursor.execute(sql, values)
            result = self.cursor.fetchone()
            if result:
                backtest = Backtest(*result)
        except:
            print(traceback.format_exc())
        return backtest

    def getBacktestBySymbol(self, symbol):
        backtest = None
        try:
            sql = "SELECT * FROM Backtest WHERE Symbol = %s"
            values = (symbol,)
            self.cursor.execute(sql, values)
            result = self.cursor.fetchone()
            if result:
                backtest = Backtest(*result)
        except:
            print(traceback.format_exc())
        return backtest

    def listBacktest(self):
        backtests = []
        try:
            sql = "SELECT * FROM Backtest ORDER BY BacktestId desc"
            self.cursor.execute(sql)
            results = self.cursor.fetchall()
            if results:
                backtests = [Backtest(*result) for result in results]
        except:
            print(traceback.format_exc())
        return backtests

    def listBacktestBySuccess(self, optimizationRunId):
        backtests = []
        try:
            sql = "SELECT * FROM Backtest WHERE OptimizationRunId = %s ORDER BY PLPercentage desc LIMIT 10"
            values = (optimizationRunId,)
            self.cursor.execute(sql, values)

            results = self.cursor.fetchall()
            if results:
                backtests = [Backtest(*result) for result in results]
        except:
            print(traceback.format_exc())
        return backtests

    def insertBacktest(self, backtest):
        backtestId = -1
        try:
            sql = "INSERT INTO Backtest ("
            sql = sql + "Symbol, Timeframe, OptimizationRunId, CreatedDate, StartDate, EndDate, TickCount, DurationInMinutes, Params, SpId, SpCount, SpIndex,"
            sql = sql + "TotalTrades, TotalTradesPerHour, PLPercentage, PLAmount, PLAmountPerHour, PLUsd,"
            sql = sql + "AvgPLTrade, AvgPLPercentage, AvgTradeAmount, AvgTimeInTradeInMinutes"

            sql = sql + ") "
            sql = sql + "VALUES (%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s)"

            values = (
            backtest.Symbol, backtest.Timeframe, backtest.OptimizationRunId, backtest.CreatedDate, backtest.StartDate, backtest.EndDate, backtest.TickCount, backtest.DurationInMinutes,
            backtest.Params, backtest.SpId, backtest.SpCount, backtest.SpIndex, backtest.TotalTrades, backtest.TotalTradesPerHour, backtest.PLPercentage,
            backtest.PLAmount, backtest.PLAmountPerHour, backtest.PLUsd,
            backtest.AvgPLTrade, backtest.AvgPLPercentage, backtest.AvgTradeAmount,backtest.AvgTimeInTradeInMinutes
            )

            self.cursor.execute(sql, values)
            backtestId = self.cursor.lastrowid
            self.db.commit()

        except:
            print(traceback.format_exc())

        return backtestId

    def updateBacktest(self, backtest):
        try:
            sql = "UPDATE Backtest SET "
            sql = sql + "Symbol = %s, Timeframe = %s, OptimizationRunId = %s, CreatedDate = %s, StartDate = %s, EndDate = %s, TickCount = %s, DurationInMinutes = %s, Params = %s, SpId = %s, SpCount = %s, SpIndex = %s, "
            sql = sql + "TotalTrades = %s, TotalTradesPerHour = %s, PLPercentage = %s, PLAmount = %s, PLAmountPerHour = %s, PLUsd = %s, "
            sql = sql + "AvgPLTrade = %s, AvgPLPercentage = %s, AvgTradeAmount = %s, AvgTimeInTradeInMinutes = %s"

            sql = sql + " WHERE BacktestId = %s"

            values = (
            backtest.Symbol, backtest.Timeframe, backtest.OptimizationRunId, backtest.CreatedDate, backtest.StartDate, backtest.EndDate, backtest.TickCount, backtest.DurationInMinutes,
            backtest.Params, backtest.SpId, backtest.SpCount, backtest.SpIndex, backtest.TotalTrades, backtest.TotalTradesPerHour, backtest.PLPercentage,
            backtest.PLAmount, backtest.PLAmountPerHour, backtest.PLUsd,
            backtest.AvgPLTrade, backtest.AvgPLPercentage, backtest.AvgTradeAmount,backtest.AvgTimeInTradeInMinutes,backtest.BacktestId
            )

            self.cursor.execute(sql, values)
            self.db.commit()

        except:
            print(traceback.format_exc())


    def deleteBacktest(self, backtest_id):
        try:
            sql = "DELETE FROM Backtest WHERE BacktestId = %s"
            values = (backtest_id,)
            self.cursor.execute(sql, values)
            self.db.commit()
        except:
            print(traceback.format_exc())
