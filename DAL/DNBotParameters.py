from Common.BotParameters import BotParameters
from DAL.DNBase import DNBase
import traceback
from Utils.Encryption import Encryption

class DNBotParameters(DNBase):
    def getBotParameters(self):
        botPar = None
        try:
            sql = "SELECT * FROM BotParameters WHERE BotParametersId = %s"
            values = (1,)
            self.cursor.execute(sql, values)
            result = self.cursor.fetchone()
            if result:
                botPar = BotParameters(*result)
                enc = Encryption()
                botPar.apiKey = enc.decrypt_message(botPar.apiKey)
                botPar.secretKey = enc.decrypt_message(botPar.secretKey)

        except:
            print(traceback.format_exc())
        return botPar

    def listBotParameters(self):
        botPars = None
        try:
            sql = "SELECT * FROM BotParameters"
            self.cursor.execute(sql)
            results = self.cursor.fetchall()
            if results:
                botPars = [BotParameters(*result) for result in results]
                enc = Encryption()
                botPars[0].apiKey = enc.decrypt_message(botPars[0].apiKey)
                botPars[0].secretKey = enc.decrypt_message(botPars[0].secretKey)
        except:
            print(traceback.format_exc())
        return botPars

    def insertBotParameters(self, botPar):
        botPars = None
        try:
            enc = Encryption()
            botPar.apiKey = enc.encrypt_message(botPar.apiKey)
            botPar.secretKey = enc.encrypt_message(botPar.secretKey)

            sql = "INSERT INTO BotParameters ("
            sql = sql + "ApiKey, SecretKey, MaxConcurrentTradeNumber, MinPrice, MinDailyVolume, BankingPercentage,"
            sql = sql + "RunOnSelectedMarkets, MarketUpdateDate, OptimizationMode, OptStartDate, OptEndDate, OptTimeframe, OptSymbol, OptUpdateStrategyParameters"

            sql = sql + ") "
            sql = sql + "VALUES (%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s)"


            values = (
            botPar.apiKey, botPar.secretKey, botPar.maxConcurrentTradeNumber, botPar.minPrice, botPar.minDailyVolume,
            botPar.bankingPercentage, botPar.runOnSelectedMarkets, botPar.marketUpdateDate, botPar.optimizationMode,
            botPar.optStartDate,botPar.optEndDate,botPar.optTimeframe,botPar.optSymbol,botPar.optUpdateStrategyParameters,
            )

            self.cursor.execute(sql, values)
            self.db.commit()

        except:
            print(traceback.format_exc())
        return botPars

    def updateBotParameters(self, botPar):
        botPars = None
        try:
            enc = Encryption()
            botPar.apiKey = enc.encrypt_message(botPar.apiKey)
            botPar.secretKey = enc.encrypt_message(botPar.secretKey)

            sql = "UPDATE BotParameters SET "

            sql = sql + "ApiKey = %s, SecretKey = %s, MaxConcurrentTradeNumber = %s, "
            sql = sql + "MinPrice = %s, MinDailyVolume = %s, BankingPercentage = %s, RunOnSelectedMarkets = %s, MarketUpdateDate = %s, OptimizationMode = %s, OptUpdateStrategyParameters = %s"

            sql = sql + " WHERE BotParametersId = %s"

            values = (botPar.apiKey, botPar.secretKey, botPar.maxConcurrentTradeNumber, botPar.minPrice, botPar.minDailyVolume, botPar.bankingPercentage, botPar.runOnSelectedMarkets, botPar.marketUpdateDate, botPar.optimizationMode, botPar.optUpdateStrategyParameters, 1,)

            self.cursor.execute(sql, values)
            self.db.commit()

        except:
            print(traceback.format_exc())
        return botPars

    def updateControlValues(self, botPar):
        botPars = None
        try:
            sql = "UPDATE BotParameters SET "

            sql = sql + "OptStartDate = %s, OptEndDate = %s, OptTimeframe = %s, OptSymbol = %s"

            sql = sql + " WHERE BotParametersId = %s"

            values = (botPar.optStartDate, botPar.optEndDate, botPar.optTimeframe, botPar.optSymbol, 1,)

            self.cursor.execute(sql, values)
            self.db.commit()

        except:
            print(traceback.format_exc())
        return botPars





    def deleteBotParameters(self, botPar_id):
        botPar = None
        try:
            sql = "DELETE FROM BotParameters WHERE BotParametersId = %s"
            values = (botPar_id,)
            self.cursor.execute(sql, values)
            self.db.commit()

        except:
            print(traceback.format_exc())
        return botPar
