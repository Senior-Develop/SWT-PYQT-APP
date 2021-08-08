from Common.Trade import Trade
from DAL.DNBase import DNBase
import traceback


class DNTrade(DNBase):
    def getTrade(self, trade_id):
        trade = None
        try:
            sql = "SELECT * FROM Trade WHERE TradeId = %s"
            values = (trade_id,)
            self.cursor.execute(sql, values)
            result = self.cursor.fetchone()
            if result:
                trade = Trade(*result)
        except:
            print(traceback.format_exc())
        return trade

    def listTrade(self):
        trades = None
        try:
            sql = "SELECT * FROM Trade"
            self.cursor.execute(sql)
            results = self.cursor.fetchall()
            if results:
                trades = [Trade(*result) for result in results]
        except:
            print(traceback.format_exc())
        return trades

    def listTradeByDate(self, dateFrom, dateTo):
        trades = None
        try:
            sql = "SELECT * FROM Trade WHERE BacktestId = 0 AND EntryDate >= %s AND EntryDate < DATE_ADD(%s, INTERVAL 1 MINUTE)  ORDER BY EntryDate desc"
            values = (dateFrom, dateTo, )
            self.cursor.execute(sql,values)
            results = self.cursor.fetchall()
            if results:
                trades = [Trade(*result) for result in results]
        except:
            print(traceback.format_exc())
        return trades


    def listOpenTrade(self, backtestId=0):
        trades = None
        try:
            sql = "SELECT * FROM Trade WHERE BacktestId = %s AND IsOpen = 1 ORDER BY EntryDate DESC"
            values = (backtestId,)
            self.cursor.execute(sql, values)
            results = self.cursor.fetchall()
            if results:
                trades = [Trade(*result) for result in results]
        except:
            print(traceback.format_exc())
        return trades

    def listOpenTradeBySymbol(self, symbol, backtestId=0):
        trades = None
        try:
            sql = "SELECT * FROM Trade WHERE BacktestId = %s AND IsOpen = 1 AND Symbol = %s ORDER BY EntryDate DESC"
            values = (backtestId,symbol,)
            self.cursor.execute(sql, values)
            results = self.cursor.fetchall()
            if results:
                trades = [Trade(*result) for result in results]
        except:
            print(traceback.format_exc())
        return trades

    def listRebuyTrade(self, symbol, strategyName, dateFrom, rebuyLimit, backtestId=0):
        trades = None
        try:
            sql = "SELECT * FROM Trade WHERE BacktestId = %s AND Symbol = %s AND IsOpen = 0 AND StrategyName = %s AND ExitDate >= %s AND ReEntryNumber < %s ORDER BY ExitDate desc LIMIT 1"
            values = (backtestId, symbol, strategyName, dateFrom, rebuyLimit,)
            self.cursor.execute(sql, values)
            results = self.cursor.fetchall()
            if results:
                trades = [Trade(*result) for result in results]
        except:
            print(traceback.format_exc())
        return trades

    def listOpenTradeByBaseAsset(self, assetName):
        trades = None
        try:
            symbolList = "'" + assetName + "BTC',"
            symbolList = symbolList + "'" + assetName + "USDT',"
            symbolList = symbolList + "'" + assetName + "ETH',"
            symbolList = symbolList + "'" + assetName + "BNB'"

            sql = "SELECT * FROM Trade WHERE IsOpen = 1 AND Symbol IN (" + symbolList + ") ORDER BY EntryDate DESC"

            self.cursor.execute(sql)
            results = self.cursor.fetchall()
            if results:
                trades = [Trade(*result) for result in results]
        except:
            print(traceback.format_exc())
        return trades

    def listOpenTradeByQuoteAsset(self, assetName, backtestId=0):
        trades = None
        try:
            sql = "SELECT * FROM Trade WHERE BacktestId = 0 AND IsOpen = 1 AND Symbol LIKE '%" + assetName + "' ORDER BY EntryDate DESC"

            self.cursor.execute(sql)

            results = self.cursor.fetchall()
            if results:
                trades = [Trade(*result) for result in results]
        except:
            print(traceback.format_exc())
        return trades


    def listClosedTrade(self):
        trades = None
        try:
            sql = "SELECT * FROM Trade WHERE IsOpen = 0 ORDER BY ExitDate DESC LIMIT 1000"
            self.cursor.execute(sql)
            results = self.cursor.fetchall()
            if results:
                trades = [Trade(*result) for result in results]
        except:
            print(traceback.format_exc())
        return trades

    def listClosedTradeBySymbol(self, symbol):
        trades = None
        try:
            sql = "SELECT * FROM Trade WHERE IsOpen = 0 AND Symbol = %s ORDER BY ExitDate DESC LIMIT 1000"
            values = (symbol,)
            self.cursor.execute(sql, values)

            results = self.cursor.fetchall()
            if results:
                trades = [Trade(*result) for result in results]
        except:
            print(traceback.format_exc())
        return trades

    def listClosedTradeByBacktestId(self, backtestId):
        trades = None
        try:
            sql = "SELECT * FROM Trade WHERE IsOpen = 0 AND BacktestId = %s ORDER BY ExitDate DESC"
            values = (backtestId,)
            self.cursor.execute(sql, values)

            results = self.cursor.fetchall()
            if results:
                trades = [Trade(*result) for result in results]
        except:
            print(traceback.format_exc())
        return trades

    def insertTrade(self, trade):
        tradeId = 0
        try:
            sql = "INSERT INTO Trade ("
            sql = sql + "Symbol, StrategyName, IsOpen, TradeType, Amount, QuoteAmount, EntryPrice, ExitPrice, StopLoss, EntryDate, ExitDate, EntryCandleDate, TimerInSeconds, EntryTriggerPrice, ExitTriggerPrice, ModifiedDate, CurrentPrice, PLAmount, PLPercentage, EntryCommission, ExitCommission, TargetPrice, ReEntryNumber, IsTslActivated, BacktestId"
            sql = sql + ") "
            sql = sql + "VALUES (%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s)"

            values = (trade.Symbol, trade.StrategyName, trade.IsOpen, trade.TradeType, trade.Amount, trade.QuoteAmount, trade.EntryPrice,
                      trade.ExitPrice, trade.StopLoss, trade.EntryDate, trade.ExitDate, trade.EntryCandleDate, trade.TimerInSeconds,
                      trade.EntryTriggerPrice, trade.ExitTriggerPrice, trade.ModifiedDate, trade.CurrentPrice, trade.PLAmount, trade.PLPercentage, trade.EntryCommission, trade.ExitCommission, trade.TargetPrice, trade.ReEntryNumber, trade.IsTslActivated, trade.BacktestId,)

            self.cursor.execute(sql, values)
            tradeId = self.cursor.lastrowid
            self.db.commit()

        except:
            print(traceback.format_exc())
        return tradeId

    def updateTrade(self, trade):
        trades = None
        try:
            sql = "UPDATE Trade SET "

            sql = sql + "Symbol = %s, StrategyName = %s, IsOpen = %s, TradeType = %s, Amount = %s, QuoteAmount = %s, EntryPrice = %s, ExitPrice = %s,"
            sql = sql + "StopLoss = %s, EntryDate = %s, ExitDate = %s, EntryCandleDate = %s, TimerInSeconds = %s, EntryTriggerPrice = %s, ExitTriggerPrice = %s, ModifiedDate = %s, CurrentPrice = %s, PLAmount = %s, PLPercentage = %s, EntryCommission = %s, ExitCommission = %s, TargetPrice = %s, ReEntryNumber = %s, IsTslActivated = %s, BacktestId = %s"
            sql = sql + " WHERE TradeId = %s"

            values = (trade.Symbol, trade.StrategyName, trade.IsOpen, trade.TradeType, trade.Amount, trade.QuoteAmount, trade.EntryPrice,
                      trade.ExitPrice, trade.StopLoss, trade.EntryDate, trade.ExitDate, trade.EntryCandleDate, trade.TimerInSeconds,
                      trade.EntryTriggerPrice, trade.ExitTriggerPrice, trade.ModifiedDate, trade.CurrentPrice,
                      trade.PLAmount, trade.PLPercentage, trade.EntryCommission, trade.ExitCommission, trade.TargetPrice, trade.ReEntryNumber, trade.IsTslActivated, trade.BacktestId, trade.TradeId,)

            self.cursor.execute(sql, values)
            self.db.commit()

        except:
            print(traceback.format_exc())
        return trades

    def deleteTrade(self, trade_id):
        trade = None
        try:
            sql = "DELETE FROM Trade WHERE TradeId = %s"
            values = (trade_id,)
            self.cursor.execute(sql, values)
            self.db.commit()

        except:
            print(traceback.format_exc())
        return trade

    def truncateTrade(self):
        try:
            sql = "TRUNCATE TABLE Trade"
            self.cursor.execute(sql)
            self.db.commit()
        except:
            print(traceback.format_exc())

