from Common.Market import Market
from DAL.DNBase import DNBase
import traceback
from datetime import datetime, timedelta


class DNMarket(DNBase):
    def getMarket(self, market_id):
        market = None
        try:
            sql = "SELECT * FROM Market WHERE MarketId = %s"
            values = (market_id,)
            self.cursor.execute(sql, values)
            result = self.cursor.fetchone()
            if result:
                market = Market(*result)
        except:
            print(traceback.format_exc())
        return market

    def getMarketBySymbol(self, symbol):
        market = None
        try:
            sql = "SELECT * FROM Market WHERE Symbol = %s"
            values = (symbol,)
            self.cursor.execute(sql, values)
            result = self.cursor.fetchone()
            if result:
                market = Market(*result)
        except:
            print(traceback.format_exc())
        return market

    def listMarket(self):
        markets = []
        try:
            sql = "SELECT * FROM Market WHERE QuoteAsset IN ('BTC','USDT','USD','ETH')"
            self.cursor.execute(sql)
            results = self.cursor.fetchall()
            if results:
                markets = [Market(*result) for result in results]
        except:
            print(traceback.format_exc())
        return markets

    def listMarketByQuoteAsset(self, btcEnabled, usdtEnabled, bnbEnabled, ethEnabled):
        markets = []
        try:
            quoteAssets = ""
            if btcEnabled:
                quoteAssets = quoteAssets + "'BTC',"
            if usdtEnabled:
                quoteAssets = quoteAssets + "'USDT',"
            if ethEnabled:
                quoteAssets = quoteAssets + "'ETH',"
            if bnbEnabled:
                quoteAssets = quoteAssets + "'USD',"

            if quoteAssets == "":
                return markets

            quoteAssets = quoteAssets[0:len(quoteAssets)-1]

            sql = "SELECT * FROM Market WHERE QuoteAsset IN (" + quoteAssets + ")"
            #print(sql)
            self.cursor.execute(sql)
            results = self.cursor.fetchall()
            if results:
                markets = [Market(*result) for result in results]

            #print(len(markets))
        except:
            print(traceback.format_exc())
        return markets

    def searchMarketBySymbol(self, searchString):
        markets = []
        try:
            sql = "SELECT * FROM Market WHERE Symbol LIKE '%' %s '%'"
            values = (searchString,)
            self.cursor.execute(sql, values)
            results = self.cursor.fetchall()
            if results:
                markets = [Market(*result) for result in results]

            #print(len(markets))
        except:
            print(traceback.format_exc())
        return markets


    def listSelectedMarkets(self):
        markets = []
        try:
            sql = "SELECT * FROM Market WHERE IsSelected = 1"
            self.cursor.execute(sql)
            results = self.cursor.fetchall()
            if results:
                markets = [Market(*result) for result in results]
        except:
            print(traceback.format_exc())
        return markets

    def listTradeableMarkets(self):
        markets = []
        try:
            sql = "SELECT * FROM Market WHERE IsTradable = 1 ORDER BY Symbol"
            self.cursor.execute(sql)
            results = self.cursor.fetchall()
            if results:
                markets = [Market(*result) for result in results]
        except:
            print(traceback.format_exc())
        return markets

    def listUnCheckedMarkets(self, days):
        markets = []
        try:
            cut_date = datetime.now() - timedelta(days=days)
            sql = "SELECT * FROM Market where CheckedDate is null or CheckedDate < '{}'".format(cut_date.strftime('%Y-%m-%d %H:%M:%S'))
            self.cursor.execute(sql)
            results = self.cursor.fetchall()
            if results:
                markets = [Market(*result) for result in results]
        except:
            print(traceback.format_exc())
        return markets

    def insertMarkets(self, markets):
        try:
            cursor = self.db.cursor()
            sql = 'INSERT INTO Market ' \
                  '(Symbol, BaseAsset, QuoteAsset, AmountDecimalDigits, MinQuantity, MinAmountToTrade) ' \
                  'VALUES (%s, %s, %s, %s, %s, %s) '\
                  'ON DUPLICATE KEY UPDATE ' \
                  'AmountDecimalDigits=VALUES(AmountDecimalDigits), ' \
                  'MinQuantity=VALUES(MinQuantity), ' \
                  'MinAmountToTrade=VALUES(MinAmountToTrade)'
            values = [(market.Symbol,
                       market.BaseAsset,
                       market.QuoteAsset,
                       market.AmountDecimalDigits,
                       market.MinQuantity,
                       market.MinAmountToTrade) for market in markets]
            cursor.executemany(sql, values)
            self.db.commit()
            #print("{} record(s) affected.".format(cursor.rowcount))
        except:
            print(traceback.format_exc())

    def makeMarketsNonTradable(self, quote_asset):
        try:
            cursor = self.db.cursor()
            sql = 'UPDATE Market SET ' \
                  'IsTradable = 0 ' \
                  'WHERE QuoteAsset IN ' + str(tuple(quote_asset))
            cursor.execute(sql)
            self.db.commit()
            #print("{} record(s) affected.".format(cursor.rowcount))
        except:
            print(traceback.format_exc())

    def makeAllMarketsNonTradable(self):
        try:
            cursor = self.db.cursor()
            sql = 'UPDATE Market SET ' \
                  'IsTradable = 0 '
            cursor.execute(sql)
            self.db.commit()
            #print("{} record(s) affected.".format(cursor.rowcount))
        except:
            print(traceback.format_exc())

    def makeMarketsTradable(self, quoteAsset, dailyVolume, dailyPrice):
        try:
            sql = "UPDATE Market SET IsTradable = 1 WHERE QuoteAsset = %s AND DailyVolume >= %s AND DailyPrice >= %s"
            #sql = "UPDATE Market SET IsTradable = 1 WHERE QuoteAsset = %s AND DailyVolume >= %s"

            values = (quoteAsset, dailyVolume, dailyPrice)
            #values = (quoteAsset, )
            self.cursor.execute(sql, values)
            self.db.commit()
            #print("{} record(s) affected.".format(self.cursor.rowcount))
        except:
            print(traceback.format_exc())

    def addSelectedMarket(self, symbol):
        try:
            sql = "UPDATE Market SET "
            sql = sql + "IsSelected = 1"
            sql = sql + " WHERE Symbol = %s"

            values = (symbol,)

            self.cursor.execute(sql, values)
            self.db.commit()

        except:
            print(traceback.format_exc())

    def resetSelectedMarket(self):
        try:
            sql = "UPDATE Market SET "
            sql = sql + "IsSelected = 0"

            self.cursor.execute(sql, )
            self.db.commit()

        except:
            print(traceback.format_exc())

    def deleteSelectedMarket(self, marketId):
        try:
            sql = "UPDATE Market SET "
            sql = sql + "IsSelected = %s"
            sql = sql + " WHERE MarketId = %s"

            values = (False, marketId)

            self.cursor.execute(sql, values)
            self.db.commit()
        except:
            print(traceback.format_exc())


    def insertMarket(self, market):
        try:
            sql = "INSERT INTO Market ("
            sql = sql + "Symbol, BaseAsset, QuoteAsset, "
            sql = sql + "AmountDecimalDigits, MinQuantity, MinAmountToTrade, "
            sql = sql + "IsSelected, LastPrice, R_ROC_Value, "
            sql = sql + "R_ROC_Signal, R_MPT_Value, R_NV_BuyPercent, R_NV_SellPercent, R_NV_NetVolume,  "
            sql = sql + "R_ROC_MPT_Signal, Trend_Signal, EMAX_Signal, VSTOP_Signal, R_NV_Signal, F_NV_Signal, R_Signal, F_ROC_Value, "
            sql = sql + "F_ROC_Signal, F_ROC_MPT_Signal, F_Signal, S_ROC_Value, "
            sql = sql + "S_Rsi_Value, S_Stoch_Value, S_ROC_Signal, S_Rsi_Signal,"
            sql = sql + "S_Stoch_Signal, S_Signal, ModifiedDate, CheckedDate, DailyPrice, DailyVolume  "


            sql = sql + ") "
            sql = sql + "VALUES (%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s)"

            values = (market.Symbol, market.BaseAsset, market.QuoteAsset,
                      market.AmountDecimalDigits, market.MinQuantity, market.MinAmountToTrade,
                      market.IsSelected, market.LastPrice, market.R_ROC_Value, market.R_ROC_Signal, market.R_MPT_Value,
                      market.R_NV_BuyPercent, market.R_NV_SellPercent, market.R_NV_NetVolume, market.R_ROC_MPT_Signal,
                      market.Trend_Signal, market.EMAX_Signal, market.VSTOP_Signal, market.R_NV_Signal, market.R_Signal, market.F_ROC_Value,
                      market.F_ROC_Signal, market.F_ROC_MPT_Signal, market.F_Signal, market.S_ROC_Value,
                      market.S_Rsi_Value, market.S_Stoch_Value, market.S_ROC_Signal, market.S_Rsi_Signal,
                      market.S_Stoch_Signal, market.S_Signal, market.ModifiedDate, market.CheckedDate, market.DailyPrice, market.DailyVolume
                      )

            self.cursor.execute(sql, values)
            self.db.commit()
        except:
            print(traceback.format_exc())

    def updateMarket(self, market):
        try:
            sql = "UPDATE Market SET "
            sql = sql + "BaseAsset = %s, QuoteAsset = %s, AmountDecimalDigits = %s, MinQuantity = %s, "
            sql = sql + "MinAmountToTrade = %s, IsSelected = %s, LastPrice = %s, R_ROC_Value = %s, "
            sql = sql + "R_ROC_Signal = %s, R_MPT_Value = %s, R_NV_BuyPercent = %s, R_NV_SellPercent = %s, R_NV_NetVolume = %s, "
            sql = sql + "R_ROC_MPT_Signal = %s, Trend_Signal = %s, EMAX_Signal = %s, VSTOP_Signal = %s, R_NV_Signal = %s, F_NV_Signal = %s, R_Signal = %s, F_ROC_Value = %s, "
            sql = sql + "F_ROC_Signal = %s, F_ROC_MPT_Signal = %s, F_Signal = %s, S_ROC_Value = %s, "
            sql = sql + "S_Rsi_Value = %s, S_Stoch_Value = %s, S_ROC_Signal = %s, S_Rsi_Signal = %s, "
            sql = sql + "S_Stoch_Signal = %s, S_Signal = %s, ModifiedDate = %s, CheckedDate = %s, IsTradable = %s, DailyPrice = %s, DailyVolume = %s"
            sql = sql + " WHERE Symbol = %s"

            values = (market.BaseAsset, market.QuoteAsset, market.AmountDecimalDigits, market.MinQuantity,
                      market.MinAmountToTrade, market.IsSelected, market.LastPrice, market.R_ROC_Value,
                      market.R_ROC_Signal, market.R_MPT_Value, market.R_NV_BuyPercent, market.R_NV_SellPercent, market.R_NV_NetVolume,
                      market.R_ROC_MPT_Signal, market.Trend_Signal, market.EMAX_Signal, market.VSTOP_Signal, market.R_NV_Signal, market.F_NV_Signal, market.R_Signal, market.F_ROC_Value,
                      market.F_ROC_Signal, market.F_ROC_MPT_Signal, market.F_Signal, market.S_ROC_Value,
                      market.S_Rsi_Value, market.S_Stoch_Value, market.S_ROC_Signal, market.S_Rsi_Signal,
                      market.S_Stoch_Signal, market.S_Signal,
                      market.ModifiedDate, market.CheckedDate, market.IsTradable, market.DailyPrice, market.DailyVolume,
                      market.Symbol
                      )

            self.cursor.execute(sql, values)
            self.db.commit()
        except:
            print(traceback.format_exc())

    def updateMarketStats(self, market):
        try:
            sql = "INSERT INTO Market ("
            sql = sql + "Symbol, LastPrice, R_ROC_Value, "
            sql = sql + "R_ROC_Signal, R_MPT_Value, R_NV_BuyPercent, R_NV_SellPercent, R_NV_NetVolume, R_ROC_MPT_Signal, "
            sql = sql + "Trend_Signal, EMAX_Signal,  VSTOP_Signal, R_NV_Signal, F_NV_Signal, R_Signal, F_ROC_Value, "
            sql = sql + "F_ROC_Signal, F_ROC_MPT_Signal, F_Signal, S_ROC_Value, "
            sql = sql + "S_Rsi_Value, S_Stoch_Value, S_ROC_Signal, S_Rsi_Signal,"
            sql = sql + "S_Stoch_Signal, S_Signal, ModifiedDate "
            sql = sql + ") "
            sql = sql + "VALUES (%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s) "
            sql = sql + "ON DUPLICATE KEY UPDATE "
            sql = sql + "LastPrice=VALUES(LastPrice), " \
                        "R_ROC_Value=VALUES(R_ROC_Value), " \
                        "R_ROC_Signal=VALUES(R_ROC_Signal), " \
                        "R_MPT_Value=VALUES(R_MPT_Value), " \
                        "R_NV_BuyPercent=VALUES(R_NV_BuyPercent), " \
                        "R_NV_SellPercent=VALUES(R_NV_SellPercent), "\
                        "R_NV_NetVolume=VALUES(R_NV_NetVolume), " \
                        "R_ROC_MPT_Signal=VALUES(R_ROC_MPT_Signal), " \
                        "Trend_Signal=VALUES(Trend_Signal), " \
                        "EMAX_Signal=VALUES(EMAX_Signal), " \
                        "VSTOP_Signal=VALUES(VSTOP_Signal), " \
                        "R_NV_Signal=VALUES(R_NV_Signal), " \
                        "F_NV_Signal=VALUES(F_NV_Signal), " \
                        "R_Signal=VALUES(R_Signal), " \
                        "F_ROC_Value=VALUES(F_ROC_Value), " \
                        "F_ROC_Signal=VALUES(F_ROC_Signal), " \
                        "F_ROC_MPT_Signal=VALUES(F_ROC_MPT_Signal), " \
                        "F_Signal=VALUES(F_Signal), " \
                        "S_ROC_Value=VALUES(S_ROC_Value), " \
                        "S_Rsi_Value=VALUES(S_Rsi_Value), " \
                        "S_Stoch_Value=VALUES(S_Stoch_Value), " \
                        "S_ROC_Signal=VALUES(S_ROC_Signal), " \
                        "S_Rsi_Signal=VALUES(S_Rsi_Signal), " \
                        "S_Stoch_Signal=VALUES(S_Stoch_Signal), " \
                        "S_Signal=VALUES(S_Signal), " \
                        "ModifiedDate=VALUES(ModifiedDate)"
            values = (market.Symbol, market.LastPrice, market.R_ROC_Value,
                      market.R_ROC_Signal, market.R_MPT_Value, market.R_NV_BuyPercent, market.R_NV_SellPercent, market.R_NV_NetVolume,
                      market.R_ROC_MPT_Signal, market.Trend_Signal, market.EMAX_Signal, market.VSTOP_Signal, market.R_NV_Signal, market.F_NV_Signal, market.R_Signal, market.F_ROC_Value,
                      market.F_ROC_Signal, market.F_ROC_MPT_Signal, market.F_Signal, market.S_ROC_Value,
                      market.S_Rsi_Value, market.S_Stoch_Value, market.S_ROC_Signal, market.S_Rsi_Signal,
                      market.S_Stoch_Signal, market.S_Signal, market.ModifiedDate
                      )

            #print(values)

            self.cursor.execute(sql, values)
            self.db.commit()
        except:
            print(traceback.format_exc())

    def deleteMarket(self, market_id):
        try:
            sql = "DELETE FROM Market WHERE MarketId = %s"
            values = (market_id,)
            self.cursor.execute(sql, values)
            self.db.commit()
        except:
            print(traceback.format_exc())
