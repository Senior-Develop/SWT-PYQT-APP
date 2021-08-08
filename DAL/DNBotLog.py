from Common.BotLog import BotLog
from DAL.DNBase import DNBase
import traceback


class DNBotLog(DNBase):
    def getBotLog(self, botlog_id):
        botLog = None
        try:
            sql = "SELECT * FROM BotLog WHERE BotLogId = %s"
            values = (botlog_id,)
            self.cursor.execute(sql, values)
            result = self.cursor.fetchone()
            if result:
                botLog = BotLog(*result)
        except:
            print(traceback.format_exc())
        return botLog

    def listBotLog(self):
        items = None
        try:
            sql = "SELECT * FROM BotLog ORDER BY BotLogId desc LIMIT 3000"
            self.cursor.execute(sql)
            results = self.cursor.fetchall()
            if results:
                items = [BotLog(*result) for result in results]
        except:
            print(traceback.format_exc())
        return items

    def searchBotLog(self, keyword):
        items = None
        try:
            sql = "SELECT * FROM BotLog WHERE ShortLog LIKE '%" + keyword + "%' ORDER BY BotLogId desc"
            self.cursor.execute(sql)
            results = self.cursor.fetchall()
            if results:
                items = [BotLog(*result) for result in results]
        except:
            print(traceback.format_exc())
        return items

    def insertBotLog(self, botLog):
        trades = None
        try:
            sql = "INSERT INTO BotLog ("
            sql = sql + "Symbol, ShortLog, LongLog, CreatedDate"
            sql = sql + ") "
            sql = sql + "VALUES (%s,%s,%s,%s)"

            values = (botLog.Symbol, botLog.ShortLog, botLog.LongLog, botLog.CreatedDate,)

            self.cursor.execute(sql, values)
            self.db.commit()

        except:
            print(traceback.format_exc())
        return trades

    def updateBotLog(self, botLog):
        trades = None
        try:
            sql = "UPDATE BotLog SET "

            sql = sql + "Symbol = %s, ShortLog = %s, LongLog = %s, CreatedDate = %s"
            sql = sql + " WHERE BotLogId = %s"

            values = (botLog.Symbol, botLog.ShortLog, botLog.LongLog, botLog.CreatedDate, botLog.BotLogId,)

            self.cursor.execute(sql, values)
            self.db.commit()

        except:
            print(traceback.format_exc())
        return trades

    def deleteBotLog(self, botlog_id):
        botLog = None
        try:
            sql = "DELETE FROM BotLog WHERE BotLogId = %s"
            values = (botlog_id,)
            self.cursor.execute(sql, values)
            self.db.commit()

        except:
            print(traceback.format_exc())
        return botLog

    def truncateBotLog(self):
        try:
            sql = "TRUNCATE TABLE BotLog"
            self.cursor.execute(sql)
            self.db.commit()
        except:
            print(traceback.format_exc())