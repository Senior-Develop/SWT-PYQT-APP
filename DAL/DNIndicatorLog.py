from Common.IndicatorLog import IndicatorLog
from DAL.DNBase import DNBase
import traceback
from datetime import datetime, timedelta


class DNIndicatorLog(DNBase):
    def getIndicatorLog(self, iLog_id):
        iLog = None
        try:
            sql = "SELECT * FROM IndicatorLog WHERE IndicatorLogId = %s"
            values = (iLog_id,)
            self.cursor.execute(sql, values)
            result = self.cursor.fetchone()
            if result:
                iLog = IndicatorLog(*result)
        except:
            print(traceback.format_exc())
        return iLog

    def getIndicatorLogBySymbol(self, symbol):
        iLog = None
        try:
            sql = "SELECT * FROM IndicatorLog WHERE Symbol = %s"
            values = (symbol,)
            self.cursor.execute(sql, values)
            result = self.cursor.fetchone()
            if result:
                iLog = IndicatorLog(*result)
        except:
            print(traceback.format_exc())
        return iLog

    def listIndicatorLog(self):
        iLogs = []
        try:
            sql = "SELECT * FROM IndicatorLog ORDER BY IndicatorLogId desc LIMIT 1000"
            self.cursor.execute(sql)
            results = self.cursor.fetchall()
            if results:
                iLogs = [IndicatorLog(*result) for result in results]
        except:
            print(traceback.format_exc())
        return iLogs


    def listIndicatorLogBySymbol(self, symbol):
        iLogs = []
        try:
            sql = "SELECT * FROM IndicatorLog WHERE Symbol LIKE '%' %s '%' ORDER BY CreatedDate desc LIMIT 1000"
            values = (symbol,)
            self.cursor.execute(sql, values)
            results = self.cursor.fetchall()
            if results:
                iLogs = [IndicatorLog(*result) for result in results]
        except:
            print(traceback.format_exc())
        return iLogs

    def listIndicatorLogByBacktestId(self, backtestId):
        iLogs = []
        try:
            sql = "SELECT * FROM IndicatorLog WHERE BacktestId = %s ORDER BY CreatedDate desc"
            values = (backtestId,)
            self.cursor.execute(sql, values)
            results = self.cursor.fetchall()
            if results:
                iLogs = [IndicatorLog(*result) for result in results]
        except:
            print(traceback.format_exc())
        return iLogs

    """
    def listIndicatorLogForPullbackEntry(self, symbol, strategyName, dateFrom, targetPrice):
        iLogs = []
        try:
            if strategyName == "R_Buy":
                sql = "SELECT * FROM IndicatorLog WHERE Symbol = %s AND R_Signal = 1 AND CreatedDate >= %s AND CurrentPrice >= %s ORDER BY CreatedDate desc LIMIT 1"
            else:
                sql = "SELECT * FROM IndicatorLog WHERE Symbol = %s AND F_Signal = 1 AND CreatedDate >= %s AND CurrentPrice <= %s ORDER BY CreatedDate desc LIMIT 1"

            values = (symbol, dateFrom, targetPrice, )
            self.cursor.execute(sql, values)
            results = self.cursor.fetchall()
            if results:
                iLogs = [IndicatorLog(*result) for result in results]
        except:
            print(traceback.format_exc())
        return iLogs

    def listIndicatorLogForExpiredPullbackWait(self, symbol, strategyName, dateFrom, dateTo):
        iLogs = []
        try:
            #print(dateFrom)
            #print(dateTo)

            if strategyName == "R_Buy":
                sql = "SELECT * FROM IndicatorLog WHERE Symbol = %s AND R_Signal = 1 AND CreatedDate >= %s AND CreatedDate <= %s ORDER BY CreatedDate desc LIMIT 1"
            else:
                sql = "SELECT * FROM IndicatorLog WHERE Symbol = %s AND F_Signal = 1 AND CreatedDate >= %s AND CreatedDate <= %s ORDER BY CreatedDate desc LIMIT 1"

            values = (symbol, dateFrom, dateTo,)
            self.cursor.execute(sql, values)
            results = self.cursor.fetchall()
            if results:
                iLogs = [IndicatorLog(*result) for result in results]
        except:
            print(traceback.format_exc())
        return iLogs
    """

    def insertIndicatorLog(self, iLog):
        try:
            sql = "INSERT INTO IndicatorLog ("
            sql = sql + "Symbol, CreatedDate, CandleDate, CurrentPrice, R_ROC_Value, "
            sql = sql + "R_ROC_Signal, R_MPT_Value, R_NV_BuyPercent, R_NV_SellPercent, R_NV_NetVolume, "
            sql = sql + "R_ROC_MPT_Signal, Trend_Signal, EMAX_Signal, VSTOP_Signal, R_NV_Signal, R_Signal, F_ROC_Value, "
            sql = sql + "F_ROC_Signal, F_ROC_MPT_Signal, F_NV_Signal, F_Signal, S_ROC_Value, "
            sql = sql + "S_Rsi_Value, S_Stoch_Value, S_ROC_Signal, S_Rsi_Signal,"
            sql = sql + "S_Stoch_Signal, S_Signal, R_Open_Count, F_Open_Count, S_Open_Count, BacktestId"

            sql = sql + ") "
            sql = sql + "VALUES ("+"%s,"*31+"%s)"

            values = (iLog.Symbol, iLog.CreatedDate, iLog.CandleDate, iLog.CurrentPrice, iLog.R_ROC_Value,
                      iLog.R_ROC_Signal, iLog.R_MPT_Value, iLog.R_NV_BuyPercent, iLog.R_NV_SellPercent, iLog.R_NV_NetVolume,
                      iLog.R_ROC_MPT_Signal, iLog.Trend_Signal, iLog.EMAX_Signal, iLog.VSTOP_Signal, iLog.R_NV_Signal, iLog.R_Signal, iLog.F_ROC_Value,
                      iLog.F_ROC_Signal, iLog.F_ROC_MPT_Signal, iLog.F_NV_Signal, iLog.F_Signal, iLog.S_ROC_Value,
                      iLog.S_Rsi_Value, iLog.S_Stoch_Value, iLog.S_ROC_Signal, iLog.S_Rsi_Signal,
                      iLog.S_Stoch_Signal, iLog.S_Signal, iLog.R_Open_Count, iLog.F_Open_Count, iLog.S_Open_Count, iLog.BacktestId
                      )

            self.cursor.execute(sql, values)
            self.db.commit()
        except:
            print(traceback.format_exc())

    def updateIndicatorLog(self, iLog):
        try:
            sql = "UPDATE IndicatorLog SET "
            sql = sql + "Symbol = %s, CreatedDate = %s, CurrentPrice = %s, R_ROC_Value = %s, "
            sql = sql + "R_ROC_Signal = %s, R_MPT_Value = %s, R_NV_BuyPercent = %s, R_NV_SellPercent = %s, R_NV_NetVolume = %s, "
            sql = sql + "R_ROC_MPT_Signal = %s, Trend_Signal = %s, EMAX_Signal = %s, VSTOP_Signal = %s, R_NV_Signal = %s, R_Signal = %s, F_ROC_Value = %s, "
            sql = sql + "F_ROC_Signal = %s, F_ROC_MPT_Signal = %s, F_NV_Signal = %s, F_Signal = %s, S_ROC_Value = %s, "
            sql = sql + "S_Rsi_Value = %s, S_Stoch_Value = %s, S_ROC_Signal = %s, S_Rsi_Signal = %s, "
            sql = sql + "S_Stoch_Signal = %s, S_Signal = %s, R_Open_Count = %s, F_Open_Count = %s, S_Open_Count = %s"
            sql = sql + " WHERE IndicatorLogId = %s"

            values = (iLog.Symbol, iLog.CreatedDate, iLog.CandleDate, iLog.CurrentPrice,iLog.R_ROC_Value,
                      iLog.R_ROC_Signal, iLog.R_MPT_Value, iLog.R_NV_BuyPercent, iLog.R_NV_SellPercent, iLog.R_NV_NetVolume,
                      iLog.R_ROC_MPT_Signal, iLog.Trend_Signal, iLog.EMAX_Signal, iLog.VSTOP_Signal, iLog.R_NV_Signal, iLog.R_Signal, iLog.F_ROC_Value,
                      iLog.F_ROC_Signal, iLog.F_ROC_MPT_Signal, iLog.F_NV_Signal, iLog.F_Signal, iLog.S_ROC_Value,
                      iLog.S_Rsi_Value, iLog.S_Stoch_Value, iLog.S_ROC_Signal, iLog.S_Rsi_Signal,
                      iLog.S_Stoch_Signal, iLog.S_Signal, iLog.R_Open_Count, iLog.F_Open_Count, iLog.S_Open_Count, iLog.IndicatorLogId
                      )

            self.cursor.execute(sql, values)
            self.db.commit()
        except:

            print(traceback.format_exc())

    def deleteIndicatorLog(self, iLog_id):
        try:
            sql = "DELETE FROM IndicatorLog WHERE IndicatorLogId = %s"
            values = (iLog_id,)
            self.cursor.execute(sql, values)
            self.db.commit()
        except:
            print(traceback.format_exc())

    def truncateIndicatorLog(self):
        try:
            sql = "TRUNCATE TABLE IndicatorLog"
            self.cursor.execute(sql)
            self.db.commit()
        except:
            print(traceback.format_exc())