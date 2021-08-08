from datetime import datetime

from BL.Exchanges.Binance.BinanceClient import BinanceLibrary
from Exchange.bot.SwT import SwT
from Common.IndicatorLog import IndicatorLog
from Common.Trade import Trade
from Common.TradeLog import TradeLog
from DAL.DNBotParameters import DNBotParameters
from DAL.DNIndicatorLog import DNIndicatorLog
from DAL.DNTrade import DNTrade
from DAL.DNTradeLog import DNTradeLog
import time
import os
import ntplib
import traceback

# These are some functions used for testing. Not used in the prod version of the app.

class Tester:
    binance = None

    def sendOrder(self, asset, side, amount):
        swt = SwT()
        response = swt.sendBinanceOrder(asset, side, amount)
        if response:
            print(response['avgPrice'])
            print(response['totalCommission'])
            print(response['status'])
            print(response['transactTime'])
            print(response['clientOrderId'])
            print(response['price'])
            print(response['executedQty'])

            for f in response['fills']:
                print(f['tradeId'])
                print(f['qty'])
                print(f['price'])
                print(f['commission'])
                print(f['commissionAsset'])


    def printBalance(self, asset):
        self.initBinance()
        ba = self.binance.get_asset_balance(asset)
        print(asset + ": " + str(ba.free))

    def getBalance(self, asset):
        self.initBinance()
        ba = self.binance.get_asset_balance(asset)
        return ba.free

    def initBinance(self):
        dnBotParameters = DNBotParameters()
        self.bot_parameters = dnBotParameters.getBotParameters()
        self.binance = BinanceLibrary(self.bot_parameters.apiKey, self.bot_parameters.secretKey)

    def updateTimerTime(self, tradeId, min):
        dnTrade = DNTrade()
        trade = dnTrade.getTrade(tradeId)
        currentTime = int(round(time.time()))
        trade.TimerInSeconds = currentTime + min * 60
        dnTrade.updateTrade(trade)

    def updateStopLoss(self, tradeId, stopLoss):
        dnTrade = DNTrade()
        trade = dnTrade.getTrade(tradeId)
        trade.StopLoss = stopLoss
        dnTrade.updateTrade(trade)

    def insertTrade(self):
        print("insertTrade")
        dnTrade = DNTrade()
        trade = Trade()
        trade.Symbol = "BTCUSDT"
        trade.Amount = 123
        trade.EntryPrice = 0.123
        trade.EntryDate = datetime.now()

        dnTrade.insertTrade(trade)

        items = dnTrade.listTrade()
        print(len(items))

    def insertTradeLog(self):
        print("insertTradeLog")
        dnTradeLog = DNTradeLog()
        tradeLog = TradeLog()
        tradeLog.Symbol = "BTCUSDT"
        tradeLog.Amount = 0.012
        tradeLog.Action = "Action"
        tradeLog.CreatedDate = datetime.now()

        dnTradeLog.insertTradeLog(tradeLog)

        items = dnTradeLog.listTradeLog()
        print(len(items))

    def insertIndicatorLog(self):
        print("insertIndicatorLog")
        dnIndLog = DNIndicatorLog()
        iLog = IndicatorLog()
        iLog.Symbol = "BTCUSDT"
        iLog.CurrentPrice = 0.012
        iLog.R_ROC_Signal = True
        iLog.CreatedDate = datetime.now()

        dnIndLog.insertIndicatorLog(iLog)

        items = dnIndLog.listIndicatorLog()
        print(len(items))

    # this may require administrative rights.
    # https://www.softwareok.com/?seite=faq-Windows-Console&faq=31
    # https://stackoverflow.com/questions/30635627/how-extract-real-time-form-time-gov-in-python
    def syncTime(self):
        try:
            client = ntplib.NTPClient()
            response = client.request('time.nist.gov') # time.nist.gov
            print(response.tx_time)
            os.system('date ' + time.strftime('%m%d%Y%H%M.%S', time.localtime(response.tx_time)))
        except:
            print(traceback.format_exc())

