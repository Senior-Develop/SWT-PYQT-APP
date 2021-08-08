from PyQt5.QtWidgets import *
from PyQt5.QtGui import *
from PyQt5 import QtWidgets
from PyQt5.QtCore import *
from PyQt5 import QtCore
from PyQt5.QtWidgets import QMainWindow
from PyQt5.QtWidgets import QApplication
import sys
from os import path
from PyQt5.uic import loadUiType

import Config
from BL.ExchangeClient import ExchangeClient, ExchangeType
from BL.bot.SwT import SwT
from Common.BotLog import BotLog
from Common.BotParameters import BotParameters
from Common.Market import Market
from Common.Optimization import Optimization
from Common.OptimizationRun import OptimizationRun
from Common.QcParameters import QcParameters
from Common.StrategyParameters import StrategyParameters
from Common.Trade import Trade
from DAL.DNAsset import DNAsset
from DAL.DNBacktest import DNBacktest
from DAL.DNBotLog import DNBotLog
from DAL.DNBotParameters import DNBotParameters
from DAL.DNIndicatorLog import DNIndicatorLog
from DAL.DNMarket import DNMarket
from DAL.DNOptimization import DNOptimization
from DAL.DNOptimizationRun import DNOptimizationRun
from DAL.DNQcParameters import DNQcParameters
from DAL.DNStrategyParameters import DNStrategyParameters
from DAL.DNTickData import DNTickData
from DAL.DNTrade import DNTrade
from datetime import datetime, timedelta
import time
import traceback
import decimal
import csv
from PyQt5.QtCore import QSettings, QPoint, QSize

from DAL.DNTradeLog import DNTradeLog

FORM_CLASS, _ = loadUiType(path.join(path.dirname('__file__'), "UI/Main.ui"))


