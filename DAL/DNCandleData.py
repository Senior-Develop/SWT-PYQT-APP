from Common.CandleData import CandleData
from DAL.DNBase import DNBase
import traceback


class DNCandleData(DNBase):
    def getCandleData(self, symbol, timeframe, openTimeInMillis):
        candleData = None
        try:
            sql = "SELECT * FROM CandleData WHERE Symbol = %s AND Timeframe = %s AND OpenTimeInMillis = %s LIMIT 1"
            values = (symbol,timeframe,openTimeInMillis,)
            self.cursor.execute(sql, values)
            result = self.cursor.fetchone()
            if result:
                candleData = CandleData(*result)
        except:
            print(traceback.format_exc())
        return candleData

    def listCandleDataLast(self):
        items = None
        try:
            sql = "SELECT * FROM CandleData ORDER BY CandleDataId desc LIMIT 10"

            self.cursor.execute(sql)
            results = self.cursor.fetchall()
            if results:
                items = [CandleData(*result) for result in results]
        except:
            print(traceback.format_exc())
        return items

    def insertCandleDataDownload(self, symbol, timeframe, dateFrom, dateTo, dateCurrent):
        trades = None
        try:
            sql = "INSERT INTO CandleDataDownload ("
            sql = sql + "Symbol, Timeframe, DateFrom, DateTo, CreatedDate"
            sql = sql + ") "
            sql = sql + "VALUES (%s,%s,%s,%s,%s)"

            values = (symbol, timeframe, dateFrom, dateTo, dateCurrent, )

            self.cursor.execute(sql, values)
            self.db.commit()

        except:
            print(traceback.format_exc())
        return trades

    def isCandleListDownloadedBefore(self, symbol, timeframe, dateFrom, dateTo):
        try:
            sql = "SELECT * FROM CandleDataDownload WHERE Symbol = %s AND Timeframe = %s AND DateFrom = %s AND DateTo = %s LIMIT 1"
            values = (symbol,timeframe,dateFrom,dateTo,)
            self.cursor.execute(sql, values)
            result = self.cursor.fetchone()
            if result:
                return True

        except:
            print(traceback.format_exc())
        return False

    def candleSetExists(self, symbol, timeframe, dateFrom, dateTo):
        timeFrameInMinutes = 1
        if timeframe == "5m":
            timeFrameInMinutes = 5
        elif timeframe == "15m":
            timeFrameInMinutes = 15

        #neededCandleNumber = (dateToInMillis - dateFromInMillis) / 1000 / 60 / timeFrameInMinutes

        minutes_diff = int((dateTo - dateFrom).total_seconds() / 60.0)
        neededCandleNumber = minutes_diff / timeFrameInMinutes + 1

        #print("candleSetExists: dateFrom:" + str(dateFrom))
        #print("candleSetExists: dateTo:" + str(dateTo))
        #print("candleSetExists: minutes_diff:" + str(minutes_diff))
        #print("candleSetExists: candleNumber needed:" + str(neededCandleNumber))

        exists = False
        count = 0
        items = None
        try:
            sql = "SELECT * FROM CandleData WHERE Symbol = %s AND Timeframe = %s AND OpenTime >= %s AND OpenTime <= %s"

            values = (symbol, timeframe, dateFrom, dateTo,)
            self.cursor.execute(sql,values)
            results = self.cursor.fetchall()
            if results:
                items = [CandleData(*result) for result in results]
                count = len(items)
                #print("count:" + str(count))
                #if count == neededCandleNumber :
                #    exists = True

                if items[0].OpenTime == dateFrom and items[len(items)-1].OpenTime == dateTo:
                    exists = True

                #if not exists:
                #    isDownloadedBefore = self.isCandleListDownloadedBefore(symbol, timeframe, dateFrom, dateTo)
                #    if isDownloadedBefore:
                #        print("Candles between these dates are downloaded before.")
                #        exists = True

        except:
            print(traceback.format_exc())

        #print("candleSetExists: candleNumber:" + str(count) + "/" + str(neededCandleNumber) + ", Exists: " + str(exists))

        return exists

    def listCandleData(self, symbol, timeframe, dateFrom, dateTo):
        items = None
        try:
            sql = "SELECT * FROM CandleData WHERE Symbol = %s AND Timeframe = %s AND OpenTime >= %s AND OpenTime <= %s ORDER BY OpenTime asc"
            values = (symbol, timeframe, dateFrom, dateTo,)
            self.cursor.execute(sql, values)
            results = self.cursor.fetchall()
            if results:
                items = [CandleData(*result) for result in results]
        except:
            print(traceback.format_exc())
        return items


    def listCandleDataBySymbol(self, symbol, dateFrom, dateTo):
        items = None
        try:
            sql = "SELECT * FROM CandleData WHERE Symbol = %s AND CreatedDate >= %s AND CreatedDate < DATE_ADD(%s, INTERVAL 1 MINUTE) ORDER BY EventTime asc"

            values = (symbol, dateFrom, dateTo, )
            self.cursor.execute(sql, values)
            results = self.cursor.fetchall()
            if results:
                items = [CandleData(*result) for result in results]
        except:
            print(traceback.format_exc())
        return items

    def insertCandleData(self, candleData):
        trades = None
        try:
            sql = "INSERT INTO CandleData ("
            sql = sql + "Symbol, Timeframe, Close, Open, High, Low, OpenTime, CloseTime, NumTrades, Volume, QuoteAssetVolume, TakerBuyBaseAssetVolume, TakerBuyQuoteAssetVolume, CreatedDate, OpenTimeInMillis, CloseTimeInMillis"
            sql = sql + ") "
            sql = sql + "VALUES (%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s)"

            values = (candleData.Symbol, candleData.Timeframe, candleData.Close, candleData.Open, candleData.High, candleData.Low,
                      candleData.OpenTime, candleData.CloseTime, candleData.NumTrades, candleData.Volume,
                      candleData.QuoteAssetVolume, candleData.TakerBuyBaseAssetVolume, candleData.TakerBuyQuoteAssetVolume, candleData.CreatedDate, candleData.OpenTimeInMillis, candleData.CloseTimeInMillis,)

            self.cursor.execute(sql, values)
            self.db.commit()

        except:
            print(traceback.format_exc())
        return trades

    def deleteCandleData(self, tickdata_id):
        candleData = None
        try:
            sql = "DELETE FROM CandleData WHERE CandleDataId = %s"
            values = (tickdata_id,)
            self.cursor.execute(sql, values)
            self.db.commit()

        except:
            print(traceback.format_exc())
        return candleData

    def truncateCandleData(self):
        try:
            sql = "TRUNCATE TABLE CandleData"
            self.cursor.execute(sql)
            self.db.commit()
        except:
            print(traceback.format_exc())