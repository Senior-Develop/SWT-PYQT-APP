from Common.Signal import Signal
from DAL.DNBase import DNBase
import traceback
from datetime import datetime, timedelta


class DNSignal(DNBase):
    def getSignal(self, signal_id):
        signal = None
        try:
            sql = "SELECT * FROM TradeSignal WHERE SignalId = %s"
            values = (signal_id,)
            self.cursor.execute(sql, values)
            result = self.cursor.fetchone()
            if result:
                signal = Signal(*result)
        except:
            print(traceback.format_exc())
        return signal

    def getSignalBySymbol(self, symbol):
        signal = None
        try:
            sql = "SELECT * FROM TradeSignal WHERE Symbol = %s"
            values = (symbol,)
            self.cursor.execute(sql, values)
            result = self.cursor.fetchone()
            if result:
                signal = Signal(*result)
        except:
            print(traceback.format_exc())
        return signal

    def listSignal(self):
        signals = []
        try:
            sql = "SELECT * FROM TradeSignal ORDER BY SignalId desc LIMIT 1000"
            self.cursor.execute(sql)
            results = self.cursor.fetchall()
            if results:
                signals = [Signal(*result) for result in results]
        except:
            print(traceback.format_exc())
        return signals


    def listSignalBySymbol(self, symbol):
        signals = []
        try:
            sql = "SELECT * FROM TradeSignal WHERE Symbol LIKE '%' %s '%' ORDER BY CreatedDate desc LIMIT 1000"
            values = (symbol,)
            self.cursor.execute(sql, values)
            results = self.cursor.fetchall()
            if results:
                signals = [Signal(*result) for result in results]
        except:
            print(traceback.format_exc())
        return signals

    def listSignalForPullbackEntry(self, symbol, strategyName, dateFrom, targetPrice, backtestId=0):
        signals = []
        try:
            if strategyName == "R_Buy":
                sql = "SELECT * FROM TradeSignal WHERE BacktestId = %s AND Symbol = %s AND StrategyName = %s AND CreatedDate >= %s AND CurrentPrice >= %s ORDER BY CreatedDate desc LIMIT 1"
            else:
                sql = "SELECT * FROM TradeSignal WHERE BacktestId = %s AND Symbol = %s AND StrategyName = %s AND CreatedDate >= %s AND CurrentPrice <= %s ORDER BY CreatedDate desc LIMIT 1"

            values = (backtestId, symbol, strategyName, dateFrom, targetPrice, )
            self.cursor.execute(sql, values)
            results = self.cursor.fetchall()
            if results:
                signals = [Signal(*result) for result in results]
        except:
            print(traceback.format_exc())
        return signals

    def listSignalForExpiredPullbackWait(self, symbol, strategyName, dateFrom, dateTo, backtestId=0):
        signals = []
        try:
            sql = "SELECT * FROM TradeSignal WHERE BacktestId = %s AND Symbol = %s AND StrategyName = %s AND CreatedDate >= %s AND CreatedDate <= %s ORDER BY CreatedDate desc LIMIT 1"

            values = (backtestId, symbol, strategyName, dateFrom, dateTo,)
            self.cursor.execute(sql, values)
            results = self.cursor.fetchall()
            if results:
                signals = [Signal(*result) for result in results]
        except:
            print(traceback.format_exc())
        return signals

    def insertSignal(self, signal):
        try:
            sql = "INSERT INTO TradeSignal ("
            sql = sql + "Symbol, CreatedDate, CandleDate, CurrentPrice, StrategyName, BacktestId"
            sql = sql + ") "
            sql = sql + "VALUES (%s,%s,%s,%s,%s,%s)"

            values = (signal.Symbol, signal.CreatedDate, signal.CandleDate, signal.CurrentPrice, signal.StrategyName, signal.BacktestId)

            self.cursor.execute(sql, values)
            self.db.commit()
        except:
            print(traceback.format_exc())

    def deleteSignal(self, signal_id):
        try:
            sql = "DELETE FROM TradeSignal WHERE SignalId = %s"
            values = (signal_id,)
            self.cursor.execute(sql, values)
            self.db.commit()
        except:
            print(traceback.format_exc())