class Main(QMainWindow, FORM_CLASS):
    client = None
    exchange_type = ExchangeType.BITTREX
    timer = None
    swt = None
    botStartTime = 0
    botStartTimeInSeconds = 0
    dataCollectorStartTimeInSeconds = 0

    spCombinationList = []
    optimizationId = 0
    optimizationRunning = False
    optimizationMarkets = []
    optimizationMarketIndex = 0
    loopedOptimizationId = 0
    maxParalleleOptimizationNumber = 1
    runSingleOptimizationLoop = False
    swtList = []
    completedSwtDict = {}
    dialog = None

    def __init__(self, parent=None):
        super(Main, self).__init__(parent)
        QMainWindow.__init__(self)

        self.setupUi(self)
        self.settings = QSettings('SwT', 'SwT')

        # Initial window size/pos last saved. Use default values for first time
        self.resize(self.settings.value("size", QSize(self.frameGeometry().width(), self.frameGeometry().height())))
        self.move(self.settings.value("pos", QPoint(0, 0)))

        self.initClient()
        self.initSwt()

        self.hideStrategy1Controls()
        self.launchSecondWindow(parent)

        self.initControls()
        self.initHandlers()
        self.initValidators()

        self.onMainmenuTabChanged(self.tabMainMenu.currentIndex())

        # if not self.isOptimizationMode():
        #   self.onMainmenuTabChanged(self.tabMainMenu.currentIndex())
        # self.onSubmenuTabChanged(self.tabSubmenu.currentIndex())
        # self.onLogMenuTabChanged(self.tabLogMenu.currentIndex())
        # else:
        #    self.onOptimizationMenuTabChanged(self.tabOptimizationMenu.currentIndex())

        # current_env = getattr(Config, 'CURRENT_ENVIRONMENT', 'test')

        # if current_env == 'test':
        # oktar
        #   dateFrom = datetime(2020, 8, 18, 2, 0, 0)
        #    dateTo = datetime(2020, 8, 18, 3, 0, 0)

    # else:
    # nat
    #    dateFrom = datetime(2020, 10, 29, 1, 0, 0)
    #    dateTo = datetime(2020, 10, 30, 1, 0, 0)

    # self.dateFromBacktest.setDateTime(dateFrom)
    # self.dateToBacktest.setDateTime(dateTo)

    # self.dateFromOpt.setDateTime(dateFrom)
    # self.dateToOpt.setDateTime(dateTo)

    # self.txtBacktestSymbol.setText("EOSBTC")
    # self.txtSymbolOpt.setText("EOSBTC")
    def closeEvent(self, e):
        # Write window size and position to config file
        self.settings.setValue("size", self.size())
        self.settings.setValue("pos", self.pos())

        e.accept()

    def initControls(self):
        current_env = getattr(Config, 'CURRENT_ENVIRONMENT', 'test')
        currentVersion = getattr(Config, 'CURRENT_VERSION', '')

        if current_env == 'col':
            self.setWindowIcon(QIcon('UI/Icon/eth.png'))
        else:
            self.setWindowIcon(QIcon('UI/Icon/btc.png'))

        self.setWindowTitle("SwT-" + str(currentVersion))

        self.timer = QTimer()
        self.timer.timeout.connect(self.onTick)
        self.statusBar = QStatusBar()
        self.setStatusBar(self.statusBar)
        self.progressBar.setMaximum(100)
        self.progressBar.setValue(0)
        self.progressBar.hide()
        self.progressBarBacktest.setMaximum(100)
        self.progressBarBacktest.setValue(0)
        self.progressBarBacktest.hide()
        self.progressBarOpt.setMaximum(100)
        self.progressBarOpt.setValue(0)
        self.progressBarOpt.hide()

        if current_env == 'col':
            tabStyle = "QTabBar {font-size: 8pt;} QTabBar::tab:!selected {width: 200px;color:Red} QTabBar::tab:selected {height:40px; width: 200px;}"
        else:
            tabStyle = "QTabBar {font-size: 8pt;} QTabBar::tab:!selected {width: 200px;} QTabBar::tab:selected {height:40px; width: 200px;}"

        self.tabMainMenu.tabBar().setStyleSheet(tabStyle)
        self.tabSubmenu.tabBar().setStyleSheet(tabStyle)
        self.tabLogMenu.tabBar().setStyleSheet(tabStyle)
        self.tabOptimizationMenu.tabBar().setStyleSheet(tabStyle)
        self.tblQuickStats.horizontalHeader().hide()
        self.tblQuickStats.verticalHeader().hide()

        # light theme pl colors
        # self.trueColor = QColor(147, 196, 125)
        # self.falseColor = QColor(224, 102, 102)

        # dark theme pl colors
        self.trueColor = QColor(64, 101, 48)
        self.falseColor = QColor(164, 51, 24)

        if self.swt.getEntryEnabled():
            self.btnStopEntries.setText("Pause Entries")
        else:
            self.btnStopEntries.setText("Resume Entries")

        qss_file = open('UI/swt.qss').read()
        self.setStyleSheet(qss_file)
        self.btnExitAllTrades.setStyleSheet("background-color: #A43318;")

        dTo = datetime.now() + timedelta(days=4 * 365)
        self.dateToStats.setDateTime(dTo)

        dFrom = datetime.now() - timedelta(days=1)
        self.dateFromStats.setDateTime(dFrom)

        self.dateToBacktest.setDateTime(datetime.now())
        db = datetime.now() - timedelta(days=7)
        self.dateFromBacktest.setDateTime(db)
        self.drpBacktestTimeframe.setCurrentIndex(1)
        self.drpTimeframeOpt.setCurrentIndex(1)

        self.updateOptimizationModeControls()

        # add the option to chose them all for optimization
        if self.isOptimizationMode():
            self.drpRocEnabled.addItem("all")
            self.drpRocAppliedPriceR.addItem("all")
            self.drpRocAppliedPriceF.addItem("all")
            self.drpMptEnabled.addItem("all")
            self.drpMptAppliedPrice.addItem("all")
            self.drpTrendEnabled.addItem("all")
            self.drpTrendAppliedPrice.addItem("all")
            self.drpNvEnabled.addItem("all")
            self.drpSELL_IndicatorEnabled.addItem("all")
            self.drpSELL_RSI_Src.addItem("all")
            self.drpSELL_Stoch_Src.addItem("all")
            self.drpR_TradingEnabled.addItem("all")
            self.drpF_TradingEnabled.addItem("all")
            self.drpS_TradingEnabled.addItem("all")

            dnBotParameters = DNBotParameters()
            botPar = dnBotParameters.getBotParameters()

            self.dateFromOpt.setDateTime(botPar.optStartDate)
            self.dateToOpt.setDateTime(botPar.optEndDate)
            self.drpTimeframeOpt.setCurrentText(botPar.optTimeframe)
            self.txtSymbolOpt.setText(botPar.optSymbol)

            self.dateFromBacktest.setDateTime(botPar.optStartDate)
            self.dateToBacktest.setDateTime(botPar.optEndDate)
            self.drpBacktestTimeframe.setCurrentText(botPar.optTimeframe)
            self.txtBacktestSymbol.setText(botPar.optSymbol)

            if self.dialog is not None:
                self.tabMainMenu.setCurrentWidget(self.tabMainMenu.findChild(QWidget, "tabOptimization"))
            else:
                self.tabMainMenu.setCurrentWidget(self.tabMainMenu.findChild(QWidget, "tabSettings"))

            self.lblOptUpdateStrategyParameters.setText("Auto Update Parameters")
        else:
            self.tabMainMenu.setCurrentWidget(self.tabMainMenu.findChild(QWidget, "tabTrades"))
            self.lblOptUpdateStrategyParameters.setText("Use Optimized Parameters")

    def updateOptimizationModeControls(self):
        isOptimizationMode = self.isOptimizationMode()
        if isOptimizationMode:
            self.txtBacktestIdTradeLogs.show()
            self.txtBacktestIdTradeHistory.show()
            self.txtBacktestIdStats.show()
            self.txtBacktestIdIndLogs.show()
            self.tabTrades.setEnabled(False)
            self.tabOptimization.setEnabled(True)
            self.btnStartOptimizationLoop_IndPar.show()
            self.btnStartOptimization_TradePar.show()
        else:
            self.txtBacktestIdTradeLogs.hide()
            self.txtBacktestIdTradeHistory.hide()
            self.txtBacktestIdStats.hide()
            self.txtBacktestIdIndLogs.hide()
            self.tabTrades.setEnabled(True)
            self.tabOptimization.setEnabled(False)
            self.btnStartOptimizationLoop_IndPar.hide()
            self.btnStartOptimizationLoop_TradePar.hide()

        self.btnStartOptimization_IndPar.hide()
        self.btnStartOptimization_TradePar.hide()

        lastBacktestId = self.getLastBacktestId()
        if isOptimizationMode and lastBacktestId > 0:
            self.txtBacktestIdTradeLogs.setText(str(lastBacktestId))
            self.txtBacktestIdTradeHistory.setText(str(lastBacktestId))
            self.txtBacktestIdStats.setText(str(lastBacktestId))
            self.txtBacktestIdIndLogs.setText(str(lastBacktestId))

    def initClient(self):
        dnBotParameters = DNBotParameters()
        bot_parameters = dnBotParameters.getBotParameters()
        self.client = ExchangeClient(self.exchange_type, bot_parameters.apiKey, bot_parameters.secretKey)

    def initSwt(self):
        self.swt = SwT()
        self.swt.setTerminationEnabled(True)
        self.swt.swtMarketUpdateProgress.connect(self.onMarketUpdateProgress)
        self.swt.swtCandleUpdateProgress.connect(self.onCandleUpdateProgress)
        self.swt.swtCandleDownloadProgress.connect(self.onCandleDownloadProgress)
        self.swt.swtUpdate.connect(self.onSwtUpdate)
        self.swt.swtUpdateOpt.connect(self.onSwtUpdateOpt)
        self.swt.swtUpdateBacktest.connect(self.onSwtUpdateBacktest)

    def createSwt(self):
        swt = SwT()
        swt.setTerminationEnabled(True)
        swt.swtMarketUpdateProgress.connect(self.onMarketUpdateProgress)
        swt.swtCandleUpdateProgress.connect(self.onCandleUpdateProgress)
        swt.swtCandleDownloadProgress.connect(self.onCandleDownloadProgress)
        swt.swtUpdate.connect(self.onSwtUpdate)
        swt.swtUpdateOpt.connect(self.onSwtUpdateOpt)
        swt.swtUpdateBacktest.connect(self.onSwtUpdateBacktest)
        return swt

    def onMarketUpdateProgress(self, value):
        try:
            if self.isOptimizationMode():
                self.progressBarOpt.show()
                self.progressBarOpt.setValue(value)
            else:
                self.progressBar.show()
                self.progressBar.setValue(value)
        except:
            self.printLog("Exception: onMarketUpdateProgress", traceback.format_exc())

    def onCandleDownloadProgress(self, value):
        try:
            # print("onCandleDownloadProgress: " + str(value))
            self.progressBarBacktest.show()
            self.progressBarBacktest.setValue(value)
        except:
            self.printLog("Exception: onCandleDownloadProgress", traceback.format_exc())

    def onCandleUpdateProgress(self, value):
        try:
            # print("onCandleUpdateProgress: " + str(value))
            self.progressBar.show()
            self.progressBar.setValue(value)
        except:
            self.printLog("Exception: onCandleUpdateProgress", traceback.format_exc())

    def onSwtUpdate(self, value):
        try:
            self.lblSwtUpdate.hide()

            if value == "UpdateMarketsFinished":
                self.progressBar.hide()
            elif value == "CandleUpdateFinished":
                self.progressBar.hide()
            elif value == "ExitAllTradesFinished":
                self.listOpenTrade()
            elif value == "PcClockOutOfSync":
                QMessageBox.question(self, "Clock out of sync", "PC clock is out of sync. Please sync clock.",
                                     QMessageBox.Ok)
            elif value == "UpdateMarketsForOptimizationFinished":
                self.lblSwtUpdateOpt.show()
                self.lblSwtUpdateOpt.setText("Market update completed.")
                self.progressBarOpt.hide()
            else:
                self.lblSwtUpdate.show()
                self.lblSwtUpdate.setText(value)

        except:
            self.printLog("Exception: onSwtUpdate", traceback.format_exc())

    def onSwtUpdateBacktest(self, value):
        try:
            self.lblSwtUpdateBacktest.hide()

            if value == "CandleDownloadFinished":
                self.progressBarBacktest.hide()
                self.progressBarBacktest.setValue(0)
            else:
                self.lblSwtUpdateBacktest.show()
                self.lblSwtUpdateBacktest.setText(value)

            if "Backtest finished" in value:
                self.updateOptimizationModeControls()
                self.listBacktest()

        except:
            self.printLog("Exception: onSwtUpdateBacktest", traceback.format_exc())

    # oktar
    def onSwtUpdateOpt(self, value):
        try:
            self.lblSwtUpdateOpt.show()

            parts = value.split(";")

            if not parts or len(parts) < 2:
                return

            count = 0
            for row in range(self.tblOptimizationRuns.rowCount()):
                if count >= 10:
                    break

                id = self.tblOptimizationRuns.item(row, 0).text()
                # print(str(id) + " " + parts[0])
                if id == parts[0]:

                    self.tblOptimizationRuns.item(row, 11).setText(parts[1])
                    if parts[1] == "Completed.":
                        # self.listOptimizationRun(self.optimizationId) # it crashes without this line. Not sure why.

                        self.listOptimizationRun()
                        self.updateOptimizationModeControls()
                        # time.sleep(0.3)

                        if id in self.completedSwtDict.keys():
                            # print("Already completed. skip")
                            return

                        self.completedSwtDict[id] = "1"

                        # print("Completed called for  " + id)
                        # print(value)

                        if self.optimizationRunning and self.loopedOptimizationId > 0:
                            self.enqueueOptimization()

                count = count + 1



        except:
            self.printLog("Exception: onSwtUpdateOpt", traceback.format_exc())

    def onMarketUpdateFinished(self):
        print("onMarketUpdateFinished")
        self.progressBar.setValue(0)
        self.progressBar.hide()

    def updateControls(self, value):
        self.drpBotTimeframe.setEnabled(value)
        self.btnAddSelectedMarket.setEnabled(value)
        self.btnSaveIndicatorParameters.setEnabled(value)
        self.btnSaveTradeParameters.setEnabled(value)
        self.btcSaveQcParameters.setEnabled(value)
        self.btcSaveBotParameters.setEnabled(value)
        self.btnTruncateTrade.setEnabled(value)
        self.btnTruncateTradeLog.setEnabled(value)
        self.btnTruncateIndicatorLog.setEnabled(value)
        self.btnTruncateBotLog.setEnabled(value)

    def onBuyNowButtonClicked(self):
        try:
            print("onBuyNowButtonClicked")
            symbol = self.drpSymbolBuyNow.currentText()

            if symbol == "":
                self.statusBar.showMessage("Please enter a symbol!", 2000)
                return

            if self.swt.isBotRunning():
                self.swt.manualBuy(symbol)
            else:
                self.statusBar.showMessage("Buy now cant work when the bot is not running", 2000)
        except:
            self.printLog("Exception: onBuyNowButtonClicked", traceback.format_exc())

    def onStartBotButtonClicked(self):
        try:
            print("onStartBotButtonClicked")
            if self.swt.isBotRunning():
                self.swt.stop()
                self.btnStartBot.setText("Start Bot")
                self.lblBotStatus.setText("Stopped")
                self.botStartTimeInSeconds = 0

                self.timer.stop()
                self.updateControls(True)
                # self.progressBar.hide()
            else:
                if self.isOptimizationMode():
                    self.statusBar.showMessage("Bot cannot trade in Optimization mode!", 2000)
                    return

                self.btnStartBot.setText("Stop Bot")
                self.lblBotStatus.setText("Running")
                self.updateControls(False)
                self.swt.setInterval(self.drpBotTimeframe.currentText())
                self.progressBar.setValue(0)
                self.swt.start()
                self.timer.start(1000)
                self.botStartTimeInSeconds = int(round(time.time()))
                self.botStartTime = datetime.now()

        except:
            self.printLog("Exception: onStartBotButtonClicked", traceback.format_exc())

    def onStartDataCollectorButtonClicked(self):
        try:
            print("onStartDataCollectorButtonClicked")

            if not self.isOptimizationMode():
                self.statusBar.showMessage("Data collector can only run in Optimization mode!", 2000)
                return

            if self.swt.isDataCollectorRunning():
                self.swt.stopDataCollector()
                self.btnStartDataCollector.setText("Start Data Collector")
                self.lblDataCollectorStatus.setText("Stopped")

                self.dataCollectorStartTimeInSeconds = 0
                self.timer.stop()

            else:
                self.btnStartDataCollector.setText("Stop Data Collector")
                self.lblDataCollectorStatus.setText("Running")
                self.swt.setInterval("1m")

                # self.swt.setInterval(self.drpBotTimeframe.currentText())
                # self.progressBar.setValue(0)
                self.swt.setDataCollectorModeEnabled(True)
                self.swt.start()
                self.timer.start(1000)
                self.dataCollectorStartTimeInSeconds = int(round(time.time()))

        except:
            self.printLog("Exception: onStartDataCollectorButtonClicked", traceback.format_exc())

    def onStartBacktestButtonClicked(self):
        try:
            print("onStartBacktestButtonClicked")

            dnBotParameters = DNBotParameters()
            botPar = BotParameters()
            botPar.optStartDate = self.dateFromBacktest.dateTime().toPyDateTime()
            botPar.optEndDate = self.dateToBacktest.dateTime().toPyDateTime()
            botPar.optTimeframe = self.drpBacktestTimeframe.currentText()
            botPar.optSymbol = self.txtBacktestSymbol.text().upper().strip()
            dnBotParameters.updateControlValues(botPar)

            if not self.isOptimizationMode():
                self.statusBar.showMessage("Backtester can only run in Optimization mode!", 2000)
                return

            timeframe = self.drpBacktestTimeframe.currentText()
            dateFrom = self.dateFromBacktest.dateTime().toPyDateTime()
            dateTo = self.dateToBacktest.dateTime().toPyDateTime()
            symbol = self.txtBacktestSymbol.text().upper().strip()

            if symbol == "":
                self.statusBar.showMessage("Please enter a symbol!", 2000)
                return

            self.swt.setBacktestModeEnabled(True)
            self.swt.setBacktestParams(timeframe, dateFrom, dateTo, symbol, False, 0, 0)
            self.swt.start()

        except:
            self.printLog("Exception: onStartBacktestButtonClicked", traceback.format_exc())

    def onDownloadCandlesButtonClicked(self):
        try:
            print("onDownloadCandlesButtonClicked")

            if not self.isOptimizationMode():
                self.statusBar.showMessage("Candle download can only run in Optimization mode!", 2000)
                return

            # if not self.swt.isBacktestRunning():
            timeframe = self.drpBacktestTimeframe.currentText()
            dateFrom = self.dateFromBacktest.dateTime().toPyDateTime()
            dateTo = self.dateToBacktest.dateTime().toPyDateTime()
            symbol = self.txtBacktestSymbol.text().upper().strip()

            self.swt.setBacktestModeEnabled(True)
            self.swt.setBacktestParams(timeframe, dateFrom, dateTo, symbol, True, 0, 0)
            self.swt.start()

        except:
            self.printLog("Exception: onDownloadCandlesButtonClicked", traceback.format_exc())

    def onUpdateMarketsOptButtonClicked(self):
        try:
            print("onUpdateMarketsOptButtonClicked")

            self.swt.setUpdateMarketsForOptimizationModeEnabled(True)
            self.swt.start()
        except:
            self.printLog("Exception: onUpdateMarketsOptButtonClicked", traceback.format_exc())

    def onStartOptimizationButtonClicked(self):
        try:
            print("onStartOptimizationButtonClicked")

            if self.dialog is None:
                self.tabMainMenu.setCurrentWidget(self.tabMainMenu.findChild(QWidget, "tabOptimization"))
            else:
                self.dialog.onStartOptimizationButtonClicked()

            dnBotParameters = DNBotParameters()
            botPar = BotParameters()
            botPar.optStartDate = self.dateFromOpt.dateTime().toPyDateTime()
            botPar.optEndDate = self.dateToOpt.dateTime().toPyDateTime()
            botPar.optTimeframe = self.drpTimeframeOpt.currentText()
            botPar.optSymbol = self.txtSymbolOpt.text().upper().strip()
            dnBotParameters.updateControlValues(botPar)

            if not self.isOptimizationMode():
                self.statusBar.showMessage("Optimizer can only run in Optimization mode!", 2000)
                return

            timeframe = self.drpTimeframeOpt.currentText()
            dateFrom = self.dateFromOpt.dateTime().toPyDateTime()
            dateTo = self.dateToOpt.dateTime().toPyDateTime()
            symbol = self.txtSymbolOpt.text().upper().strip()

            self.lblSwtUpdateOpt.show()
            self.lblSwtUpdateOpt.setText("Saving combinations...")
            # This takes time if there is too many combinations
            # self.insertSpCombinationsForOpt()
            # self.lblSwtUpdateOpt.setText("Total combinations: " + str(len(self.spCombinationList)))
            self.lblSwtUpdateOpt.setText("Optimization started.")

            dnMarket = DNMarket()
            markets = []
            if symbol == "":
                markets = dnMarket.listSelectedMarkets()
            else:
                market = dnMarket.getMarketBySymbol(symbol)
                markets.append(market)

            if not markets:
                errorMsg = "No selected markets. Optimization will not start"
                print(errorMsg)
                self.statusBar.showMessage(errorMsg, 2000)
                return

            dnOptimization = DNOptimization()
            dnOptimizationRun = DNOptimizationRun()

            optimization = Optimization()
            optimization.CreatedDate = datetime.now()
            optimization.StartDate = dateFrom
            optimization.EndDate = dateTo
            optimization.CombinationCount = 0  # len(self.spCombinationList)
            optimization.Symbol = symbol
            optimization.Timeframe = timeframe
            optimization.BestBacktestId = 0
            optimization.BestSpId = 0

            optimizationId = dnOptimization.insertOptimization(optimization)
            self.optimizationId = optimizationId

            # insert all param combinations for this optimization
            # dnStrategyParameters = DNStrategyParameters()
            # for sp in self.spCombinationList:
            #    sp.OptimizationId = optimizationId
            #    sp.Name = "option"
            #    dnStrategyParameters.insertStrategyParameters(sp)

            # run optimization for each market in parallel
            for market in markets:
                optimizationRun = OptimizationRun()
                optimizationRun.OptimizationId = optimizationId
                optimizationRun.CreatedDate = datetime.now()
                optimizationRun.StartDate = dateFrom
                optimizationRun.EndDate = dateTo
                optimizationRun.CombinationCount = len(self.spCombinationList)
                optimizationRun.Symbol = market.Symbol
                optimizationRun.Timeframe = timeframe
                optimizationRun.BestBacktestId = 0
                optimizationRun.BestSpId = 0

                optimizationRunId = dnOptimizationRun.insertOptimizationRun(optimizationRun)

                swt = self.createSwt()
                swt.setBacktestModeEnabled(True)
                swt.setBacktestParams(timeframe, dateFrom, dateTo, market.Symbol, False, optimizationId,
                                      optimizationRunId)
                swt.start()

            self.statusBar.showMessage("Optimization started.", 2000)

            self.listOptimizationRun()
            self.optimizationRunning = True






        except:
            self.printLog("Exception: onStartOptimizationButtonClicked", traceback.format_exc())

    def onListAllOptimizationRunsButtonClicked(self):
        try:
            print("onListAllOptimizationRunsButtonClicked")
            self.listOptimizationRun(0)

        except:
            self.printLog("Exception: onListAllOptimizationRunsButtonClicked", traceback.format_exc())

    def onStartOptimizationSingleLoopButtonClicked(self):
        try:
            print("onStartOptimizationSingleLoopButtonClicked")

            # if self.dialog is None:
            #    self.runSingleOptimizationLoop = True
            #    self.tabMainMenu.setCurrentWidget(self.tabMainMenu.findChild(QWidget, "tabOptimization"))
            # else:

            # self.btnStartOptimizationLoop_IndPar.setText("Stop Optimization Loop")
            # self.btnStartOptimizationLoop_TradePar.setText("Stop Optimization Loop")

            self.dialog.runSingleOptimizationLoop = True
            self.dialog.onStartOptimizationLoopButtonClicked()

        except:
            self.printLog("Exception: onStartOptimizationSingleLoopButtonClicked", traceback.format_exc())

    def onStartOptimizationLoopButtonClicked(self):
        try:
            print("onStartOptimizationLoopButtonClicked")

            if not self.isOptimizationMode():
                self.statusBar.showMessage("Optimizer can only run in Optimization mode!", 2000)
                return

            if self.optimizationRunning:
                self.btnStartOptimizationLoop.setText("Start Optimization Loop")
                self.lblSwtUpdateOpt.setText("Optimization loop stopped.")
                self.optimizationRunning = False
                return

            self.optimizationMarketIndex = 0
            dnBotParameters = DNBotParameters()
            botPar = BotParameters()
            botPar.optStartDate = self.dateFromOpt.dateTime().toPyDateTime()
            botPar.optEndDate = self.dateToOpt.dateTime().toPyDateTime()
            botPar.optTimeframe = self.drpTimeframeOpt.currentText()
            botPar.optSymbol = self.txtSymbolOpt.text().upper().strip()
            dnBotParameters.updateControlValues(botPar)

            timeframe = self.drpTimeframeOpt.currentText()

            self.lblSwtUpdateOpt.show()
            self.lblSwtUpdateOpt.setText("Saving combinations...")

            # self.insertSpCombinationsForOpt()
            # self.lblSwtUpdateOpt.setText("Total combinations: " + str(len(self.spCombinationList)))
            self.lblSwtUpdateOpt.setText("Optimization loop started.")

            dnBotParameters = DNBotParameters()
            botPar = dnBotParameters.getBotParameters()

            dnMarket = DNMarket()
            self.optimizationMarkets = []
            if botPar.runOnSelectedMarkets:
                self.optimizationMarkets = dnMarket.listSelectedMarkets()
            else:
                self.optimizationMarkets = dnMarket.listTradeableMarkets()

            if not self.optimizationMarkets:
                errorMsg = "No selected markets. Optimization will not start"
                print(errorMsg)
                self.statusBar.showMessage(errorMsg, 2000)
                return

            dnOptimization = DNOptimization()
            dnOptimizationRun = DNOptimizationRun()

            optimization = Optimization()
            optimization.CreatedDate = datetime.now()
            # optimization.StartDate = dateFrom
            # optimization.EndDate = dateTo
            optimization.CombinationCount = 0  # len(self.spCombinationList)
            optimization.Symbol = "Batch"
            optimization.Timeframe = timeframe
            optimization.BestBacktestId = 0
            optimization.BestSpId = 0

            self.loopedOptimizationId = dnOptimization.insertOptimization(optimization)

            # insert all param combinations for this optimization
            # dnStrategyParameters = DNStrategyParameters()
            # for sp in self.spCombinationList:
            #    sp.OptimizationId = self.loopedOptimizationId
            #    sp.Name = "option"
            #    dnStrategyParameters.insertStrategyParameters(sp)

            self.statusBar.showMessage("Optimization started.", 2000)

            self.listOptimizationRun()
            self.optimizationRunning = True

            self.btnStartOptimizationLoop.setText("Stop Optimization Loop")

            for i in range(self.maxParalleleOptimizationNumber):
                self.enqueueOptimization()

        except:
            self.printLog("Exception: onStartOptimizationLoopButtonClicked", traceback.format_exc())

    def enqueueOptimization(self):
        # if Start Optimization Loop button is clicked from the Settings page, stop the loop after 1 iteration
        dnMarket = DNMarket()
        selectedMarkets = dnMarket.listSelectedMarkets()
        if self.runSingleOptimizationLoop and self.optimizationMarketIndex == len(selectedMarkets):
            # self.btnStartOptimizationLoop_IndPar.setText("Start Optimization Loop")
            # self.btnStartOptimizationLoop_TradePar.setText("Start Optimization Loop")
            self.runSingleOptimizationLoop = False
            self.optimizationRunning = False
            return

        index = self.optimizationMarketIndex % len(self.optimizationMarkets)
        market = self.optimizationMarkets[index]

        print("index: " + str(index))
        print("market: " + market.Symbol)

        timeframe = self.drpTimeframeOpt.currentText()
        dateTo = datetime.now()
        dateFrom = dateTo - timedelta(days=1)

        optimizationRun = OptimizationRun()
        optimizationRun.OptimizationId = self.loopedOptimizationId
        optimizationRun.CreatedDate = datetime.now()
        optimizationRun.StartDate = dateFrom
        optimizationRun.EndDate = dateTo
        optimizationRun.CombinationCount = len(self.spCombinationList)
        optimizationRun.Symbol = market.Symbol
        optimizationRun.Timeframe = timeframe
        optimizationRun.BestBacktestId = 0
        optimizationRun.BestSpId = 0

        dnOptimizationRun = DNOptimizationRun()
        optimizationRunId = dnOptimizationRun.insertOptimizationRun(optimizationRun)
        self.listOptimizationRun()
        optimizationId = self.loopedOptimizationId

        # swt = self.createSwt()
        # swt.setBacktestModeEnabled(True)
        # swt.setBacktestParams(timeframe, dateFrom, dateTo, market.Symbol, False, optimizationId, optimizationRunId)
        # self.swtList.append(swt)
        # swt.start()

        # swtIndex = self.optimizationMarketIndex % self.maxParalleleOptimizationNumber
        # self.swtList[swtIndex].setBacktestParams(timeframe, dateFrom, dateTo, market.Symbol, False, optimizationId, optimizationRunId)
        # self.swtList[swtIndex].start()

        print("Running optimizationRunId: " + str(optimizationRunId))

        swt = self.createSwt()
        swt.setBacktestModeEnabled(True)
        swt.setBacktestParams(timeframe, dateFrom, dateTo, market.Symbol, False, optimizationId, optimizationRunId)
        swt.start()

        self.swtList.append(swt)

        # print("Running swtindex: " + str(swtIndex))

        self.optimizationMarketIndex = self.optimizationMarketIndex + 1

    def insertSpCombinationsForOpt(self):
        try:
            timeframe = self.drpTimeframeOpt.currentText()
            self.spCombinationList = []

            dnStrategyParameters = DNStrategyParameters()
            spMin = dnStrategyParameters.getStrategyParameters(timeframe, "min", 0)
            spMax = dnStrategyParameters.getStrategyParameters(timeframe, "max", 0)
            spStep = dnStrategyParameters.getStrategyParameters(timeframe, "step", 0)

            sp = dnStrategyParameters.set(spMin, False)
            sp.Name = "option"
            sp.OptimizationId = 1

            self.spCombinationList.append(sp)

            self.addToSpCombinationList(spMin, spMax, spStep, "ROC_IndicatorEnabled")
            self.addToSpCombinationList(spMin, spMax, spStep, "ROC_AppliedPrice_R")
            self.addToSpCombinationList(spMin, spMax, spStep, "ROC_AppliedPrice_F")
            self.addToSpCombinationList(spMin, spMax, spStep, "ROC_Period_R")
            self.addToSpCombinationList(spMin, spMax, spStep, "ROC_Period_F")

            self.addToSpCombinationList(spMin, spMax, spStep, "ROC_R_BuyIncreasePercentage")
            self.addToSpCombinationList(spMin, spMax, spStep, "ROC_F_BuyDecreasePercentage")
            self.addToSpCombinationList(spMin, spMax, spStep, "MPT_IndicatorEnabled")
            self.addToSpCombinationList(spMin, spMax, spStep, "MPT_AppliedPrice")
            self.addToSpCombinationList(spMin, spMax, spStep, "MPT_ShortMAPeriod")
            self.addToSpCombinationList(spMin, spMax, spStep, "MPT_LongMAPeriod")

            self.addToSpCombinationList(spMin, spMax, spStep, "NV_IndicatorEnabled")
            self.addToSpCombinationList(spMin, spMax, spStep, "NV_IncreasePercentage")
            self.addToSpCombinationList(spMin, spMax, spStep, "NV_MinNetVolume")

            self.addToSpCombinationList(spMin, spMax, spStep, "TREND_IndicatorEnabled")
            self.addToSpCombinationList(spMin, spMax, spStep, "TREND_AppliedPrice")
            self.addToSpCombinationList(spMin, spMax, spStep, "TREND_LongEmaPeriod")
            self.addToSpCombinationList(spMin, spMax, spStep, "TREND_ShortEmaPeriod")

            self.addToSpCombinationList(spMin, spMax, spStep, "EMAX_IndicatorEnabled")
            self.addToSpCombinationList(spMin, spMax, spStep, "EMAX_AppliedPrice")
            self.addToSpCombinationList(spMin, spMax, spStep, "EMAX_LongEmaPeriod")
            self.addToSpCombinationList(spMin, spMax, spStep, "EMAX_ShortEmaPeriod")

            self.addToSpCombinationList(spMin, spMax, spStep, "VSTOP_IndicatorEnabled")
            self.addToSpCombinationList(spMin, spMax, spStep, "VSTOP_AppliedPrice")
            self.addToSpCombinationList(spMin, spMax, spStep, "VSTOP_Period")
            self.addToSpCombinationList(spMin, spMax, spStep, "VSTOP_Factor")

            self.addToSpCombinationList(spMin, spMax, spStep, "SELL_IndicatorEnabled")
            self.addToSpCombinationList(spMin, spMax, spStep, "SELL_DecreasePercentage")
            self.addToSpCombinationList(spMin, spMax, spStep, "SELL_Period")
            self.addToSpCombinationList(spMin, spMax, spStep, "SELL_RSI_AppliedPrice")
            self.addToSpCombinationList(spMin, spMax, spStep, "SELL_RSI_Period")
            self.addToSpCombinationList(spMin, spMax, spStep, "SELL_RSI_UpperLevel")
            self.addToSpCombinationList(spMin, spMax, spStep, "SELL_RSI_LowerLevel")
            self.addToSpCombinationList(spMin, spMax, spStep, "SELL_Stoch_KPeriod")
            self.addToSpCombinationList(spMin, spMax, spStep, "SELL_Stoch_DPeriod")
            self.addToSpCombinationList(spMin, spMax, spStep, "SELL_Stoch_Slowing")
            self.addToSpCombinationList(spMin, spMax, spStep, "SELL_Stoch_UpperLevel")
            self.addToSpCombinationList(spMin, spMax, spStep, "SELL_Stoch_LowerLevel")

            self.addToSpCombinationList(spMin, spMax, spStep, "R_TradingEnabled")
            self.addToSpCombinationList(spMin, spMax, spStep, "R_SL1Percentage")
            self.addToSpCombinationList(spMin, spMax, spStep, "R_SL2Percentage")
            self.addToSpCombinationList(spMin, spMax, spStep, "R_SLTimerInMinutes")
            self.addToSpCombinationList(spMin, spMax, spStep, "R_TSLActivationPercentage")
            self.addToSpCombinationList(spMin, spMax, spStep, "R_TSLTrailPercentage")
            self.addToSpCombinationList(spMin, spMax, spStep, "F_TradingEnabled")
            self.addToSpCombinationList(spMin, spMax, spStep, "F_SL1Percentage")
            self.addToSpCombinationList(spMin, spMax, spStep, "F_SL2Percentage")
            self.addToSpCombinationList(spMin, spMax, spStep, "F_SLTimerInMinutes")
            self.addToSpCombinationList(spMin, spMax, spStep, "F_TSLActivationPercentage")
            self.addToSpCombinationList(spMin, spMax, spStep, "F_TSLTrailPercentage")
            self.addToSpCombinationList(spMin, spMax, spStep, "S_TradingEnabled")
            self.addToSpCombinationList(spMin, spMax, spStep, "S_SL1Percentage")
            self.addToSpCombinationList(spMin, spMax, spStep, "S_SL2Percentage")
            self.addToSpCombinationList(spMin, spMax, spStep, "S_SLTimerInMinutes")
            self.addToSpCombinationList(spMin, spMax, spStep, "S_TSLActivationPercentage")
            self.addToSpCombinationList(spMin, spMax, spStep, "S_TSLTrailPercentage")
            self.addToSpCombinationList(spMin, spMax, spStep, "TargetPercentage")
            self.addToSpCombinationList(spMin, spMax, spStep, "RebuyTimeInSeconds")
            self.addToSpCombinationList(spMin, spMax, spStep, "RebuyPercentage")
            self.addToSpCombinationList(spMin, spMax, spStep, "RebuyMaxLimit")
            self.addToSpCombinationList(spMin, spMax, spStep, "PullbackEntryPercentage")
            self.addToSpCombinationList(spMin, spMax, spStep, "PullbackEntryWaitTimeInSeconds")

            print("Total Param Combinations: " + str(len(self.spCombinationList)))

        except:
            self.printLog("Exception: insertSpCombinationsForOpt", traceback.format_exc())

    def addToSpCombinationList(self, spMin, spMax, spStep, propertyName):
        try:
            if spMin is None:
                self.printLog("addToSpCombinationList: spMin cant be None.")
                return
            if spMax is None:
                self.printLog("addToSpCombinationList: spMax cant be None.")
                return
            if spStep is None:
                self.printLog("addToSpCombinationList: spStep cant be None.")
                return

            dnStrategyParameters = DNStrategyParameters()
            spListNew = []

            minValue = getattr(spMin, propertyName)
            maxValue = getattr(spMax, propertyName)
            stepValue = getattr(spStep, propertyName)

            if "AppliedPrice" in propertyName:
                minValue = int(minValue)
                maxValue = int(maxValue)
                stepValue = int(stepValue)

            # step = 0 means that we only use 1 value for this parameter. this parameter is not being optimized.
            if stepValue == 0:
                return

            for sp in self.spCombinationList:
                if not sp.ROC_IndicatorEnabled and propertyName != "ROC_IndicatorEnabled" and propertyName.startswith(
                        "ROC_"):
                    continue
                if not sp.MPT_IndicatorEnabled and propertyName != "MPT_IndicatorEnabled" and propertyName.startswith(
                        "MPT_"):
                    continue
                if not sp.TREND_IndicatorEnabled and propertyName != "TREND_IndicatorEnabled" and propertyName.startswith(
                        "TREND_"):
                    continue
                if not sp.EMAX_IndicatorEnabled and propertyName != "EMAX_IndicatorEnabled" and propertyName.startswith(
                        "EMAX_"):
                    continue
                if not sp.VSTOP_IndicatorEnabled and propertyName != "VSTOP_IndicatorEnabled" and propertyName.startswith(
                        "VSTOP_"):
                    continue
                if not sp.NV_IndicatorEnabled and propertyName != "NV_IndicatorEnabled" and propertyName.startswith(
                        "NV_"):
                    continue
                if not sp.SELL_IndicatorEnabled and propertyName != "SELL_IndicatorEnabled" and propertyName.startswith(
                        "SELL_"):
                    continue
                if not sp.R_TradingEnabled and propertyName != "R_TradingEnabled" and propertyName.startswith("R_"):
                    continue
                if not sp.F_TradingEnabled and propertyName != "F_TradingEnabled" and propertyName.startswith("F_"):
                    continue
                if not sp.S_TradingEnabled and propertyName != "S_TradingEnabled" and propertyName.startswith("S_"):
                    continue

                # print("Adding for 1: " + propertyName)

                value = minValue + stepValue
                while value <= maxValue:
                    spNew = dnStrategyParameters.set(sp, False)
                    setattr(spNew, propertyName, value)
                    # print("Adding for: " + propertyName + ": " + str(value))

                    spListNew.append(spNew)
                    value = value + stepValue

            for spNew in spListNew:
                self.spCombinationList.append(spNew)

        except:
            self.printLog("Exception: addToSpCombinationList", traceback.format_exc())

    def onStopEntriesButtonClicked(self):
        try:
            print("onStopEntriesButtonClicked")
            if self.swt.getEntryEnabled():
                self.swt.setEntryEnabled(False)
                self.btnStopEntries.setText("Resume Entries")
                self.statusBar.showMessage("Trade entries paused.", 2000)
            else:
                self.swt.setEntryEnabled(True)
                self.btnStopEntries.setText("Pause Entries")
                self.statusBar.showMessage("Trade entries resumed.", 2000)
        except:
            self.printLog("Exception: onStopEntriesButtonClicked", traceback.format_exc())

    def onExitAllTradesButtonClicked(self):
        try:
            self.printLog("onExitAllTradesButtonClicked")
            self.swt.exitAllTrades()
        except:
            self.printLog("Exception: onExitAllTradesButtonClicked", traceback.format_exc())

    def listQuickStats(self):
        self.listStats()
        self.tblQuickStats.horizontalHeader().setSectionResizeMode(0, QtWidgets.QHeaderView.Stretch)
        self.tblQuickStats.horizontalHeader().setSectionResizeMode(1, QtWidgets.QHeaderView.Stretch)
        if self.tblStats.item(6, 1):
            plPercBtc = "BTC: " + self.tblStats.item(6, 0).text() + "%"
            usdPercBtc = "USDT: " + self.tblStats.item(6, 1).text() + "%"
            ethPercBtc = "ETH: " + self.tblStats.item(6, 2).text() + "%"
            bnbPercBtc = "USD: " + self.tblStats.item(6, 3).text() + "%"
            self.tblQuickStats.setItem(0, 0, QTableWidgetItem(str(plPercBtc)))
            self.tblQuickStats.setItem(0, 1, QTableWidgetItem(str(usdPercBtc)))
            self.tblQuickStats.setItem(1, 0, QTableWidgetItem(str(ethPercBtc)))
            self.tblQuickStats.setItem(1, 1, QTableWidgetItem(str(bnbPercBtc)))

    def listOpenTrade(self):
        try:
            dnTrade = DNTrade()
            resultList = dnTrade.listOpenTrade(0)
            self.initOpenTradeDatagrid(resultList, self.tblTrades)
        except:
            self.printLog("Exception: listOpenTrade", traceback.format_exc())

    def listBacktest(self):
        try:
            dnBacktest = DNBacktest()
            resultList = dnBacktest.listBacktest()
            self.initBacktestDatagrid(resultList, self.tblBacktests)
        except:
            self.printLog("Exception: listBacktest", traceback.format_exc())

    def listOptimizationRun(self, limit=50):
        try:
            dnOptimizationRun = DNOptimizationRun()
            resultList = dnOptimizationRun.listOptimizationRun(limit)

            self.initOptimizationRunDatagrid(resultList, self.tblOptimizationRuns)
        except:
            self.printLog("Exception: listOptimizationRun", traceback.format_exc())

    def listClosedTrade(self):
        try:
            dnTrade = DNTrade()
            symbol = self.txtSymbolTradeHistory.text().upper().strip()
            tradeId = self.txtTradeIdTradeHistory.text().upper().strip()
            backtestId = self.txtBacktestIdTradeHistory.text().upper().strip()

            trades = []
            if symbol != "":
                trades = dnTrade.listClosedTradeBySymbol(symbol)
            elif tradeId != "":
                t = dnTrade.getTrade(int(tradeId))
                trades.append(t)
            elif backtestId != "":
                trades = dnTrade.listClosedTradeByBacktestId(backtestId)
            else:
                trades = dnTrade.listClosedTrade()

            self.initClosedTradeDatagrid(trades, self.tblClosedTrades)

        except:
            self.printLog("Exception: listClosedTrade", traceback.format_exc())

    def listStats(self):
        try:
            # self.printLog("listStats started.")
            dnTrade = DNTrade()
            dateFrom = self.dateFromStats.dateTime().toPyDateTime()
            dateTo = self.dateToStats.dateTime().toPyDateTime()
            backtestId = self.txtBacktestIdStats.text().upper().strip()

            if backtestId != "":
                trades = dnTrade.listClosedTradeByBacktestId(backtestId)
            else:
                trades = dnTrade.listTradeByDate(dateFrom, dateTo)

            self.initStatsDatagrid(trades, self.tblStats)
            # self.printLog("listStats ended.")

        except:
            self.printLog("Exception: listStats", traceback.format_exc())

    def listTradeLogs(self):
        try:
            dnTradeLog = DNTradeLog()
            symbol = self.txtSymbolTradeLogs.text().upper().strip()
            tradeId = self.txtTradeIdTradeLogs.text().upper().strip()
            backtestId = self.txtBacktestIdTradeLogs.text().upper().strip()

            if symbol != "":
                tradeLogs = dnTradeLog.listTradeLogBySymbol(symbol)
            elif tradeId != "":
                tradeLogs = dnTradeLog.listTradeLogByTradeId(int(tradeId))
            elif backtestId != "":
                tradeLogs = dnTradeLog.listTradeLogByBacktestId(int(backtestId))
            else:
                tradeLogs = dnTradeLog.listTradeLog()

            self.initTradeLogDatagrid(tradeLogs, self.tblTradeLogs)

        except:
            self.printLog("Exception: listTradeLogs", traceback.format_exc())

    def listTickData(self):
        try:
            dnTickData = DNTickData()
            tickDataList = dnTickData.listTickDataLast()

            self.initTickDataDatagrid(tickDataList, self.tblTickData)

        except:
            self.printLog("Exception: listTradeLogs", traceback.format_exc())

    def onSubmenuTabChanged(self, index):
        try:
            if index == 0:
                self.listSelectedMarket()
                self.listTradedMarket()
            if index == 1:
                self.getIndicatorParameters()
            if index == 2:
                self.getTradeParameters()
            if index == 3:
                self.getQcParameters("BTC")
                self.getQcParameters("USDT")
                self.getQcParameters("ETH")
                self.getQcParameters("BNB")
            if index == 4:
                self.getBotParameters()
        except:
            self.printLog("Exception: onSubmenuTabChanged", traceback.format_exc())

    def initSelectedMarketDropdown(self):
        try:
            self.drpSymbolBuyNow.clear()
            dnMarket = DNMarket()
            markets = dnMarket.listSelectedMarkets()
            if not markets:
                return

            for item in markets:
                self.drpSymbolBuyNow.addItem(item.Symbol)

        except:
            self.printLog("Exception: initSelectedMarketDropdown", traceback.format_exc())

    def onMainmenuTabChanged(self, index):
        try:
            if not self.isOptimizationMode():
                if index == 0:
                    self.listOpenTrade()
                    self.initSelectedMarketDropdown()
                elif index == 1:
                    self.listClosedTrade()
                elif index == 2:
                    # dTo = datetime.now() + timedelta(days=4 * 365)
                    # self.dateToStats.setDateTime(dTo)
                    # self.dateToStats.setDateTime(datetime.now())
                    self.listStats()
                elif index == 3:
                    self.onSubmenuTabChanged(self.tabSubmenu.currentIndex())
                elif index == 4:
                    self.listScannerMarket()
                elif index == 5:
                    self.onLogMenuTabChanged(self.tabLogMenu.currentIndex())
                elif index == 6:
                    self.onOptimizationMenuTabChanged(self.tabOptimizationMenu.currentIndex())
            else:
                # if this is the sub window
                if self.dialog is None:
                    print("onOptimizationMenuTabChanged")
                    self.onOptimizationMenuTabChanged(self.tabOptimizationMenu.currentIndex())
                # else:
                #    print("onSettingsSubmenuTabChanged")
                #    self.onSubmenuTabChanged(self.tabSubmenu.currentIndex())

            # else:
            #    if index == 6:
            #        self.listOptimizationRun()


        except:
            self.printLog("Exception: onMainmenuTabChanged", traceback.format_exc())

    def getLastBacktestId(self):
        dnBacktest = DNBacktest()
        backtests = dnBacktest.listBacktest()
        if backtests:
            return backtests[0].BacktestId
        return 0

    def onLogMenuTabChanged(self, index):
        try:
            if index == 0:
                self.listTradeLogs()
            if index == 1:
                self.listIndicatorLogs()
                print("onLogMenuTabChanged")
            if index == 2:
                self.listBotLogs()
        except:
            self.printLog("Exception: onLogMenuTabChanged", traceback.format_exc())

    def onOptimizationMenuTabChanged(self, index):
        try:
            if index == 1:
                self.listBacktest()
            if index == 2:
                self.listOptimizationRun()

        except:
            self.printLog("Exception: onOptimizationMenuTabChanged", traceback.format_exc())

    def onTick(self):
        try:
            currentTimeInSeconds = int(round(time.time()))

            self.updateTimer()
            if self.tabMainMenu.currentIndex() == 0 and self.chkAutoRefreshOpenTrades.isChecked():
                self.listOpenTrade()
                if currentTimeInSeconds % 15 == 0 or currentTimeInSeconds % 15 == 1:
                    # self.printLog(currentTimeInSeconds)
                    self.listQuickStats()

            elif self.tabMainMenu.currentIndex() == 1 and self.chkAutoRefreshTradeHistory.isChecked():
                self.listClosedTrade()
            elif self.tabMainMenu.currentIndex() == 4:
                self.listScannerMarket()
            elif self.tabMainMenu.currentIndex() == 5:
                if self.tabLogMenu.currentIndex() == 0 and self.chkAutoRefreshTradeLogs.isChecked():
                    self.listTradeLogs()
                elif self.tabLogMenu.currentIndex() == 1 and self.chkAutoRefreshIndLog.isChecked():
                    self.listIndicatorLogs()
                elif self.tabLogMenu.currentIndex() == 2 and self.chkAutoRefreshBotLogs.isChecked():
                    self.listBotLogs()
            elif self.tabMainMenu.currentIndex() == 6:
                if self.tabOptimizationMenu.currentIndex() == 0 and self.chkAutoRefreshDataCollector.isChecked():
                    self.listTickData()
                # elif self.tabOptimizationMenu.currentIndex() == 2 and self.optimizationRunning:
                # self.listOptimizationRun(self.optimizationId)

            # if we have the second window, update the trade history and stats
            if self.dialog is not None:
                if currentTimeInSeconds % 60 == 0:
                    # self.dialog.listStats()
                    self.dialog.listClosedTrade()

        except:
            self.printLog("Exception: onTick", traceback.format_exc())

    def updateTimer(self):
        try:
            if not self.swt.isDataCollectorRunning():
                timeInSeconds = self.botStartTimeInSeconds
            else:
                timeInSeconds = self.dataCollectorStartTimeInSeconds

            currentTimeInSeconds = int(round(time.time()))
            elapsedTimeInSeconds = currentTimeInSeconds - timeInSeconds
            elapsedHours = int(elapsedTimeInSeconds / 60 / 60)
            elapsedMinutes = int(elapsedTimeInSeconds / 60) % 60
            elapsedSeconds = elapsedTimeInSeconds % 60

            hourStr = str(elapsedHours)
            minStr = str(elapsedMinutes)
            secStr = str(elapsedSeconds)

            if elapsedHours < 10:
                hourStr = "0" + str(elapsedHours)
            if elapsedMinutes < 10:
                minStr = "0" + str(elapsedMinutes)
            if elapsedSeconds < 10:
                secStr = "0" + str(elapsedSeconds)

            t = hourStr + ":" + minStr + ":" + secStr

            if not self.swt.isDataCollectorRunning():
                self.lblBotRunTime.setText(t)
            else:
                self.lblDataCollectorRunTime.setText(t)
        except:
            self.printLog("Exception: updateTimer", traceback.format_exc())

    def initHandlers(self):
        try:
            self.btnAddSelectedMarket.clicked.connect(self.onAddSelectedMarketButtonClicked)
            self.btnSaveIndicatorParameters.clicked.connect(self.onSaveIndicatorParametersButtonClicked)
            self.tabMainMenu.currentChanged.connect(self.onMainmenuTabChanged)
            self.tabSubmenu.currentChanged.connect(self.onSubmenuTabChanged)
            self.tabLogMenu.currentChanged.connect(self.onLogMenuTabChanged)
            self.tabOptimizationMenu.currentChanged.connect(self.onOptimizationMenuTabChanged)

            # self.drpIndicatorTimeframe.currentIndexChanged.connect(self.onIndicatorTimeframeIndexChanged)
            self.btnSaveTradeParameters.clicked.connect(self.onSaveTradeParametersButtonClicked)
            # self.drpTradeParamsTimeframe.currentIndexChanged.connect(self.onTradeParamsTimeframeIndexChanged)
            self.btcSaveQcParameters.clicked.connect(self.onSaveQcParametersButtonClicked)
            self.btcSaveBotParameters.clicked.connect(self.onSaveBotParametersButtonClicked)

            self.btnStartBot.clicked.connect(self.onStartBotButtonClicked)
            self.btnBuyNow.clicked.connect(self.onBuyNowButtonClicked)

            self.btnStopEntries.clicked.connect(self.onStopEntriesButtonClicked)
            self.btnExitAllTrades.clicked.connect(self.onExitAllTradesButtonClicked)

            self.txtSpendPercentageBtc.textChanged.connect(self.onRangePercBtcChanged)
            self.txtRangePercBtc1.textChanged.connect(self.onRangePercBtcChanged)
            self.txtRangePercBtc2.textChanged.connect(self.onRangePercBtcChanged)
            self.txtRangePercBtc3.textChanged.connect(self.onRangePercBtcChanged)
            self.txtRangePercBtc4.textChanged.connect(self.onRangePercBtcChanged)
            self.txtRangePercBtc5.textChanged.connect(self.onRangePercBtcChanged)
            self.txtRangePercBtc6.textChanged.connect(self.onRangePercBtcChanged)

            self.txtSpendPercentageUsdt.textChanged.connect(self.onRangePercUsdtChanged)
            self.txtRangePercUsdt1.textChanged.connect(self.onRangePercUsdtChanged)
            self.txtRangePercUsdt2.textChanged.connect(self.onRangePercUsdtChanged)
            self.txtRangePercUsdt3.textChanged.connect(self.onRangePercUsdtChanged)
            self.txtRangePercUsdt4.textChanged.connect(self.onRangePercUsdtChanged)
            self.txtRangePercUsdt5.textChanged.connect(self.onRangePercUsdtChanged)
            self.txtRangePercUsdt6.textChanged.connect(self.onRangePercUsdtChanged)

            self.txtSpendPercentageEth.textChanged.connect(self.onRangePercEthChanged)
            self.txtRangePercEth1.textChanged.connect(self.onRangePercEthChanged)
            self.txtRangePercEth2.textChanged.connect(self.onRangePercEthChanged)
            self.txtRangePercEth3.textChanged.connect(self.onRangePercEthChanged)
            self.txtRangePercEth4.textChanged.connect(self.onRangePercEthChanged)
            self.txtRangePercEth5.textChanged.connect(self.onRangePercEthChanged)
            self.txtRangePercEth6.textChanged.connect(self.onRangePercEthChanged)

            self.txtSpendPercentageBnb.textChanged.connect(self.onRangePercBnbChanged)
            self.txtRangePercBnb1.textChanged.connect(self.onRangePercBnbChanged)
            self.txtRangePercBnb2.textChanged.connect(self.onRangePercBnbChanged)
            self.txtRangePercBnb3.textChanged.connect(self.onRangePercBnbChanged)
            self.txtRangePercBnb4.textChanged.connect(self.onRangePercBnbChanged)
            self.txtRangePercBnb5.textChanged.connect(self.onRangePercBnbChanged)
            self.txtRangePercBnb6.textChanged.connect(self.onRangePercBnbChanged)

            self.btnSearchMarket.clicked.connect(self.onSearchMarketButtonClicked)
            self.btnSearchMarketIndLog.clicked.connect(self.onSearchMarketIndLogButtonClicked)
            self.btnSearchTradeHistory.clicked.connect(self.onSearchTradeHistoryButtonClicked)
            self.btnSearchTradeLogs.clicked.connect(self.onSearchTradeLogsButtonClicked)
            self.btnSearchBotLogs.clicked.connect(self.onSearchBotLogsButtonClicked)
            self.btnSearchStats.clicked.connect(self.onSearchStatsButtonClicked)

            self.btnTruncateTrade.clicked.connect(self.onTruncateTradeButtonClicked)
            self.btnTruncateBotLog.clicked.connect(self.onTruncateBotLogButtonClicked)
            self.btnTruncateIndicatorLog.clicked.connect(self.onTruncateIndicatorLogButtonClicked)
            self.btnTruncateTradeLog.clicked.connect(self.onTruncateTradeLogButtonClicked)

            self.btnStartDataCollector.clicked.connect(self.onStartDataCollectorButtonClicked)
            self.btnStartBacktest.clicked.connect(self.onStartBacktestButtonClicked)
            self.btnDownloadCandles.clicked.connect(self.onDownloadCandlesButtonClicked)
            self.btnStartOptimization.clicked.connect(self.onStartOptimizationButtonClicked)
            self.btnStartOptimization_IndPar.clicked.connect(self.onStartOptimizationButtonClicked)
            self.btnStartOptimization_TradePar.clicked.connect(self.onStartOptimizationButtonClicked)

            self.btnStartOptimizationLoop_IndPar.clicked.connect(self.onStartOptimizationSingleLoopButtonClicked)
            self.btnStartOptimizationLoop_TradePar.clicked.connect(self.onStartOptimizationSingleLoopButtonClicked)

            self.tblOptimizationRuns.clicked.connect(self.onOptimizationRunsClicked)
            self.tblBotLogs.clicked.connect(self.onBotLogsClicked)

            self.btnUpdateMarketsOpt.clicked.connect(self.onUpdateMarketsOptButtonClicked)
            self.btnStartOptimizationLoop.clicked.connect(self.onStartOptimizationLoopButtonClicked)
            self.btnListAllOptimizationRuns.clicked.connect(self.onListAllOptimizationRunsButtonClicked)

            self.tblScannerMarket.clicked.connect(self.onScannerClicked)

            self.btnImportSelectedMarkets.clicked.connect(self.onImportSelectedMarkets)
            self.btnExportSelectedMarkets.clicked.connect(self.onExportSelectedMarkets)




        except:
            self.printLog("Exception: initHandlers", traceback.format_exc())

    # QC Parameters

    def computeRangeAmount(self, asset, perc):
        try:
            if asset == "BTC":
                totalBalance = float(self.txtTotalBalanceBtc.text())
                spendPerc = float(self.txtSpendPercentageBtc.text())
            elif asset == "USDT":
                totalBalance = float(self.txtTotalBalanceUsdt.text())
                spendPerc = float(self.txtSpendPercentageUsdt.text())
            elif asset == "ETH":
                totalBalance = float(self.txtTotalBalanceEth.text())
                spendPerc = float(self.txtSpendPercentageEth.text())
            elif asset == "BNB":
                totalBalance = float(self.txtTotalBalanceBnb.text())
                spendPerc = float(self.txtSpendPercentageBnb.text())

            val = totalBalance / 100 * spendPerc
            val = val / 100 * perc

            if asset == "BTC":
                val = round(val, 8)
            elif asset == "ETH":
                val = round(val, 8)
            else:
                val = round(val, 2)

            valStr = str(val)
            if "E-" in valStr or "e-" in valStr:
                val = format(val, '.8f')

        except:
            self.printLog("Exception: computeRangeAmount", traceback.format_exc())

        return val

    def onRangePercBtcChanged(self):
        try:
            if self.txtSpendPercentageBtc.text() == "":
                return

            if self.txtRangePercBtc1.text() != "":
                self.txtRangeAmountBtc1.setText(
                    str(self.computeRangeAmount("BTC", float(self.txtRangePercBtc1.text()))))
            if self.txtRangePercBtc2.text() != "":
                self.txtRangeAmountBtc2.setText(
                    str(self.computeRangeAmount("BTC", float(self.txtRangePercBtc2.text()))))
            if self.txtRangePercBtc3.text() != "":
                self.txtRangeAmountBtc3.setText(
                    str(self.computeRangeAmount("BTC", float(self.txtRangePercBtc3.text()))))
            if self.txtRangePercBtc4.text() != "":
                self.txtRangeAmountBtc4.setText(
                    str(self.computeRangeAmount("BTC", float(self.txtRangePercBtc4.text()))))
            if self.txtRangePercBtc5.text() != "":
                self.txtRangeAmountBtc5.setText(
                    str(self.computeRangeAmount("BTC", float(self.txtRangePercBtc5.text()))))
            if self.txtRangePercBtc6.text() != "":
                self.txtRangeAmountBtc6.setText(
                    str(self.computeRangeAmount("BTC", float(self.txtRangePercBtc6.text()))))
        except:
            self.printLog("Exception: onRangePercBtcChanged", traceback.format_exc())

    def onRangePercUsdtChanged(self):
        try:
            if self.txtSpendPercentageUsdt.text() == "":
                return

            if self.txtRangePercUsdt1.text() != "":
                self.txtRangeAmountUsdt1.setText(
                    str(self.computeRangeAmount("USDT", float(self.txtRangePercUsdt1.text()))))
            if self.txtRangePercUsdt2.text() != "":
                self.txtRangeAmountUsdt2.setText(
                    str(self.computeRangeAmount("USDT", float(self.txtRangePercUsdt2.text()))))
            if self.txtRangePercUsdt3.text() != "":
                self.txtRangeAmountUsdt3.setText(
                    str(self.computeRangeAmount("USDT", float(self.txtRangePercUsdt3.text()))))
            if self.txtRangePercUsdt4.text() != "":
                self.txtRangeAmountUsdt4.setText(
                    str(self.computeRangeAmount("USDT", float(self.txtRangePercUsdt4.text()))))
            if self.txtRangePercUsdt5.text() != "":
                self.txtRangeAmountUsdt5.setText(
                    str(self.computeRangeAmount("USDT", float(self.txtRangePercUsdt5.text()))))
            if self.txtRangePercUsdt6.text() != "":
                self.txtRangeAmountUsdt6.setText(
                    str(self.computeRangeAmount("USDT", float(self.txtRangePercUsdt6.text()))))

        except:
            self.printLog("Exception: onRangePercUsdtChanged", traceback.format_exc())

    def onRangePercEthChanged(self):
        try:
            if self.txtSpendPercentageEth.text() == "":
                return

            if self.txtRangePercEth1.text() != "":
                self.txtRangeAmountEth1.setText(
                    str(self.computeRangeAmount("ETH", float(self.txtRangePercEth1.text()))))
            if self.txtRangePercEth2.text() != "":
                self.txtRangeAmountEth2.setText(
                    str(self.computeRangeAmount("ETH", float(self.txtRangePercEth2.text()))))
            if self.txtRangePercEth3.text() != "":
                self.txtRangeAmountEth3.setText(
                    str(self.computeRangeAmount("ETH", float(self.txtRangePercEth3.text()))))
            if self.txtRangePercEth4.text() != "":
                self.txtRangeAmountEth4.setText(
                    str(self.computeRangeAmount("ETH", float(self.txtRangePercEth4.text()))))
            if self.txtRangePercEth5.text() != "":
                self.txtRangeAmountEth5.setText(
                    str(self.computeRangeAmount("ETH", float(self.txtRangePercEth5.text()))))
            if self.txtRangePercEth6.text() != "":
                self.txtRangeAmountEth6.setText(
                    str(self.computeRangeAmount("ETH", float(self.txtRangePercEth6.text()))))

        except:
            self.printLog("Exception: onRangePercEthChanged", traceback.format_exc())

    def onRangePercBnbChanged(self):
        try:
            if self.txtSpendPercentageBnb.text() == "":
                return

            if self.txtRangePercBnb1.text() != "":
                self.txtRangeAmountBnb1.setText(
                    str(self.computeRangeAmount("BNB", float(self.txtRangePercBnb1.text()))))
            if self.txtRangePercBnb2.text() != "":
                self.txtRangeAmountBnb2.setText(
                    str(self.computeRangeAmount("BNB", float(self.txtRangePercBnb2.text()))))
            if self.txtRangePercBnb3.text() != "":
                self.txtRangeAmountBnb3.setText(
                    str(self.computeRangeAmount("BNB", float(self.txtRangePercBnb3.text()))))
            if self.txtRangePercBnb4.text() != "":
                self.txtRangeAmountBnb4.setText(
                    str(self.computeRangeAmount("BNB", float(self.txtRangePercBnb4.text()))))
            if self.txtRangePercBnb5.text() != "":
                self.txtRangeAmountBnb5.setText(
                    str(self.computeRangeAmount("BNB", float(self.txtRangePercBnb5.text()))))
            if self.txtRangePercBnb6.text() != "":
                self.txtRangeAmountBnb6.setText(
                    str(self.computeRangeAmount("BNB", float(self.txtRangePercBnb6.text()))))

        except:
            self.printLog("Exception: onRangePercBnbChanged", traceback.format_exc())

    def initValidators(self):
        try:
            # self.txtRocPeriodR.setValidator(QIntValidator(0, 100, self))
            self.txtSpendPercentageBtc.setValidator(QDoubleValidator(0, 100, 1, self))
            self.txtRangePercBtc1.setValidator(QDoubleValidator(0, 100, 1, self))
            self.txtRangePercBtc2.setValidator(QDoubleValidator(0, 100, 1, self))
            self.txtRangePercBtc3.setValidator(QDoubleValidator(0, 100, 1, self))
            self.txtRangePercBtc4.setValidator(QDoubleValidator(0, 100, 1, self))
            self.txtRangePercBtc5.setValidator(QDoubleValidator(0, 100, 1, self))
            self.txtRangePercBtc6.setValidator(QDoubleValidator(0, 100, 1, self))
            self.txtRebuyTriggerAmountBtc.setValidator(QDoubleValidator(0, 100, 8, self))
            self.txtRebuyAmountBtc.setValidator(QDoubleValidator(0, 100, 8, self))

            self.txtSpendPercentageUsdt.setValidator(QDoubleValidator(0, 100, 1, self))
            self.txtRangePercUsdt1.setValidator(QDoubleValidator(0, 100, 1, self))
            self.txtRangePercUsdt2.setValidator(QDoubleValidator(0, 100, 1, self))
            self.txtRangePercUsdt3.setValidator(QDoubleValidator(0, 100, 1, self))
            self.txtRangePercUsdt4.setValidator(QDoubleValidator(0, 100, 1, self))
            self.txtRangePercUsdt5.setValidator(QDoubleValidator(0, 100, 1, self))
            self.txtRangePercUsdt6.setValidator(QDoubleValidator(0, 100, 1, self))

            self.txtSpendPercentageEth.setValidator(QDoubleValidator(0, 100, 1, self))
            self.txtRangePercEth1.setValidator(QDoubleValidator(0, 100, 1, self))
            self.txtRangePercEth2.setValidator(QDoubleValidator(0, 100, 1, self))
            self.txtRangePercEth3.setValidator(QDoubleValidator(0, 100, 1, self))
            self.txtRangePercEth4.setValidator(QDoubleValidator(0, 100, 1, self))
            self.txtRangePercEth5.setValidator(QDoubleValidator(0, 100, 1, self))
            self.txtRangePercEth6.setValidator(QDoubleValidator(0, 100, 1, self))
            self.txtRebuyTriggerAmountEth.setValidator(QDoubleValidator(0, 100, 2, self))
            self.txtRebuyAmountEth.setValidator(QDoubleValidator(0, 100, 2, self))

            self.txtSpendPercentageBnb.setValidator(QDoubleValidator(0, 100, 1, self))
            self.txtRangePercBnb1.setValidator(QDoubleValidator(0, 100, 1, self))
            self.txtRangePercBnb2.setValidator(QDoubleValidator(0, 100, 1, self))
            self.txtRangePercBnb3.setValidator(QDoubleValidator(0, 100, 1, self))
            self.txtRangePercBnb4.setValidator(QDoubleValidator(0, 100, 1, self))
            self.txtRangePercBnb5.setValidator(QDoubleValidator(0, 100, 1, self))
            self.txtRangePercBnb6.setValidator(QDoubleValidator(0, 100, 1, self))
            self.txtRebuyTriggerAmountBnb.setValidator(QDoubleValidator(0, 100, 2, self))
            self.txtRebuyAmountBnb.setValidator(QDoubleValidator(0, 100, 2, self))

        except:
            self.printLog("Exception: setupValidators", traceback.format_exc())

    # Bot Parameters

    def getBotParameters(self):
        try:
            dnBotParameters = DNBotParameters()
            bp = dnBotParameters.getBotParameters()
            if bp is None:
                return

            self.txtApiKey.setText(bp.apiKey)
            self.txtSecretKey.setText(bp.secretKey)
            self.txtMaxConcurrentTradeNumber.setText(str(bp.maxConcurrentTradeNumber))
            self.txtMinPrice.setText(self.formatPrice("BTC", bp.minPrice))
            self.txtMinDailyVolume.setText(str(round(bp.minDailyVolume, 2)))
            self.drpRunOnSelectedMarkets.setCurrentIndex(bp.runOnSelectedMarkets)
            self.drpOptimizationMode.setCurrentIndex(bp.optimizationMode)
            self.txtBankingPercentage.setText(str(round(bp.bankingPercentage, 2)))
            self.drpOptUpdateStrategyParameters.setCurrentIndex(bp.optUpdateStrategyParameters)
        except:
            self.printLog("Exception: getBotParameters", traceback.format_exc())

    def onSaveBotParametersButtonClicked(self):
        try:
            print("onSaveBotParametersButtonClicked")
            dnBotParameters = DNBotParameters()
            bp = dnBotParameters.getBotParameters()

            update = False
            if bp is None:
                bp = BotParameters()
            else:
                update = True

            bp.apiKey = self.txtApiKey.text()
            bp.secretKey = self.txtSecretKey.text()
            bp.maxConcurrentTradeNumber = int(self.txtMaxConcurrentTradeNumber.text())
            bp.minPrice = float(self.txtMinPrice.text())
            bp.minDailyVolume = float(self.txtMinDailyVolume.text())
            bp.runOnSelectedMarkets = self.drpRunOnSelectedMarkets.currentText() == 'true'
            bp.marketUpdateDate = 0
            bp.optimizationMode = self.drpOptimizationMode.currentText() == 'true'
            bp.bankingPercentage = float(self.txtBankingPercentage.text())
            bp.optUpdateStrategyParameters = self.drpOptUpdateStrategyParameters.currentText() == 'true'

            if update:
                dnBotParameters.updateBotParameters(bp)
            else:
                dnBotParameters.insertBotParameters(bp)

            self.getBotParameters()

            self.updateOptimizationModeControls()

            self.statusBar.showMessage("Bot parameters are saved successfully!", 2000)

        except:
            self.printLog("Exception: onSaveBotParametersButtonClicked", traceback.format_exc())

    def saveQcParameters(self, asset):
        try:
            dnMarket = DNMarket()
            dnQcParameters = DNQcParameters()
            qcPar = dnQcParameters.getQcParameters(asset)
            prevEnabled = qcPar.tradeEnabled

            update = False
            if qcPar is None:
                qcPar = QcParameters()
            else:
                update = True

            minRebuyAmount = 0
            amount1 = 0
            amount2 = 0
            amount3 = 0
            amount4 = 0
            amount5 = 0
            amount6 = 0

            qcPar.asset = asset
            if asset == "BTC":
                qcPar.minVolume1 = float(self.txtRangeMinBtc1.text())
                qcPar.maxVolume1 = float(self.txtRangeMaxBtc1.text())
                qcPar.perc1 = float(self.txtRangePercBtc1.text())
                qcPar.minVolume2 = float(self.txtRangeMinBtc2.text())
                qcPar.maxVolume2 = float(self.txtRangeMaxBtc2.text())
                qcPar.perc2 = float(self.txtRangePercBtc2.text())
                qcPar.minVolume3 = float(self.txtRangeMinBtc3.text())
                qcPar.maxVolume3 = float(self.txtRangeMaxBtc3.text())
                qcPar.perc3 = float(self.txtRangePercBtc3.text())
                qcPar.minVolume4 = float(self.txtRangeMinBtc4.text())
                qcPar.maxVolume4 = float(self.txtRangeMaxBtc4.text())
                qcPar.perc4 = float(self.txtRangePercBtc4.text())
                qcPar.minVolume5 = float(self.txtRangeMinBtc5.text())
                qcPar.maxVolume5 = float(self.txtRangeMaxBtc5.text())
                qcPar.perc5 = float(self.txtRangePercBtc5.text())
                qcPar.minVolume6 = float(self.txtRangeMinBtc6.text())
                qcPar.maxVolume6 = float(self.txtRangeMaxBtc6.text())
                qcPar.perc6 = float(self.txtRangePercBtc6.text())
                qcPar.dailySpendPerc = float(self.txtSpendPercentageBtc.text())
                qcPar.tradeEnabled = self.drpTradingEnabledBtc.currentText() == 'true'
                qcPar.rebuyTriggerAmount = float(self.txtRebuyTriggerAmountBtc.text())
                qcPar.rebuyAmount = float(self.txtRebuyAmountBtc.text())
                market = dnMarket.getMarketBySymbol("BTCUSDT")
                # minRebuyAmount = market.MinAmountToTrade / market.DailyPrice
                # minRebuyAmount = minRebuyAmount * decimal.Decimal(1.1)
                # minRebuyAmount = round(minRebuyAmount, 8)

                if qcPar.tradeEnabled:
                    amount1 = float(self.txtRangeAmountBtc1.text())
                    amount2 = float(self.txtRangeAmountBtc2.text())
                    amount3 = float(self.txtRangeAmountBtc3.text())
                    amount4 = float(self.txtRangeAmountBtc4.text())
                    amount5 = float(self.txtRangeAmountBtc5.text())
                    amount6 = float(self.txtRangeAmountBtc6.text())

                    print(amount1)

                    amount1 = self.roundFloat(amount1, "BTC")
                    amount2 = self.roundFloat(amount2, "BTC")
                    amount3 = self.roundFloat(amount3, "BTC")
                    amount4 = self.roundFloat(amount4, "BTC")
                    amount5 = self.roundFloat(amount5, "BTC")
                    amount6 = self.roundFloat(amount6, "BTC")

                    print(amount1)

            if asset == "USDT":
                qcPar.minVolume1 = float(self.txtRangeMinUsdt1.text())
                qcPar.maxVolume1 = float(self.txtRangeMaxUsdt1.text())
                qcPar.perc1 = float(self.txtRangePercUsdt1.text())
                qcPar.minVolume2 = float(self.txtRangeMinUsdt2.text())
                qcPar.maxVolume2 = float(self.txtRangeMaxUsdt2.text())
                qcPar.perc2 = float(self.txtRangePercUsdt2.text())
                qcPar.minVolume3 = float(self.txtRangeMinUsdt3.text())
                qcPar.maxVolume3 = float(self.txtRangeMaxUsdt3.text())
                qcPar.perc3 = float(self.txtRangePercUsdt3.text())
                qcPar.minVolume4 = float(self.txtRangeMinUsdt4.text())
                qcPar.maxVolume4 = float(self.txtRangeMaxUsdt4.text())
                qcPar.perc4 = float(self.txtRangePercUsdt4.text())
                qcPar.minVolume5 = float(self.txtRangeMinUsdt5.text())
                qcPar.maxVolume5 = float(self.txtRangeMaxUsdt5.text())
                qcPar.perc5 = float(self.txtRangePercUsdt5.text())
                qcPar.minVolume6 = float(self.txtRangeMinUsdt6.text())
                qcPar.maxVolume6 = float(self.txtRangeMaxUsdt6.text())
                qcPar.perc6 = float(self.txtRangePercUsdt6.text())
                qcPar.dailySpendPerc = float(self.txtSpendPercentageUsdt.text())
                qcPar.tradeEnabled = self.drpTradingEnabledUsdt.currentText() == 'true'
                qcPar.rebuyTriggerAmount = float(self.txtMinUsdtAmount.text())  # we use this field for Min USDT Amount
                qcPar.rebuyAmount = 0
                minRebuyAmount = 0

            if asset == "ETH":
                qcPar.minVolume1 = float(self.txtRangeMinEth1.text())
                qcPar.maxVolume1 = float(self.txtRangeMaxEth1.text())
                qcPar.perc1 = float(self.txtRangePercEth1.text())
                qcPar.minVolume2 = float(self.txtRangeMinEth2.text())
                qcPar.maxVolume2 = float(self.txtRangeMaxEth2.text())
                qcPar.perc2 = float(self.txtRangePercEth2.text())
                qcPar.minVolume3 = float(self.txtRangeMinEth3.text())
                qcPar.maxVolume3 = float(self.txtRangeMaxEth3.text())
                qcPar.perc3 = float(self.txtRangePercEth3.text())
                qcPar.minVolume4 = float(self.txtRangeMinEth4.text())
                qcPar.maxVolume4 = float(self.txtRangeMaxEth4.text())
                qcPar.perc4 = float(self.txtRangePercEth4.text())
                qcPar.minVolume5 = float(self.txtRangeMinEth5.text())
                qcPar.maxVolume5 = float(self.txtRangeMaxEth5.text())
                qcPar.perc5 = float(self.txtRangePercEth5.text())
                qcPar.minVolume6 = float(self.txtRangeMinEth6.text())
                qcPar.maxVolume6 = float(self.txtRangeMaxEth6.text())
                qcPar.perc6 = float(self.txtRangePercEth6.text())
                qcPar.dailySpendPerc = float(self.txtSpendPercentageEth.text())
                qcPar.tradeEnabled = self.drpTradingEnabledEth.currentText() == 'true'
                qcPar.rebuyTriggerAmount = float(self.txtRebuyTriggerAmountEth.text())
                qcPar.rebuyAmount = float(self.txtRebuyAmountEth.text())
                market = dnMarket.getMarketBySymbol("ETHUSDT")
                # minRebuyAmount = market.MinAmountToTrade / market.DailyPrice
                # minRebuyAmount = minRebuyAmount * decimal.Decimal(1.1)
                # minRebuyAmount = round(minRebuyAmount, 2)

                if qcPar.tradeEnabled:
                    amount1 = float(self.txtRangeAmountEth1.text())
                    amount2 = float(self.txtRangeAmountEth2.text())
                    amount3 = float(self.txtRangeAmountEth3.text())
                    amount4 = float(self.txtRangeAmountEth4.text())
                    amount5 = float(self.txtRangeAmountEth5.text())
                    amount6 = float(self.txtRangeAmountEth6.text())
                    amount1 = self.roundFloat(amount1, "ETH")
                    amount2 = self.roundFloat(amount2, "ETH")
                    amount3 = self.roundFloat(amount3, "ETH")
                    amount4 = self.roundFloat(amount4, "ETH")
                    amount5 = self.roundFloat(amount5, "ETH")
                    amount6 = self.roundFloat(amount6, "ETH")

            if asset == "BNB":
                qcPar.minVolume1 = float(self.txtRangeMinBnb1.text())
                qcPar.maxVolume1 = float(self.txtRangeMaxBnb1.text())
                qcPar.perc1 = float(self.txtRangePercBnb1.text())
                qcPar.minVolume2 = float(self.txtRangeMinBnb2.text())
                qcPar.maxVolume2 = float(self.txtRangeMaxBnb2.text())
                qcPar.perc2 = float(self.txtRangePercBnb2.text())
                qcPar.minVolume3 = float(self.txtRangeMinBnb3.text())
                qcPar.maxVolume3 = float(self.txtRangeMaxBnb3.text())
                qcPar.perc3 = float(self.txtRangePercBnb3.text())
                qcPar.minVolume4 = float(self.txtRangeMinBnb4.text())
                qcPar.maxVolume4 = float(self.txtRangeMaxBnb4.text())
                qcPar.perc4 = float(self.txtRangePercBnb4.text())
                qcPar.minVolume5 = float(self.txtRangeMinBnb5.text())
                qcPar.maxVolume5 = float(self.txtRangeMaxBnb5.text())
                qcPar.perc5 = float(self.txtRangePercBnb5.text())
                qcPar.minVolume6 = float(self.txtRangeMinBnb6.text())
                qcPar.maxVolume6 = float(self.txtRangeMaxBnb6.text())
                qcPar.perc6 = float(self.txtRangePercBnb6.text())
                qcPar.dailySpendPerc = float(self.txtSpendPercentageBnb.text())
                qcPar.tradeEnabled = self.drpTradingEnabledBnb.currentText() == 'true'
                qcPar.rebuyTriggerAmount = float(self.txtRebuyTriggerAmountBnb.text())
                qcPar.rebuyAmount = float(self.txtRebuyAmountBnb.text())
                market = dnMarket.getMarketBySymbol("BNBUSDT")
                # minRebuyAmount = market.MinAmountToTrade / market.DailyPrice
                # minRebuyAmount = minRebuyAmount * decimal.Decimal(1.1)
                # minRebuyAmount = round(minRebuyAmount, 2)

                if qcPar.tradeEnabled:
                    amount1 = float(self.txtRangeAmountBnb1.text())
                    amount2 = float(self.txtRangeAmountBnb2.text())
                    amount3 = float(self.txtRangeAmountBnb3.text())
                    amount4 = float(self.txtRangeAmountBnb4.text())
                    amount5 = float(self.txtRangeAmountBnb5.text())
                    amount6 = float(self.txtRangeAmountBnb6.text())
                    amount1 = self.roundFloat(amount1, "BNB")
                    amount2 = self.roundFloat(amount2, "BNB")
                    amount3 = self.roundFloat(amount3, "BNB")
                    amount4 = self.roundFloat(amount4, "BNB")
                    amount5 = self.roundFloat(amount5, "BNB")
                    amount6 = self.roundFloat(amount6, "BNB")

            # warn but save anyways.

            if 0 < qcPar.rebuyAmount < minRebuyAmount:
                QMessageBox.question(self, "Error",
                                     asset + " Rebuy Amount cannot be smaller than the minimum buy amount of " + str(
                                         minRebuyAmount), QMessageBox.Ok)
                # return False
            if 0 < amount1 < minRebuyAmount:
                QMessageBox.question(self, "Error",
                                     asset + " Range Amount 1 cannot be smaller than the minimum buy amount of " + str(
                                         minRebuyAmount), QMessageBox.Ok)
                # return False
            if 0 < amount2 < minRebuyAmount:
                QMessageBox.question(self, "Error",
                                     asset + " Range Amount 2 cannot be smaller than the minimum buy amount of " + str(
                                         minRebuyAmount), QMessageBox.Ok)
                # return False
            if 0 < amount3 < minRebuyAmount:
                QMessageBox.question(self, "Error",
                                     asset + " Range Amount 3 cannot be smaller than the minimum buy amount of " + str(
                                         minRebuyAmount), QMessageBox.Ok)
                # return False
            if 0 < amount4 < minRebuyAmount:
                QMessageBox.question(self, "Error",
                                     asset + " Range Amount 4 cannot be smaller than the minimum buy amount of " + str(
                                         minRebuyAmount), QMessageBox.Ok)
                # return False
            if 0 < amount5 < minRebuyAmount:
                QMessageBox.question(self, "Error",
                                     asset + " Range Amount 5 cannot be smaller than the minimum buy amount of " + str(
                                         minRebuyAmount), QMessageBox.Ok)
                # return False
            if 0 < amount6 < minRebuyAmount:
                QMessageBox.question(self, "Error",
                                     asset + " Range Amount 6 cannot be smaller than the minimum buy amount of " + str(
                                         minRebuyAmount), QMessageBox.Ok)
                # return False

            if prevEnabled != qcPar.tradeEnabled:
                dnBotParameters = DNBotParameters()
                bp = dnBotParameters.getBotParameters()
                bp.marketUpdateDate = 0
                dnBotParameters.updateBotParameters(bp)

            if update:
                dnQcParameters.updateQcParameters(qcPar)
            else:
                dnQcParameters.insertQcParameters(qcPar)

            return True

        except:
            self.printLog("Exception: saveQcParameters", traceback.format_exc())
            return False

    def onSaveQcParametersButtonClicked(self):
        try:
            print("onSaveQcParametersButtonClicked")
            successBtc = self.saveQcParameters("BTC")
            successUsdt = self.saveQcParameters("USDT")
            successEth = self.saveQcParameters("ETH")
            successBnb = self.saveQcParameters("BNB")

            if successBtc:
                self.getQcParameters("BTC")
            if successUsdt:
                self.getQcParameters("USDT")
            if successEth:
                self.getQcParameters("ETH")
            if successBnb:
                self.getQcParameters("BNB")

            self.statusBar.showMessage("Qc parameters are saved successfully!", 2000)

        except:
            self.printLog("Exception: onSaveQcParametersButtonClicked", traceback.format_exc())

    def getBalance(self, assetName, useCache):
        try:
            balance = 0
            if not useCache:
                clientBalance = self.client.get_asset_balance(assetName)
                balance = clientBalance.free
            else:
                dnAsset = DNAsset()
                asset = dnAsset.getAsset(assetName)

                if asset is None or asset.BalanceFree == -1:
                    clientBalance = self.client.get_asset_balance(assetName)
                    balance = clientBalance.free
                else:
                    balance = asset.BalanceFree

            return balance
        except:
            self.printLog("Exception: getBalance", traceback.format_exc())

    def roundFloat(self, value, asset):
        try:
            if value == 0:
                return 0

            digits = 2
            if asset == "BTC":
                digits = 8

            return round(value, digits)

        except:
            self.printLog("Exception: roundFloat", traceback.format_exc())

    def getQcParameters(self, asset):
        try:
            dnQcParameters = DNQcParameters()
            qcPar = dnQcParameters.getQcParameters(asset)

            dnAsset = DNAsset()

            if qcPar is None:
                return

            if asset == "BTC":
                balanceBtc = self.getBalance("BTC", False)
                self.txtTotalBalanceBtc.setText(str(format(balanceBtc, '.8f')))

                self.drpTradingEnabledBtc.setCurrentIndex(qcPar.tradeEnabled)
                self.txtSpendPercentageBtc.setText(str(qcPar.dailySpendPerc))
                self.txtRangeMinBtc1.setText(str(qcPar.minVolume1))
                self.txtRangeMinBtc2.setText(str(qcPar.minVolume2))
                self.txtRangeMinBtc3.setText(str(qcPar.minVolume3))
                self.txtRangeMinBtc4.setText(str(qcPar.minVolume4))
                self.txtRangeMinBtc5.setText(str(qcPar.minVolume5))
                self.txtRangeMinBtc6.setText(str(qcPar.minVolume6))
                self.txtRangeMaxBtc1.setText(str(qcPar.maxVolume1))
                self.txtRangeMaxBtc2.setText(str(qcPar.maxVolume2))
                self.txtRangeMaxBtc3.setText(str(qcPar.maxVolume3))
                self.txtRangeMaxBtc4.setText(str(qcPar.maxVolume4))
                self.txtRangeMaxBtc5.setText(str(qcPar.maxVolume5))
                self.txtRangeMaxBtc6.setText(str(qcPar.maxVolume6))
                self.txtRangePercBtc1.setText(str(qcPar.perc1))
                self.txtRangePercBtc2.setText(str(qcPar.perc2))
                self.txtRangePercBtc3.setText(str(qcPar.perc3))
                self.txtRangePercBtc4.setText(str(qcPar.perc4))
                self.txtRangePercBtc5.setText(str(qcPar.perc5))
                self.txtRangePercBtc6.setText(str(qcPar.perc6))
                self.txtRebuyTriggerAmountBtc.setText(str(self.roundFloat(qcPar.rebuyTriggerAmount, "BTC")))
                self.txtRebuyAmountBtc.setText(str(self.roundFloat(qcPar.rebuyAmount, "BTC")))
                self.onRangePercBtcChanged()

            if asset == "USDT":
                balanceUsdt = self.getBalance("USDT", False)
                # self.txtTotalBalanceUsdt.setText(str(balanceUsdt))
                self.txtTotalBalanceUsdt.setText(str(format(balanceUsdt, '.8f')))

                self.drpTradingEnabledUsdt.setCurrentIndex(qcPar.tradeEnabled)
                self.txtSpendPercentageUsdt.setText(str(qcPar.dailySpendPerc))
                self.txtRangeMinUsdt1.setText(str(qcPar.minVolume1))
                self.txtRangeMinUsdt2.setText(str(qcPar.minVolume2))
                self.txtRangeMinUsdt3.setText(str(qcPar.minVolume3))
                self.txtRangeMinUsdt4.setText(str(qcPar.minVolume4))
                self.txtRangeMinUsdt5.setText(str(qcPar.minVolume5))
                self.txtRangeMinUsdt6.setText(str(qcPar.minVolume6))
                self.txtRangeMaxUsdt1.setText(str(qcPar.maxVolume1))
                self.txtRangeMaxUsdt2.setText(str(qcPar.maxVolume2))
                self.txtRangeMaxUsdt3.setText(str(qcPar.maxVolume3))
                self.txtRangeMaxUsdt4.setText(str(qcPar.maxVolume4))
                self.txtRangeMaxUsdt5.setText(str(qcPar.maxVolume5))
                self.txtRangeMaxUsdt6.setText(str(qcPar.maxVolume6))
                self.txtRangePercUsdt1.setText(str(qcPar.perc1))
                self.txtRangePercUsdt2.setText(str(qcPar.perc2))
                self.txtRangePercUsdt3.setText(str(qcPar.perc3))
                self.txtRangePercUsdt4.setText(str(qcPar.perc4))
                self.txtRangePercUsdt5.setText(str(qcPar.perc5))
                self.txtRangePercUsdt6.setText(str(qcPar.perc6))
                self.txtMinUsdtAmount.setText(str(self.roundFloat(qcPar.rebuyTriggerAmount, "USDT")))
                self.onRangePercUsdtChanged()

            if asset == "ETH":
                balanceEth = self.getBalance("ETH", False)
                # self.txtTotalBalanceEth.setText(str(balanceEth))
                self.txtTotalBalanceEth.setText(str(format(balanceEth, '.8f')))

                self.drpTradingEnabledEth.setCurrentIndex(qcPar.tradeEnabled)
                self.txtSpendPercentageEth.setText(str(qcPar.dailySpendPerc))
                self.txtRangeMinEth1.setText(str(qcPar.minVolume1))
                self.txtRangeMinEth2.setText(str(qcPar.minVolume2))
                self.txtRangeMinEth3.setText(str(qcPar.minVolume3))
                self.txtRangeMinEth4.setText(str(qcPar.minVolume4))
                self.txtRangeMinEth5.setText(str(qcPar.minVolume5))
                self.txtRangeMinEth6.setText(str(qcPar.minVolume6))
                self.txtRangeMaxEth1.setText(str(qcPar.maxVolume1))
                self.txtRangeMaxEth2.setText(str(qcPar.maxVolume2))
                self.txtRangeMaxEth3.setText(str(qcPar.maxVolume3))
                self.txtRangeMaxEth4.setText(str(qcPar.maxVolume4))
                self.txtRangeMaxEth5.setText(str(qcPar.maxVolume5))
                self.txtRangeMaxEth6.setText(str(qcPar.maxVolume6))
                self.txtRangePercEth1.setText(str(qcPar.perc1))
                self.txtRangePercEth2.setText(str(qcPar.perc2))
                self.txtRangePercEth3.setText(str(qcPar.perc3))
                self.txtRangePercEth4.setText(str(qcPar.perc4))
                self.txtRangePercEth5.setText(str(qcPar.perc5))
                self.txtRangePercEth6.setText(str(qcPar.perc6))
                self.txtRebuyTriggerAmountEth.setText(str(self.roundFloat(qcPar.rebuyTriggerAmount, "ETH")))
                self.txtRebuyAmountEth.setText(str(self.roundFloat(qcPar.rebuyAmount, "ETH")))
                self.onRangePercEthChanged()

            if asset == "BNB":
                balanceBnb = self.getBalance("USD", False)
                # self.txtTotalBalanceBnb.setText(str(balanceBnb))
                self.txtTotalBalanceBnb.setText(str(format(balanceBnb, '.2f')))

                self.drpTradingEnabledBnb.setCurrentIndex(qcPar.tradeEnabled)
                self.txtSpendPercentageBnb.setText(str(qcPar.dailySpendPerc))
                self.txtRangeMinBnb1.setText(str(qcPar.minVolume1))
                self.txtRangeMinBnb2.setText(str(qcPar.minVolume2))
                self.txtRangeMinBnb3.setText(str(qcPar.minVolume3))
                self.txtRangeMinBnb4.setText(str(qcPar.minVolume4))
                self.txtRangeMinBnb5.setText(str(qcPar.minVolume5))
                self.txtRangeMinBnb6.setText(str(qcPar.minVolume6))
                self.txtRangeMaxBnb1.setText(str(qcPar.maxVolume1))
                self.txtRangeMaxBnb2.setText(str(qcPar.maxVolume2))
                self.txtRangeMaxBnb3.setText(str(qcPar.maxVolume3))
                self.txtRangeMaxBnb4.setText(str(qcPar.maxVolume4))
                self.txtRangeMaxBnb5.setText(str(qcPar.maxVolume5))
                self.txtRangeMaxBnb6.setText(str(qcPar.maxVolume6))
                self.txtRangePercBnb1.setText(str(qcPar.perc1))
                self.txtRangePercBnb2.setText(str(qcPar.perc2))
                self.txtRangePercBnb3.setText(str(qcPar.perc3))
                self.txtRangePercBnb4.setText(str(qcPar.perc4))
                self.txtRangePercBnb5.setText(str(qcPar.perc5))
                self.txtRangePercBnb6.setText(str(qcPar.perc6))
                self.txtRebuyTriggerAmountBnb.setText(str(self.roundFloat(qcPar.rebuyTriggerAmount, "BNB")))
                self.txtRebuyAmountBnb.setText(str(self.roundFloat(qcPar.rebuyAmount, "BNB")))
                self.onRangePercBnbChanged()

        except:
            self.printLog("Exception: makeQcBuys", traceback.format_exc())

    # Trade Parameters

    def onTradeParamsTimeframeIndexChanged(self, index):
        try:
            self.getTradeParameters()
        except:
            self.printLog("Exception: onTradeParamsTimeframeIndexChanged", traceback.format_exc())

    def onSaveTradeParametersButtonClicked(self):
        try:
            print("onSaveTradeParametersButtonClicked")
            if self.isOptimizationMode():
                self.saveTradeParametersForOpt()
                return

            dnStrategyParameters = DNStrategyParameters()
            sp = dnStrategyParameters.getStrategyParameters(self.drpBotTimeframe.currentText())

            update = False
            if sp is None:
                sp = StrategyParameters()
            else:
                update = True

            sp.Timeframe = self.drpBotTimeframe.currentText()

            sp.R_TradingEnabled = self.drpR_TradingEnabled.currentText() == 'true'
            sp.R_SL1Percentage = float(self.txtR_SL1Percentage.text())
            sp.R_SL2Percentage = float(self.txtR_SL2Percentage.text())
            sp.R_SLTimerInMinutes = float(self.txtR_SLTimerInMinutes.text())
            sp.R_TSLActivationPercentage = float(self.txtR_TSLActivationPercentage.text())
            sp.R_TSLTrailPercentage = float(self.txtR_TSLTrailPercentage.text())

            sp.F_TradingEnabled = self.drpF_TradingEnabled.currentText() == 'true'
            sp.F_SL1Percentage = float(self.txtF_SL1Percentage.text())
            sp.F_SL2Percentage = float(self.txtF_SL2Percentage.text())
            sp.F_SLTimerInMinutes = float(self.txtF_SLTimerInMinutes.text())
            sp.F_TSLActivationPercentage = float(self.txtF_TSLActivationPercentage.text())
            sp.F_TSLTrailPercentage = float(self.txtF_TSLTrailPercentage.text())

            sp.S_TradingEnabled = self.drpS_TradingEnabled.currentText() == 'true'
            sp.S_SL1Percentage = float(self.txtS_SL1Percentage.text())
            sp.S_SL2Percentage = float(self.txtS_SL2Percentage.text())
            sp.S_SLTimerInMinutes = float(self.txtS_SLTimerInMinutes.text())
            sp.S_TSLActivationPercentage = float(self.txtS_TSLActivationPercentage.text())
            sp.S_TSLTrailPercentage = float(self.txtS_TSLTrailPercentage.text())

            sp.TargetPercentage = float(self.txtTargetPercentage.text())
            sp.RebuyTimeInSeconds = int(self.txtRebuyTimeInSeconds.text())
            sp.RebuyPercentage = float(self.txtRebuyPercentage.text())
            sp.RebuyMaxLimit = int(self.txtRebuyMaxLimit.text())
            sp.PullbackEntryPercentage = float(self.txtPullbackEntryPercentage.text())
            sp.PullbackEntryWaitTimeInSeconds = int(self.txtPullbackEntryWaitTimeInSeconds.text())

            if update:
                dnStrategyParameters.updateStrategyParameters(sp)
            else:
                dnStrategyParameters.insertStrategyParameters(sp)

            self.statusBar.showMessage("Parameters are saved successfully!", 2000)

        except:
            self.printLog("Exception: onSaveTradeParametersButtonClicked", traceback.format_exc())

    def saveTradeParametersForOpt(self):
        try:
            print("saveTradeParametersForOpt")

            if self.dialog is None:
                timeframe = self.drpTimeframeOpt.currentText()
            else:
                timeframe = self.dialog.drpTimeframeOpt.currentText()

            dnStrategyParameters = DNStrategyParameters()
            spMin = dnStrategyParameters.getStrategyParameters(timeframe, "min", 0)
            spMax = dnStrategyParameters.getStrategyParameters(timeframe, "max", 0)
            spStep = dnStrategyParameters.getStrategyParameters(timeframe, "step", 0)

            updateMin = False
            if spMin is None:
                spMin = StrategyParameters()
                spMin.Name = "min"
                spMin.OptimizationId = 0
            else:
                updateMin = True

            updateMax = False
            if spMax is None:
                spMax = StrategyParameters()
                spMax.Name = "max"
                spMax.OptimizationId = 0
            else:
                updateMax = True

            updateStep = False
            if spStep is None:
                spStep = StrategyParameters()
                spStep.Name = "step"
                spStep.OptimizationId = 0
            else:
                updateStep = True

            spMin.Timeframe = timeframe
            spMax.Timeframe = timeframe
            spStep.Timeframe = timeframe

            if self.drpR_TradingEnabled.currentText() == "all":
                spMin.R_TradingEnabled = False
                spMax.R_TradingEnabled = True
                spStep.R_TradingEnabled = True
            else:
                spMin.R_TradingEnabled = self.drpR_TradingEnabled.currentText() == 'true'
                spMax.R_TradingEnabled = self.drpR_TradingEnabled.currentText() == 'true'
                spStep.R_TradingEnabled = False

            if self.drpF_TradingEnabled.currentText() == "all":
                spMin.F_TradingEnabled = False
                spMax.F_TradingEnabled = True
                spStep.F_TradingEnabled = True
            else:
                spMin.F_TradingEnabled = self.drpF_TradingEnabled.currentText() == 'true'
                spMax.F_TradingEnabled = self.drpF_TradingEnabled.currentText() == 'true'
                spStep.F_TradingEnabled = False

            if self.drpS_TradingEnabled.currentText() == "all":
                spMin.S_TradingEnabled = False
                spMax.S_TradingEnabled = True
                spStep.S_TradingEnabled = True
            else:
                spMin.S_TradingEnabled = self.drpS_TradingEnabled.currentText() == 'true'
                spMax.S_TradingEnabled = self.drpS_TradingEnabled.currentText() == 'true'
                spStep.S_TradingEnabled = False

            value = self.txtR_SL1Percentage.text()
            spMin.R_SL1Percentage = self.getSpMin(value)
            spMax.R_SL1Percentage = self.getSpMax(value)
            spStep.R_SL1Percentage = self.getSpStep(value)

            value = self.txtR_SL2Percentage.text()
            spMin.R_SL2Percentage = self.getSpMin(value)
            spMax.R_SL2Percentage = self.getSpMax(value)
            spStep.R_SL2Percentage = self.getSpStep(value)

            value = self.txtR_SLTimerInMinutes.text()
            spMin.R_SLTimerInMinutes = self.getSpMin(value)
            spMax.R_SLTimerInMinutes = self.getSpMax(value)
            spStep.R_SLTimerInMinutes = self.getSpStep(value)

            value = self.txtR_TSLActivationPercentage.text()
            spMin.R_TSLActivationPercentage = self.getSpMin(value)
            spMax.R_TSLActivationPercentage = self.getSpMax(value)
            spStep.R_TSLActivationPercentage = self.getSpStep(value)

            value = self.txtR_TSLTrailPercentage.text()
            spMin.R_TSLTrailPercentage = self.getSpMin(value)
            spMax.R_TSLTrailPercentage = self.getSpMax(value)
            spStep.R_TSLTrailPercentage = self.getSpStep(value)

            value = self.txtF_SL1Percentage.text()
            spMin.F_SL1Percentage = self.getSpMin(value)
            spMax.F_SL1Percentage = self.getSpMax(value)
            spStep.F_SL1Percentage = self.getSpStep(value)

            value = self.txtF_SL2Percentage.text()
            spMin.F_SL2Percentage = self.getSpMin(value)
            spMax.F_SL2Percentage = self.getSpMax(value)
            spStep.F_SL2Percentage = self.getSpStep(value)

            value = self.txtF_SLTimerInMinutes.text()
            spMin.F_SLTimerInMinutes = self.getSpMin(value)
            spMax.F_SLTimerInMinutes = self.getSpMax(value)
            spStep.F_SLTimerInMinutes = self.getSpStep(value)

            value = self.txtF_TSLActivationPercentage.text()
            spMin.F_TSLActivationPercentage = self.getSpMin(value)
            spMax.F_TSLActivationPercentage = self.getSpMax(value)
            spStep.F_TSLActivationPercentage = self.getSpStep(value)

            value = self.txtF_TSLTrailPercentage.text()
            spMin.F_TSLTrailPercentage = self.getSpMin(value)
            spMax.F_TSLTrailPercentage = self.getSpMax(value)
            spStep.F_TSLTrailPercentage = self.getSpStep(value)

            value = self.txtS_SL1Percentage.text()
            spMin.S_SL1Percentage = self.getSpMin(value)
            spMax.S_SL1Percentage = self.getSpMax(value)
            spStep.S_SL1Percentage = self.getSpStep(value)

            value = self.txtS_SL2Percentage.text()
            spMin.S_SL2Percentage = self.getSpMin(value)
            spMax.S_SL2Percentage = self.getSpMax(value)
            spStep.S_SL2Percentage = self.getSpStep(value)

            value = self.txtS_SLTimerInMinutes.text()
            spMin.S_SLTimerInMinutes = self.getSpMin(value)
            spMax.S_SLTimerInMinutes = self.getSpMax(value)
            spStep.S_SLTimerInMinutes = self.getSpStep(value)

            value = self.txtS_TSLActivationPercentage.text()
            spMin.S_TSLActivationPercentage = self.getSpMin(value)
            spMax.S_TSLActivationPercentage = self.getSpMax(value)
            spStep.S_TSLActivationPercentage = self.getSpStep(value)

            value = self.txtS_TSLTrailPercentage.text()
            spMin.S_TSLTrailPercentage = self.getSpMin(value)
            spMax.S_TSLTrailPercentage = self.getSpMax(value)
            spStep.S_TSLTrailPercentage = self.getSpStep(value)

            value = self.txtTargetPercentage.text()
            spMin.TargetPercentage = self.getSpMin(value)
            spMax.TargetPercentage = self.getSpMax(value)
            spStep.TargetPercentage = self.getSpStep(value)

            value = self.txtRebuyTimeInSeconds.text()
            spMin.RebuyTimeInSeconds = self.getSpMin(value)
            spMax.RebuyTimeInSeconds = self.getSpMax(value)
            spStep.RebuyTimeInSeconds = self.getSpStep(value)

            value = self.txtRebuyPercentage.text()
            spMin.RebuyPercentage = self.getSpMin(value)
            spMax.RebuyPercentage = self.getSpMax(value)
            spStep.RebuyPercentage = self.getSpStep(value)

            value = self.txtRebuyMaxLimit.text()
            spMin.RebuyMaxLimit = self.getSpMin(value)
            spMax.RebuyMaxLimit = self.getSpMax(value)
            spStep.RebuyMaxLimit = self.getSpStep(value)

            value = self.txtPullbackEntryPercentage.text()
            spMin.PullbackEntryPercentage = self.getSpMin(value)
            spMax.PullbackEntryPercentage = self.getSpMax(value)
            spStep.PullbackEntryPercentage = self.getSpStep(value)

            value = self.txtPullbackEntryWaitTimeInSeconds.text()
            spMin.PullbackEntryWaitTimeInSeconds = self.getSpMin(value)
            spMax.PullbackEntryWaitTimeInSeconds = self.getSpMax(value)
            spStep.PullbackEntryWaitTimeInSeconds = self.getSpStep(value)

            if updateMin:
                dnStrategyParameters.updateStrategyParameters(spMin)
            else:
                dnStrategyParameters.insertStrategyParameters(spMin)

            if updateMax:
                dnStrategyParameters.updateStrategyParameters(spMax)
            else:
                dnStrategyParameters.insertStrategyParameters(spMax)

            if updateStep:
                dnStrategyParameters.updateStrategyParameters(spStep)
            else:
                dnStrategyParameters.insertStrategyParameters(spStep)

            self.statusBar.showMessage("Opt. Parameters are saved successfully!", 4000)


        except:
            self.printLog("Exception: saveTradeParametersForOpt", traceback.format_exc())

    def getTradeParameters(self):
        try:
            if self.isOptimizationMode():
                self.getTradeParametersForOpt()
                return

            dnStrategyParameters = DNStrategyParameters()
            sp = dnStrategyParameters.getStrategyParameters(self.drpBotTimeframe.currentText())
            if sp is None:
                sp = StrategyParameters()
                sp.Timeframe = self.drpBotTimeframe.currentText()
                dnStrategyParameters.insertStrategyParameters(sp)

            self.drpR_TradingEnabled.setCurrentIndex(sp.R_TradingEnabled)
            self.txtR_SL1Percentage.setText(str(sp.R_SL1Percentage))
            self.txtR_SL2Percentage.setText(str(sp.R_SL2Percentage))
            self.txtR_SLTimerInMinutes.setText(str(sp.R_SLTimerInMinutes))
            self.txtR_TSLActivationPercentage.setText(str(sp.R_TSLActivationPercentage))
            self.txtR_TSLTrailPercentage.setText(str(sp.R_TSLTrailPercentage))

            self.drpF_TradingEnabled.setCurrentIndex(sp.F_TradingEnabled)
            self.txtF_SL1Percentage.setText(str(sp.F_SL1Percentage))
            self.txtF_SL2Percentage.setText(str(sp.F_SL2Percentage))
            self.txtF_SLTimerInMinutes.setText(str(sp.F_SLTimerInMinutes))
            self.txtF_TSLActivationPercentage.setText(str(sp.F_TSLActivationPercentage))
            self.txtF_TSLTrailPercentage.setText(str(sp.F_TSLTrailPercentage))

            self.drpS_TradingEnabled.setCurrentIndex(sp.S_TradingEnabled)
            self.txtS_SL1Percentage.setText(str(sp.S_SL1Percentage))
            self.txtS_SL2Percentage.setText(str(sp.S_SL2Percentage))
            self.txtS_SLTimerInMinutes.setText(str(sp.S_SLTimerInMinutes))
            self.txtS_TSLActivationPercentage.setText(str(sp.S_TSLActivationPercentage))
            self.txtS_TSLTrailPercentage.setText(str(sp.S_TSLTrailPercentage))

            self.txtTargetPercentage.setText(str(sp.TargetPercentage))
            self.txtRebuyTimeInSeconds.setText(str(sp.RebuyTimeInSeconds))
            self.txtRebuyPercentage.setText(str(sp.RebuyPercentage))
            self.txtRebuyMaxLimit.setText(str(sp.RebuyMaxLimit))
            self.txtPullbackEntryPercentage.setText(str(sp.PullbackEntryPercentage))
            self.txtPullbackEntryWaitTimeInSeconds.setText(str(sp.PullbackEntryWaitTimeInSeconds))

        except:
            self.printLog("Exception: getTradeParameters", traceback.format_exc())

    def getTradeParametersForOpt(self):
        try:
            if self.dialog is None:
                timeframe = self.drpTimeframeOpt.currentText()
            else:
                timeframe = self.dialog.drpTimeframeOpt.currentText()

            dnStrategyParameters = DNStrategyParameters()

            spMin = dnStrategyParameters.getStrategyParameters(timeframe, "min", 0)
            spMax = dnStrategyParameters.getStrategyParameters(timeframe, "max", 0)
            spStep = dnStrategyParameters.getStrategyParameters(timeframe, "step", 0)

            if spMin is None:
                spMin = dnStrategyParameters.getStrategyParameters("15m", "min", 0)
                spMin.Timeframe = timeframe
                spMin.Name = "min"
                spMin.OptimizationId = 0
                dnStrategyParameters.insertStrategyParameters(spMin)

            if spMax is None:
                spMax = dnStrategyParameters.getStrategyParameters("15m", "max", 0)
                spMax.Timeframe = timeframe
                spMax.Name = "max"
                spMax.OptimizationId = 0
                dnStrategyParameters.insertStrategyParameters(spMax)

            if spStep is None:
                spStep = dnStrategyParameters.getStrategyParameters("15m", "step", 0)
                spStep.Timeframe = timeframe
                spStep.Name = "step"
                spStep.OptimizationId = 0
                dnStrategyParameters.insertStrategyParameters(spStep)

            """
            if spMin is None:
                spMin = StrategyParameters()
                spMin.Timeframe = timeframe
                spMin.Name = "min"
                spMin.OptimizationId = 0
                dnStrategyParameters.insertStrategyParameters(spMin)

            if spMax is None:
                spMax = StrategyParameters()
                spMax.Timeframe = timeframe
                spMax.Name = "max"
                spMax.OptimizationId = 0
                dnStrategyParameters.insertStrategyParameters(spMax)

            if spStep is None:
                spStep = StrategyParameters()
                spStep.Timeframe = timeframe
                spStep.Name = "step"
                spStep.OptimizationId = 0
                dnStrategyParameters.insertStrategyParameters(spStep)
            """

            # true/false controls

            if not spMin.R_TradingEnabled and spMax.R_TradingEnabled:
                self.drpR_TradingEnabled.setCurrentText("all")
            else:
                self.drpR_TradingEnabled.setCurrentIndex(spMin.R_TradingEnabled)

            if not spMin.F_TradingEnabled and spMax.F_TradingEnabled:
                self.drpF_TradingEnabled.setCurrentText("all")
            else:
                self.drpF_TradingEnabled.setCurrentIndex(spMin.F_TradingEnabled)

            if not spMin.S_TradingEnabled and spMax.S_TradingEnabled:
                self.drpS_TradingEnabled.setCurrentText("all")
            else:
                self.drpS_TradingEnabled.setCurrentIndex(spMin.S_TradingEnabled)

            # textboxes

            self.txtR_SL1Percentage.setText(
                str(spMin.R_SL1Percentage) + "," + str(spMax.R_SL1Percentage) + "," + str(spStep.R_SL1Percentage))
            self.removeZeros(self.txtR_SL1Percentage)

            self.txtR_SL2Percentage.setText(
                str(spMin.R_SL2Percentage) + "," + str(spMax.R_SL2Percentage) + "," + str(spStep.R_SL2Percentage))
            self.removeZeros(self.txtR_SL2Percentage)

            self.txtR_SLTimerInMinutes.setText(
                str(spMin.R_SLTimerInMinutes) + "," + str(spMax.R_SLTimerInMinutes) + "," + str(
                    spStep.R_SLTimerInMinutes))
            self.removeZeros(self.txtR_SLTimerInMinutes)

            self.txtR_TSLActivationPercentage.setText(
                str(spMin.R_TSLActivationPercentage) + "," + str(spMax.R_TSLActivationPercentage) + "," + str(
                    spStep.R_TSLActivationPercentage))
            self.removeZeros(self.txtR_TSLActivationPercentage)

            self.txtR_TSLTrailPercentage.setText(
                str(spMin.R_TSLTrailPercentage) + "," + str(spMax.R_TSLTrailPercentage) + "," + str(
                    spStep.R_TSLTrailPercentage))
            self.removeZeros(self.txtR_TSLTrailPercentage)

            self.txtF_SL1Percentage.setText(
                str(spMin.F_SL1Percentage) + "," + str(spMax.F_SL1Percentage) + "," + str(spStep.F_SL1Percentage))
            self.removeZeros(self.txtF_SL1Percentage)

            self.txtF_SL2Percentage.setText(
                str(spMin.F_SL2Percentage) + "," + str(spMax.F_SL2Percentage) + "," + str(spStep.F_SL2Percentage))
            self.removeZeros(self.txtF_SL2Percentage)

            self.txtF_SLTimerInMinutes.setText(
                str(spMin.F_SLTimerInMinutes) + "," + str(spMax.F_SLTimerInMinutes) + "," + str(
                    spStep.F_SLTimerInMinutes))
            self.removeZeros(self.txtF_SLTimerInMinutes)

            self.txtF_TSLActivationPercentage.setText(
                str(spMin.F_TSLActivationPercentage) + "," + str(spMax.F_TSLActivationPercentage) + "," + str(
                    spStep.F_TSLActivationPercentage))
            self.removeZeros(self.txtF_TSLActivationPercentage)

            self.txtF_TSLTrailPercentage.setText(
                str(spMin.F_TSLTrailPercentage) + "," + str(spMax.F_TSLTrailPercentage) + "," + str(
                    spStep.F_TSLTrailPercentage))
            self.removeZeros(self.txtF_TSLTrailPercentage)

            self.txtS_SL1Percentage.setText(
                str(spMin.S_SL1Percentage) + "," + str(spMax.S_SL1Percentage) + "," + str(
                    spStep.S_SL1Percentage))
            self.removeZeros(self.txtS_SL1Percentage)

            self.txtS_SL2Percentage.setText(
                str(spMin.S_SL2Percentage) + "," + str(spMax.S_SL2Percentage) + "," + str(
                    spStep.S_SL2Percentage))
            self.removeZeros(self.txtS_SL2Percentage)

            self.txtS_SLTimerInMinutes.setText(
                str(spMin.S_SLTimerInMinutes) + "," + str(spMax.S_SLTimerInMinutes) + "," + str(
                    spStep.S_SLTimerInMinutes))
            self.removeZeros(self.txtS_SLTimerInMinutes)

            self.txtS_TSLActivationPercentage.setText(
                str(spMin.S_TSLActivationPercentage) + "," + str(spMax.S_TSLActivationPercentage) + "," + str(
                    spStep.S_TSLActivationPercentage))
            self.removeZeros(self.txtS_TSLActivationPercentage)

            self.txtS_TSLTrailPercentage.setText(
                str(spMin.S_TSLTrailPercentage) + "," + str(spMax.S_TSLTrailPercentage) + "," + str(
                    spStep.S_TSLTrailPercentage))
            self.removeZeros(self.txtS_TSLTrailPercentage)

            self.txtTargetPercentage.setText(
                str(spMin.TargetPercentage) + "," + str(spMax.TargetPercentage) + "," + str(
                    spStep.TargetPercentage))
            self.removeZeros(self.txtTargetPercentage)

            self.txtRebuyTimeInSeconds.setText(
                str(spMin.RebuyTimeInSeconds) + "," + str(spMax.RebuyTimeInSeconds) + "," + str(
                    spStep.RebuyTimeInSeconds))
            self.removeZeros(self.txtRebuyTimeInSeconds)

            self.txtRebuyPercentage.setText(
                str(spMin.RebuyPercentage) + "," + str(spMax.RebuyPercentage) + "," + str(
                    spStep.RebuyPercentage))
            self.removeZeros(self.txtRebuyPercentage)

            self.txtRebuyMaxLimit.setText(
                str(spMin.RebuyMaxLimit) + "," + str(spMax.RebuyMaxLimit) + "," + str(
                    spStep.RebuyMaxLimit))
            self.removeZeros(self.txtRebuyMaxLimit)

            self.txtPullbackEntryPercentage.setText(
                str(spMin.PullbackEntryPercentage) + "," + str(spMax.PullbackEntryPercentage) + "," + str(
                    spStep.PullbackEntryPercentage))
            self.removeZeros(self.txtPullbackEntryPercentage)

            self.txtPullbackEntryWaitTimeInSeconds.setText(
                str(spMin.PullbackEntryWaitTimeInSeconds) + "," + str(spMax.PullbackEntryWaitTimeInSeconds) + "," + str(
                    spStep.PullbackEntryWaitTimeInSeconds))
            self.removeZeros(self.txtPullbackEntryWaitTimeInSeconds)


        except:
            self.printLog("Exception: getTradeParametersForOpt", traceback.format_exc())

    # Indicator Parameters

    def onIndicatorTimeframeIndexChanged(self, index):
        try:
            self.getIndicatorParameters()
        except:
            self.printLog("Exception: onIndicatorTimeframeIndexChanged", traceback.format_exc())

    def onSaveIndicatorParametersButtonClicked(self):
        try:
            print("onSaveIndicatorParametersButtonClicked")

            if self.isOptimizationMode():
                self.saveIndicatorParametersForOpt()
                return

            dnStrategyParameters = DNStrategyParameters()
            sp = dnStrategyParameters.getStrategyParameters(self.drpBotTimeframe.currentText())

            update = False
            if sp is None:
                sp = StrategyParameters()
            else:
                update = True

            sp.Timeframe = self.drpBotTimeframe.currentText()
            sp.ROC_IndicatorEnabled = self.drpRocEnabled.currentText() == 'true'
            sp.ROC_AppliedPrice_R = self.drpRocAppliedPriceR.currentText()
            sp.ROC_AppliedPrice_F = self.drpRocAppliedPriceF.currentText()
            sp.ROC_Period_R = int(self.txtRocPeriodR.text())
            sp.ROC_Smoothing_R = int(self.txtRocSmoothingR.text())
            sp.ROC_Period_F = int(self.txtRocPeriodF.text())
            sp.ROC_R_BuyIncreasePercentage = float(self.txtRocRBuyIncreasePercentage.text())
            sp.ROC_F_BuyDecreasePercentage = float(self.txtRocFBuyDecreasePercentage.text())
            sp.MPT_IndicatorEnabled = self.drpMptEnabled.currentText() == 'true'
            sp.MPT_AppliedPrice = self.drpMptAppliedPrice.currentText()
            sp.MPT_ShortMAPeriod = int(self.txtMptShortEmaPeriod.text())
            sp.MPT_LongMAPeriod = int(self.txtMptLongEmaPeriod.text())

            sp.TREND_IndicatorEnabled = self.drpTrendEnabled.currentText() == 'true'
            sp.TREND_AppliedPrice = self.drpTrendAppliedPrice.currentText()
            sp.TREND_LongEmaPeriod = int(self.txtTrendLongEmaPeriod.text())
            sp.TREND_ShortEmaPeriod = int(self.txtTrendShortEmaPeriod.text())

            sp.EMAX_IndicatorEnabled = self.drpEmaxEnabled.currentText() == 'true'
            sp.EMAX_AppliedPrice = self.drpEmaxAppliedPrice.currentText()
            sp.EMAX_LongEmaPeriod = int(self.txtEmaxLongEmaPeriod.text())
            sp.EMAX_ShortEmaPeriod = int(self.txtEmaxShortEmaPeriod.text())

            sp.VSTOP_IndicatorEnabled = self.drpVstopEnabled.currentText() == 'true'
            sp.VSTOP_AppliedPrice = self.drpVstopAppliedPrice.currentText()
            sp.VSTOP_Period = int(self.txtVstopPeriod.text())
            sp.VSTOP_Factor = float(self.txtVstopFactor.text())

            sp.NV_IndicatorEnabled = self.drpNvEnabled.currentText() == 'true'
            sp.NV_IncreasePercentage = float(self.txtNvIncreasePercentage.text())
            sp.NV_MinNetVolume = float(self.txtNvMinNetVolume.text())
            sp.SELL_IndicatorEnabled = self.drpSELL_IndicatorEnabled.currentText() == 'true'
            sp.SELL_DecreasePercentage = float(self.txtSELL_DecreasePercentage.text())
            sp.SELL_Period = int(self.txtSELL_Period.text())
            sp.ROC_Smoothing_S = int(self.txtRocSmoothingS.text())
            sp.SELL_RSI_AppliedPrice = self.drpSELL_RSI_Src.currentText()
            sp.SELL_RSI_Period = int(self.txtSELL_RSI_Period.text())
            sp.SELL_RSI_UpperLevel = float(self.txtSELL_RSI_UpperLevel.text())
            sp.SELL_RSI_LowerLevel = float(self.txtSELL_RSI_LowerLevel.text())
            sp.SELL_Stoch_AppliedPrice = self.drpSELL_Stoch_Src.currentText()
            sp.SELL_Stoch_KPeriod = int(self.txtSELL_Stoch_KPeriod.text())
            sp.SELL_Stoch_DPeriod = int(self.txtSELL_Stoch_DPeriod.text())
            sp.SELL_Stoch_Slowing = int(self.txtSELL_Stoch_Slowing.text())
            sp.SELL_Stoch_UpperLevel = float(self.txtSELL_Stoch_UpperLevel.text())
            sp.SELL_Stoch_LowerLevel = float(self.txtSELL_Stoch_LowerLevel.text())

            if update:
                dnStrategyParameters.updateStrategyParameters(sp)
            else:
                dnStrategyParameters.insertStrategyParameters(sp)

            self.statusBar.showMessage("Parameters are saved successfully!", 2000)

        except:
            self.printLog("Exception: onSaveIndicatorParametersButtonClicked", traceback.format_exc())

    def saveIndicatorParametersForOpt(self):
        try:
            print("saveIndicatorParametersForOpt")
            if self.dialog is None:
                timeframe = self.drpTimeframeOpt.currentText()
            else:
                timeframe = self.dialog.drpTimeframeOpt.currentText()

            dnStrategyParameters = DNStrategyParameters()
            spMin = dnStrategyParameters.getStrategyParameters(timeframe, "min", 0)
            spMax = dnStrategyParameters.getStrategyParameters(timeframe, "max", 0)
            spStep = dnStrategyParameters.getStrategyParameters(timeframe, "step", 0)

            updateMin = False
            if spMin is None:
                spMin = StrategyParameters()
                spMin.Name = "min"
                spMin.OptimizationId = 0
            else:
                updateMin = True

            updateMax = False
            if spMax is None:
                spMax = StrategyParameters()
                spMax.Name = "max"
                spMax.OptimizationId = 0
            else:
                updateMax = True

            updateStep = False
            if spStep is None:
                spStep = StrategyParameters()
                spStep.Name = "step"
                spStep.OptimizationId = 0
            else:
                updateStep = True

            spMin.Timeframe = timeframe
            spMax.Timeframe = timeframe
            spStep.Timeframe = timeframe

            if self.drpRocEnabled.currentText() == "all":
                spMin.ROC_IndicatorEnabled = False
                spMax.ROC_IndicatorEnabled = True
                spStep.ROC_IndicatorEnabled = True
            else:
                spMin.ROC_IndicatorEnabled = self.drpRocEnabled.currentText() == 'true'
                spMax.ROC_IndicatorEnabled = self.drpRocEnabled.currentText() == 'true'
                spStep.ROC_IndicatorEnabled = False

            if self.drpMptEnabled.currentText() == "all":
                spMin.MPT_IndicatorEnabled = False
                spMax.MPT_IndicatorEnabled = True
                spStep.MPT_IndicatorEnabled = True
            else:
                spMin.MPT_IndicatorEnabled = self.drpMptEnabled.currentText() == 'true'
                spMax.MPT_IndicatorEnabled = self.drpMptEnabled.currentText() == 'true'
                spStep.MPT_IndicatorEnabled = False

            if self.drpTrendEnabled.currentText() == "all":
                spMin.TREND_IndicatorEnabled = False
                spMax.TREND_IndicatorEnabled = True
                spStep.TREND_IndicatorEnabled = True
            else:
                spMin.TREND_IndicatorEnabled = self.drpTrendEnabled.currentText() == 'true'
                spMax.TREND_IndicatorEnabled = self.drpTrendEnabled.currentText() == 'true'
                spStep.TREND_IndicatorEnabled = False

            if self.drpEmaxEnabled.currentText() == "all":
                spMin.EMAX_IndicatorEnabled = False
                spMax.EMAX_IndicatorEnabled = True
                spStep.EMAX_IndicatorEnabled = True
            else:
                spMin.EMAX_IndicatorEnabled = self.drpEmaxEnabled.currentText() == 'true'
                spMax.EMAX_IndicatorEnabled = self.drpEmaxEnabled.currentText() == 'true'
                spStep.EMAX_IndicatorEnabled = False

            if self.drpVstopEnabled.currentText() == "all":
                spMin.VSTOP_IndicatorEnabled = False
                spMax.VSTOP_IndicatorEnabled = True
                spStep.VSTOP_IndicatorEnabled = True
            else:
                spMin.VSTOP_IndicatorEnabled = self.drpVstopEnabled.currentText() == 'true'
                spMax.VSTOP_IndicatorEnabled = self.drpVstopEnabled.currentText() == 'true'
                spStep.VSTOP_IndicatorEnabled = False

            if self.drpNvEnabled.currentText() == "all":
                spMin.NV_IndicatorEnabled = False
                spMax.NV_IndicatorEnabled = True
                spStep.NV_IndicatorEnabled = True
            else:
                spMin.NV_IndicatorEnabled = self.drpNvEnabled.currentText() == 'true'
                spMax.NV_IndicatorEnabled = self.drpNvEnabled.currentText() == 'true'
                spStep.NV_IndicatorEnabled = False

            if self.drpSELL_IndicatorEnabled.currentText() == "all":
                spMin.SELL_IndicatorEnabled = False
                spMax.SELL_IndicatorEnabled = True
                spStep.SELL_IndicatorEnabled = True
            else:
                spMin.SELL_IndicatorEnabled = self.drpSELL_IndicatorEnabled.currentText() == 'true'
                spMax.SELL_IndicatorEnabled = self.drpSELL_IndicatorEnabled.currentText() == 'true'
                spStep.SELL_IndicatorEnabled = False

            if self.drpSELL_RSI_Src.currentText() == "all":
                spMin.SELL_RSI_AppliedPrice = False
                spMax.SELL_RSI_AppliedPrice = True
                spStep.SELL_RSI_AppliedPrice = True
            else:
                spMin.SELL_RSI_AppliedPrice = self.drpSELL_RSI_Src.currentText() == 'true'
                spMax.SELL_RSI_AppliedPrice = self.drpSELL_RSI_Src.currentText() == 'true'
                spStep.SELL_RSI_AppliedPrice = False

            if self.drpRocAppliedPriceR.currentText() == "all":
                spMin.ROC_AppliedPrice_R = "0"
                spMax.ROC_AppliedPrice_R = "3"
                spStep.ROC_AppliedPrice_R = "1"
            else:
                spMin.ROC_AppliedPrice_R = self.drpRocAppliedPriceR.currentIndex()
                spMax.ROC_AppliedPrice_R = self.drpRocAppliedPriceR.currentIndex()
                spStep.ROC_AppliedPrice_R = "0"

            if self.drpRocAppliedPriceF.currentText() == "all":
                spMin.ROC_AppliedPrice_F = "0"
                spMax.ROC_AppliedPrice_F = "3"
                spStep.ROC_AppliedPrice_F = "1"
            else:
                spMin.ROC_AppliedPrice_F = self.drpRocAppliedPriceF.currentIndex()
                spMax.ROC_AppliedPrice_F = self.drpRocAppliedPriceF.currentIndex()
                spStep.ROC_AppliedPrice_F = "0"

            if self.drpMptAppliedPrice.currentText() == "all":
                spMin.MPT_AppliedPrice = "0"
                spMax.MPT_AppliedPrice = "3"
                spStep.MPT_AppliedPrice = "1"
            else:
                spMin.MPT_AppliedPrice = self.drpMptAppliedPrice.currentIndex()
                spMax.MPT_AppliedPrice = self.drpMptAppliedPrice.currentIndex()
                spStep.MPT_AppliedPrice = "0"

            if self.drpTrendAppliedPrice.currentText() == "all":
                spMin.TREND_AppliedPrice = "0"
                spMax.TREND_AppliedPrice = "3"
                spStep.TREND_AppliedPrice = "1"
            else:
                spMin.TREND_AppliedPrice = self.drpTrendAppliedPrice.currentIndex()
                spMax.TREND_AppliedPrice = self.drpTrendAppliedPrice.currentIndex()
                spStep.TREND_AppliedPrice = "0"

            if self.drpEmaxAppliedPrice.currentText() == "all":
                spMin.EMAX_AppliedPrice = "0"
                spMax.EMAX_AppliedPrice = "3"
                spStep.EMAX_AppliedPrice = "1"
            else:
                spMin.EMAX_AppliedPrice = self.drpEmaxAppliedPrice.currentIndex()
                spMax.EMAX_AppliedPrice = self.drpEmaxAppliedPrice.currentIndex()
                spStep.EMAX_AppliedPrice = "0"

            if self.drpVstopAppliedPrice.currentText() == "all":
                spMin.VSTOP_AppliedPrice = "0"
                spMax.VSTOP_AppliedPrice = "3"
                spStep.VSTOP_AppliedPrice = "1"
            else:
                spMin.VSTOP_AppliedPrice = self.drpVstopAppliedPrice.currentIndex()
                spMax.VSTOP_AppliedPrice = self.drpVstopAppliedPrice.currentIndex()
                spStep.VSTOP_AppliedPrice = "0"

            if self.drpSELL_RSI_Src.currentText() == "all":
                spMin.SELL_RSI_AppliedPrice = "0"
                spMax.SELL_RSI_AppliedPrice = "3"
                spStep.SELL_RSI_AppliedPrice = "1"
            else:
                spMin.SELL_RSI_AppliedPrice = self.drpSELL_RSI_Src.currentIndex()
                spMax.SELL_RSI_AppliedPrice = self.drpSELL_RSI_Src.currentIndex()
                spStep.SELL_RSI_AppliedPrice = "0"

            value = self.txtRocPeriodR.text()
            spMin.ROC_Period_R = self.getSpMin(value)
            spMax.ROC_Period_R = self.getSpMax(value)
            spStep.ROC_Period_R = self.getSpStep(value)

            value = self.txtRocSmoothingR.text()
            spMin.ROC_Smoothing_R = self.getSpMin(value)
            spMax.ROC_Smoothing_R = self.getSpMax(value)
            spStep.ROC_Smoothing_R = self.getSpStep(value)

            value = self.txtRocPeriodF.text()
            spMin.ROC_Period_F = self.getSpMin(value)
            spMax.ROC_Period_F = self.getSpMax(value)
            spStep.ROC_Period_F = self.getSpStep(value)

            value = self.txtRocRBuyIncreasePercentage.text()
            spMin.ROC_R_BuyIncreasePercentage = self.getSpMin(value)
            spMax.ROC_R_BuyIncreasePercentage = self.getSpMax(value)
            spStep.ROC_R_BuyIncreasePercentage = self.getSpStep(value)

            value = self.txtRocFBuyDecreasePercentage.text()
            spMin.ROC_F_BuyDecreasePercentage = self.getSpMin(value)
            spMax.ROC_F_BuyDecreasePercentage = self.getSpMax(value)
            spStep.ROC_F_BuyDecreasePercentage = self.getSpStep(value)

            value = self.txtMptShortEmaPeriod.text()
            spMin.MPT_ShortMAPeriod = self.getSpMin(value)
            spMax.MPT_ShortMAPeriod = self.getSpMax(value)
            spStep.MPT_ShortMAPeriod = self.getSpStep(value)

            value = self.txtMptLongEmaPeriod.text()
            spMin.MPT_LongMAPeriod = self.getSpMin(value)
            spMax.MPT_LongMAPeriod = self.getSpMax(value)
            spStep.MPT_LongMAPeriod = self.getSpStep(value)

            value = self.txtTrendLongEmaPeriod.text()
            spMin.TREND_LongEmaPeriod = self.getSpMin(value)
            spMax.TREND_LongEmaPeriod = self.getSpMax(value)
            spStep.TREND_LongEmaPeriod = self.getSpStep(value)

            value = self.txtTrendShortEmaPeriod.text()
            spMin.TREND_ShortEmaPeriod = self.getSpMin(value)
            spMax.TREND_ShortEmaPeriod = self.getSpMax(value)
            spStep.TREND_ShortEmaPeriod = self.getSpStep(value)

            value = self.txtEmaxLongEmaPeriod.text()
            spMin.EMAX_LongEmaPeriod = self.getSpMin(value)
            spMax.EMAX_LongEmaPeriod = self.getSpMax(value)
            spStep.EMAX_LongEmaPeriod = self.getSpStep(value)

            value = self.txtEmaxShortEmaPeriod.text()
            spMin.EMAX_ShortEmaPeriod = self.getSpMin(value)
            spMax.EMAX_ShortEmaPeriod = self.getSpMax(value)
            spStep.EMAX_ShortEmaPeriod = self.getSpStep(value)

            value = self.txtVstopPeriod.text()
            spMin.VSTOP_Period = self.getSpMin(value)
            spMax.VSTOP_Period = self.getSpMax(value)
            spStep.VSTOP_Period = self.getSpStep(value)

            value = self.txtVstopFactor.text()
            spMin.VSTOP_Factor = self.getSpMin(value)
            spMax.VSTOP_Factor = self.getSpMax(value)
            spStep.VSTOP_Factor = self.getSpStep(value)

            value = self.txtNvIncreasePercentage.text()
            spMin.NV_IncreasePercentage = self.getSpMin(value)
            spMax.NV_IncreasePercentage = self.getSpMax(value)
            spStep.NV_IncreasePercentage = self.getSpStep(value)

            value = self.txtNvMinNetVolume.text()
            spMin.NV_MinNetVolume = self.getSpMin(value)
            spMax.NV_MinNetVolume = self.getSpMax(value)
            spStep.NV_MinNetVolume = self.getSpStep(value)

            value = self.txtSELL_DecreasePercentage.text()
            spMin.SELL_DecreasePercentage = self.getSpMin(value)
            spMax.SELL_DecreasePercentage = self.getSpMax(value)
            spStep.SELL_DecreasePercentage = self.getSpStep(value)

            value = self.txtSELL_Period.text()
            spMin.SELL_Period = self.getSpMin(value)
            spMax.SELL_Period = self.getSpMax(value)
            spStep.SELL_Period = self.getSpStep(value)

            value = self.txtRocSmoothingS.text()
            spMin.ROC_Smoothing_S = self.getSpMin(value)
            spMax.ROC_Smoothing_S = self.getSpMax(value)
            spStep.ROC_Smoothing_S = self.getSpStep(value)

            value = self.txtSELL_RSI_Period.text()
            spMin.SELL_RSI_Period = self.getSpMin(value)
            spMax.SELL_RSI_Period = self.getSpMax(value)
            spStep.SELL_RSI_Period = self.getSpStep(value)

            value = self.txtSELL_RSI_UpperLevel.text()
            spMin.SELL_RSI_UpperLevel = self.getSpMin(value)
            spMax.SELL_RSI_UpperLevel = self.getSpMax(value)
            spStep.SELL_RSI_UpperLevel = self.getSpStep(value)

            value = self.txtSELL_RSI_LowerLevel.text()
            spMin.SELL_RSI_LowerLevel = self.getSpMin(value)
            spMax.SELL_RSI_LowerLevel = self.getSpMax(value)
            spStep.SELL_RSI_LowerLevel = self.getSpStep(value)

            value = self.txtSELL_Stoch_KPeriod.text()
            spMin.SELL_Stoch_KPeriod = self.getSpMin(value)
            spMax.SELL_Stoch_KPeriod = self.getSpMax(value)
            spStep.SELL_Stoch_KPeriod = self.getSpStep(value)

            value = self.txtSELL_Stoch_DPeriod.text()
            spMin.SELL_Stoch_DPeriod = self.getSpMin(value)
            spMax.SELL_Stoch_DPeriod = self.getSpMax(value)
            spStep.SELL_Stoch_DPeriod = self.getSpStep(value)

            value = self.txtSELL_Stoch_Slowing.text()
            spMin.SELL_Stoch_Slowing = self.getSpMin(value)
            spMax.SELL_Stoch_Slowing = self.getSpMax(value)
            spStep.SELL_Stoch_Slowing = self.getSpStep(value)

            value = self.txtSELL_Stoch_UpperLevel.text()
            spMin.SELL_Stoch_UpperLevel = self.getSpMin(value)
            spMax.SELL_Stoch_UpperLevel = self.getSpMax(value)
            spStep.SELL_Stoch_UpperLevel = self.getSpStep(value)

            value = self.txtSELL_Stoch_LowerLevel.text()
            spMin.SELL_Stoch_LowerLevel = self.getSpMin(value)
            spMax.SELL_Stoch_LowerLevel = self.getSpMax(value)
            spStep.SELL_Stoch_LowerLevel = self.getSpStep(value)

            if updateMin:
                dnStrategyParameters.updateStrategyParameters(spMin)
            else:
                dnStrategyParameters.insertStrategyParameters(spMin)

            if updateMax:
                dnStrategyParameters.updateStrategyParameters(spMax)
            else:
                dnStrategyParameters.insertStrategyParameters(spMax)

            if updateStep:
                dnStrategyParameters.updateStrategyParameters(spStep)
            else:
                dnStrategyParameters.insertStrategyParameters(spStep)

            # self.insertSpCombinationsForOpt()

            self.statusBar.showMessage("Opt. Parameters are saved successfully!", 4000)



        except:
            self.printLog("Exception: saveIndicatorParametersForOpt", traceback.format_exc())

    def getSpMin(self, value):
        if "," not in value:
            return value

        parts = value.split(",")

        if "." in value:
            return float(parts[0])
        else:
            return int(parts[0])

    def getSpMax(self, value):
        if "," not in value:
            return value

        parts = value.split(",")

        if "." in value:
            return float(parts[1])
        else:
            return int(parts[1])

    def getSpStep(self, value):
        if "," not in value:
            return 0

        parts = value.split(",")
        if parts and len(parts) > 2:
            if "." in value:
                return float(parts[2])
            else:
                return int(parts[2])

        return 0

    def getIndicatorParameters(self):
        try:
            if self.isOptimizationMode():
                self.getIndicatorParametersForOpt()
                return

            dnStrategyParameters = DNStrategyParameters()
            sp = dnStrategyParameters.getStrategyParameters(self.drpBotTimeframe.currentText())
            if sp is None:
                sp = StrategyParameters()
                sp.Timeframe = self.drpBotTimeframe.currentText()
                dnStrategyParameters.insertStrategyParameters(sp)

            self.drpRocEnabled.setCurrentIndex(sp.ROC_IndicatorEnabled)
            self.drpRocAppliedPriceR.setCurrentText(str(sp.ROC_AppliedPrice_R))
            self.drpRocAppliedPriceF.setCurrentText(str(sp.ROC_AppliedPrice_F))
            self.txtRocPeriodR.setText(str(sp.ROC_Period_R))
            self.txtRocSmoothingR.setText(str(sp.ROC_Smoothing_R))
            self.txtRocPeriodF.setText(str(sp.ROC_Period_F))
            self.txtRocRBuyIncreasePercentage.setText(str(sp.ROC_R_BuyIncreasePercentage))
            self.txtRocFBuyDecreasePercentage.setText(str(sp.ROC_F_BuyDecreasePercentage))
            self.drpMptEnabled.setCurrentIndex(sp.MPT_IndicatorEnabled)
            self.drpMptAppliedPrice.setCurrentText(str(sp.MPT_AppliedPrice))
            self.txtMptShortEmaPeriod.setText(str(sp.MPT_ShortMAPeriod))
            self.txtMptLongEmaPeriod.setText(str(sp.MPT_LongMAPeriod))

            self.drpTrendEnabled.setCurrentIndex(sp.TREND_IndicatorEnabled)
            self.drpTrendAppliedPrice.setCurrentText(str(sp.TREND_AppliedPrice))
            self.txtTrendLongEmaPeriod.setText(str(sp.TREND_LongEmaPeriod))
            self.txtTrendShortEmaPeriod.setText(str(sp.TREND_ShortEmaPeriod))

            self.drpEmaxEnabled.setCurrentIndex(sp.EMAX_IndicatorEnabled)
            self.drpEmaxAppliedPrice.setCurrentText(str(sp.EMAX_AppliedPrice))
            self.txtEmaxLongEmaPeriod.setText(str(sp.EMAX_LongEmaPeriod))
            self.txtEmaxShortEmaPeriod.setText(str(sp.EMAX_ShortEmaPeriod))

            self.drpVstopEnabled.setCurrentIndex(sp.VSTOP_IndicatorEnabled)
            self.drpVstopAppliedPrice.setCurrentText(str(sp.VSTOP_AppliedPrice))
            self.txtVstopPeriod.setText(str(sp.VSTOP_Period))
            self.txtVstopFactor.setText(str(sp.VSTOP_Factor))

            self.drpNvEnabled.setCurrentIndex(sp.NV_IndicatorEnabled)
            self.txtNvIncreasePercentage.setText(str(sp.NV_IncreasePercentage))
            self.txtNvMinNetVolume.setText(str(sp.NV_MinNetVolume))
            self.drpSELL_IndicatorEnabled.setCurrentIndex(sp.SELL_IndicatorEnabled)
            self.txtSELL_DecreasePercentage.setText(str(sp.SELL_DecreasePercentage))
            self.txtSELL_Period.setText(str(sp.SELL_Period))
            self.txtRocSmoothingS.setText(str(sp.ROC_Smoothing_S))
            self.drpSELL_RSI_Src.setCurrentText(str(sp.SELL_RSI_AppliedPrice))
            self.txtSELL_RSI_Period.setText(str(sp.SELL_RSI_Period))
            self.txtSELL_RSI_UpperLevel.setText(str(sp.SELL_RSI_UpperLevel))
            self.txtSELL_RSI_LowerLevel.setText(str(sp.SELL_RSI_LowerLevel))
            self.drpSELL_Stoch_Src.setCurrentText(str(sp.SELL_Stoch_AppliedPrice))
            self.txtSELL_Stoch_KPeriod.setText(str(sp.SELL_Stoch_KPeriod))
            self.txtSELL_Stoch_DPeriod.setText(str(sp.SELL_Stoch_DPeriod))
            self.txtSELL_Stoch_Slowing.setText(str(sp.SELL_Stoch_Slowing))
            self.txtSELL_Stoch_UpperLevel.setText(str(sp.SELL_Stoch_UpperLevel))
            self.txtSELL_Stoch_LowerLevel.setText(str(sp.SELL_Stoch_LowerLevel))

        except:
            self.printLog("Exception: getIndicatorParameters", traceback.format_exc())

    def removeZeros(self, control):
        control.setText(control.text().replace(".00", ""))

    def getIndicatorParametersForOpt(self):
        try:
            if self.dialog is None:
                timeframe = self.drpTimeframeOpt.currentText()
            else:
                timeframe = self.dialog.drpTimeframeOpt.currentText()

            dnStrategyParameters = DNStrategyParameters()

            spMin = dnStrategyParameters.getStrategyParameters(timeframe, "min", 0)
            spMax = dnStrategyParameters.getStrategyParameters(timeframe, "max", 0)
            spStep = dnStrategyParameters.getStrategyParameters(timeframe, "step", 0)

            if spMin is None:
                spMin = dnStrategyParameters.getStrategyParameters("15m", "min", 0)
                spMin.Timeframe = timeframe
                spMin.Name = "min"
                spMin.OptimizationId = 0
                dnStrategyParameters.insertStrategyParameters(spMin)

            if spMax is None:
                spMax = dnStrategyParameters.getStrategyParameters("15m", "max", 0)
                spMax.Timeframe = timeframe
                spMax.Name = "max"
                spMax.OptimizationId = 0
                dnStrategyParameters.insertStrategyParameters(spMax)

            if spStep is None:
                spStep = dnStrategyParameters.getStrategyParameters("15m", "step", 0)
                spStep.Timeframe = timeframe
                spStep.Name = "step"
                spStep.OptimizationId = 0
                dnStrategyParameters.insertStrategyParameters(spStep)

            # true/false controls

            if not spMin.ROC_IndicatorEnabled and spMax.ROC_IndicatorEnabled:
                self.drpRocEnabled.setCurrentText("all")
            else:
                self.drpRocEnabled.setCurrentIndex(spMin.ROC_IndicatorEnabled)

            if not spMin.MPT_IndicatorEnabled and spMax.MPT_IndicatorEnabled:
                self.drpMptEnabled.setCurrentText("all")
            else:
                self.drpMptEnabled.setCurrentIndex(spMin.MPT_IndicatorEnabled)

            if not spMin.TREND_IndicatorEnabled and spMax.TREND_IndicatorEnabled:
                self.drpTrendEnabled.setCurrentText("all")
            else:
                self.drpTrendEnabled.setCurrentIndex(spMin.TREND_IndicatorEnabled)

            if not spMin.EMAX_IndicatorEnabled and spMax.EMAX_IndicatorEnabled:
                self.drpEmaxEnabled.setCurrentText("all")
            else:
                self.drpEmaxEnabled.setCurrentIndex(spMin.EMAX_IndicatorEnabled)

            if not spMin.VSTOP_IndicatorEnabled and spMax.VSTOP_IndicatorEnabled:
                self.drpVstopEnabled.setCurrentText("all")
            else:
                self.drpVstopEnabled.setCurrentIndex(spMin.VSTOP_IndicatorEnabled)

            if not spMin.NV_IndicatorEnabled and spMax.NV_IndicatorEnabled:
                self.drpNvEnabled.setCurrentText("all")
            else:
                self.drpNvEnabled.setCurrentIndex(spMin.NV_IndicatorEnabled)

            if not spMin.SELL_IndicatorEnabled and spMax.SELL_IndicatorEnabled:
                self.drpSELL_IndicatorEnabled.setCurrentText("all")
            else:
                self.drpSELL_IndicatorEnabled.setCurrentIndex(spMin.SELL_IndicatorEnabled)

            # applied price controls

            if spMin.ROC_AppliedPrice_R == "0" and spMax.ROC_AppliedPrice_R == "3":
                self.drpRocAppliedPriceR.setCurrentText("all")
            else:
                self.drpRocAppliedPriceR.setCurrentText(
                    dnStrategyParameters.convertAppliedPrice(spMin.ROC_AppliedPrice_R))

            if spMin.ROC_AppliedPrice_F == "0" and spMax.ROC_AppliedPrice_F == "3":
                self.drpRocAppliedPriceF.setCurrentText("all")
            else:
                self.drpRocAppliedPriceF.setCurrentText(
                    dnStrategyParameters.convertAppliedPrice(spMin.ROC_AppliedPrice_F))

            if spMin.MPT_AppliedPrice == "0" and spMax.MPT_AppliedPrice == "3":
                self.drpMptAppliedPrice.setCurrentText("all")
            else:
                self.drpMptAppliedPrice.setCurrentText(dnStrategyParameters.convertAppliedPrice(spMin.MPT_AppliedPrice))

            if spMin.TREND_AppliedPrice == "0" and spMax.TREND_AppliedPrice == "3":
                self.drpTrendAppliedPrice.setCurrentText("all")
            else:
                self.drpTrendAppliedPrice.setCurrentText(
                    dnStrategyParameters.convertAppliedPrice(spMin.TREND_AppliedPrice))

            if spMin.EMAX_AppliedPrice == "0" and spMax.EMAX_AppliedPrice == "3":
                self.drpEmaxEnabled.setCurrentText("all")
            else:
                self.drpEmaxEnabled.setCurrentText(dnStrategyParameters.convertAppliedPrice(spMin.EMAX_AppliedPrice))

            if spMin.VSTOP_AppliedPrice == "0" and spMax.VSTOP_AppliedPrice == "3":
                self.drpVstopAppliedPrice.setCurrentText("all")
            else:
                self.drpVstopAppliedPrice.setCurrentText(
                    dnStrategyParameters.convertAppliedPrice(spMin.VSTOP_AppliedPrice))

            if spMin.SELL_RSI_AppliedPrice == "0" and spMax.SELL_RSI_AppliedPrice == "3":
                self.drpSELL_RSI_Src.setCurrentText("all")
            else:
                self.drpSELL_RSI_Src.setCurrentText(
                    dnStrategyParameters.convertAppliedPrice(spMin.SELL_RSI_AppliedPrice))

            # textboxes

            self.txtRocPeriodR.setText(
                str(spMin.ROC_Period_R) + "," + str(spMax.ROC_Period_R) + "," + str(spStep.ROC_Period_R))
            self.removeZeros(self.txtRocPeriodR)

            self.txtRocSmoothingR.setText(
                str(spMin.ROC_Smoothing_R) + "," + str(spMax.ROC_Smoothing_R) + "," + str(spStep.ROC_Smoothing_R))
            self.removeZeros(self.txtRocSmoothingR)

            self.txtRocPeriodF.setText(
                str(spMin.ROC_Period_F) + "," + str(spMax.ROC_Period_F) + "," + str(spStep.ROC_Period_F))
            self.removeZeros(self.txtRocPeriodF)

            self.txtRocRBuyIncreasePercentage.setText(
                str(spMin.ROC_R_BuyIncreasePercentage) + "," + str(spMax.ROC_R_BuyIncreasePercentage) + "," + str(
                    spStep.ROC_R_BuyIncreasePercentage))
            self.removeZeros(self.txtRocRBuyIncreasePercentage)

            self.txtRocFBuyDecreasePercentage.setText(
                str(spMin.ROC_F_BuyDecreasePercentage) + "," + str(spMax.ROC_F_BuyDecreasePercentage) + "," + str(
                    spStep.ROC_F_BuyDecreasePercentage))
            self.removeZeros(self.txtRocFBuyDecreasePercentage)

            self.txtMptShortEmaPeriod.setText(
                str(spMin.MPT_ShortMAPeriod) + "," + str(spMax.MPT_ShortMAPeriod) + "," + str(spStep.MPT_ShortMAPeriod))
            self.removeZeros(self.txtMptShortEmaPeriod)

            self.txtMptLongEmaPeriod.setText(
                str(spMin.MPT_LongMAPeriod) + "," + str(spMax.MPT_LongMAPeriod) + "," + str(spStep.MPT_LongMAPeriod))
            self.removeZeros(self.txtMptLongEmaPeriod)

            self.txtTrendLongEmaPeriod.setText(
                str(spMin.TREND_LongEmaPeriod) + "," + str(spMax.TREND_LongEmaPeriod) + "," + str(
                    spStep.TREND_LongEmaPeriod))
            self.removeZeros(self.txtTrendLongEmaPeriod)

            self.txtTrendShortEmaPeriod.setText(
                str(spMin.TREND_ShortEmaPeriod) + "," + str(spMax.TREND_ShortEmaPeriod) + "," + str(
                    spStep.TREND_ShortEmaPeriod))
            self.removeZeros(self.txtTrendShortEmaPeriod)

            self.txtEmaxLongEmaPeriod.setText(
                str(spMin.EMAX_LongEmaPeriod) + "," + str(spMax.EMAX_LongEmaPeriod) + "," + str(
                    spStep.EMAX_LongEmaPeriod))
            self.removeZeros(self.txtEmaxLongEmaPeriod)

            self.txtEmaxShortEmaPeriod.setText(
                str(spMin.EMAX_ShortEmaPeriod) + "," + str(spMax.EMAX_ShortEmaPeriod) + "," + str(
                    spStep.EMAX_ShortEmaPeriod))
            self.removeZeros(self.txtEmaxShortEmaPeriod)

            self.txtVstopPeriod.setText(
                str(spMin.VSTOP_Period) + "," + str(spMax.VSTOP_Period) + "," + str(spStep.VSTOP_Period))
            self.removeZeros(self.txtVstopPeriod)

            self.txtVstopFactor.setText(
                str(spMin.VSTOP_Factor) + "," + str(spMax.VSTOP_Factor) + "," + str(spStep.VSTOP_Factor))
            self.removeZeros(self.txtVstopFactor)

            self.txtNvIncreasePercentage.setText(
                str(spMin.NV_IncreasePercentage) + "," + str(spMax.NV_IncreasePercentage) + "," + str(
                    spStep.NV_IncreasePercentage))
            self.removeZeros(self.txtNvIncreasePercentage)

            self.txtNvMinNetVolume.setText(
                str(spMin.NV_MinNetVolume) + "," + str(spMax.NV_MinNetVolume) + "," + str(spStep.NV_MinNetVolume))
            self.removeZeros(self.txtNvMinNetVolume)

            self.txtSELL_DecreasePercentage.setText(
                str(spMin.SELL_DecreasePercentage) + "," + str(spMax.SELL_DecreasePercentage) + "," + str(
                    spStep.SELL_DecreasePercentage))
            self.removeZeros(self.txtSELL_DecreasePercentage)

            self.txtSELL_Period.setText(
                str(spMin.SELL_Period) + "," + str(spMax.SELL_Period) + "," + str(spStep.SELL_Period))
            self.removeZeros(self.txtSELL_Period)

            self.txtRocSmoothingS.setText(
                str(spMin.ROC_Smoothing_S) + "," + str(spMax.ROC_Smoothing_S) + "," + str(spStep.ROC_Smoothing_S))
            self.removeZeros(self.txtRocSmoothingS)

            self.txtSELL_RSI_Period.setText(
                str(spMin.SELL_RSI_Period) + "," + str(spMax.SELL_RSI_Period) + "," + str(spStep.SELL_RSI_Period))
            self.removeZeros(self.txtSELL_RSI_Period)

            self.txtSELL_RSI_UpperLevel.setText(
                str(spMin.SELL_RSI_UpperLevel) + "," + str(spMax.SELL_RSI_UpperLevel) + "," + str(
                    spStep.SELL_RSI_UpperLevel))
            self.removeZeros(self.txtSELL_RSI_UpperLevel)

            self.txtSELL_RSI_LowerLevel.setText(
                str(spMin.SELL_RSI_LowerLevel) + "," + str(spMax.SELL_RSI_LowerLevel) + "," + str(
                    spStep.SELL_RSI_LowerLevel))
            self.removeZeros(self.txtSELL_RSI_LowerLevel)

            self.txtSELL_Stoch_KPeriod.setText(
                str(spMin.SELL_Stoch_KPeriod) + "," + str(spMax.SELL_Stoch_KPeriod) + "," + str(
                    spStep.SELL_Stoch_KPeriod))
            self.removeZeros(self.txtSELL_Stoch_KPeriod)

            self.txtSELL_Stoch_DPeriod.setText(
                str(spMin.SELL_Stoch_DPeriod) + "," + str(spMax.SELL_Stoch_DPeriod) + "," + str(
                    spStep.SELL_Stoch_DPeriod))
            self.removeZeros(self.txtSELL_Stoch_DPeriod)

            self.txtSELL_Stoch_Slowing.setText(
                str(spMin.SELL_Stoch_Slowing) + "," + str(spMax.SELL_Stoch_Slowing) + "," + str(
                    spStep.SELL_Stoch_Slowing))
            self.removeZeros(self.txtSELL_Stoch_Slowing)

            self.txtSELL_Stoch_UpperLevel.setText(
                str(spMin.SELL_Stoch_UpperLevel) + "," + str(spMax.SELL_Stoch_UpperLevel) + "," + str(
                    spStep.SELL_Stoch_UpperLevel))
            self.removeZeros(self.txtSELL_Stoch_UpperLevel)

            self.txtSELL_Stoch_LowerLevel.setText(
                str(spMin.SELL_Stoch_LowerLevel) + "," + str(spMax.SELL_Stoch_LowerLevel) + "," + str(
                    spStep.SELL_Stoch_LowerLevel))
            self.removeZeros(self.txtSELL_Stoch_LowerLevel)



        except:
            self.printLog("Exception: getIndicatorParametersForOpt", traceback.format_exc())

    # Markets

    def onAddSelectedMarketButtonClicked(self):
        try:
            print("onAddSelectedMarketButtonClicked")
            dnMarket = DNMarket()
            market = Market()
            market.symbol = self.txtNewSelectedMarket.text().upper().strip()
            dnMarket.addSelectedMarket(market.symbol)
            self.listSelectedMarket()
            self.txtNewSelectedMarket.setText("")
        except:
            self.printLog("Exception: onAddSelectedMarketButtonClicked", traceback.format_exc())

    def onExportSelectedMarkets(self):
        try:
            print("onExportSelectedMarkets")

            dnMarket = DNMarket()
            markets = dnMarket.listSelectedMarkets()
            # open the file in the write mode
            with open('SelectedMarketList.csv', 'w') as f1:
                writer = csv.writer(f1, delimiter='\n', lineterminator='\n', )
                for market in markets:
                    row = [market.Symbol]
                    writer.writerow(row)

            print("SelectedMarketList.csv is created.")
            self.statusBar.showMessage("SelectedMarketList.csv is created.", 2000)
        except:
            self.printLog("Exception: onExportSelectedMarkets", traceback.format_exc())

    def onImportSelectedMarkets(self):
        try:
            print("onImportSelectedMarkets")
            filename = QFileDialog.getOpenFileName(self, 'Open File', '.')
            if not filename:
                print("No file selected")
                return

            print(filename[0])
            dnMarket = DNMarket()
            dnMarket.resetSelectedMarket()

            # with open(str("C:/Users/oktar/Desktop/oktar.csv")) as csv_file:
            with open(str(filename[0])) as csv_file:
                csv_reader = csv.reader(csv_file, delimiter='\n')
                line_count = 0
                for row in csv_reader:
                    # if line_count == 0:
                    #    print(f'Column names are {", ".join(row)}')
                    #    line_count += 1
                    # else:

                    if row[0] == "":
                        continue

                    sym = row[0]
                    sym = sym.upper()
                    sym = sym.replace("-", "")

                    if sym.endswith("USD"):
                        sym = sym.replace("USD", "-USD")
                    elif sym.endswith("USDT"):
                        sym = sym.replace("USDT", "-USDT")
                    elif sym.endswith("BTC"):
                        sym = sym.replace("BTC", "-BTC")
                    elif sym.endswith("ETH"):
                        sym = sym.replace("ETH", "-ETH")
                    else:
                        continue

                    dnMarket.addSelectedMarket(sym)

                    print(sym)
                    line_count += 1
                # print(f'Processed {line_count} lines.')

            self.listSelectedMarket()
            self.txtNewSelectedMarket.setText("")

        except:
            self.printLog("Exception: onImportSelectedMarkets", traceback.format_exc())

    def onSearchMarketButtonClicked(self):
        try:
            print("onSearchMarketButtonClicked")
            dnMarket = DNMarket()
            symbol = self.txtSearchMarket.text().upper().strip()
            if symbol == "":
                markets = dnMarket.listTradeableMarkets()
            else:
                markets = dnMarket.searchMarketBySymbol(symbol)
            self.initTradedMarketDatagrid(markets, self.tblTradedMarkets)

        except:
            self.printLog("Exception: onSearchMarketButtonClicked", traceback.format_exc())

    def onSearchMarketIndLogButtonClicked(self):
        try:
            print("onSearchMarketIndLogButtonClicked")
            self.listIndicatorLogs()

        except:
            self.printLog("Exception: onSearchMarketIndLogButtonClicked", traceback.format_exc())

    def onSearchTradeHistoryButtonClicked(self):
        try:
            print("onSearchTradeHistoryButtonClicked")
            self.listClosedTrade()
        except:
            self.printLog("Exception: onSearchTradeHistoryButtonClicked", traceback.format_exc())

    def onSearchTradeLogsButtonClicked(self):
        try:
            print("onSearchTradeLogsButtonClicked")
            self.listTradeLogs()
        except:
            self.printLog("Exception: onSearchTradeLogsButtonClicked", traceback.format_exc())

    def onSearchBotLogsButtonClicked(self):
        try:
            print("onSearchBotLogsButtonClicked")
            self.listBotLogs()
        except:
            self.printLog("Exception: onSearchBotLogsButtonClicked", traceback.format_exc())

    def onSearchStatsButtonClicked(self):
        try:
            print("onSearchStatsButtonClicked")
            self.listStats()
        except:
            self.printLog("Exception: onSearchStatsButtonClicked", traceback.format_exc())

    def onTruncateTradeButtonClicked(self):
        try:
            print("onTruncateTradeButtonClicked")
            dnTrade = DNTrade()
            openTrades = dnTrade.listOpenTrade(0)
            if openTrades is not None and len(openTrades) > 0:
                QMessageBox.question(self, "Delete Trade History",
                                     "Can't delete trade history because you have open trades. Close open trades then try again.",
                                     QMessageBox.Ok)
                return

            buttonReply = QMessageBox.question(self, "Delete Trade History",
                                               "All trade history will be deleted! Are you sure?",
                                               QMessageBox.No | QMessageBox.Yes, QMessageBox.No)
            if buttonReply == QMessageBox.Yes:
                print('Yes clicked.')

                dnTrade.truncateTrade()
                self.listClosedTrade()
                self.statusBar.showMessage("Trade history deleted.", 2000)


        except:
            self.printLog("Exception: onTruncateTradeButtonClicked", traceback.format_exc())

    def onTruncateTradeLogButtonClicked(self):
        try:
            print("onTruncateTradeLogButtonClicked")
            dnTrade = DNTrade()
            openTrades = dnTrade.listOpenTrade(0)

            if openTrades is not None and len(openTrades) > 0:
                QMessageBox.question(self, "Delete Trade Logs",
                                     "Can't delete trade logs because you have open trades. Close open trades then try again.",
                                     QMessageBox.Ok)
                return

            buttonReply = QMessageBox.question(self, "Delete Trade Logs",
                                               "All trade logs will be deleted! Are you sure?",
                                               QMessageBox.No | QMessageBox.Yes, QMessageBox.No)
            if buttonReply == QMessageBox.Yes:
                print('Yes clicked.')
                dnTradeLog = DNTradeLog()
                dnTradeLog.truncateTradeLog()
                self.listTradeLogs()
                self.statusBar.showMessage("Trade logs deleted.", 2000)

        except:
            self.printLog("Exception: onTruncateTradeLogButtonClicked", traceback.format_exc())

    def onTruncateBotLogButtonClicked(self):
        try:
            print("onTruncateBotLogButtonClicked")

            buttonReply = QMessageBox.question(self, "Delete Bot Logs",
                                               "All bot logs will be deleted! Are you sure?",
                                               QMessageBox.No | QMessageBox.Yes, QMessageBox.No)
            if buttonReply == QMessageBox.Yes:
                print('Yes clicked.')
                dnBotLog = DNBotLog()
                dnBotLog.truncateBotLog()
                self.listBotLogs()
                self.statusBar.showMessage("Bot logs deleted.", 2000)

        except:
            self.printLog("Exception: onTruncateBotLogButtonClicked", traceback.format_exc())

    def onTruncateIndicatorLogButtonClicked(self):
        try:
            print("onTruncateIndicatorLogButtonClicked")

            buttonReply = QMessageBox.question(self, "Delete Indicator Logs",
                                               "All indicator logs will be deleted! Are you sure?",
                                               QMessageBox.No | QMessageBox.Yes, QMessageBox.No)
            if buttonReply == QMessageBox.Yes:
                print('Yes clicked.')
                dnIndicatorLog = DNIndicatorLog()
                dnIndicatorLog.truncateIndicatorLog()
                self.listIndicatorLogs()
                self.statusBar.showMessage("Indicator logs deleted.", 2000)

        except:
            self.printLog("Exception: onTruncateIndicatorLogButtonClicked", traceback.format_exc())

    def onDeleteSelectedMarketButtonClicked(self, row, col):
        try:
            print("onDeleteMarketClicked")
            id = self.tblSelectedMarket.item(row, 0).text()
            dnMarket = DNMarket()
            dnMarket.deleteSelectedMarket(id)
            self.listSelectedMarket()
        except:
            self.printLog("Exception: onDeleteSelectedMarketButtonClicked", traceback.format_exc())

    def listSelectedMarket(self):
        try:
            dnMarket = DNMarket()
            markets = dnMarket.listSelectedMarkets()
            self.initSelectedMarketDatagrid(markets, self.tblSelectedMarket)
        except:
            self.printLog("Exception: listSelectedMarket", traceback.format_exc())

    def listTradedMarket(self):
        try:
            dnMarket = DNMarket()
            markets = dnMarket.listTradeableMarkets()
            self.initTradedMarketDatagrid(markets, self.tblTradedMarkets)
        except:
            self.printLog("Exception: listTradedMarket", traceback.format_exc())

    def listScannerMarket(self):
        try:
            dnMarket = DNMarket()
            dnBotParameters = DNBotParameters()
            bot_parameters = dnBotParameters.getBotParameters()

            if bot_parameters.runOnSelectedMarkets:
                markets = dnMarket.listSelectedMarkets()
            else:
                markets = dnMarket.listTradeableMarkets()

            self.initScannerMarketDatagrid(markets, self.tblScannerMarket)
        except:
            self.printLog("Exception: listScannerMarket", traceback.format_exc())

    def listIndicatorLogs(self):
        try:
            dnIndicatorLog = DNIndicatorLog()
            symbol = self.txtSearchMarketIndLog.text().upper().strip()
            backtestId = self.txtBacktestIdIndLogs.text().upper().strip()

            if symbol != "":
                iLogs = dnIndicatorLog.listIndicatorLogBySymbol(symbol)
            elif backtestId != "":
                iLogs = dnIndicatorLog.listIndicatorLogByBacktestId(backtestId)
            else:
                iLogs = dnIndicatorLog.listIndicatorLog()

            self.initIndicatorLogDatagrid(iLogs, self.tblIndicatorLogs)
        except:
            self.printLog("Exception: listIndicatorLogs", traceback.format_exc())

    def listBotLogs(self):
        try:
            dnBotLog = DNBotLog()
            keyword = self.txtKeywordBotLogs.text().upper().strip()
            if keyword == "":
                botLogs = dnBotLog.listBotLog()
            else:
                botLogs = dnBotLog.searchBotLog(keyword)

            self.initBotLogDatagrid(botLogs, self.tblBotLogs)
        except:
            self.printLog("Exception: listBotLogs", traceback.format_exc())

    def onMarkClosedButtonClicked(self, row, col):
        try:
            print("onMarkClosedButtonClicked")
            buttonReply = QMessageBox.question(self, "Mark as closed",
                                               "Are you sure that you want to mark this trade as closed?",
                                               QMessageBox.No | QMessageBox.Yes, QMessageBox.No)
            if buttonReply == QMessageBox.Yes:
                print('Yes clicked.')
                tradeId = self.tblTrades.item(row, 0).text()
                self.swt.markTradeAsClosed(tradeId, "Marked Close")
                self.listOpenTrade()
                self.statusBar.showMessage("Trade is marked as closed.", 2000)

        except:
            self.printLog("Exception: onMarkClosedButtonClicked", traceback.format_exc())

    def onCloseButtonClicked(self, row, col):
        try:
            print("onCloseButtonClicked")
            tradeId = self.tblTrades.item(row, 0).text()

            self.swt.exitTrade(tradeId)

            # dnTrade = DNTrade()
            # trade = dnTrade.getTrade(tradeId)
            # self.swt.computeExitAmount(trade)

            self.listOpenTrade()
            self.statusBar.showMessage("Trade is closed.", 2000)

        except:
            self.printLog("Exception: onCloseButtonClicked", traceback.format_exc())

    def onSaveButtonClicked(self):
        try:
            print("onSaveButtonClicked")

            dnTrade = DNTrade()
            trade = Trade()
            trade.symbol = self.txtSymbol.toPlainText()
            trade.strategy_name = self.txtStrategyName.toPlainText()
            trade.trade_type = self.drpTradeType.currentText()

            if self.txtId.toPlainText() != "":
                trade.trade_id = int(self.txtId.toPlainText())
                dnTrade.updateTrade(trade)
            else:
                dnTrade.insertTrade(trade)

            self.listTrade()

        except:
            self.printLog("Exception: onSaveButtonClicked", traceback.format_exc())

    # Datagrid initializations

    def formatPrice(self, symbol, value):
        try:
            digits = 8
            if symbol.endswith("USDT") or symbol.endswith("USD"):
                digits = 5

            value = round(value, digits)
            valStr = str(value)
            if "E-" in valStr or "e-" in valStr:
                value = format(value, '.' + str(digits) + 'f')

            return str(value)
        except:
            self.printLog("Exception: formatPrice", traceback.format_exc())

    def formatAmount(self, symbol, value):
        try:
            digits = 8
            if not symbol.endswith("USDT") and not symbol.endswith("USD"):
                digits = 2

            value = round(value, digits)
            valStr = str(value)
            if "E-" in valStr or "e-" in valStr:
                value = format(value, '.' + str(digits) + 'f')

            return str(value)
        except:
            self.printLog("Exception: formatAmount", traceback.format_exc())

    def initOpenTradeDatagrid(self, resultList, datagrid):
        try:
            datagrid.setEditTriggers(QtWidgets.QTableWidget.NoEditTriggers)
            datagrid.setRowCount(0)
            row_number = 0

            # make the cells tighter
            header = datagrid.horizontalHeader()

            for i in range(16):
                if i < 4:
                    header.setSectionResizeMode(i, QtWidgets.QHeaderView.ResizeToContents)
                elif i == 8:
                    header.setSectionResizeMode(i, QtWidgets.QHeaderView.ResizeToContents)
                else:
                    header.setSectionResizeMode(i, QtWidgets.QHeaderView.Stretch)

            if not self.chkShowDetailColumns.isChecked():
                datagrid.setColumnHidden(1, True)
                datagrid.setColumnHidden(2, True)
                datagrid.setColumnHidden(5, True)
                datagrid.setColumnHidden(6, True)
                datagrid.setColumnHidden(7, True)
                datagrid.setColumnHidden(8, True)
                datagrid.setColumnHidden(9, True)
                datagrid.setColumnHidden(10, True)
                datagrid.setColumnHidden(11, True)
                datagrid.setColumnHidden(13, True)
            else:
                datagrid.setColumnHidden(1, False)
                datagrid.setColumnHidden(2, False)
                datagrid.setColumnHidden(5, False)
                datagrid.setColumnHidden(6, False)
                datagrid.setColumnHidden(7, False)
                datagrid.setColumnHidden(8, False)
                datagrid.setColumnHidden(9, False)
                datagrid.setColumnHidden(10, False)
                datagrid.setColumnHidden(11, False)
                datagrid.setColumnHidden(13, False)

            # hide some columns that are not needed anymore
            datagrid.setColumnHidden(2, True)
            # datagrid.setColumnHidden(5, True)
            datagrid.setColumnHidden(10, True)
            datagrid.setColumnHidden(11, True)

            if not resultList:
                return

            trueColor = self.trueColor
            falseColor = self.falseColor
            yellowColor = QColor(255, 194, 0)

            for item in resultList:
                k = 0
                s = item.Symbol
                datagrid.insertRow(row_number)

                datagrid.setItem(row_number, k, QTableWidgetItem(str(item.TradeId)))
                k = k + 1

                datagrid.setItem(row_number, k, QTableWidgetItem(str(item.EntryDate)))
                k = k + 1

                datagrid.setItem(row_number, k, QTableWidgetItem(str(item.EntryCandleDate)))
                k = k + 1

                updateStr = ""
                if item.ModifiedDate is not None:
                    dateDiff = datetime.now() - item.ModifiedDate
                    updateStr = str(dateDiff.seconds) + " sec."
                datagrid.setItem(row_number, k, QTableWidgetItem(str(updateStr)))
                k = k + 1

                btnLink = QLabel()
                btnLink.setText(
                    '<a style="color:#d8c569; text-decoration:none;" href="https://tradingview.com/chart?symbol=BITTREX:' + str(
                        item.Symbol.replace("-", "")) + '"> ' + str(item.Symbol) + '</a>')
                index = QtCore.QPersistentModelIndex(datagrid.model().index(row_number, k))
                btnLink.linkActivated.connect(self.openLink)
                datagrid.setCellWidget(row_number, k, btnLink)
                k = k + 1

                datagrid.setItem(row_number, k, QTableWidgetItem(str(item.StrategyName)))
                k = k + 1

                datagrid.setItem(row_number, k, QTableWidgetItem(self.formatPrice(s, item.EntryPrice)))
                k = k + 1

                currentPriceStr = self.formatPrice(s, item.CurrentPrice)
                datagrid.setItem(row_number, k, QTableWidgetItem(currentPriceStr))
                k = k + 1

                targetPriceStr = ""
                if item.TargetPrice > 0:
                    targetPriceStr = self.formatPrice(s, item.TargetPrice)
                datagrid.setItem(row_number, k, QTableWidgetItem(targetPriceStr))
                k = k + 1

                slStr = self.formatPrice(s, item.StopLoss)
                if item.TimerInSeconds > 0 and self.swt.isRunning:
                    currentTimeInSeconds = int(round(time.time()))
                    elapsedTimeInSeconds = item.TimerInSeconds - currentTimeInSeconds
                    if elapsedTimeInSeconds > 0:
                        elapsedMinutes = int(elapsedTimeInSeconds / 60) % 60
                        elapsedSeconds = elapsedTimeInSeconds % 60
                    else:
                        elapsedMinutes = 0
                        elapsedSeconds = 0
                    minStr = str(elapsedMinutes)
                    secStr = str(elapsedSeconds)
                    if elapsedMinutes < 10:
                        minStr = "0" + str(elapsedMinutes)
                    if elapsedSeconds < 10:
                        secStr = "0" + str(elapsedSeconds)
                    slTimeStr = minStr + ":" + secStr
                    slStr = slStr + " | " + slTimeStr + ""

                datagrid.setItem(row_number, k, QTableWidgetItem(slStr))
                if item.IsTslActivated:
                    datagrid.item(row_number, k).setBackground(QBrush(trueColor))
                else:
                    datagrid.item(row_number, k).setBackground(QBrush(falseColor))
                k = k + 1

                datagrid.setItem(row_number, k, QTableWidgetItem(self.formatAmount(s, item.Amount)))
                k = k + 1

                datagrid.setItem(row_number, k, QTableWidgetItem(self.formatPrice(s, item.QuoteAmount)))
                k = k + 1

                datagrid.setItem(row_number, k, QTableWidgetItem(self.formatPrice(s, item.PLAmount)))
                if item.PLAmount > 0:
                    datagrid.item(row_number, k).setBackground(QBrush(trueColor))
                else:
                    datagrid.item(row_number, k).setBackground(QBrush(falseColor))
                k = k + 1

                datagrid.setItem(row_number, k, QTableWidgetItem(str(item.PLPercentage)))
                if item.PLAmount > 0:
                    datagrid.item(row_number, k).setBackground(QBrush(trueColor))
                else:
                    datagrid.item(row_number, k).setBackground(QBrush(falseColor))
                k = k + 1

                btnClose = QPushButton()
                btnClose.setText("Mark Closed")
                index = QtCore.QPersistentModelIndex(datagrid.model().index(row_number, k))
                btnClose.clicked.connect(
                    lambda *args, index=index: self.onMarkClosedButtonClicked(index.row(), index.column()))
                datagrid.setCellWidget(row_number, k, btnClose)
                k = k + 1

                btnClose = QPushButton()
                btnClose.setText("Close Now")
                index = QtCore.QPersistentModelIndex(datagrid.model().index(row_number, k))
                btnClose.clicked.connect(
                    lambda *args, index=index: self.onCloseButtonClicked(index.row(), index.column()))
                datagrid.setCellWidget(row_number, k, btnClose)
                k = k + 1

                row_number += 1





        except:
            self.printLog("Exception: initTradeDatagrid", traceback.format_exc())

    def initBacktestDatagrid(self, resultList, datagrid):
        try:
            datagrid.setEditTriggers(QtWidgets.QTableWidget.NoEditTriggers)
            datagrid.setRowCount(0)
            row_number = 0

            # make the cells tighter
            header = datagrid.horizontalHeader()

            colCount = datagrid.columnCount()
            for i in range(colCount):
                if i < 6:
                    header.setSectionResizeMode(i, QtWidgets.QHeaderView.ResizeToContents)

            if not resultList:
                return

            for item in resultList:
                k = 0
                s = item.Symbol
                datagrid.insertRow(row_number)

                datagrid.setItem(row_number, k, QTableWidgetItem(str(item.BacktestId)))
                k = k + 1

                datagrid.setItem(row_number, k, QTableWidgetItem(str(item.OptimizationRunId)))
                k = k + 1

                datagrid.setItem(row_number, k, QTableWidgetItem(str(item.Symbol)))
                k = k + 1

                datagrid.setItem(row_number, k, QTableWidgetItem(str(item.CreatedDate)))
                k = k + 1

                datagrid.setItem(row_number, k, QTableWidgetItem(str(item.StartDate)))
                k = k + 1

                datagrid.setItem(row_number, k, QTableWidgetItem(str(item.EndDate)))
                k = k + 1

                datagrid.setItem(row_number, k, QTableWidgetItem(str(item.DurationInMinutes)))
                k = k + 1

                datagrid.setItem(row_number, k, QTableWidgetItem(str(item.TotalTrades)))
                k = k + 1

                datagrid.setItem(row_number, k, QTableWidgetItem(str(item.AvgTimeInTradeInMinutes)))
                k = k + 1

                datagrid.setItem(row_number, k, QTableWidgetItem(str(item.TotalTradesPerHour)))
                k = k + 1

                datagrid.setItem(row_number, k, QTableWidgetItem(str(item.AvgPLPercentage)))
                k = k + 1

                datagrid.setItem(row_number, k, QTableWidgetItem(str(item.PLAmountPerHour)))
                k = k + 1

                datagrid.setItem(row_number, k, QTableWidgetItem(self.formatPrice(s, item.PLAmount)))
                k = k + 1

                datagrid.setItem(row_number, k, QTableWidgetItem(str(item.PLPercentage)))
                if item.PLAmount > 0:
                    datagrid.item(row_number, k).setBackground(QBrush(self.trueColor))
                else:
                    datagrid.item(row_number, k).setBackground(QBrush(self.falseColor))
                k = k + 1

                row_number += 1
        except:
            self.printLog("Exception: initBacktestDatagrid", traceback.format_exc())

    def onOptimizationRunsClicked(self, item):
        if item.column() != 9:
            return

        self.onBestParamsButtonClicked(item.row(), item.column())

        # sf = "You clicked on {0}x{1}".format(item.column(), item.row())
        # bestSpId = self.tblOptimizationRuns.item(item.row(), item.column()).text()
        # print(bestSpId)

    def onBotLogsClicked(self, item):
        if item.column() != 3:
            return

        self.onLogDetailButtonClicked(item.row(), item.column())

    def onScannerClicked(self, item):
        if item.column() != 4:
            return

        self.onUsedParamsButtonClicked(item.row(), item.column())

    def initOptimizationRunDatagrid(self, resultList, datagrid):
        try:
            datagrid.setEditTriggers(QtWidgets.QTableWidget.NoEditTriggers)
            datagrid.setRowCount(0)
            row_number = 0

            header = datagrid.horizontalHeader()

            colCount = datagrid.columnCount()
            for i in range(colCount):
                if i < 11:
                    header.setSectionResizeMode(i, QtWidgets.QHeaderView.ResizeToContents)
                else:
                    header.setSectionResizeMode(i, QtWidgets.QHeaderView.Stretch)

            if not resultList:
                return

            for item in resultList:
                k = 0
                s = item.Symbol
                datagrid.insertRow(row_number)

                datagrid.setItem(row_number, k, QTableWidgetItem(str(item.OptimizationRunId)))
                k = k + 1

                datagrid.setItem(row_number, k, QTableWidgetItem(str(item.OptimizationId)))
                k = k + 1

                datagrid.setItem(row_number, k, QTableWidgetItem(str(item.Symbol)))
                k = k + 1

                datagrid.setItem(row_number, k, QTableWidgetItem(str(item.CreatedDate)))
                k = k + 1

                datagrid.setItem(row_number, k, QTableWidgetItem(str(item.StartDate)))
                k = k + 1

                datagrid.setItem(row_number, k, QTableWidgetItem(str(item.EndDate)))
                k = k + 1

                datagrid.setItem(row_number, k, QTableWidgetItem(str(item.DurationInMinutes)))
                k = k + 1

                datagrid.setItem(row_number, k, QTableWidgetItem(str(item.CombinationCount)))
                k = k + 1

                datagrid.setItem(row_number, k, QTableWidgetItem(str(item.BestBacktestId)))
                k = k + 1

                datagrid.setItem(row_number, k, QTableWidgetItem(str(item.BestSpId)))
                k = k + 1

                datagrid.setItem(row_number, k, QTableWidgetItem(""))
                if item.BestBacktestId > 0:
                    datagrid.setItem(row_number, k, QTableWidgetItem(str(item.PLPercentage)))
                    if item.PLPercentage > 0:
                        datagrid.item(row_number, k).setBackground(QBrush(self.trueColor))
                    else:
                        datagrid.item(row_number, k).setBackground(QBrush(self.falseColor))
                k = k + 1

                datagrid.setItem(row_number, k, QTableWidgetItem(item.State))
                k = k + 1

                row_number += 1
        except:
            self.printLog("Exception: initBacktestDatagrid", traceback.format_exc())

    def initClosedTradeDatagrid(self, resultList, datagrid):
        try:
            datagrid.setEditTriggers(QtWidgets.QTableWidget.NoEditTriggers)
            datagrid.setRowCount(0)
            row_number = 0

            # make the cells tighhter
            header = datagrid.horizontalHeader()
            for i in range(12):
                if i < 5:
                    header.setSectionResizeMode(i, QtWidgets.QHeaderView.ResizeToContents)
                else:
                    header.setSectionResizeMode(i, QtWidgets.QHeaderView.Stretch)

            if not self.chkShowDetailColumns.isChecked():
                datagrid.setColumnHidden(3, True)
                datagrid.setColumnHidden(4, True)
                datagrid.setColumnHidden(5, True)
                datagrid.setColumnHidden(6, True)
                datagrid.setColumnHidden(7, True)

                datagrid.setColumnHidden(8, True)
                datagrid.setColumnHidden(9, True)
                datagrid.setColumnHidden(10, True)
            else:
                datagrid.setColumnHidden(3, False)
                datagrid.setColumnHidden(4, False)
                datagrid.setColumnHidden(5, False)
                datagrid.setColumnHidden(6, False)
                datagrid.setColumnHidden(7, False)

                datagrid.setColumnHidden(8, False)
                datagrid.setColumnHidden(9, False)
                datagrid.setColumnHidden(10, False)

            # datagrid.setColumnHidden(2, True)
            datagrid.setColumnHidden(7, True)

            if not resultList:
                return

            for item in resultList:
                k = 0
                datagrid.insertRow(row_number)
                s = item.Symbol

                datagrid.setItem(row_number, k, QTableWidgetItem(str(item.TradeId)))
                k = k + 1

                datagrid.setItem(row_number, k, QTableWidgetItem(str(item.Symbol)))
                k = k + 1

                datagrid.setItem(row_number, k, QTableWidgetItem(str(item.StrategyName)))
                k = k + 1

                datagrid.setItem(row_number, k, QTableWidgetItem(str(item.EntryDate)))
                k = k + 1

                datagrid.setItem(row_number, k, QTableWidgetItem(str(item.ExitDate)))
                k = k + 1

                entryPriceStr = self.formatPrice(s, item.EntryPrice) + " | T: " + self.formatPrice(s,
                                                                                                   item.EntryTriggerPrice)
                datagrid.setItem(row_number, k, QTableWidgetItem(entryPriceStr))
                k = k + 1

                exitPriceStr = self.formatPrice(s, item.ExitPrice) + " | T: " + self.formatPrice(s,
                                                                                                 item.ExitTriggerPrice)
                datagrid.setItem(row_number, k, QTableWidgetItem(exitPriceStr))
                k = k + 1

                targetPriceStr = ""
                if item.TargetPrice > 0:
                    targetPriceStr = self.formatPrice(s, item.TargetPrice)
                datagrid.setItem(row_number, k, QTableWidgetItem(targetPriceStr))
                k = k + 1

                datagrid.setItem(row_number, k, QTableWidgetItem(self.formatAmount(s, item.Amount)))
                k = k + 1

                datagrid.setItem(row_number, k, QTableWidgetItem(self.formatPrice(s, item.QuoteAmount)))
                k = k + 1

                datagrid.setItem(row_number, k, QTableWidgetItem(self.formatPrice(s, item.PLAmount)))
                if item.PLAmount > 0:
                    datagrid.item(row_number, k).setBackground(QBrush(self.trueColor))
                else:
                    datagrid.item(row_number, k).setBackground(QBrush(self.falseColor))
                k = k + 1

                datagrid.setItem(row_number, k, QTableWidgetItem(str(item.PLPercentage)))
                if item.PLAmount > 0:
                    datagrid.item(row_number, k).setBackground(QBrush(self.trueColor))
                else:
                    datagrid.item(row_number, k).setBackground(QBrush(self.falseColor))
                k = k + 1

                row_number += 1
        except:
            self.printLog("Exception: initClosedTradeDatagrid", traceback.format_exc())

    def initStatsDatagrid(self, trades, datagrid):
        try:
            datagrid.setEditTriggers(QtWidgets.QTableWidget.NoEditTriggers)
            datagrid.setRowCount(13)

            header = datagrid.horizontalHeader()
            for i in range(4):
                header.setSectionResizeMode(i, QtWidgets.QHeaderView.ResizeToContents)

            cellHeight = 60
            fontSize = 20
            fnt = datagrid.font()
            fnt.setPointSize(fontSize)
            datagrid.setFont(fnt)

            datagrid.horizontalHeader().setFixedHeight(cellHeight)

            datagrid.verticalHeader().setVisible(True)
            datagrid.verticalHeaderItem(0).setText("Total Trades")
            datagrid.verticalHeaderItem(1).setText("Closed Trades")
            datagrid.verticalHeaderItem(2).setText("Open Trades")
            datagrid.verticalHeaderItem(3).setText("Amount In Use")
            datagrid.verticalHeaderItem(4).setText("Avg PL")
            datagrid.verticalHeaderItem(5).setText("PL")
            datagrid.verticalHeaderItem(6).setText("PL %")
            datagrid.verticalHeaderItem(7).setText("Avg PL %")  # 11

            datagrid.verticalHeaderItem(8).setText("PL $")
            datagrid.verticalHeaderItem(9).setText("Avg Trade Amount")
            datagrid.verticalHeaderItem(10).setText("Avg Time In Trade (Min)")
            datagrid.verticalHeaderItem(11).setText("Total Trades / Hour")

            datagrid.verticalHeaderItem(12).setText("Total PL / Hour")

            if not trades:
                return

            secondsDiff = self.dateFromStats.dateTime().secsTo(self.dateToStats.dateTime())
            dateDiffInHours = decimal.Decimal(secondsDiff / (60 * 60))

            totalTradeCount = [0, 0, 0, 0]
            closedTradeCount = [0, 0, 0, 0]
            openTradeCount = [0, 0, 0, 0]
            amountInUse = [0, 0, 0, 0]
            avgPLTrade = [0, 0, 0, 0]
            plAmount = [0, 0, 0, 0]
            plPercentage = [0, 0, 0, 0]
            plUsd = [0, 0, 0, 0]
            avgTradeAmount = [0, 0, 0, 0]
            avgTimeInTradeInMinutes = [0, 0, 0, 0]
            tradeCountPerHour = [0, 0, 0, 0]
            avgPLPercentage = [0, 0, 0, 0]
            plAmountPerHour = [0, 0, 0, 0]

            for t in trades:
                index = -1
                if t.Symbol.endswith('BTC'):
                    index = 0
                elif t.Symbol.endswith('USDT'):
                    index = 1
                elif t.Symbol.endswith('ETH'):
                    index = 2
                elif t.Symbol.endswith('USD'):
                    index = 3
                else:
                    continue

                totalTradeCount[index] = totalTradeCount[index] + 1
                if t.IsOpen:
                    openTradeCount[index] = openTradeCount[index] + 1
                    amountInUse[index] = amountInUse[index] + t.QuoteAmount
                else:
                    closedTradeCount[index] = closedTradeCount[index] + 1
                    plAmount[index] = plAmount[index] + t.PLAmount
                    plPercentage[index] = plPercentage[index] + t.PLPercentage
                    avgTradeAmount[index] = avgTradeAmount[index] + t.QuoteAmount

                    if t.ExitDate is not None and t.EntryDate is not None:
                        dateDiff = t.ExitDate - t.EntryDate
                        avgTimeInTradeInMinutes[index] = avgTimeInTradeInMinutes[index] + decimal.Decimal(
                            dateDiff.seconds / 60)

                        # seconds_in_day = 24 * 60 * 60
                        # print(divmod(difference.days * seconds_in_day + difference.seconds, 60))

            dnMarket = DNMarket()
            if index == 0:
                btcusdt = dnMarket.getMarketBySymbol("BTC-USDT")
                plUsd[0] = plAmount[0] * btcusdt.LastPrice
            elif index == 1:
                plUsd[1] = plAmount[1]
            elif index == 2:
                ethusdt = dnMarket.getMarketBySymbol("ETH-USDT")
                plUsd[2] = plAmount[2] * ethusdt.LastPrice
            elif index == 3:
                # bnbusdt = dnMarket.getMarketBySymbol("BNB-USDT")
                plUsd[3] = plAmount[3]  # * bnbusdt.LastPrice

            for i in range(4):
                if closedTradeCount[i] > 0:
                    avgPLTrade[i] = plAmount[i] / closedTradeCount[i]
                    avgTradeAmount[i] = avgTradeAmount[i] / closedTradeCount[i]
                    avgTimeInTradeInMinutes[i] = avgTimeInTradeInMinutes[i] / closedTradeCount[i]
                    avgPLPercentage[i] = plPercentage[i] / closedTradeCount[i]

                # if avgTimeInTradeInMinutes[i] > 0:

                if dateDiffInHours > 0:
                    tradeCountPerHour[i] = closedTradeCount[i] / dateDiffInHours
                    plAmountPerHour[i] = plAmount[i] / dateDiffInHours
                    # if i ==1:
                    #    print(plAmountPerHour[i])

            for i in range(13):
                self.insertStatsRow(datagrid, i, totalTradeCount, closedTradeCount, openTradeCount, amountInUse,
                                    avgPLTrade, plAmount, plPercentage, plUsd, avgTradeAmount, avgTimeInTradeInMinutes,
                                    tradeCountPerHour, avgPLPercentage, plAmountPerHour)
                datagrid.setRowHeight(i, cellHeight);


        except:
            self.printLog("Exception: initStatsDatagrid", traceback.format_exc())

    def insertStatsRow(self, datagrid, row_number, totalTradeCount, closedTradeCount, openTradeCount, amountInUse,
                       avgPLTrade, plAmount, plPercentage, plUsd, avgTradeAmount, avgTimeInTradeInMinutes,
                       tradeCountPerHour, avgPLPercentage, plAmountPerHour):
        try:

            data = [0, 0, 0, 0]
            useFormatPrice = False
            useRound2 = False

            if row_number == 0:
                data = totalTradeCount
            elif row_number == 1:
                data = closedTradeCount
            elif row_number == 2:
                data = openTradeCount
            elif row_number == 3:
                data = amountInUse
                useFormatPrice = True
            elif row_number == 4:
                data = avgPLTrade
                useFormatPrice = True
            elif row_number == 5:
                data = plAmount
                useFormatPrice = True
            elif row_number == 6:
                data = plPercentage
            elif row_number == 7:
                data = avgPLPercentage
                useRound2 = True
            elif row_number == 8:
                data = plUsd
                useRound2 = True
            elif row_number == 9:
                data = avgTradeAmount
                useFormatPrice = True
            elif row_number == 10:
                data = avgTimeInTradeInMinutes
                useRound2 = True
            elif row_number == 11:
                data = tradeCountPerHour
                useRound2 = True
            elif row_number == 12:
                data = plAmountPerHour
                useFormatPrice = True

            # datagrid.insertRow(row_number)

            for i in range(4):
                s = ""
                if i == 0:
                    s = "BTC"
                elif i == 1:
                    s = "USDT"
                elif i == 2:
                    s = "ETH"
                elif i == 3:
                    s = "USD"

                value = str(data[i])
                if useFormatPrice:
                    value = self.formatPrice(s, data[i])
                elif useRound2:
                    value = str(round(data[i], 2))

                datagrid.setItem(row_number, i, QTableWidgetItem(value))

        except:
            self.printLog("Exception: insertStatsRow", traceback.format_exc())

    def isOptimizationMode(self):
        dnBotParameters = DNBotParameters()
        bp = dnBotParameters.getBotParameters()

        if bp is not None:
            return bp.optimizationMode
        return False

    def initTradeLogDatagrid(self, resultList, datagrid):
        try:
            datagrid.setEditTriggers(QtWidgets.QTableWidget.NoEditTriggers)
            datagrid.setRowCount(0)
            row_number = 0

            optimizationMode = self.isOptimizationMode()

            compressedColCount = 5
            if optimizationMode:
                compressedColCount = compressedColCount + 1

            header = datagrid.horizontalHeader()
            for i in range(15):
                if i < compressedColCount:
                    header.setSectionResizeMode(i, QtWidgets.QHeaderView.ResizeToContents)
                else:
                    header.setSectionResizeMode(i, QtWidgets.QHeaderView.Stretch)

            if not resultList:
                return

            for item in resultList:
                k = 0
                datagrid.insertRow(row_number)
                s = item.Symbol

                datagrid.setItem(row_number, k, QTableWidgetItem(str(item.TradeId)))
                k = k + 1

                datagrid.setItem(row_number, k, QTableWidgetItem(str(item.BacktestId)))
                k = k + 1

                datagrid.setItem(row_number, k, QTableWidgetItem(str(item.CreatedDate)))
                k = k + 1

                datagrid.setItem(row_number, k, QTableWidgetItem(str(item.Symbol)))
                k = k + 1

                datagrid.setItem(row_number, k, QTableWidgetItem(str(item.StrategyName)))
                k = k + 1

                datagrid.setItem(row_number, k, QTableWidgetItem(str(item.Action)))
                if item.Action == "Buy" or item.Action == "Sell":
                    datagrid.item(row_number, k).setBackground(QBrush(self.trueColor))
                elif item.Action == "Close":
                    datagrid.item(row_number, k).setBackground(QBrush(self.falseColor))
                k = k + 1

                datagrid.setItem(row_number, k, QTableWidgetItem(str(item.Comment)))
                k = k + 1

                datagrid.setItem(row_number, k, QTableWidgetItem(self.formatAmount(s, item.Amount)))
                k = k + 1

                datagrid.setItem(row_number, k, QTableWidgetItem(self.formatPrice(s, item.QuoteAmount)))
                k = k + 1

                datagrid.setItem(row_number, k, QTableWidgetItem(self.formatPrice(s, item.EntryPrice)))
                k = k + 1

                targetPriceStr = ""
                if item.TargetPrice > 0:
                    targetPriceStr = self.formatPrice(s, item.TargetPrice)
                datagrid.setItem(row_number, k, QTableWidgetItem(targetPriceStr))
                k = k + 1

                datagrid.setItem(row_number, k, QTableWidgetItem(self.formatPrice(s, item.CurrentPrice)))
                k = k + 1

                datagrid.setItem(row_number, k, QTableWidgetItem(self.formatPrice(s, item.StopLoss)))
                k = k + 1

                plAmountStr = self.formatPrice(s, item.PLAmount)
                plPercentageStr = str(item.PLPercentage)

                if item.Action != "Close":
                    plAmountStr = ""
                    plPercentageStr = ""

                datagrid.setItem(row_number, k, QTableWidgetItem(plAmountStr))
                if plAmountStr != "" and item.PLAmount > 0:
                    datagrid.item(row_number, k).setBackground(QBrush(self.trueColor))
                elif plAmountStr != "" and item.PLAmount <= 0:
                    datagrid.item(row_number, k).setBackground(QBrush(self.falseColor))
                k = k + 1

                datagrid.setItem(row_number, k, QTableWidgetItem(plPercentageStr))
                if plPercentageStr != "" and item.PLAmount > 0:
                    datagrid.item(row_number, k).setBackground(QBrush(self.trueColor))
                elif plPercentageStr != "" and item.PLAmount <= 0:
                    datagrid.item(row_number, k).setBackground(QBrush(self.falseColor))
                k = k + 1

                commissionStr = ""
                if item.Action == "Close" or item.Action == "Buy" or item.Action == "Sell":
                    commissionStr = str(item.Commission)

                datagrid.setItem(row_number, k, QTableWidgetItem(commissionStr))
                k = k + 1

                row_number += 1
            # sort column logs -> Trade logs
            datagrid.setSortingEnabled(True)
            datagrid.sortItems(0, QtCore.Qt.AscendingOrder)
            datagrid.sortItems(1, QtCore.Qt.AscendingOrder)
            datagrid.sortItems(2, QtCore.Qt.AscendingOrder)
            # adjust columns
            header = datagrid.horizontalHeader()
            header.setSectionResizeMode(0, QtWidgets.QHeaderView.Stretch)
            header.setSectionResizeMode(1, QtWidgets.QHeaderView.ResizeToContents)
            header.setSectionResizeMode(2, QtWidgets.QHeaderView.ResizeToContents)
        except:
            self.printLog("Exception: initTradeLogDatagrid", traceback.format_exc())

    def initTickDataDatagrid(self, resultList, datagrid):
        try:
            datagrid.setEditTriggers(QtWidgets.QTableWidget.NoEditTriggers)
            datagrid.setRowCount(0)
            row_number = 0

            header = datagrid.horizontalHeader()
            for i in range(4):
                header.setSectionResizeMode(i, QtWidgets.QHeaderView.ResizeToContents)

            if not resultList:
                return

            for item in resultList:
                k = 0
                datagrid.insertRow(row_number)
                s = item.Symbol

                datagrid.setItem(row_number, k, QTableWidgetItem(str(item.TickDataId)))
                k = k + 1

                datagrid.setItem(row_number, k, QTableWidgetItem(str(item.OpenTime)))
                k = k + 1

                datagrid.setItem(row_number, k, QTableWidgetItem(str(item.CreatedDate)))
                k = k + 1

                datagrid.setItem(row_number, k, QTableWidgetItem(str(item.Symbol)))
                k = k + 1

                datagrid.setItem(row_number, k, QTableWidgetItem(str(item.Close)))
                k = k + 1

                row_number += 1
        except:
            self.printLog("Exception: initTickDataDatagrid", traceback.format_exc())

    def initBotLogDatagrid(self, resultList, datagrid):
        try:
            datagrid.setEditTriggers(QtWidgets.QTableWidget.NoEditTriggers)
            datagrid.setRowCount(0)
            row_number = 0

            header = datagrid.horizontalHeader()

            header.setSectionResizeMode(0, QtWidgets.QHeaderView.ResizeToContents)  # ResizeToContents
            header.setSectionResizeMode(1, QtWidgets.QHeaderView.ResizeToContents)  # ResizeToContents
            header.setSectionResizeMode(2, QtWidgets.QHeaderView.Stretch)
            header.setSectionResizeMode(3, QtWidgets.QHeaderView.ResizeToContents)  # ResizeToContents

            if not resultList:
                return

            for item in resultList:
                k = 0
                datagrid.insertRow(row_number)

                datagrid.setItem(row_number, k, QTableWidgetItem(str(item.BotLogId)))
                k = k + 1

                datagrid.setItem(row_number, k, QTableWidgetItem(str(item.CreatedDate)))
                k = k + 1

                datagrid.setItem(row_number, k, QTableWidgetItem(str(item.ShortLog)))
                k = k + 1

                if str(item.LongLog) != "":
                    datagrid.setItem(row_number, k, QTableWidgetItem("Detail"))
                    k = k + 1

                row_number += 1
        except:
            self.printLog("Exception: initBotLogDatagrid", traceback.format_exc())

    def onLogDetailButtonClicked(self, row, col):
        try:
            print("onLogDetailButtonClicked")
            id = self.tblBotLogs.item(row, 0).text()

            dnBotLog = DNBotLog()
            botLog = dnBotLog.getBotLog(id)
            QMessageBox.question(self, "Log Detail: " + str(id), botLog.LongLog, QMessageBox.Ok)

        except:
            self.printLog("Exception: onLogDetailButtonClicked", traceback.format_exc())

    def onUsedParamsButtonClicked(self, row, col):
        try:
            print("onUsedParamsButtonClicked")
            symbol = self.tblScannerMarket.item(row, 1).text()

            dnStrategyParameters = DNStrategyParameters()
            sp = dnStrategyParameters.getStrategyParametersBySymbolForTrader(self.drpBotTimeframe.currentText(), symbol)

            dnBotParameters = DNBotParameters()
            botPar = dnBotParameters.getBotParameters()

            if botPar.optUpdateStrategyParameters and sp is not None:
                spStr = dnStrategyParameters.convertStrategyParametersToString(sp)
                spStr = spStr.replace(",", ",\n")
                QMessageBox.question(self, "Optimized Params for " + symbol, spStr, QMessageBox.Ok)
            else:
                sp = dnStrategyParameters.getStrategyParametersBySymbolForTrader(self.drpBotTimeframe.currentText(), "")
                spStr = dnStrategyParameters.convertStrategyParametersToString(sp)
                spStr = spStr.replace(",", ",\n")
                QMessageBox.question(self, "Default Params for " + symbol, spStr, QMessageBox.Ok)

        except:
            self.printLog("Exception: onUsedParamsButtonClicked", traceback.format_exc())

    def onBestParamsButtonClicked(self, row, col):
        try:
            print("onBestParamsButtonClicked")
            id = self.tblOptimizationRuns.item(row, 0).text()

            dnOptimizationRun = DNOptimizationRun()
            optimizationRun = dnOptimizationRun.getOptimizationRun(id)

            if not optimizationRun:
                return

            dnStrategyParameters = DNStrategyParameters()
            sp = dnStrategyParameters.getStrategyParametersById(optimizationRun.BestSpId)
            spStr = dnStrategyParameters.convertStrategyParametersToString(sp)
            spStr = spStr.replace(",", ",\n")

            QMessageBox.question(self, "Best Params: " + str(optimizationRun.BestSpId), spStr, QMessageBox.Ok)

        except:
            self.printLog("Exception: onBestParamsButtonClicked", traceback.format_exc())

    def initSelectedMarketDatagrid(self, resultList, datagrid):
        try:
            datagrid.setEditTriggers(QtWidgets.QTableWidget.NoEditTriggers)
            datagrid.setRowCount(0)
            row_number = 0

            # datagrid.horizontalHeader().hide()
            datagrid.horizontalHeader().hideSection(0)
            datagrid.verticalHeader().hide()

            # for i in range(6):
            #    header.setSectionResizeMode(i, QtWidgets.QHeaderView.ResizeToContents)

            # datagrid.setColumnHidden(0, True)

            datagrid.horizontalHeader().setSectionResizeMode(0, QtWidgets.QHeaderView.ResizeToContents)
            datagrid.horizontalHeader().setSectionResizeMode(1, QtWidgets.QHeaderView.Stretch)
            datagrid.horizontalHeader().setSectionResizeMode(2, QtWidgets.QHeaderView.ResizeToContents)

            if not resultList:
                return

            for item in resultList:
                datagrid.insertRow(row_number)
                datagrid.setItem(row_number, 0, QTableWidgetItem(str(item.MarketId)))
                datagrid.setItem(row_number, 1, QTableWidgetItem(str(item.Symbol)))

                # Add delete button to table
                btnDeleteMarket = QPushButton("")
                btnDeleteMarket.setText("Remove")
                index = QtCore.QPersistentModelIndex(datagrid.model().index(row_number, 2))
                btnDeleteMarket.clicked.connect(
                    lambda *args, index=index: self.onDeleteSelectedMarketButtonClicked(index.row(), index.column()))
                datagrid.setCellWidget(row_number, 2, btnDeleteMarket)

                # Add delete image to button
                # btnDeleteMarket.setFixedWidth(35)
                # btnDeleteMarket.setFixedHeight(30)
                # pixmapD = QPixmap("UI/Icon/delete.png")
                # buttonIconD = QIcon(pixmapD)
                # btnDeleteMarket.setIcon(buttonIconD)
                # btnDeleteMarket.setIconSize(pixmapD.rect().size() / 5)

                # btnClose = QPushButton()
                # btnClose.setText("Delete")
                # index = QtCore.QPersistentModelIndex(datagrid.model().index(row_number, k))
                # btnClose.clicked.connect(lambda *args, index=index: self.onCloseButtonClicked(index.row(), index.column()))
                # datagrid.setCellWidget(row_number, k, btnClose)
                # k = k + 1

                row_number += 1
        except:
            self.printLog("Exception: initSelectedMarketDatagrid", traceback.format_exc())

    def initTradedMarketDatagrid(self, resultList, datagrid):
        try:
            datagrid.setEditTriggers(QtWidgets.QTableWidget.NoEditTriggers)
            datagrid.setRowCount(0)
            row_number = 0

            # datagrid.horizontalHeader().hide()
            datagrid.horizontalHeader().hideSection(0)
            datagrid.verticalHeader().hide()

            datagrid.horizontalHeader().setSectionResizeMode(0, QtWidgets.QHeaderView.Stretch)
            datagrid.horizontalHeader().setSectionResizeMode(1, QtWidgets.QHeaderView.Stretch)
            datagrid.horizontalHeader().setSectionResizeMode(2, QtWidgets.QHeaderView.Stretch)
            datagrid.horizontalHeader().setSectionResizeMode(3, QtWidgets.QHeaderView.Stretch)

            if not resultList:
                return

            for item in resultList:
                datagrid.insertRow(row_number)
                datagrid.setItem(row_number, 0, QTableWidgetItem(str(item.MarketId)))
                datagrid.setItem(row_number, 1, QTableWidgetItem(str(item.Symbol)))
                datagrid.setItem(row_number, 2, QTableWidgetItem(str(item.DailyVolume)))

                dp = item.DailyPrice
                dpStr = str(dp)
                if dp == 0:
                    dpStr = "0"
                if dp < 0.00000100:
                    dp = dp * 100000000
                    dpStr = "0.000000" + str(int(dp))

                datagrid.setItem(row_number, 3, QTableWidgetItem(dpStr))

                row_number += 1
        except:
            self.printLog("Exception: initTradedMarketDatagrid", traceback.format_exc())

    def initScannerMarketDatagrid(self, resultList, datagrid):
        try:
            datagrid.setEditTriggers(QtWidgets.QTableWidget.NoEditTriggers)
            datagrid.setRowCount(0)
            row_number = 0
            datagrid.horizontalHeader().hideSection(0)
            datagrid.verticalHeader().hide()

            for i in range(12):
                datagrid.horizontalHeader().setSectionResizeMode(i, QtWidgets.QHeaderView.Stretch)

            for item in resultList:
                if self.botStartTimeInSeconds == 0 or item.ModifiedDate is None or item.ModifiedDate < self.botStartTime:
                    continue

                datagrid.insertRow(row_number)
                s = item.Symbol
                k = 0

                datagrid.setItem(row_number, k, QTableWidgetItem(str(item.MarketId)))
                k = k + 1

                # datagrid.setItem(row_number, k, QTableWidgetItem(str(item.Symbol)))
                # k = k + 1

                btnLink = QLabel()
                btnLink.setText(
                    '<a style="color:#d8c569; text-decoration:none;" href="https://tradingview.com/chart?symbol=BITTREX:' + str(
                        item.Symbol.replace("-", "")) + '"> ' + str(item.Symbol) + '</a>')
                index = QtCore.QPersistentModelIndex(datagrid.model().index(row_number, k))
                btnLink.linkActivated.connect(self.openLink)
                datagrid.setCellWidget(row_number, k, btnLink)
                k = k + 1

                datagrid.setItem(row_number, k, QTableWidgetItem(self.formatPrice(s, item.LastPrice)))
                k = k + 1

                updateStr = ""
                if item.ModifiedDate is not None:
                    dateDiff = datetime.now() - item.ModifiedDate
                    if dateDiff.seconds < 10000:
                        updateStr = str(dateDiff.seconds) + " sec."
                datagrid.setItem(row_number, k, QTableWidgetItem(str(updateStr)))
                k = k + 1

                datagrid.setItem(row_number, k, QTableWidgetItem("Params"))
                k = k + 1

                datagrid.setItem(row_number, k, QTableWidgetItem(str(item.R_ROC_Value)))
                if item.R_ROC_Signal:
                    datagrid.item(row_number, k).setBackground(QBrush(self.trueColor))
                else:
                    datagrid.item(row_number, k).setBackground(QBrush(self.falseColor))
                k = k + 1

                datagrid.setItem(row_number, k, QTableWidgetItem(self.formatPrice(s, item.R_MPT_Value)))
                if item.LastPrice > item.R_MPT_Value:
                    datagrid.item(row_number, k).setBackground(QBrush(self.trueColor))
                else:
                    datagrid.item(row_number, k).setBackground(QBrush(self.falseColor))
                k = k + 1

                # datagrid.setItem(row_number, k, QTableWidgetItem(str(item.R_NV_BuyPercent)))
                # if item.R_NV_Signal:
                #    datagrid.item(row_number, k).setBackground(QBrush(self.trueColor))
                # k = k + 1

                # datagrid.setItem(row_number, k, QTableWidgetItem(str(format(item.R_NV_NetVolume, '.2f'))))
                # if item.R_NV_Signal or item.F_NV_Signal:
                #    datagrid.item(row_number, k).setBackground(QBrush(self.trueColor))
                # k = k + 1

                # datagrid.setItem(row_number, k, QTableWidgetItem(str(item.F_ROC_Value)))
                # if item.F_ROC_Signal:
                #    datagrid.item(row_number, k).setBackground(QBrush(self.trueColor))
                # k = k + 1

                # nvSellStr = str(item.R_NV_SellPercent)
                # if item.R_NV_SellPercent > 0:
                #    nvSellStr = "-" + str(item.R_NV_SellPercent)
                # datagrid.setItem(row_number, k, QTableWidgetItem(nvSellStr))
                # if item.F_NV_Signal:
                #    datagrid.item(row_number, k).setBackground(QBrush(self.trueColor))
                # k = k + 1

                datagrid.setItem(row_number, k, QTableWidgetItem(str(item.Trend_Signal)))

                if item.Trend_Signal:
                    datagrid.item(row_number, k).setBackground(QBrush(self.trueColor))
                else:
                    datagrid.item(row_number, k).setBackground(QBrush(self.falseColor))
                k = k + 1

                datagrid.setItem(row_number, k, QTableWidgetItem(str(item.EMAX_Signal)))
                if item.EMAX_Signal:
                    datagrid.item(row_number, k).setBackground(QBrush(self.trueColor))
                else:
                    datagrid.item(row_number, k).setBackground(QBrush(self.falseColor))
                k = k + 1

                datagrid.setItem(row_number, k, QTableWidgetItem(str(item.VSTOP_Signal)))
                if item.VSTOP_Signal:
                    datagrid.item(row_number, k).setBackground(QBrush(self.trueColor))
                else:
                    datagrid.item(row_number, k).setBackground(QBrush(self.falseColor))
                k = k + 1

                datagrid.setItem(row_number, k, QTableWidgetItem(str(item.S_ROC_Value)))
                if item.S_ROC_Signal:
                    datagrid.item(row_number, k).setBackground(QBrush(self.trueColor))
                else:
                    datagrid.item(row_number, k).setBackground(QBrush(self.falseColor))
                k = k + 1

                # datagrid.setItem(row_number, k, QTableWidgetItem(str(item.S_Rsi_Value)))
                # if item.S_Rsi_Signal:
                #    datagrid.item(row_number, k).setBackground(QBrush(self.trueColor))
                # k = k + 1

                # datagrid.setItem(row_number, k, QTableWidgetItem(str(item.S_Stoch_Value)))
                # if item.S_Stoch_Signal:
                #    datagrid.item(row_number, k).setBackground(QBrush(self.trueColor))
                # k = k + 1

                datagrid.setItem(row_number, k, QTableWidgetItem(str(item.R_Signal)))
                if item.R_Signal:
                    datagrid.item(row_number, k).setBackground(QBrush(self.trueColor))
                else:
                    datagrid.item(row_number, k).setBackground(QBrush(self.falseColor))
                k = k + 1

                # datagrid.setItem(row_number, k, QTableWidgetItem(str(item.F_Signal)))
                # if item.F_Signal:
                #    datagrid.item(row_number, k).setBackground(QBrush(self.trueColor))
                # else:
                #    datagrid.item(row_number, k).setBackground(QBrush(self.falseColor))
                # k = k + 1

                datagrid.setItem(row_number, k, QTableWidgetItem(str(item.S_Signal)))
                if item.S_Signal:
                    datagrid.item(row_number, k).setBackground(QBrush(self.trueColor))
                else:
                    datagrid.item(row_number, k).setBackground(QBrush(self.falseColor))

                row_number += 1
        except:
            self.printLog("Exception: initScannerMarketDatagrid", traceback.format_exc())

    def initIndicatorLogDatagrid(self, resultList, datagrid):
        try:
            datagrid.setEditTriggers(QtWidgets.QTableWidget.NoEditTriggers)
            datagrid.setRowCount(0)
            row_number = 0

            datagrid.verticalHeader().hide()

            for i in range(14):
                if i < 3:
                    datagrid.horizontalHeader().setSectionResizeMode(i, QtWidgets.QHeaderView.ResizeToContents)
                else:
                    datagrid.horizontalHeader().setSectionResizeMode(i, QtWidgets.QHeaderView.Stretch)

            trueColor = self.trueColor
            falseColor = self.falseColor

            for item in resultList:
                datagrid.insertRow(row_number)
                s = item.Symbol
                k = 0

                datagrid.setItem(row_number, k, QTableWidgetItem(str(item.Symbol)))
                k = k + 1

                datagrid.setItem(row_number, k, QTableWidgetItem(str(item.CreatedDate)))
                k = k + 1

                datagrid.setItem(row_number, k, QTableWidgetItem(str(item.CandleDate)))
                k = k + 1

                datagrid.setItem(row_number, k, QTableWidgetItem(self.formatPrice(s, item.CurrentPrice)))
                k = k + 1

                datagrid.setItem(row_number, k, QTableWidgetItem(str(item.R_ROC_Value)))
                if item.R_ROC_Signal:
                    datagrid.item(row_number, k).setBackground(QBrush(trueColor))
                k = k + 1

                datagrid.setItem(row_number, k, QTableWidgetItem(self.formatPrice(s, item.R_MPT_Value)))
                if item.CurrentPrice > item.R_MPT_Value:
                    datagrid.item(row_number, k).setBackground(QBrush(trueColor))
                k = k + 1

                # datagrid.setItem(row_number, k, QTableWidgetItem(str(item.R_NV_BuyPercent)))
                # if item.R_NV_Signal:
                #    datagrid.item(row_number, k).setBackground(QBrush(trueColor))
                # k = k + 1

                # datagrid.setItem(row_number, k, QTableWidgetItem(str(format(item.R_NV_NetVolume, '.2f'))))
                # if item.R_NV_Signal or item.F_NV_Signal:
                #    datagrid.item(row_number, k).setBackground(QBrush(trueColor))
                # k = k + 1

                # datagrid.setItem(row_number, k, QTableWidgetItem(str(item.F_ROC_Value)))
                # if item.F_ROC_Signal:
                #    datagrid.item(row_number, k).setBackground(QBrush(trueColor))
                # k = k + 1

                # nvSellStr = str(item.R_NV_SellPercent)
                # if item.R_NV_SellPercent > 0:
                #    nvSellStr = "-" + str(item.R_NV_SellPercent)
                # datagrid.setItem(row_number, k, QTableWidgetItem(nvSellStr))
                # if item.F_NV_Signal:
                #    datagrid.item(row_number, k).setBackground(QBrush(trueColor))
                # k = k + 1

                datagrid.setItem(row_number, k, QTableWidgetItem(str(item.Trend_Signal)))
                if item.Trend_Signal:
                    datagrid.item(row_number, k).setBackground(QBrush(trueColor))
                else:
                    datagrid.item(row_number, k).setBackground(QBrush(falseColor))
                k = k + 1

                datagrid.setItem(row_number, k, QTableWidgetItem(str(item.EMAX_Signal)))
                if item.EMAX_Signal:
                    datagrid.item(row_number, k).setBackground(QBrush(trueColor))
                else:
                    datagrid.item(row_number, k).setBackground(QBrush(falseColor))
                k = k + 1

                datagrid.setItem(row_number, k, QTableWidgetItem(str(item.VSTOP_Signal)))
                if item.VSTOP_Signal:
                    datagrid.item(row_number, k).setBackground(QBrush(trueColor))
                else:
                    datagrid.item(row_number, k).setBackground(QBrush(falseColor))
                k = k + 1

                datagrid.setItem(row_number, k, QTableWidgetItem(str(item.S_ROC_Value)))
                if item.S_ROC_Signal:
                    datagrid.item(row_number, k).setBackground(QBrush(trueColor))
                k = k + 1

                # datagrid.setItem(row_number, k, QTableWidgetItem(str(item.S_Rsi_Value)))
                # if item.S_Rsi_Signal:
                #    datagrid.item(row_number, k).setBackground(QBrush(trueColor))
                # k = k + 1

                # datagrid.setItem(row_number, k, QTableWidgetItem(str(item.S_Stoch_Value)))
                # if item.S_Stoch_Signal:
                #    datagrid.item(row_number, k).setBackground(QBrush(trueColor))
                # k = k + 1

                datagrid.setItem(row_number, k, QTableWidgetItem(str(item.R_Signal)))
                if item.R_Signal:
                    datagrid.item(row_number, k).setBackground(QBrush(trueColor))
                else:
                    datagrid.item(row_number, k).setBackground(QBrush(falseColor))
                k = k + 1

                # datagrid.setItem(row_number, k, QTableWidgetItem(str(item.F_Signal)))
                # if item.F_Signal:
                #    datagrid.item(row_number, k).setBackground(QBrush(trueColor))
                # else:
                #    datagrid.item(row_number, k).setBackground(QBrush(falseColor))
                # k = k + 1

                datagrid.setItem(row_number, k, QTableWidgetItem(str(item.S_Signal)))
                if item.S_Signal:
                    datagrid.item(row_number, k).setBackground(QBrush(trueColor))
                else:
                    datagrid.item(row_number, k).setBackground(QBrush(falseColor))
                k = k + 1

                datagrid.setItem(row_number, k, QTableWidgetItem(str(item.R_Open_Count)))
                k = k + 1

                # datagrid.setItem(row_number, k, QTableWidgetItem(str(item.F_Open_Count)))
                # k = k + 1

                datagrid.setItem(row_number, k, QTableWidgetItem(str(item.S_Open_Count)))
                k = k + 1

                row_number += 1

        except:
            self.printLog("Exception: initIndicatorLogDatagrid", traceback.format_exc())

    def printLog(self, shortLog, longLog="", logToDb=True):
        try:
            print(shortLog, longLog)
            if logToDb:
                self.insertBotLog(shortLog, longLog)
        except:
            self.printLog("Exception: printLog", traceback.format_exc())

    def insertBotLog(self, shortLog, longLog):
        try:
            dnBotLog = DNBotLog()
            botLog = BotLog()
            botLog.ShortLog = shortLog
            botLog.LongLog = longLog
            botLog.CreatedDate = datetime.now()
            dnBotLog.insertBotLog(botLog)
        except:
            self.printLog("Exception: insertBotLog", traceback.format_exc())

    def keyPressEvent(self, event):
        if event.key() == QtCore.Qt.Key_D:
            self.chkShowDetailColumns.setChecked(not self.chkShowDetailColumns.isChecked())

        event.accept()

    def closeApp(self):
        try:
            self.swt.exit()
        except:
            self.printLog("Exception: closeApp", traceback.format_exc())

    def openLink(self, linkUrl):
        QDesktopServices.openUrl(QUrl(linkUrl))

    def launchSecondWindow(self, parent):
        current_env = getattr(Config, 'CURRENT_ENVIRONMENT', 'test')
        # if current_env == 'test':
        #    return

        if self.isOptimizationMode():
            if parent is None:
                self.dialog = Main(self)
                self.dialog.show()
                self.tabMainMenu.removeTab(6)
            else:
                self.tabMainMenu.removeTab(0)
                self.tabMainMenu.removeTab(0)
                self.tabMainMenu.removeTab(0)
                self.tabMainMenu.removeTab(0)
                self.tabMainMenu.removeTab(0)
                self.tabMainMenu.removeTab(0)
                self.tabMainMenu.setCurrentWidget(self.tabMainMenu.findChild(QWidget, "tabOptimizer"))
        """
        else:
            if parent is None:
                self.dialog = Main(self)
                self.dialog.show()
            #opens second window with stats and history
            
            else:
                self.tabMainMenu.removeTab(0)
                self.tabMainMenu.removeTab(2)
                self.tabMainMenu.removeTab(2)
                self.tabMainMenu.removeTab(2)
                self.tabMainMenu.removeTab(2)
                self.tabMainMenu.setCurrentWidget(self.tabMainMenu.findChild(QWidget, "tabTradeHistory"))
        """

    def hideStrategy1Controls(self):
        self.lblNvEnabled.hide()
        self.drpNvEnabled.hide()

        self.lblRocPeriodF.hide()
        self.txtRocPeriodF.hide()

        self.txtRocFBuyDecreasePercentage.hide()
        self.lblRocFBuyDecreasePercentage.hide()

        self.drpRocAppliedPriceF.hide()
        self.lblRocAppliedPriceF.hide()

        self.lblF_TradingEnabled_2.hide()
        self.drpF_TradingEnabled.hide()
        self.lblF_SL1Percentage_2.hide()
        self.txtF_SL1Percentage.hide()
        self.lblF_SL2Percentage_2.hide()
        self.txtF_SL2Percentage.hide()

        self.lblF_SLTimerInMinutes_2.hide()
        self.txtF_SLTimerInMinutes.hide()
        self.lblF_TSLActivationPercentage_2.hide()
        self.txtF_TSLActivationPercentage.hide()
        self.lblF_TSLTrailPercentage_2.hide()
        self.txtF_TSLTrailPercentage.hide()

        self.lblNvIncreasePercentage.hide()
        self.txtNvIncreasePercentage.hide()
        self.lblNvMinNetVolume.hide()
        self.txtNvMinNetVolume.hide()

        self.lblSELL_RSI_Src.hide()
        self.drpSELL_RSI_Src.hide()
        self.lblSELL_RSI_Period.hide()
        self.txtSELL_RSI_Period.hide()
        self.lblSELL_RSI_UpperLevel.hide()
        self.txtSELL_RSI_UpperLevel.hide()
        self.lblSELL_RSI_LowerLevel.hide()
        self.txtSELL_RSI_LowerLevel.hide()
        self.lblSELL_Stoch_Src.hide()
        self.drpSELL_Stoch_Src.hide()
        self.lblSELL_Stoch_KPeriod.hide()
        self.txtSELL_Stoch_KPeriod.hide()
        self.lblSELL_Stoch_DPeriod.hide()
        self.txtSELL_Stoch_DPeriod.hide()
        self.lblSELL_Stoch_Slowing.hide()
        self.txtSELL_Stoch_Slowing.hide()
        self.lblSELL_Stoch_UpperLevel.hide()
        self.txtSELL_Stoch_UpperLevel.hide()
        self.lblSELL_Stoch_LowerLevel.hide()
        self.txtSELL_Stoch_LowerLevel.hide()

        self.lblSPCEnabled.hide()
        self.txtTargetPercentage.hide()
        self.lblPullbackEntryPercentage.hide()
        self.txtPullbackEntryPercentage.hide()
        self.lblPullbackEntryWaitTimeInSeconds.hide()
        self.txtPullbackEntryWaitTimeInSeconds.hide()


