from Common.TickData import TickData
from DAL.DNBase import DNBase
import traceback


class DNTickData(DNBase):
    def getTickData(self, botlog_id):
        tickData = None
        try:
            sql = "SELECT * FROM TickData WHERE TickDataId = %s"
            values = (botlog_id,)
            self.cursor.execute(sql, values)
            result = self.cursor.fetchone()
            if result:
                tickData = TickData(*result)
        except:
            print(traceback.format_exc())
        return tickData

    def listTickDataLast(self):
        items = None
        try:
            sql = "SELECT * FROM TickData ORDER BY TickDataId desc LIMIT 10"

            self.cursor.execute(sql)
            results = self.cursor.fetchall()
            if results:
                items = [TickData(*result) for result in results]
        except:
            print(traceback.format_exc())
        return items

    def listTickData(self, dateFrom, dateTo):
        items = None
        try:
            sql = "SELECT * FROM TickData WHERE OpenTime >= %s AND OpenTime < DATE_ADD(%s, INTERVAL 1 MINUTE) ORDER BY EventTime asc, TickDataId asc"

            values = (dateFrom, dateTo,)
            self.cursor.execute(sql, values)
            results = self.cursor.fetchall()
            if results:
                items = [TickData(*result) for result in results]
        except:
            print(traceback.format_exc())
        return items


    def listTickDataBySymbol(self, symbol, dateFrom, dateTo):
        items = None
        try:
            sql = "SELECT * FROM TickData WHERE Symbol = %s AND OpenTime >= %s AND OpenTime < DATE_ADD(%s, INTERVAL 1 MINUTE) ORDER BY EventTime asc, TickDataId asc"

            values = (symbol, dateFrom, dateTo, )
            self.cursor.execute(sql, values)
            results = self.cursor.fetchall()
            if results:
                items = [TickData(*result) for result in results]
        except:
            print(traceback.format_exc())
        return items

    def insertTickData(self, tickData):
        trades = None
        try:
            sql = "INSERT INTO TickData ("
            sql = sql + "Symbol, Timeframe, Close, Open, High, Low, OpenTime, CloseTime, NumTrades, Volume, QuoteAssetVolume, TakerBuyBaseAssetVolume, TakerBuyQuoteAssetVolume, CreatedDate, EventTime"
            sql = sql + ") "
            sql = sql + "VALUES (%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s)"

            values = (tickData.Symbol, tickData.Timeframe, tickData.Close, tickData.Open, tickData.High, tickData.Low,
                      tickData.OpenTime, tickData.CloseTime, tickData.NumTrades, tickData.Volume,
                      tickData.QuoteAssetVolume, tickData.TakerBuyBaseAssetVolume, tickData.TakerBuyQuoteAssetVolume, tickData.CreatedDate, tickData.EventTime,)

            self.cursor.execute(sql, values)
            self.db.commit()

        except:
            print(traceback.format_exc())
        return trades

    def deleteTickData(self, tickdata_id):
        tickData = None
        try:
            sql = "DELETE FROM TickData WHERE TickDataId = %s"
            values = (tickdata_id,)
            self.cursor.execute(sql, values)
            self.db.commit()

        except:
            print(traceback.format_exc())
        return tickData

    def truncateTickData(self):
        try:
            sql = "TRUNCATE TABLE TickData"
            self.cursor.execute(sql)
            self.db.commit()
        except:
            print(traceback.format_exc())