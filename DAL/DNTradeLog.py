from Common.TradeLog import TradeLog
from DAL.DNBase import DNBase
import traceback


class DNTradeLog(DNBase):
    def getTradeLog(self, tradelog_id):
        tradeLog = None
        try:
            sql = "SELECT * FROM TradeLog WHERE TradeLogId = %s"
            values = (tradelog_id,)
            self.cursor.execute(sql, values)
            result = self.cursor.fetchone()
            if result:
                tradeLog = TradeLog(*result)
        except:
            print(traceback.format_exc())
        return tradeLog

    def listTradeLog(self):
        items = None
        try:
            sql = "SELECT * FROM TradeLog ORDER BY CreatedDate desc LIMIT 1000"
            self.cursor.execute(sql)
            results = self.cursor.fetchall()
            if results:
                items = [TradeLog(*result) for result in results]
        except:
            print(traceback.format_exc())
        return items

    def listTradeLogByTradeId(self, tradeId):
        items = None
        try:
            sql = "SELECT * FROM TradeLog WHERE TradeId = %s ORDER BY CreatedDate desc"
            values = (tradeId,)
            self.cursor.execute(sql, values)
            results = self.cursor.fetchall()
            if results:
                items = [TradeLog(*result) for result in results]
        except:
            print(traceback.format_exc())
        return items

    def listTradeLogByBacktestId(self, backtestId):
        items = None
        try:
            sql = "SELECT * FROM TradeLog WHERE BacktestId = %s ORDER BY CreatedDate desc"
            values = (backtestId,)
            self.cursor.execute(sql, values)
            results = self.cursor.fetchall()
            if results:
                items = [TradeLog(*result) for result in results]
        except:
            print(traceback.format_exc())
        return items

    def listTradeLogBySymbol(self, symbol):
        items = None
        try:
            sql = "SELECT * FROM TradeLog WHERE Symbol = %s ORDER BY CreatedDate desc LIMIT 1000"
            values = (symbol,)
            self.cursor.execute(sql, values)
            results = self.cursor.fetchall()
            if results:
                items = [TradeLog(*result) for result in results]
        except:
            print(traceback.format_exc())
        return items

    def insertTradeLog(self, tradeLog):
        try:
            sql = "INSERT INTO TradeLog ("
            sql = sql + "TradeId, Symbol, CandleDate, CreatedDate, StrategyName, TradeType, Action, Comment, Amount, QuoteAmount, EntryPrice, CurrentPrice, StopLoss, PLAmount, PLPercentage, Commission, Balance, TargetPrice, BacktestId"
            sql = sql + ") "
            sql = sql + "VALUES (%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s)"

            values = (tradeLog.TradeId, tradeLog.Symbol, tradeLog.CandleDate, tradeLog.CreatedDate, tradeLog.StrategyName, tradeLog.TradeType, tradeLog.Action,
                      tradeLog.Comment, tradeLog.Amount, tradeLog.QuoteAmount, tradeLog.EntryPrice, tradeLog.CurrentPrice, tradeLog.StopLoss,
                      tradeLog.PLAmount, tradeLog.PLPercentage, tradeLog.Commission, tradeLog.Balance, tradeLog.TargetPrice, tradeLog.BacktestId,)

            self.cursor.execute(sql, values)
            self.db.commit()

        except:
            print(traceback.format_exc())


    def updateTradeLog(self, tradeLog):
        try:
            sql = "UPDATE TradeLog SET "

            sql = sql + "TradeId = %s, Symbol = %s, CandleDate = %s, CreatedDate = %s, StrategyName = %s, TradeType = %s, Action = %s, Comment = %s, Amount = %s,  QuoteAmount = %s,"
            sql = sql + "EntryPrice = %s, CurrentPrice = %s, StopLoss = %s, PLAmount = %s, PLPercentage = %s, Commission = %s, Balance = %s, TargetPrice = %s"
            sql = sql + " WHERE TradeLogId = %s"

            values = (tradeLog.TradeId, tradeLog.Symbol, tradeLog.CandleDate, tradeLog.CreatedDate, tradeLog.StrategyName, tradeLog.TradeType, tradeLog.Action,
                      tradeLog.Comment, tradeLog.Amount, tradeLog.QuoteAmount, tradeLog.EntryPrice, tradeLog.CurrentPrice, tradeLog.StopLoss,
                      tradeLog.PLAmount, tradeLog.PLAmount, tradeLog.PLPercentage, tradeLog.Commission,
                      tradeLog.Balance, tradeLog.TargetPrice, tradeLog.TradeLogId,)

            self.cursor.execute(sql, values)
            self.db.commit()

        except:
            print(traceback.format_exc())


    def deleteTradeLog(self, tradelog_id):
        try:
            sql = "DELETE FROM TradeLog WHERE TradeLogId = %s"
            values = (tradelog_id,)
            self.cursor.execute(sql, values)
            self.db.commit()

        except:
            print(traceback.format_exc())

    def truncateTradeLog(self):
        try:
            sql = "TRUNCATE TABLE TradeLog"
            self.cursor.execute(sql)
            self.db.commit()
        except:
            print(traceback.format_exc())