Main.window = None


def main():
    app = QApplication(sys.argv)
    app.aboutToQuit.connect(aboutToQuitHandler)
    Main.window = Main()
    Main.window.show()
    app.exec_()


def aboutToQuitHandler():
    print("App is closing...")
    Main.window.closeApp()


if __name__ == '__main__':
    main()
    # client = ExchangeClient(ExchangeType.BITTREX,
    #                         api_key=b'5a34baff06d241ada579f037af058b34',
    #                         api_secret=b'850367c7534f4b928b1039a5db66d09d')
    # print(*client.get_markets(["BTC"]), sep="\n")
    # daily = client.get_market_daily_summary("BTC-USDT")
    # print(daily)
    # print(*client.get_asset_balances(), sep="\n")
    # print(client.get_asset_balance("BTC"))
    # candles = client.get_candles_historical("BTC-USDT", "1h", start_time=1616492221000, end_time=1621772206000)
    # print(len(candles))
    # print(*candles, sep="\n")

# self.tabSubmenu.setStyleSheet("background-color: #595959");

# These maybe needed to make the table compact
# self.tblTrades.resizeRowsToContents()
# self.tblTrades.verticalHeader().setDefaultSectionSize(self.tblTrades.rowHeight(0))


# Add edit image to button
# btnEdit.setFixedWidth(35)
# btnEdit.setFixedHeight(30)
# pixmap = QPixmap("UI/edit.png")
# buttonIcon = QIcon(pixmap)
# btnEdit.setIcon(buttonIcon)
# btnEdit.setIconSize(pixmap.rect().size() / 5)

# Add delete button to table
# btnDelete = QPushButton("")
# index = QtCore.QPersistentModelIndex(datagrid.model().index(row_number, 5))
# btnDelete.clicked.connect(
#    lambda *args, index=index: self.onDeleteButtonClicked(index.row(), index.column()))
# datagrid.setCellWidget(row_number, 5, btnDelete)

# Add delete image to button
# btnDelete.setFixedWidth(35)
# btnDelete.setFixedHeight(30)
# pixmapD = QPixmap("UI/delete.png")
# buttonIconD = QIcon(pixmapD)
# btnDelete.setIcon(buttonIconD)
# btnDelete.setIconSize(pixmapD.rect().size() / 5)
