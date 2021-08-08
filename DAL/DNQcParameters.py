from Common.QcParameters import QcParameters
from DAL.DNBase import DNBase
import traceback


class DNQcParameters(DNBase):
    def getQcParameters(self, asset):
        qcPar = None
        try:
            sql = "SELECT * FROM QcParameters WHERE asset = %s"
            values = (asset,)
            self.cursor.execute(sql, values)
            result = self.cursor.fetchone()
            if result:
                qcPar = QcParameters(*result)
        except:
            print(traceback.format_exc())
        return qcPar

    def listQcParameters(self):
        qcPars = None
        try:
            sql = "SELECT * FROM QcParameters"
            self.cursor.execute(sql)
            results = self.cursor.fetchall()
            if results:
                qcPars = [QcParameters(*result) for result in results]
        except:
            print(traceback.format_exc())
        return qcPars

    def insertQcParameters(self, qcPar):
        qcPars = None
        try:
            sql = "INSERT INTO QcParameters ("
            sql = sql + "Asset,"
            sql = sql + "MinVolume1, MaxVolume1, Perc1, MinVolume2, MaxVolume2, Perc2,"
            sql = sql + "MinVolume3, MaxVolume3, Perc3, MinVolume4, MaxVolume4, Perc4,"
            sql = sql + "MinVolume5, MaxVolume5, Perc5, MinVolume6, MaxVolume6, Perc6,"
            sql = sql + "DailySpendPerc, TradeEnabled"
            sql = sql + "RebuyTriggerAmount, RebuyAmount"

            sql = sql + ") "
            sql = sql + "VALUES (%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s)"

            values = (qcPar.asset, qcPar.minVolume1, qcPar.maxVolume1, qcPar.perc1,
                      qcPar.minVolume2, qcPar.maxVolume2, qcPar.perc2,
                      qcPar.minVolume3, qcPar.maxVolume3, qcPar.perc3,
                      qcPar.minVolume4, qcPar.maxVolume4, qcPar.perc4,
                      qcPar.minVolume5, qcPar.maxVolume5, qcPar.perc5,
                      qcPar.minVolume6, qcPar.maxVolume6, qcPar.perc6,qcPar.dailySpendPerc, qcPar.tradeEnabled
                      )

            self.cursor.execute(sql, values)
            self.db.commit()

        except:
            print(traceback.format_exc())
        return qcPars

    def updateQcParameters(self, qcPar):
        qcPars = None
        #print("updateQcParameters" + qcPar.asset)
        #print("minVolume1" + str(qcPar.minVolume1))
        #print("minVolume2" + str(qcPar.minVolume2))

        try:
            sql = "UPDATE QcParameters SET "

            sql = sql + "minVolume1 = %s, maxVolume1 = %s, perc1 = %s, "
            sql = sql + "minVolume2 = %s, maxVolume2 = %s, perc2 = %s, "
            sql = sql + "minVolume3 = %s, maxVolume3 = %s, perc3 = %s, "
            sql = sql + "minVolume4 = %s, maxVolume4 = %s, perc4 = %s, "
            sql = sql + "minVolume5 = %s, maxVolume5 = %s, perc5 = %s, "
            sql = sql + "minVolume6 = %s, maxVolume6 = %s, perc6 = %s, "
            sql = sql + "DailySpendPerc = %s, TradeEnabled = %s, RebuyTriggerAmount = %s, RebuyAmount = %s"

            sql = sql + " WHERE asset = %s"

           # print("sql" + sql)

            values = (qcPar.minVolume1, qcPar.maxVolume1, qcPar.perc1,
                      qcPar.minVolume2, qcPar.maxVolume2, qcPar.perc2,
                      qcPar.minVolume3, qcPar.maxVolume3, qcPar.perc3,
                      qcPar.minVolume4, qcPar.maxVolume4, qcPar.perc4,
                      qcPar.minVolume5, qcPar.maxVolume5, qcPar.perc5,
                      qcPar.minVolume6, qcPar.maxVolume6, qcPar.perc6,
                      qcPar.dailySpendPerc, qcPar.tradeEnabled, qcPar.rebuyTriggerAmount, qcPar.rebuyAmount, qcPar.asset
                      )

            self.cursor.execute(sql, values)
            self.db.commit()

        except:
            print(traceback.format_exc())
        return qcPars

    def deleteQcParameters(self, qcPar_id):
        qcPar = None
        try:
            sql = "DELETE FROM QcParameters WHERE QcParametersId = %s"
            values = (qcPar_id,)
            self.cursor.execute(sql, values)
            self.db.commit()

        except:
            print(traceback.format_exc())
        return qcPar
