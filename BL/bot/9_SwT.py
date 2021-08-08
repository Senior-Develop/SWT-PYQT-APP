import decimal
from logging import debug

from PyQt5.QtCore import QThread, pyqtSignal

from BL.ExchangeClient import ExchangeClient, ExchangeType

import Config
import operator
import traceback
import time
import numpy
import calendar

from BL.indicator.emax import Emax
from BL.indicator.st import SuperTrend
from BL.indicator.vstop import Vstop
from Common.Asset import Asset

from Common.Backtest import Backtest
from Common.BotLog import BotLog
from Common.CandleData import CandleData
from Common.Constant import ENUM_INDICATOR, ENUM_APPLIED_PRICE, ENUM_ORDER_SIDE
from BL.indicator.rsi import *
from BL.indicator.stoch import *
from BL.indicator.roc import *
from BL.indicator.mpt import *
from BL.indicator.trend import *
from BL.indicator.nv import *
from Common.Exchange.OrderResponse import OrderResponse
from Common.IndicatorLog import IndicatorLog
from Common.Market import Market
from Common.Signal import Signal
from Common.StrategyParameters import StrategyParameters
from Common.TickData import TickData
from Common.Trade import Trade
from Common.TradeLog import TradeLog
from DAL.DNAsset import DNAsset
from DAL.DNBacktest import DNBacktest
from DAL.DNBotLog import DNBotLog
from DAL.DNBotParameters import DNBotParameters
from Common.BotParameters import BotParameters
from DAL.DNCandleData import DNCandleData
from DAL.DNIndicatorLog import DNIndicatorLog
from DAL.DNMarket import DNMarket
from DAL.DNOptimization import DNOptimization
from DAL.DNOptimizationRun import DNOptimizationRun
from DAL.DNQcParameters import DNQcParameters
from DAL.DNSignal import DNSignal
from DAL.DNStrategyParameters import DNStrategyParameters
from DAL.DNTickData import DNTickData
from DAL.DNTrade import DNTrade
from DAL.DNTradeLog import DNTradeLog
from Utils import utils
from pytz import timezone
from datetime import datetime, timedelta
from loguru import logger


TEST_MODE = False  # If set to True no orders will go to the exchange.
MAX_NUMBER_OF_CANDLES_AT_INITIALIZARION = 144  # The number of candles the bot will pull when started. Default was 288
ENABLED_QUOTE_CURRENCIES = []  # Quote symbols to filter markets by. Leave empty to disable filtering.
ALWAYS_GENERATE_ST_LONG_BUY_SIGNAL = False # If set to True the ST indicator will always generate buy signal.
ALWAYS_GENERATE_ST_SHORT_SELL_SIGNAL = False # If set to True the ST indicator will always genereate sell signal for the short strategy.

USE_CPD_TRADE_EXIT = True  # If set to True trades will be closed on CPD.
CPD_EXIT_PERCENT_LONG = -5  # The percent difference threshold for long trades.
CPD_EXIT_PERCENT_SHORT = 5  # The percent difference threshold for short trades.
CPD_OPEN_OPPOSITE = True  # If set to True after a trade is closed by CPD opposite trade will be open.
CPD_PRICE_SOURCE = ENUM_APPLIED_PRICE.PRICE_CLOSE  # Price source used by CPD.

logger.add('debug_logs/swt-{time}.log')
logger.info(f'Running in test mode: {TEST_MODE}')
logger.info(f'Running on selected quote currencies: {ENABLED_QUOTE_CURRENCIES or False}')
logger.info(f'Always generate ST long buy signal: {ALWAYS_GENERATE_ST_LONG_BUY_SIGNAL}')
logger.info(f'Always generate ST short sell signal: {ALWAYS_GENERATE_ST_SHORT_SELL_SIGNAL}')
logger.info(f'Use CPD to exit trades: {USE_CPD_TRADE_EXIT}')
if USE_CPD_TRADE_EXIT:
    logger.info(f'CPD exit percent long: {CPD_EXIT_PERCENT_LONG}')
    logger.info(f'CPD exit percent short: {CPD_EXIT_PERCENT_SHORT}')
    logger.info(f'CPD price source: {CPD_PRICE_SOURCE}')
    logger.info(f'CPD open opposite: {CPD_OPEN_OPPOSITE}')


def check_trade_exit_on_cpd(candles, trade, cpd_price_source, cpd_exit_percent_long, cpd_exit_percent_short):
    '''Checks if a trade should exit based on CPD.
        Args:
        candles (list): Candles list.
        trade (trade): Trade object.
        cpd_price_source (str): One of Open, Close, High, Low, HL2, HLC3
        cpd_exit_percent_long (float): Percent change to exit long trades at.
        cpd_exit_percent_short (float): Percent change to exit short trades at.

        Return: bool
    '''

    if cpd_price_source == ENUM_APPLIED_PRICE.HL2:
        high = numpy.array([candle.get_price(ENUM_APPLIED_PRICE.HIGH) for candle in candles])
        low = numpy.array([candle.get_price(ENUM_APPLIED_PRICE.LOW) for candle in candles])
        price = (high + low) / 2
    elif cpd_price_source == ENUM_APPLIED_PRICE.HLC3:
        high = numpy.array([candle.get_price(ENUM_APPLIED_PRICE.HIGH) for candle in candles])
        low = numpy.array([candle.get_price(ENUM_APPLIED_PRICE.LOW) for candle in candles])
        close = numpy.array([candle.get_price(ENUM_APPLIED_PRICE.CLOSE) for candle in candles])
        price = (high + low + close) / 3
    else:
        price = numpy.array([candle.get_price(cpd_price_source) for candle in candles])

    diff = ((price[-1] - price[-2]) / price[-1]) * 100
    if trade.TradeType == 'Buy':
        return diff > cpd_exit_percent_long
    elif trade.TradeType == 'Sell':
        return diff < cpd_exit_percent_short


class SwT(QThread):
    trading_lock = False
    client = None
    exchange_type = ExchangeType.BITTREX
    interval = "1m"
    markets = None
    market_state = {} #this is being shared among threads
    market_state_test = {}
    bot_parameters = None
    strategy_parameters = None
    strategy_parameters_default = None
    strategy_parameters_list = {}
    qc_parameters_btc = None
    qc_parameters_usdt = None
    qc_parameters_eth = None
    qc_parameters_bnb = None
    quoteAssets = ""

    SLTimerInMinutes = 0
    SL1Percentage = 0
    SL2Percentage = 0
    SLTimerInMinutes = 0
    TSLActivationPercentage = 0
    TSLTrailPercentage = 0

    TargetPercentage = 0
    RebuyTimeInSeconds = 0
    RebuyPercentage = 0
    RebuyMaxLimit = 0
    PullbackEntryPercentage = 0
    PullbackEntryWaitTimeInSeconds = 0
#	CommissionPercentage = decimal.Decimal(0.015) #binance
    CommissionPercentage = decimal.Decimal(0.15) #bittrex

    entryEnabled = True
    isRunning = False
    dataCollectorRunning = False
    dataCollectorModeEnabled = False

    # backtest / optimization
    backtestRunning = False
    backtestModeEnabled = False
    updateMarketsForOptimization = False
    btTimeframe = "1m"
    btStartDate = None
    btEndDate = None
    btSymbol = ""
    downloadCandleOnly = False
    btTradeQuoteAmount = decimal.Decimal(0.001)
    backtestId = 0
    optimizationId = 0
    optimizationRunId = 0
    optimizationRunning = False

    swtUpdate = pyqtSignal(str)
    swtUpdateBacktest = pyqtSignal(str)
    swtUpdateOpt = pyqtSignal(str)

    swtMarketUpdateProgress = pyqtSignal(int)
    swtCandleUpdateProgress = pyqtSignal(int)
    swtCandleDownloadProgress = pyqtSignal(int)

    btcTrending = False
    btcTrendingPrev = False

    indicators = {
        ENUM_INDICATOR.ROC: None,
        ENUM_INDICATOR.MPT: None,
        ENUM_INDICATOR.TREND: None,
        ENUM_INDICATOR.NV: None,
        ENUM_INDICATOR.EMAX: None,
        ENUM_INDICATOR.VSTOP: None,
    }

    def __init__(self):
        try:
            QThread.__init__(self)
        except:
            self.printLog("Exception: __init__", traceback.format_exc())


    def run(self):
        try:
            if self.dataCollectorModeEnabled:
                self.startDataCollector()
            elif self.backtestModeEnabled:
                self.startBacktesterOptimizer()
            elif self.updateMarketsForOptimization:
                self.startMarketUpdateForOptimization()
            else:
                self.startBot()

        except:
            self.printLog("Exception: run", traceback.format_exc())

    def setInterval(self, interval):
        try:
            self.interval = interval
        except:
            self.printLog("Exception: setInterval", traceback.format_exc())

    def setBacktestParams(self, btTimeframe, btStartDate, btEndDate, btSymbol, downloadCandleOnly, optimizationId, optimizationRunId):
        try:
            self.btTimeframe = btTimeframe
            self.btStartDate = btStartDate
            self.btEndDate = btEndDate
            self.btSymbol = btSymbol
            self.downloadCandleOnly = downloadCandleOnly
            self.optimizationId = optimizationId
            self.optimizationRunId = optimizationRunId

            # round start/end dates to candle times
            minutes = 1
            if btTimeframe == "5m":
                minutes = 5
            elif btTimeframe == "15m":
                minutes = 15
            elif btTimeframe == "30m":
                minutes = 30
            elif btTimeframe == "1h":
                minutes = 60
            elif btTimeframe == "4h":
                minutes = 240
            elif btTimeframe == "1d":
                minutes = 1440

            while self.btStartDate.minute % minutes != 0:
                self.btStartDate = self.btStartDate + timedelta(minutes=1)

            while self.btEndDate.minute % minutes != 0:
                self.btEndDate = self.btEndDate - timedelta(minutes=1)

            self.btStartDate = self.btStartDate.replace(second=0, microsecond=0)
            self.btEndDate = self.btEndDate.replace(second=0, microsecond=0)

            self.btStartDate = self.convertLocalDateToBinanceDate(self.btStartDate)
            self.btEndDate = self.convertLocalDateToBinanceDate(self.btEndDate)

        except:
            self.printLog("Exception: setBacktestParams", traceback.format_exc())


    def selectStrategyParametersForSymbol(self, symbol):

        # if this switch is false, dont use optimized parameters
        if not self.bot_parameters.optUpdateStrategyParameters:
            #print(symbol + ": Using Trader Parameters")
            return self.strategy_parameters_default

        dnStrategyParameters = DNStrategyParameters()
        sp = dnStrategyParameters.getStrategyParametersBySymbolForTrader(self.interval, symbol)
        if sp is not None:
            #print(symbol + ": Using Optimized Parameters")
            return sp

        #print(symbol + ": Using Trader Parameters")
        return self.strategy_parameters_default

    def startBot(self):
        try:
            self.isRunning = True

            # get bot parameters from DB
            self.printLog("Getting bot parameters from DB")
            dnBotParameters = DNBotParameters()
            self.bot_parameters = dnBotParameters.getBotParameters()

            # get strategy parameters from DB
            self.printLog("Getting strategy parameters from DB")
            dnStrategyParameters = DNStrategyParameters()

            self.strategy_parameters_default = dnStrategyParameters.getStrategyParametersBySymbolForTrader(self.interval, "")
            self.strategy_parameters = dnStrategyParameters.getStrategyParametersBySymbolForTrader(self.interval, "")
            self.setupIndicators(self.strategy_parameters_default)

            # get strategy parameters from DB
            self.printLog("Getting qc parameters from DB")
            dnQcParameters = DNQcParameters()
            self.qc_parameters_btc = dnQcParameters.getQcParameters("BTC")
            self.qc_parameters_usdt = dnQcParameters.getQcParameters("USDT")
            self.qc_parameters_eth = dnQcParameters.getQcParameters("ETH")
            self.qc_parameters_bnb = dnQcParameters.getQcParameters("BNB")
            self.quoteAssets = self.getQuoteAssets()

            if not self.validateParameters():
                self.printLog("Parameter validation failed. Bot will not start.")
                return False

            # init client api
            self.printLog("Initializing ExchangeClient Api.")
            self.client = ExchangeClient(self.exchange_type, self.bot_parameters.apiKey, self.bot_parameters.secretKey)

            # update assets from client wallet
            self.updateAssets()

            # update market symbols and filters daily
            self.printLog("Updating markets.")
            self.updateMarkets()

            # update market eligibility by checking their volume
            self.printLog("Updating market eligibility.")
            self.updateMarketEligibility()

            # get markets that will be traded
            self.printLog("Getting markets that will be traded.")
            dnMarket = DNMarket()
            if self.bot_parameters.runOnSelectedMarkets:
                self.printLog("Bot will run on selected markets only.")
                self.markets = dnMarket.listSelectedMarkets()
                self.printLog("Running on selected markets: " + str(len(self.markets)))
            else:
                self.printLog("Bot will run on all markets.")
                self.markets = dnMarket.listTradeableMarkets()
                self.printLog("Running on all markets: " + str(len(self.markets)))

            if len(self.markets) == 0:
                self.printLog("Market number is 0. Bot will not start.")
                return False

            if ENABLED_QUOTE_CURRENCIES:
                self.markets = [m for m in self.markets if m.QuoteAsset in ENABLED_QUOTE_CURRENCIES]
                logger.debug(f'Limited markets to quote currencies. Running on {len(self.markets)} markets')


            # make qc buys
            self.makeQcBuys()

            # create and setup indicators enabled by the parameters
            self.setupIndicators(self.strategy_parameters)

            # get limit number of previous candle data for all observed markets
            self.printLog("Initializing initial candles")
            maxCandleNumber = self.computeMaxCandleNumber()
            self.fillInitialCandleData(maxCandleNumber)

            # # start web sockets
            self.printLog("Starting web sockets")
            self.startWebSockets()

            # self.test_signals()

            return True
        except:
            self.printLog("Exception: start", traceback.format_exc())
            return False

    def startBacktester1(self):
        # get bot parameters from DB
        self.printLog("Getting bot parameters from DB")
        dnBotParameters = DNBotParameters()
        self.bot_parameters = dnBotParameters.getBotParameters()

        # get strategy parameters from DB
        self.printLog("Getting strategy parameters from DB")
        dnStrategyParameters = DNStrategyParameters()

        # self.strategy_parameters = dnStrategyParameters.listStrategyParameters(self.interval)
        # self.strategy_parameters = dnStrategyParameters.getStrategyParametersForBacktester(self.btTimeframe)
        self.strategy_parameters = dnStrategyParameters.getStrategyParameters(self.btTimeframe, "min", 0)
        self.strategy_parameters = dnStrategyParameters.set(self.strategy_parameters, True)

        # get qc parameters from DB
        self.printLog("Getting qc parameters from DB")
        dnQcParameters = DNQcParameters()
        self.qc_parameters_btc = dnQcParameters.getQcParameters("BTC")
        self.qc_parameters_usdt = dnQcParameters.getQcParameters("USDT")
        self.qc_parameters_eth = dnQcParameters.getQcParameters("ETH")
        self.qc_parameters_bnb = dnQcParameters.getQcParameters("BNB")
        self.quoteAssets = self.getQuoteAssets()

        if not self.validateParameters():
            self.printLog("Parameter validation failed. Backtester will not start.")
            return False

        # converted backtester/optimizer to work with a single symbol.
        if self.btSymbol == "":
            self.printLog("Please input a symbol name. Backtester will not start.")
            return False

        # init client api to download candles
        self.printLog("Initializing Client Api.")
        self.client = ExchangeClient(self.exchange_type, self.bot_parameters.apiKey, self.bot_parameters.secretKey)

        return True

    def startBacktesterOptimizer(self):
        try:
            # get bot parameters from DB
            self.printLog("Getting bot parameters from DB")
            dnBotParameters = DNBotParameters()
            self.bot_parameters = dnBotParameters.getBotParameters()

            # get strategy parameters from DB
            self.printLog("Getting strategy parameters from DB")
            dnStrategyParameters = DNStrategyParameters()

            self.strategy_parameters = dnStrategyParameters.getStrategyParameters(self.btTimeframe, "min", 0)
            if self.strategy_parameters is None:
                self.printLog("Please set parameters for this timeframe. Backtester/Optimizer will not start.")
                return False

            self.strategy_parameters = dnStrategyParameters.set(self.strategy_parameters, True)

            # converted backtester/optimizer to work with a single symbol.
            if self.btSymbol == "":
                self.printLog("Please input a symbol name. Backtester/Optimizer will not start.")
                return False

            # get markets
            dnMarket = DNMarket()

            market = dnMarket.getMarketBySymbol(self.btSymbol)
            if market is None:
                self.printLog("Market cannot be found. Backtester/Optimizer will not start.")
                return False

            self.markets = []
            self.markets.append(market)

            # get limit number of previous candle data for all observed markets
            self.printLog("Initializing initial candles")
            maxCandleNumber = self.computeMaxCandleNumber()

            #self.fillInitialCandleDataForBacktest(maxCandleNumber)
            self.downloadCandleData(maxCandleNumber)

            # if backtest mode, run backtest
            if not self.downloadCandleOnly:

                for market in self.markets:
                    # if backtest
                    if self.optimizationId == 0:
                        spList = []
                        spList.append(self.strategy_parameters)
                        self.runBacktest(market.Symbol, spList)
                        #self.runBacktest(market.Symbol)

                    # if optimization
                    else:
                        self.runBacktest(market.Symbol)

                if self.optimizationRunId > 0:
                    self.optimizationRunning = True
                else:
                    self.backtestRunning = True

            return True
        except:
            self.printLog("Exception: StartBacktester", traceback.format_exc())
            return False

    def convertTickDataToCandle(self, tickData):
        try:
            candle = Candle()
            candle.symbol = tickData.Symbol
            candle.interval = tickData.Timeframe
            candle.close = tickData.Close
            candle.open = tickData.Open
            candle.high = tickData.High
            candle.low = tickData.Low
            candle.open_time = datetime.timestamp(tickData.OpenTime) * 1000
            candle.close_time = datetime.timestamp(tickData.CloseTime) * 1000
            candle.num_trades = tickData.NumTrades
            candle.volume = tickData.Volume
            candle.quote_asset_volume = tickData.QuoteAssetVolume
            candle.taker_buy_base_asset_volume = tickData.TakerBuyBaseAssetVolume
            candle.taker_buy_quote_asset_volume = tickData.TakerBuyQuoteAssetVolume
            candle.event_time = datetime.timestamp(tickData.EventTime) * 1000

            return candle

        except:
            self.printLog("Exception: convertTickDataToCandle", traceback.format_exc())

    def convertCandleDataListToCandleList(self, candleDataList):
        try:
            candleList = []
            for candleData in candleDataList:
                candle = Candle()
                candle.symbol = candleData.Symbol
                candle.interval = candleData.Timeframe
                candle.close = candleData.Close
                candle.open = candleData.Open
                candle.high = candleData.High
                candle.low = candleData.Low
                candle.open_time = candleData.OpenTimeInMillis
                candle.close_time = candleData.CloseTimeInMillis
                candle.num_trades = candleData.NumTrades
                candle.volume = candleData.Volume
                candle.quote_asset_volume = candleData.QuoteAssetVolume
                candle.taker_buy_base_asset_volume = candleData.TakerBuyBaseAssetVolume
                candle.taker_buy_quote_asset_volume = candleData.TakerBuyQuoteAssetVolume
                candle.event_time = candleData.CloseTimeInMillis
                candleList.append(candle)

            return candleList

        except:
            self.printLog("Exception: convertCandleDataListToCandleList", traceback.format_exc())

    def insertCandleDataList(self, candleList):
        try:
            dnCandleData = DNCandleData()

            if candleList is None:
                print("Candle list is empty. Cant insert.")
                return

            for candle in candleList:
                c = dnCandleData.getCandleData(candle.symbol, candle.interval, candle.open_time)
                if c is not None:
                    continue

                if not candle.is_closed:
                    print("candle not closed", candle)
                    continue


                candleData = CandleData()

                candleData.Symbol = candle.symbol
                candleData.Timeframe = candle.interval
                candleData.Close = candle.close
                candleData.Open = candle.open
                candleData.High = candle.high
                candleData.Low = candle.low
                candleData.OpenTime = datetime.fromtimestamp(candle.open_time / 1000, timezone('Etc/GMT0'))
                candleData.CloseTime = datetime.fromtimestamp(candle.close_time / 1000, timezone('Etc/GMT0'))
                candleData.OpenTimeInMillis = candle.open_time
                candleData.CloseTimeInMillis = candle.close_time
                candleData.NumTrades = candle.num_trades
                candleData.Volume = candle.volume
                candleData.QuoteAssetVolume = candle.quote_asset_volume
                candleData.TakerBuyBaseAssetVolume = candle.taker_buy_base_asset_volume
                candleData.TakerBuyQuoteAssetVolume = candle.taker_buy_quote_asset_volume
                candleData.CreatedDate = datetime.now()

                dnCandleData.insertCandleData(candleData)

        except:
            self.printLog("Exception: insertCandleDataList", traceback.format_exc())


    def updateOptimizationRunStatus(self, status):
        try:
            if self.optimizationRunId == 0:
                return

            dnOptimizationRun = DNOptimizationRun()
            optimizationRun = dnOptimizationRun.getOptimizationRun(self.optimizationRunId)
            if not optimizationRun:
                return

            optimizationRun.State = status
            dnOptimizationRun.updateOptimizationRun(optimizationRun)

        except:
            self.printLog("Exception: updateOptimizationRunStatus", traceback.format_exc())

    def broadcastMessage(self, message):
        try:
            if self.optimizationRunId > 0:
                self.swtUpdateOpt.emit(str(self.optimizationRunId) + ";" + message)
            else:
                self.swtUpdateBacktest.emit(message)
        except:
            self.printLog("Exception: broadcastMessage", traceback.format_exc())


    def runBacktestForSp(self, symbol, sp, propertyName, candlesInitial, candles):
        dnStrategyParameters = DNStrategyParameters()
        self.strategy_parameters = dnStrategyParameters.set(sp, True)

        #print(symbol)
        #print(propertyName)
        #print(len(candlesInitial))
        #print(len(candles))

        # burada clearden sonra baslangic candleindan 1 onceki candleddan geriye dogru ne kdr donwload ettiysem hepsini alip state in icine koymam lazim.

        key = (symbol, self.btTimeframe)
        if key in self.market_state.keys():
            self.market_state[key].clear()

        self.market_state[key] = candlesInitial


        optProgressText = ""
        if self.optimizationId > 0:
            optProgressText = propertyName + ": " + str(getattr(sp, propertyName)) + "  "


        self.setupIndicators(self.strategy_parameters)

        spId = dnStrategyParameters.insertStrategyParameters(sp)

        # insert new backtest here
        dnBacktest = DNBacktest()
        backtest = Backtest()
        backtest.CreatedDate = datetime.now()
        backtest.StartDate = self.convertBinanceDateToLocalDate(self.btStartDate)
        backtest.EndDate = self.convertBinanceDateToLocalDate(self.btEndDate)
        # backtest.TickCount = len(tickDataList)
        backtest.TickCount = len(candles)
        backtest.Symbol = symbol
        backtest.Timeframe = self.btTimeframe
        backtest.OptimizationRunId = self.optimizationRunId
        backtest.Params = self.convertStrategyParametersToString(sp)
        backtest.SpId = spId
        #backtest.SpCount = spCount
        #backtest.SpIndex = spIndex

        backtestId = dnBacktest.insertBacktest(backtest)
        self.backtestId = backtestId

        # running backtest

        tic = time.time()
        candleIndex = 1
        for candle in candles:
            tickProgressText = "Candles: " + str(candleIndex) + " / " + str(len(candles))
            if self.optimizationRunId > 0:
                self.broadcastMessage(optProgressText + tickProgressText)

            self.onTickBacktest(candle)
            candleIndex = candleIndex + 1

        toc = time.time()
        self.printLog("Duration: " + str(int(toc - tic)) + " for BtId: " + str(backtestId))

        durationInMinutes = float(toc - tic) / 60
        #durationInMinutesForOpt = durationInMinutesForOpt + durationInMinutes

        # update backtest stats here
        self.computeBacktestStats(backtestId, durationInMinutes)

        #only in backtest mode
        if self.optimizationId == 0:
            self.broadcastMessage("Backtest finished for " + symbol + ". Time:" + str(int(toc - tic)) + " sec.")

        # record success rate of sp
        bt = dnBacktest.getBacktest(backtestId)
        return bt.PLPercentage

    #oktar
    def runBacktest(self, symbol):
        try:
            self.broadcastMessage("Fetching candle data for " + symbol)

            dnCandleData = DNCandleData()
            candleDataList = dnCandleData.listCandleData(symbol, self.btTimeframe, self.btStartDate, self.btEndDate)

            if not candleDataList or len(candleDataList) == 0:
                print("candleDataList is empty. Cannot continue " + self.btSymbol + ", TF: " + str(self.btTimeframe))
                return symbol

            candles = self.convertCandleDataListToCandleList(candleDataList)
            candlesInitial = self.getInitialCandlesForBacktesterOptimizer(symbol, self.btTimeframe)

            durationInMinutesForOpt = 0
            optStartTime = time.time()

            # here get all sp, for all params, foreach get min,max,step, loop.
            #set selected=min, thenupdate the winning in selected, keep using selected.

            dnStrategyParameters = DNStrategyParameters()
            spMin = dnStrategyParameters.getStrategyParameters(self.btTimeframe, "min", 0)
            spMax = dnStrategyParameters.getStrategyParameters(self.btTimeframe, "max", 0)
            spStep = dnStrategyParameters.getStrategyParameters(self.btTimeframe, "step", 0)

            spSelected = dnStrategyParameters.set(spMin, False)

            spSelected.Name = "selected"
            spSelected.OptimizationId = self.optimizationId

            combinationCount = 0

            for i in range(30):

                propertyName = self.getSpPropertyByIndex(i)
                print(i)
                print(propertyName)

                minValue = getattr(spMin, propertyName)
                maxValue = getattr(spMax, propertyName)
                stepValue = getattr(spStep, propertyName)

                if "AppliedPrice" in propertyName:
                    minValue = int(minValue)
                    maxValue = int(maxValue)
                    stepValue = int(stepValue)

                # step = 0 means that we only use 1 value for this parameter. this parameter is not being optimized.
                if i > 0 and stepValue == 0:
                    print("Fixed parameter. Skipping: " + propertyName)
                    continue

                value = minValue
                bestPlPercentage = 0
                bestValue = value
                while value <= maxValue:
                    setattr(spSelected, propertyName, value)
                    plPercentage = self.runBacktestForSp(symbol, spSelected, propertyName, candlesInitial, candles)
                    combinationCount = combinationCount + 1
                    if plPercentage > bestPlPercentage:
                        bestPlPercentage = plPercentage
                        bestValue = value

                    value = value + stepValue

                    if i == 0 and stepValue == 0:
                        break


                print("Best value: " + propertyName + ":" + str(bestValue))
                setattr(spSelected, propertyName, bestValue)

            optEndTime = time.time()
            optDurationInMinutes = float(optEndTime - optStartTime) / 60

            # log optimization results
            if self.optimizationId > 0:
                dnBacktest = DNBacktest()
                btList = dnBacktest.listBacktestBySuccess(self.optimizationRunId)
                bestSpId = 0
                bestBacktestId = 0
                bestPLPercentage = 0
                if btList:
                    bestSpId = btList[0].SpId
                    bestBacktestId = btList[0].BacktestId
                    bestPLPercentage = btList[0].PLPercentage

                dnOptimizationRun = DNOptimizationRun()
                optimizationRun = dnOptimizationRun.getOptimizationRun(self.optimizationRunId)
                optimizationRun.DurationInMinutes = optDurationInMinutes
                optimizationRun.BestSpId = bestSpId
                optimizationRun.BestBacktestId = bestBacktestId
                optimizationRun.PLPercentage = bestPLPercentage
                optimizationRun.State = "Completed"
                optimizationRun.CombinationCount = combinationCount
                dnOptimizationRun.updateOptimizationRun(optimizationRun)

                self.updateStrategyParameterForSymbolOnTrader(bestSpId, symbol)

                self.broadcastMessage("Completed.")

                self.optimizationRunId = 0

        except:
            self.printLog("Exception: runBacktest", traceback.format_exc())

    #this version is only using the winning param value and skips the rest. constructing splist in main caused memory issues. so i cant use this version when there is too many combos.
    def runBacktest2(self, symbol, spList):
        try:
            self.broadcastMessage("Fetching candle data for " + symbol)

            dnCandleData = DNCandleData()
            candleDataList = dnCandleData.listCandleData(symbol, self.btTimeframe, self.btStartDate, self.btEndDate)

            if not candleDataList or len(candleDataList) == 0:
                print("candleDataList is empty. Cannot continue " + self.btSymbol)
                return symbol

            candles = self.convertCandleDataListToCandleList(candleDataList)
            candlesInitial = self.getInitialCandlesForBacktesterOptimizer(symbol, self.btTimeframe)

            durationInMinutesForOpt = 0
            dnStrategyParameters = DNStrategyParameters()

            # here get all sp, for all params, foreach get min,max,step, loop.
            # set selected=min, thenupdate the winning in selected, keep using selected.

            spIndex = 1
            spCount = len(spList)

            for sp in spList:
                if sp.StrategyParametersId == 0:
                    print("Skipping sp: " + str(spIndex))
                    spIndex = spIndex + 1
                    continue

                self.strategy_parameters = dnStrategyParameters.set(sp, True)

                # burada clearden sonra baslangic candleindan 1 onceki candleddan geriye dogru ne kdr donwload ettiysem hepsini alip state in icine koymam lazim.

                key = (symbol, self.btTimeframe)
                if key in self.market_state.keys():
                    self.market_state[key].clear()

                self.market_state[key] = candlesInitial

                optProgressText = ""
                if self.optimizationId > 0:
                    optProgressText = "Backtests: " + str(spIndex) + " / " + str(len(spList)) + ". "

                self.setupIndicators(self.strategy_parameters)

                # insert new backtest here
                dnBacktest = DNBacktest()
                backtest = Backtest()
                backtest.CreatedDate = datetime.now()
                backtest.StartDate = self.convertBinanceDateToLocalDate(self.btStartDate)
                backtest.EndDate = self.convertBinanceDateToLocalDate(self.btEndDate)
                # backtest.TickCount = len(tickDataList)
                backtest.TickCount = len(candles)
                backtest.Symbol = symbol
                backtest.Timeframe = self.btTimeframe
                backtest.OptimizationRunId = self.optimizationRunId
                backtest.Params = self.convertStrategyParametersToString(sp)
                backtest.SpId = sp.StrategyParametersId
                backtest.SpCount = spCount
                backtest.SpIndex = spIndex

                backtestId = dnBacktest.insertBacktest(backtest)
                self.backtestId = backtestId

                # running backtest

                tic = time.time()
                candleIndex = 1
                for candle in candles:
                    tickProgressText = "Candles: " + str(candleIndex) + " / " + str(len(candles))
                    if self.optimizationRunId > 0:
                        self.broadcastMessage(optProgressText + tickProgressText)

                    self.onTickBacktest(candle)

                    candleIndex = candleIndex + 1

                toc = time.time()
                #self.printLog("Duration: " + str(int(toc - tic)) + " for BtId: " + str(backtestId))

                durationInMinutes = float(toc - tic) / 60
                durationInMinutesForOpt = durationInMinutesForOpt + durationInMinutes

                # update backtest stats here
                self.computeBacktestStats(backtestId, durationInMinutes)

                if self.optimizationId == 0:
                    self.broadcastMessage("Backtest finished for " + symbol + ". Time:" + str(int(toc - tic)) + " sec.")

                # record success rate of sp
                bt = dnBacktest.getBacktest(backtestId)
                sp.PLPercentage = bt.PLPercentage

                if spIndex > 1:
                    parName, parValue = self.getLosingParameter(sp, spPrev)
                    print("getLosingParameter: " + str(parName) + "   " + str(parValue))
                    for sp1 in spList:
                        if sp1.StrategyParametersId == 0:
                            continue

                        if getattr(sp1, parName) == parValue:
                            print("removing sp from list: " + str(sp1.StrategyParametersId))
                            sp1.StrategyParametersId = 0

                if sp.StrategyParametersId > 0:
                    spPrev = dnStrategyParameters.set(sp, False)
                spIndex = spIndex + 1

            # log optimization results
            if self.optimizationId > 0:

                btList = dnBacktest.listBacktestBySuccess(self.optimizationRunId)
                bestSpId = 0
                bestBacktestId = 0
                bestPLPercentage = 0
                if btList:
                    bestSpId = btList[0].SpId
                    bestBacktestId = btList[0].BacktestId
                    bestPLPercentage = btList[0].PLPercentage

                dnOptimizationRun = DNOptimizationRun()
                optimizationRun = dnOptimizationRun.getOptimizationRun(self.optimizationRunId)
                optimizationRun.DurationInMinutes = durationInMinutesForOpt
                optimizationRun.BestSpId = bestSpId
                optimizationRun.BestBacktestId = bestBacktestId
                optimizationRun.PLPercentage = bestPLPercentage
                optimizationRun.State = "Completed"
                dnOptimizationRun.updateOptimizationRun(optimizationRun)

                self.updateStrategyParameterForSymbolOnTrader(bestSpId, symbol)

                self.broadcastMessage("Completed.")

                self.optimizationRunId = 0

        except:
            self.printLog("Exception: runBacktest", traceback.format_exc())

    def updateStrategyParameterForSymbolOnTrader(self, bestSpIdId, symbol):
        dnBotParameters = DNBotParameters()
        bot_parameters = dnBotParameters.getBotParameters()
        if not bot_parameters.optUpdateStrategyParameters:
            print("AutoUpdate is off. Optimizer wont update the Trader parameters.")
            return

        if bestSpIdId == 0:
            print(symbol + ": bestSpIdId == 0")
            return

        current_env = getattr(Config, 'CURRENT_ENVIRONMENT', 'test')
        if current_env == 'test':
            return

        dnSp = DNStrategyParameters()
        bestSp = dnSp.getStrategyParametersById(bestSpIdId)

        if bestSp is None:
            print("bestSp is None")
            return

        dnStrategyParameters = DNStrategyParameters("traderremotenat")
        sp = dnStrategyParameters.getStrategyParametersBySymbolForTrader(self.btTimeframe, symbol)

        update = False
        if sp is None:
            sp = StrategyParameters()
            print("Sp for " + symbol + " doesnt exist.")
        else:
            update = True
            print("Sp for " + symbol + " exists.")

        sp = dnSp.set(bestSp, True)
        sp.Timeframe = self.btTimeframe
        sp.Symbol = symbol
        sp.Name = ""
        sp.OptimizationId = 0

        if update:
            dnStrategyParameters.updateStrategyParameters(sp)
            self.printLog("Strategy parameters for " + symbol + " is updated on Trader.")
        else:
            dnStrategyParameters.insertStrategyParameters(sp)
            self.printLog("Strategy parameters for " + symbol + " is created on Trader.")



    #This is for optimization 1: It tries all the available combinations. It takes so much time. So Nat decided to move to Optimization 2, which considers only the winning param value for each param.
    def runBacktest1(self, symbol, spList):
        try:
            self.broadcastMessage("Fetching candle data for " + symbol)

            #dnTickData = DNTickData()
            #tickDataList = dnTickData.listTickDataBySymbol(symbol, self.btStartDate, self.btEndDate)

            #if len(tickDataList) == 0:
            #self.printLog(symbol + ": TickData list is empty. Backtester will skip this symbol.")
            #self.broadcastMessage("No tick data found for " + symbol)
            #return False


            dnCandleData = DNCandleData()
            candleDataList = dnCandleData.listCandleData(symbol, self.btTimeframe, self.btStartDate, self.btEndDate)

            if not candleDataList or len(candleDataList) == 0:
                print("candleDataList is empty. Cannot continue " + self.btSymbol)
                return symbol

            candles = self.convertCandleDataListToCandleList(candleDataList)
            candlesInitial = self.getInitialCandlesForBacktesterOptimizer(symbol, self.btTimeframe)

            #print("candlesInitial: " + str(len(candlesInitial)) + "  " + symbol)


            durationInMinutesForOpt = 0
            dnStrategyParameters = DNStrategyParameters()

            spIndex = 1
            spCount = len(spList)

            for sp in spList:
                self.strategy_parameters = dnStrategyParameters.set(sp, True)

                #burada clearden sonra baslangic candleindan 1 onceki candleddan geriye dogru ne kdr donwload ettiysem hepsini alip state in icine koymam lazim.

                key = (symbol, self.btTimeframe)
                if key in self.market_state.keys():
                    self.market_state[key].clear()

                self.market_state[key] = candlesInitial

                optProgressText = ""
                if self.optimizationId > 0:
                    optProgressText = "Backtests: " + str(spIndex) + " / " + str(len(spList)) + ". "

                self.setupIndicators(self.strategy_parameters)

                # insert new backtest here
                dnBacktest = DNBacktest()
                backtest = Backtest()
                backtest.CreatedDate = datetime.now()
                backtest.StartDate = self.convertBinanceDateToLocalDate(self.btStartDate)
                backtest.EndDate = self.convertBinanceDateToLocalDate(self.btEndDate)
                # backtest.TickCount = len(tickDataList)
                backtest.TickCount = len(candles)
                backtest.Symbol = symbol
                backtest.Timeframe = self.btTimeframe
                backtest.OptimizationRunId = self.optimizationRunId
                backtest.Params = self.convertStrategyParametersToString(sp)
                backtest.SpId = sp.StrategyParametersId
                backtest.SpCount = spCount
                backtest.SpIndex = spIndex

                backtestId = dnBacktest.insertBacktest(backtest)
                self.backtestId = backtestId

                # running backtest

                """
                tickIndex = 1
                for tickData in tickDataList:
                    if tickIndex % 10 == 0:
                        tickProgressText = "Ticks: " + str(tickIndex) + " / " + str(len(tickDataList))
                        if self.optimizationRunId > 0:
                            self.broadcastMessage(optProgressText + tickProgressText)

                        candle = self.convertTickDataToCandle(tickData)
                        self.onTickBacktest(candle)
                    tickIndex = tickIndex + 1
                """



                tic = time.time()
                candleIndex = 1
                for candle in candles:
                    #if candleIndex == 1:
                    #    dtm = datetime.fromtimestamp(candle.open_time / 1000, timezone('Etc/GMT0'))
                    #    print("FirstTestDate: " + str(dtm))

                    tickProgressText = "Candles: " + str(candleIndex) + " / " + str(len(candles))
                    if self.optimizationRunId > 0:
                        self.broadcastMessage(optProgressText + tickProgressText)

                    self.onTickBacktest(candle)

                    candleIndex = candleIndex + 1

                toc = time.time()
                #self.printLog("Duration: " + str(int(toc - tic)) + " for BtId: " + str(backtestId))

                durationInMinutes = float(toc-tic) / 60
                durationInMinutesForOpt = durationInMinutesForOpt + durationInMinutes

                # update backtest stats here
                self.computeBacktestStats(backtestId, durationInMinutes)


                #print("CandleCount: " + str(len(candles)))

                if self.optimizationId == 0:
                    self.broadcastMessage("Backtest finished for " + symbol + ". Time:" + str(int(toc - tic)) + " sec.")

                spIndex = spIndex + 1

            # log optimization results
            if self.optimizationId > 0:
                btList = dnBacktest.listBacktestBySuccess(self.optimizationRunId)
                bestSpId = 0
                bestBacktestId = 0
                bestPLPercentage = 0
                if btList:
                    bestSpId = btList[0].SpId
                    bestBacktestId = btList[0].BacktestId
                    bestPLPercentage = btList[0].PLPercentage

                dnOptimizationRun = DNOptimizationRun()
                optimizationRun = dnOptimizationRun.getOptimizationRun(self.optimizationRunId)
                optimizationRun.DurationInMinutes = durationInMinutesForOpt
                optimizationRun.BestSpId = bestSpId
                optimizationRun.BestBacktestId = bestBacktestId
                optimizationRun.PLPercentage = bestPLPercentage
                optimizationRun.State = "Completed"
                dnOptimizationRun.updateOptimizationRun(optimizationRun)

                self.broadcastMessage("Completed.")



        except:
            self.printLog("Exception: runBacktest", traceback.format_exc())

    def getCurrentBacktestId(self):
        return self.backtestId

    def convertStrategyParametersToString(self, sp):
        try:
            result = ""

            result = result + "ROC_IndicatorEnabled"  + ":" + str(sp.ROC_IndicatorEnabled) + ", "
            result = result + "ROC_AppliedPrice_R" + ":" + str(sp.ROC_AppliedPrice_R) + ", "
            result = result + "ROC_AppliedPrice_F" + ":" + str(sp.ROC_AppliedPrice_F) + ", "
            result = result + "ROC_Period_R" + ":" + str(sp.ROC_Period_R) + ", "
            result = result + "ROC_Smoothing_R" + ":" + str(sp.ROC_Smoothing_R) + ", "
            result = result + "ROC_Period_F" + ":" + str(sp.ROC_Period_F) + ", "
            result = result + "ROC_R_BuyIncreasePercentage" + ":" + str(sp.ROC_R_BuyIncreasePercentage) + ", "
            result = result + "ROC_F_BuyDecreasePercentage" + ":" + str(sp.ROC_F_BuyDecreasePercentage) + ", "
            result = result + "MPT_IndicatorEnabled" + ":" + str(sp.MPT_IndicatorEnabled) + ", "
            result = result + "MPT_AppliedPrice" + ":" + str(sp.MPT_AppliedPrice) + ", "
            result = result + "MPT_ShortMAPeriod" + ":" + str(sp.MPT_ShortMAPeriod) + ", "
            result = result + "MPT_LongMAPeriod" + ":" + str(sp.MPT_LongMAPeriod) + ", "
            result = result + "NV_IndicatorEnabled" + ":" + str(sp.NV_IndicatorEnabled) + ", "
            result = result + "NV_IncreasePercentage" + ":" + str(sp.NV_IncreasePercentage) + ", "
            result = result + "NV_MinNetVolume" + ":" + str(sp.NV_MinNetVolume) + ", "

            result = result + "TREND_IndicatorEnabled" + ":" + str(sp.TREND_IndicatorEnabled) + ", "
            result = result + "TREND_AppliedPrice" + ":" + str(sp.TREND_AppliedPrice) + ", "
            result = result + "TREND_LongEmaPeriod" + ":" + str(sp.TREND_LongEmaPeriod) + ", "
            result = result + "TREND_ShortEmaPeriod" + ":" + str(sp.TREND_ShortEmaPeriod) + ", "

            result = result + "EMAX_IndicatorEnabled" + ":" + str(sp.EMAX_IndicatorEnabled) + ", "
            result = result + "EMAX_AppliedPrice" + ":" + str(sp.EMAX_AppliedPrice) + ", "
            result = result + "EMAX_LongEmaPeriod" + ":" + str(sp.EMAX_LongEmaPeriod) + ", "
            result = result + "EMAX_ShortEmaPeriod" + ":" + str(sp.EMAX_ShortEmaPeriod) + ", "

            result = result + "ST_IndicatorEnabled" + ":" + str(sp.ST_IndicatorEnabled) + ", "
            result = result + "ST_AppliedPrice" + ":" + str(sp.ST_AppliedPrice) + ", "
            result = result + "ST_AtrPeriod" + ":" + str(sp.ST_AtrPeriod) + ", "
            result = result + "ST_AtrMultiplier" + ":" + str(sp.ST_AtrMultiplier) + ", "
            result = result + "ST_UseWicks" + ":" + str(sp.ST_UseWicks) + ", "

            result = result + "VSTOP_IndicatorEnabled" + ":" + str(sp.VSTOP_IndicatorEnabled) + ", "
            result = result + "VSTOP_AppliedPrice" + ":" + str(sp.VSTOP_AppliedPrice) + ", "
            result = result + "VSTOP_Period" + ":" + str(sp.VSTOP_Period) + ", "
            result = result + "VSTOP_Factor" + ":" + str(sp.VSTOP_Factor) + ", "

            result = result + "SELL_IndicatorEnabled" + ":" + str(sp.SELL_IndicatorEnabled) + ", "
            result = result + "SELL_DecreasePercentage" + ":" + str(sp.SELL_DecreasePercentage) + ", "
            result = result + "SELL_Period" + ":" + str(sp.SELL_Period) + ", "
            result = result + "ROC_Smoothing_S" + ":" + str(sp.ROC_Smoothing_S) + ", "

            result = result + "SELL_RSI_AppliedPrice" + ":" + str(sp.SELL_RSI_AppliedPrice) + ", "
            result = result + "SELL_RSI_Period" + ":" + str(sp.SELL_RSI_Period) + ", "
            result = result + "SELL_RSI_UpperLevel" + ":" + str(sp.SELL_RSI_UpperLevel) + ", "
            result = result + "SELL_RSI_LowerLevel" + ":" + str(sp.SELL_RSI_LowerLevel) + ", "

            result = result + "SELL_Stoch_AppliedPrice" + ":" + str(sp.SELL_Stoch_AppliedPrice) + ", "
            result = result + "SELL_Stoch_KPeriod" + ":" + str(sp.SELL_Stoch_KPeriod) + ", "
            result = result + "SELL_Stoch_DPeriod" + ":" + str(sp.SELL_Stoch_DPeriod) + ", "
            result = result + "SELL_Stoch_Slowing" + ":" + str(sp.SELL_Stoch_Slowing) + ", "
            result = result + "SELL_Stoch_UpperLevel" + ":" + str(sp.SELL_Stoch_UpperLevel) + ", "
            result = result + "SELL_Stoch_LowerLevel" + ":" + str(sp.SELL_Stoch_LowerLevel) + ", "

            result = result + "R_TradingEnabled" + ":" + str(sp.R_TradingEnabled) + ", "
            result = result + "R_SL1Percentage" + ":" + str(sp.R_SL1Percentage) + ", "
            result = result + "R_SL2Percentage" + ":" + str(sp.R_SL2Percentage) + ", "
            result = result + "R_SLTimerInMinutes" + ":" + str(sp.R_SLTimerInMinutes) + ", "
            result = result + "R_TSLActivationPercentage" + ":" + str(sp.R_TSLActivationPercentage) + ", "
            result = result + "R_TSLTrailPercentage" + ":" + str(sp.R_TSLTrailPercentage) + ", "

            result = result + "F_TradingEnabled" + ":" + str(sp.F_TradingEnabled) + ", "
            result = result + "F_SL1Percentage" + ":" + str(sp.F_SL1Percentage) + ", "
            result = result + "F_SL2Percentage" + ":" + str(sp.F_SL2Percentage) + ", "
            result = result + "F_SLTimerInMinutes" + ":" + str(sp.F_SLTimerInMinutes) + ", "
            result = result + "F_TSLActivationPercentage" + ":" + str(sp.F_TSLActivationPercentage) + ", "
            result = result + "F_TSLTrailPercentage" + ":" + str(sp.F_TSLTrailPercentage) + ", "

            result = result + "S_TradingEnabled" + ":" + str(sp.S_TradingEnabled) + ", "
            result = result + "S_SL1Percentage" + ":" + str(sp.S_SL1Percentage) + ", "
            result = result + "S_SL2Percentage" + ":" + str(sp.S_SL2Percentage) + ", "
            result = result + "S_SLTimerInMinutes" + ":" + str(sp.S_SLTimerInMinutes) + ", "
            result = result + "S_TSLActivationPercentage" + ":" + str(sp.S_TSLActivationPercentage) + ", "
            result = result + "S_TSLTrailPercentage" + ":" + str(sp.S_TSLTrailPercentage) + ", "

            result = result + "TargetPercentage" + ":" + str(sp.TargetPercentage) + ", "
            result = result + "RebuyTimeInSeconds" + ":" + str(sp.RebuyTimeInSeconds) + ", "
            result = result + "RebuyPercentage" + ":" + str(sp.RebuyPercentage) + ", "
            result = result + "RebuyMaxLimit" + ":" + str(sp.RebuyMaxLimit) + ", "
            result = result + "PullbackEntryPercentage" + ":" + str(sp.PullbackEntryPercentage) + ", "
            result = result + "PullbackEntryWaitTimeInSeconds" + ":" + str(sp.PullbackEntryWaitTimeInSeconds) + ", "

            return result

        except:
            self.printLog("Exception: convertStrategyParametersToString", traceback.format_exc())

    def getSpPropertyByIndex(self, index):
        try:
            sps = ["ROC_IndicatorEnabled",
                   "ROC_AppliedPrice_R",
                   "ROC_Period_R",
                   "ROC_Smoothing_R",
                   "ROC_R_BuyIncreasePercentage",
                   "MPT_IndicatorEnabled",
                   "MPT_AppliedPrice",
                   "MPT_ShortMAPeriod",
                   "MPT_LongMAPeriod",
                   "TREND_IndicatorEnabled",
                   "TREND_AppliedPrice",
                   "TREND_LongEmaPeriod",
                   "TREND_ShortEmaPeriod",
                   "EMAX_IndicatorEnabled",
                   "EMAX_AppliedPrice",
                   "EMAX_LongEmaPeriod",
                   "EMAX_ShortEmaPeriod",
                   "ST_IndicatorEnabled",
                   "ST_AppliedPrice",
                   "ST_AtrPeriod",
                   "ST_AtrMultiplier",
                   "ST_UseWicks",
                   "VSTOP_IndicatorEnabled",
                   "VSTOP_AppliedPrice",
                   "VSTOP_Period",
                   "VSTOP_Factor",
                   "SELL_IndicatorEnabled",
                   "SELL_DecreasePercentage",
                   "SELL_Period",
                   "ROC_Smoothing_S",
                   "R_TradingEnabled",
                   "R_SL1Percentage",
                   "R_SL2Percentage",
                   "R_SLTimerInMinutes",
                   "R_TSLActivationPercentage",
                   "R_TSLTrailPercentage",
                   "S_TradingEnabled",
                   "S_SL1Percentage",
                   "S_SL2Percentage",
                   "S_SLTimerInMinutes",
                   "S_TSLActivationPercentage",
                   "S_TSLTrailPercentage",
                   "RebuyTimeInSeconds",
                   "RebuyPercentage",
                   "RebuyMaxLimit"
                   ]

            return sps[index]

            """
            if index == 0:
                return "ROC_IndicatorEnabled"
            elif index == 1:
                return "ROC_AppliedPrice_R"
            elif index == 2:
                return "ROC_AppliedPrice_F"
            elif index == 3:
                return "ROC_Period_R"
            elif index == 4:
                return "ROC_Period_F"
            elif index == 5:
                return "ROC_R_BuyIncreasePercentage"
            elif index == 6:
                return "ROC_F_BuyDecreasePercentage"

            elif index == 7:
                return "MPT_IndicatorEnabled"
            elif index == 8:
                return "MPT_AppliedPrice"
            elif index == 9:
                return "MPT_ShortMAPeriod"
            elif index == 10:
                return "MPT_LongMAPeriod"
            elif index == 11:
                return "NV_IndicatorEnabled"
            elif index == 12:
                return "NV_IncreasePercentage"
            elif index == 13:
                return "NV_MinNetVolume"

            elif index == 14:
                return "TREND_IndicatorEnabled"
            elif index == 15:
                return "TREND_AppliedPrice"
            elif index == 16:
                return "TREND_LongEmaPeriod"
            elif index == 17:
                return "TREND_ShortEmaPeriod"
            elif index == 18:
                return "SELL_IndicatorEnabled"
            elif index == 19:
                return "SELL_DecreasePercentage"
            elif index == 20:
                return "SELL_Period"

            elif index == 21:
                return "SELL_RSI_AppliedPrice"
            elif index == 22:
                return "SELL_RSI_Period"
            elif index == 23:
                return "SELL_RSI_UpperLevel"
            elif index == 24:
                return "SELL_RSI_LowerLevel"

            #elif index == 25:
            #    return "SELL_Stoch_AppliedPrice"
            elif index == 26:
                return "SELL_Stoch_KPeriod"
            elif index == 27:
                return "SELL_Stoch_DPeriod"
            elif index == 28:
                return "SELL_Stoch_Slowing"
            elif index == 29:
                return "SELL_Stoch_UpperLevel"
            elif index == 30:
                return "SELL_Stoch_LowerLevel"

            elif index == 31:
                return "R_TradingEnabled"
            elif index == 32:
                return "R_SL1Percentage"
            elif index == 33:
                return "R_SL2Percentage"
            elif index == 34:
                return "R_SLTimerInMinutes"
            elif index == 35:
                return "R_TSLActivationPercentage"
            elif index == 36:
                return "R_TSLTrailPercentage"

            elif index == 37:
                return "F_TradingEnabled"
            elif index == 38:
                return "F_SL1Percentage"
            elif index == 39:
                return "F_SL2Percentage"
            elif index == 40:
                return "F_SLTimerInMinutes"
            elif index == 41:
                return "F_TSLActivationPercentage"
            elif index == 42:
                return "F_TSLTrailPercentage"

            elif index == 43:
                return "S_TradingEnabled"
            elif index == 44:
                return "S_SL1Percentage"
            elif index == 45:
                return "S_SL2Percentage"
            elif index == 46:
                return "S_SLTimerInMinutes"
            elif index == 47:
                return "S_TSLActivationPercentage"
            elif index == 48:
                return "S_TSLTrailPercentage"

            elif index == 49:
                return "TargetPercentage"
            elif index == 50:
                return "RebuyTimeInSeconds"
            elif index == 51:
                return "RebuyPercentage"
            elif index == 52:
                return "RebuyMaxLimit"
            elif index == 53:
                return "PullbackEntryPercentage"
            elif index == 54:
                return "PullbackEntryWaitTimeInSeconds"

            return ""
            """

        except:
            self.printLog("Exception: getSpPropertyByIndex", traceback.format_exc())

    def startDataCollector(self):
        try:
            # get bot parameters from DB
            self.printLog("Data collector starting...")
            dnBotParameters = DNBotParameters()
            self.bot_parameters = dnBotParameters.getBotParameters()

            # init client api
            self.printLog("Initializing client Api.")
            self.client = ExchangeClient(self.exchange_type, self.bot_parameters.apiKey, self.bot_parameters.secretKey)

            # Get all symbols from client
            self.printLog("updateMarkets: Getting market symbols from client")
            all_markets = self.client.get_markets([])

            # Insert/Update all markets into DB
            self.printLog("updateMarkets: Inserting markets into DB")
            dnMarket = DNMarket()
            dnMarket.insertMarkets(all_markets)
            self.markets = dnMarket.listMarket()

            if len(self.markets) == 0:
                self.printLog("Market number is 0. Data collector will not start.")
                return False

            # # start web sockets
            self.printLog("Starting web sockets")
            self.startWebSockets()

            self.dataCollectorRunning = True
            self.printLog("Data collector started...")

            return True
        except:
            self.printLog("Exception: startDataCollector", traceback.format_exc())
            return False

    def exit(self):
        try:
            self.isRunning = False
            if self.client:
                self.client.exit_websocket()
        except:
            self.printLog("Exception: exit", traceback.format_exc())

    def stop(self):
        try:
            self.isRunning = False
            if self.client:
                self.client.stop_websocket()
        except:
            self.printLog("Exception: stop", traceback.format_exc())

    def stopDataCollector(self):
        try:
            self.dataCollectorRunning = False
            if self.client:
                self.client.stop_websocket()
        except:
            self.printLog("Exception: stopDataCollector", traceback.format_exc())

    def updateMarkets(self):
        try:
            dnMarket = DNMarket()
            markets = dnMarket.listMarket()

            currentTimeInSeconds = int(round(time.time()))
            if len(markets) > 0 and self.bot_parameters.marketUpdateDate > 0 and currentTimeInSeconds < self.bot_parameters.marketUpdateDate + 60 * 60 * 24:
                self.printLog("updateMarkets: Not time to update markets.")
                return

            # Get all symbols from binance
            self.printLog("updateMarkets: Getting market symbols from exchange")
            all_markets = self.client.get_markets([])

            # Insert/Update all markets into DB
            self.printLog("updateMarkets: Inserting markets into DB")
            dnMarket.insertMarkets(all_markets)

            #in we only use selected markets, no need to update market info
            #if self.bot_parameters.runOnSelectedMarkets:
                #return

            btcEnabled = self.qc_parameters_btc.tradeEnabled
            usdtEnabled = self.qc_parameters_usdt.tradeEnabled
            ethEnabled = self.qc_parameters_eth.tradeEnabled
            bnbEnabled = self.qc_parameters_bnb.tradeEnabled

            markets = dnMarket.listMarketByQuoteAsset(btcEnabled, usdtEnabled, bnbEnabled, ethEnabled )

            total = 0
            if markets:
                total = len(markets)

            marketCount = 0
            for market in markets:
                if not self.isRunning:
                    return

                if not self.bot_parameters.runOnSelectedMarkets or market.IsSelected:
                    stats = self.client.get_market_daily_summary(market.Symbol)
                    market.DailyPrice = stats.last_price
                    market.DailyVolume = stats.quote_volume

                    #if market.DailyPrice < min_daily_price or market.DailyVolume < min_daily_volume:
                    #	pass

                    self.printLog("updateMarkets: Updating:" + market.Symbol, "", False)
                    self.swtUpdate.emit("Updating market for " + market.Symbol)

                    market.CheckedDate = datetime.now()
                    dnMarket.updateMarket(market)

                    progress = float(marketCount) / total * 100
                    progress = int(progress)

                    self.swtMarketUpdateProgress.emit(progress)

                    marketCount = marketCount + 1
                    time.sleep(0.5)

            # Update marketUpdateDate
            self.bot_parameters.marketUpdateDate = currentTimeInSeconds
            dnBotParameters = DNBotParameters()
            dnBotParameters.updateBotParameters(self.bot_parameters)

            self.swtUpdate.emit("UpdateMarketsFinished")

        except:
            self.printLog("Exception: updateMarkets", traceback.format_exc())

    def startMarketUpdateForOptimization(self):
        try:
            dnMarket = DNMarket()
            markets = dnMarket.listMarket()

            dnBotParameters = DNBotParameters()
            self.bot_parameters = dnBotParameters.getBotParameters()

            dnQcParameters = DNQcParameters()
            self.qc_parameters_btc = dnQcParameters.getQcParameters("BTC")
            self.qc_parameters_usdt = dnQcParameters.getQcParameters("USDT")
            self.qc_parameters_eth = dnQcParameters.getQcParameters("ETH")
            self.qc_parameters_bnb = dnQcParameters.getQcParameters("BNB")

            if self.client is None:
                self.initClient()

            currentTimeInSeconds = int(round(time.time()))
            #if len(markets) > 0 and self.bot_parameters.marketUpdateDate > 0 and currentTimeInSeconds < self.bot_parameters.marketUpdateDate + 60 * 60 * 24:
            #    self.printLog("updateMarkets: Not time to update markets.")
            #    return

            # Get all symbols from binance
            self.printLog("updateMarkets: Getting market symbols from binance")
            all_markets = self.client.get_markets([])

            # Insert/Update all markets into DB
            self.printLog("updateMarkets: Inserting markets into DB")
            dnMarket.insertMarkets(all_markets)

            btcEnabled = self.qc_parameters_btc.tradeEnabled
            usdtEnabled = self.qc_parameters_usdt.tradeEnabled
            ethEnabled = self.qc_parameters_eth.tradeEnabled
            bnbEnabled = self.qc_parameters_bnb.tradeEnabled

            markets = dnMarket.listMarketByQuoteAsset(btcEnabled, usdtEnabled, ethEnabled, bnbEnabled)

            total = 0
            if markets:
                total = len(markets)

            marketCount = 0
            for market in markets:
                self.printLog("updateMarkets: Updating:" + market.Symbol, "", False)
                self.swtUpdate.emit("Updating market for " + market.Symbol)
                stats = self.client.get_market_daily_summary(market.Symbol)
                market.DailyPrice = stats.last_price
                market.DailyVolume = stats.quote_volume
                market.CheckedDate = datetime.now()
                dnMarket.updateMarket(market)

                progress = float(marketCount) / total * 100
                progress = int(progress)

                self.swtMarketUpdateProgress.emit(progress)

                marketCount = marketCount + 1
                time.sleep(1.5)

            # Update marketUpdateDate
            self.bot_parameters.marketUpdateDate = currentTimeInSeconds
            dnBotParameters = DNBotParameters()
            dnBotParameters.updateBotParameters(self.bot_parameters)

            self.swtUpdate.emit("UpdateMarketsForOptimizationFinished")

        except:
            self.printLog("Exception: updateMarketsForOptimization", traceback.format_exc())

    def updateMarketEligibility(self):
        try:
            # Reset all markets to non-tradable
            self.printLog("Reset all markets to non-tradable")
            dnMarket = DNMarket()
            dnMarket.makeAllMarketsNonTradable()

            # Set tradable markets based on qc params
#			self.printLog("QCs: " + self.quoteAssets + ", MinDailyVolume: " + str(self.bot_parameters.minDailyVolume) + ", MinPrice: " + str(self.bot_parameters.minPrice))

            if self.qc_parameters_btc.tradeEnabled:
                dnMarket.makeMarketsTradable("BTC", self.bot_parameters.minDailyVolume, self.bot_parameters.minPrice)
            if self.qc_parameters_usdt.tradeEnabled:
                dnMarket.makeMarketsTradable("USDT", self.bot_parameters.minDailyVolume, self.bot_parameters.minPrice)
            if self.qc_parameters_eth.tradeEnabled:
                dnMarket.makeMarketsTradable("ETH", self.bot_parameters.minDailyVolume, self.bot_parameters.minPrice)
            if self.qc_parameters_bnb.tradeEnabled:
                dnMarket.makeMarketsTradable("USD", self.bot_parameters.minDailyVolume, self.bot_parameters.minPrice)
            return True

        except:
            self.printLog("Exception: updateMarkets", traceback.format_exc())
            return False



    def getQuoteAssets(self):
        try:
            quoteAssets = ""
            if self.qc_parameters_btc.tradeEnabled:
                quoteAssets = quoteAssets + "BTC,"
            if self.qc_parameters_usdt.tradeEnabled:
                quoteAssets = quoteAssets + "USDT,"
            if self.qc_parameters_eth.tradeEnabled:
                quoteAssets = quoteAssets + "ETH,"
            if self.qc_parameters_bnb.tradeEnabled:
                quoteAssets = quoteAssets + "USD,"

            if quoteAssets == "":
                self.printLog("getQuoteAssets: quote_assets empty")
                return quoteAssets

            quoteAssets = quoteAssets[0:len(quoteAssets ) -1]
            return quoteAssets
        except:
            self.printLog("Exception: getQuoteAssets", traceback.format_exc())

    def startWebSockets(self):
        try:
            symbols = [market.Symbol for market in self.markets]
            if symbols:
                self.client.start_websocket(symbols, self.interval, self.onTick)
            else:
                self.printlog("No symbols to start websocket with")
        except:
            self.printLog("Exception: startWebSockets", traceback.format_exc())

    def fillInitialCandleData(self, limit):
        try:
            if not self.markets:
                return

            marketCount = 0
            marketTotal = len(self.markets)

            tic = time.time()
            for market in self.markets:
                if not self.isRunning:
                    self.swtUpdate.emit("CandleUpdateFinished")
                    return

                #print("fillInitialCandleData3")
                # if the bot already got candle data in the last 15m, dont get it again.
                get_all = True
                key = (market.Symbol, self.interval)

                if key in self.market_state.keys():
                    candles: List[Candle] = self.market_state[key]
                    print("candles In FillInitial:" + str(len(candles)))
                    if len(candles) >= limit and len(candles) >= 2:
                        prev_candle_time = int(candles[-2].open_time/1000)
                        curr_candle_time = int(candles[-1].open_time/1000)
                        interval = curr_candle_time - prev_candle_time
                        #curr_time = int(datetime.now().timestamp())
                        curr_time = int(datetime.utcnow().timestamp())
                        print(prev_candle_time, curr_candle_time, interval, curr_time, curr_time > curr_candle_time + interval)
                        if curr_time <= curr_candle_time + interval:
                            get_all = False

                # get all last x candles from exchange
                if get_all:
                    #print("Updating candles for {}".format(market.Symbol))
                    self.swtUpdate.emit("Updating candles for " + market.Symbol)
                    self.market_state[key] = self.client.get_candles(market.Symbol, self.interval, limit)

                # you can skip getting candles for this symbol
                else:
                    print("Skipping candles for {}".format(market.Symbol))
                    self.swtUpdate.emit("Skipping candles for " + market.Symbol)

                marketCount = marketCount + 1
                progress = float(marketCount) / marketTotal * 100
                progress = int(progress)
                self.swtCandleUpdateProgress.emit(progress)

            self.swtUpdate.emit("CandleUpdateFinished")
            toc = time.time()
            #print("Time: ", str(int(toc-tic)))
        except:
            self.printLog("Exception: fillInitialCandleData", traceback.format_exc())

    def convertToUnixTimeMillis(self, dt):
        epoch = datetime.utcfromtimestamp(0)
        result = (dt - epoch).total_seconds() * 1000
        result = int(result)

        return result


    def getInitialCandlesForBacktesterOptimizer(self, symbol, timeframe):

        minutesDist = 1
        if timeframe == "5m":
            minutesDist = 5
        elif timeframe == "15m":
            minutesDist = 15
        elif timeframe == "30m":
            minutesDist = 30
        elif timeframe == "1h":
            minutesDist = 60
        elif timeframe == "4h":
            minutesDist = 240
        elif timeframe == "1d":
            minutesDist = 1440

        startDate = self.btStartDate - timedelta(days=4)
        endDate = self.btStartDate - timedelta(minutes=minutesDist)

        self.printLog("MarketState StartDate: " + str(startDate))
        self.printLog("MarketState EndDate: " + str(endDate))

        dnCandleData = DNCandleData()
        candleDataList = dnCandleData.listCandleData(symbol, timeframe, startDate, endDate)
        if not candleDataList or len(candleDataList) == 0:
            print("candleDataList is empty. Cannot continue " + self.btSymbol)
            return

        candles = self.convertCandleDataListToCandleList(candleDataList)
        self.printLog("MarketState CandleSize: " + str(len(candles)))

        # This part is new start
        """
        print("ADDING NOW>.......")
        print(self.btTimeframe)
        print(self.btSymbol)
        key = (symbol, timeframe)
        candleDataListEarly = dnCandleData.listCandleData(self.btSymbol, timeframe, startDate, self.btStartDate)
        if not candleDataListEarly or len(candleDataListEarly) == 0:
         print("candleDataListEarly is empty. Cannot continue " + self.btSymbol)
         return

        candlesEarly = self.convertCandleDataListToCandleList(candleDataListEarly)
        self.market_state[key] = candlesEarly
        print("ADDING NOW>......." + str(len(candlesEarly)))
        """
        # This part is new end

        return candles




    def downloadCandleData(self, limit):
        try:
            if not self.markets:
                return

            marketCount = 0
            marketTotal = len(self.markets)
            dnCandleData = DNCandleData()

            # these are based on the number of candles i can download from binance in 1 request: 1000 is the limit
            # 1m: 1440 candle a day: iteration time: 12 hours
            # 5m: 288 candle a day: 3.47 days: 83 hours
            # 15m: 96 candle a day: 10 days: 240 hours
            # 30m: 48 candle a day: 20 days: 480 hours
            # 1h:  24 candle a day: 40 days: 960 hours
            # 4h:  6 candle a day: 160 days: 3840 hours
            # 1d:  1 candle a day: 960 days: 23040 hours

            # iterationTimeInHours = 12
            # if self.btTimeframe == "5m":
            # 	iterationTimeInHours = 83
            # elif self.btTimeframe == "15m":
            # 	iterationTimeInHours = 240
            # elif self.btTimeframe == "30m":
            # 	iterationTimeInHours = 480
            # elif self.btTimeframe == "1h":
            # 	iterationTimeInHours = 960
            # elif self.btTimeframe == "4h":
            # 	iterationTimeInHours = 3840
            # elif self.btTimeframe == "1d":
            # 	iterationTimeInHours = 23040

            downloadStartDate = self.btStartDate - timedelta(days=4)  # to cover 300 previous candles for the first ticks, I take 4 more days from start.
            downloadEndDate = self.btEndDate
            #delta = timedelta(hours=iterationTimeInHours)

            tic = time.time()

            if dnCandleData.candleSetExists(self.btSymbol, self.btTimeframe, downloadStartDate, downloadEndDate):
                self.printLog("Candle set already exists in db.")
                return

            if dnCandleData.isCandleListDownloadedBefore(self.btSymbol, self.btTimeframe, downloadStartDate, downloadEndDate):
                self.printLog("Candle set is already downloaded before.")
                return

            self.initClient()

            # downloadStartDate = self.btStartDate - timedelta(days=4)  # to cover 300 previous candles for the first ticks, I take 4 more days from start.
            # downloadEndDate = self.btEndDate
            # dowloadCurrentDate = downloadStartDate

            downloadStartDateInMillis = self.convertToUnixTimeMillis(downloadStartDate)
            downloadEndDateInMillis = self.convertToUnixTimeMillis(downloadEndDate)
            self.broadcastMessage("Downloading candles...")
            candles = self.client.get_candles_historical(self.btSymbol,
                                                         self.btTimeframe,
                                                         downloadStartDateInMillis,
                                                         downloadEndDateInMillis)
            self.insertCandleDataList(candles)

            # binancede boyle yapiliyodu ama simdi gerek yok dogrudan tarihleri verince aradaki hepsini aliyo
            # dowloadCurrentDate = downloadStartDate
            # while dowloadCurrentDate <= downloadEndDate:
            # 	if dnCandleData.candleSetExists(self.btSymbol, self.btTimeframe, dowloadCurrentDate, dowloadCurrentDate+delta):
            # 		self.printLog("Candle set already exists")
            # 		dowloadCurrentDate += delta
            # 		continue
            #
            # 	#self.swtUpdate.emit("Candle download for " + self.btSymbol + ". Markets: " + str(marketCount) + "/" + str(marketTotal))
            # 	self.broadcastMessage("Downloading candles...")
            # 	downloadStartDateInMillis = self.convertToUnixTimeMillis(dowloadCurrentDate)
            # 	downloadEndDateInMillis = self.convertToUnixTimeMillis(dowloadCurrentDate+delta)
            #
            # 	# This is the only call
            # 	candles = self.client.get_candles_historical(self.btSymbol, self.btTimeframe, downloadStartDateInMillis, downloadEndDateInMillis)
            # 	self.insertCandleDataList(candles)
            # 	dowloadCurrentDate += delta
            # 	time.sleep(0.3)

            currentDate = datetime.now()
            dnCandleData.insertCandleDataDownload(self.btSymbol, self.btTimeframe, downloadStartDate, downloadEndDate, currentDate)

            # add candles to the memory for backtest

            #This part is wrong i cant put future candles into the marketstate. marktestate should have the current candle as the last item.remove this in the future.
            """
            if not self.downloadCandleOnly:
                key = (self.btSymbol, self.btTimeframe)
                candleDataList = dnCandleData.listCandleData(self.btSymbol, self.btTimeframe, self.btStartDate, self.btEndDate)
                if not candleDataList or len(candleDataList) == 0:
                    print("candleDataList is empty. Cannot continue " + self.btSymbol)
                    return

                candles = self.convertCandleDataListToCandleList(candleDataList)
                self.market_state[key] = candles
            """

            marketCount = marketCount + 1
            progress = float(marketCount) / marketTotal * 100
            progress = int(progress)
            self.swtCandleDownloadProgress.emit(progress)


            toc = time.time()
            # print("Time: ", str(int(toc-tic)))
            self.swtUpdate.emit("Candle download finished. Time:" + str(int(toc-tic))  +" sec.")
            # self.swtUpdate.emit("CandleDownloadFinished")

            print("CandleDownloadFinished")

        except:
            self.printLog("Exception: downloadCandleData", traceback.format_exc())

    def fillInitialCandleDataForBacktest(self, limit):
        try:
            if not self.markets:
                return

            marketCount = 0
            marketTotal = len(self.markets)

            timeFrameInMinutes = 1
            if self.btTimeframe == "5m":
                timeFrameInMinutes = 5
            elif self.btTimeframe == "15m":
                timeFrameInMinutes = 15
            elif self.btTimeframe == "30m":
                timeFrameInMinutes = 30
            elif self.btTimeframe == "1h":
                timeFrameInMinutes = 60
            elif self.btTimeframe == "4h":
                timeFrameInMinutes = 240
            elif self.btTimeframe == "1d":
                timeFrameInMinutes = 1440

            for market in self.markets:
                dnTickData = DNTickData()
                marketTickDataList = dnTickData.listTickDataBySymbol(market.Symbol, self.btStartDate, self.btEndDate)
                if len(marketTickDataList) == 0:
                    continue

                candles = None
                candle = Candle()
                prevMinute = marketTickDataList[0].EventTime.minute
                candleCollectionStarted = False
                prevCandle = Candle()
                i = 0

                for tickData in marketTickDataList:
                    i = i + 1
                    currentMinute = tickData.EventTime.minute
                    currentCandle = self.convertTickDataToCandle(tickData)

                    if prevMinute != currentMinute and currentMinute % timeFrameInMinutes == 0:
                        if candleCollectionStarted:

                            # insert the currently processed candle to list
                            if candle.close != 0:
                                candle.close = prevCandle.close
                                candle.close_time = prevCandle.close_time
                                candle.is_closed = True
                                candles.append(candle)

                            # start a new candle
                            candle = Candle()
                            candle.symbol = currentCandle.symbol
                            candle.interval = self.btTimeframe
                            candle.open = currentCandle.open
                            candle.open_time = currentCandle.open_time

                        else:
                            candleCollectionStarted = True

                            # start a new candle
                            candle = Candle()
                            candle.symbol = currentCandle.symbol
                            candle.interval = self.btTimeframe
                            candle.open = currentCandle.open
                            candle.open_time = currentCandle.open_time

                    if not candleCollectionStarted:
                        continue

                    candle.low = min(candle.low, currentCandle.low)
                    candle.high = max(candle.high, currentCandle.high)

                    candle.taker_buy_quote_asset_volume = candle.taker_buy_quote_asset_volume +  currentCandle.taker_buy_quote_asset_volume
                    candle.taker_buy_base_asset_volume = candle.taker_buy_base_asset_volume + currentCandle.taker_buy_base_asset_volume
                    candle.quote_asset_volume = candle.quote_asset_volume + currentCandle.quote_asset_volume
                    candle.volume = candle.volume + currentCandle.volume
                    candle.num_trades = candle.num_trades + currentCandle.num_trades

                    # if this is the last iteration insert incomplete candle
                    if i == len(marketTickDataList) - 1:
                        candle.close = currentCandle.close
                        candle.close_time = currentCandle.event_time
                        candles.append(candle)


                    prevCandle = currentCandle
                    prevMinute = currentMinute

                key = (market.Symbol, self.btTimeframe)
                self.market_state[key] = candles
                self.swtUpdate.emit("Forming candles for " + market.Symbol)
                marketCount = marketCount + 1
                progress = float(marketCount) / marketTotal * 100
                progress = int(progress)
                self.swtCandleUpdateProgress.emit(progress)

            self.swtUpdate.emit("CandleFormationFinished")


        except:
            self.printLog("Exception: fillInitialCandleDataForBacktest", traceback.format_exc())

    def setupIndicators(self, strategy_parameters):
        try:
            '''
            Create indicators with initial parameters
            :return: None
            '''

            if strategy_parameters is None:
                self.printLog("setupIndicators: strategy_parameters is None")
                return

            self.indicators.clear()

            p = strategy_parameters
            #self.indicators[ENUM_INDICATOR.RSI] = Rsi(ENUM_APPLIED_PRICE.get_price(p.SELL_RSI_AppliedPrice),p.SELL_RSI_Period)
            # self.indicators[ENUM_INDICATOR.STOCHRSI] = StochRsi() # alternative: never used.

            #self.indicators[ENUM_INDICATOR.STOCH] = Stoch(p.SELL_Stoch_KPeriod,p.SELL_Stoch_Slowing,p.SELL_Stoch_DPeriod)
            if p.ROC_IndicatorEnabled:
                self.indicators[ENUM_INDICATOR.ROC] = Roc(ENUM_APPLIED_PRICE.get_price(p.ROC_AppliedPrice_R),
                                                          ENUM_APPLIED_PRICE.get_price(p.ROC_AppliedPrice_F),
                                                          ENUM_APPLIED_PRICE.get_price(p.ROC_AppliedPrice_R),
                                                          p.ROC_Period_R,
                                                          p.ROC_Period_F,
                                                          p.SELL_Period,
                                                          p.ROC_R_BuyIncreasePercentage,
                                                          p.ROC_F_BuyDecreasePercentage,
                                                          p.SELL_DecreasePercentage,
                                                          p.ROC_Smoothing_R,
                                                          p.ROC_Smoothing_S)
            if p.MPT_IndicatorEnabled:
                self.indicators[ENUM_INDICATOR.MPT] = Mpt(ENUM_APPLIED_PRICE.get_price(p.MPT_AppliedPrice),
                                                          p.MPT_ShortMAPeriod,
                                                          p.MPT_LongMAPeriod)
            if p.TREND_IndicatorEnabled:
                self.indicators[ENUM_INDICATOR.TREND] = Trend(ENUM_APPLIED_PRICE.get_price(p.TREND_AppliedPrice),
                                                              p.TREND_ShortEmaPeriod,
                                                              p.TREND_LongEmaPeriod)
            if p.NV_IndicatorEnabled:

                self.indicators[ENUM_INDICATOR.NV] = Nv()

            if p.EMAX_IndicatorEnabled:
                # print("p.EMAX_AppliedPrice")
                # print(p.EMAX_AppliedPrice)
                self.indicators[ENUM_INDICATOR.EMAX] = Emax(ENUM_APPLIED_PRICE.get_price(p.EMAX_AppliedPrice),
                                                            p.EMAX_ShortEmaPeriod,
                                                            p.EMAX_LongEmaPeriod)
            if p.ST_IndicatorEnabled:
                self.indicators[ENUM_INDICATOR.ST] = SuperTrend(ENUM_APPLIED_PRICE.get_price(p.ST_AppliedPrice),
                                                                p.ST_AtrPeriod,
                                                                p.ST_AtrMultiplier,
                                                                p.ST_UseWicks)
            if p.VSTOP_IndicatorEnabled:
                # print("p.VSTOP_AppliedPrice")
                # print(p.VSTOP_AppliedPrice)
                self.indicators[ENUM_INDICATOR.VSTOP] = Vstop(ENUM_APPLIED_PRICE.get_price(p.VSTOP_AppliedPrice),
                                                              ENUM_APPLIED_PRICE.get_price("high"),
                                                              ENUM_APPLIED_PRICE.get_price("low"),
                                                              p.VSTOP_Period,
                                                              p.VSTOP_Factor,
                                                              p.EMAX_ShortEmaPeriod,
                                                              p.EMAX_LongEmaPeriod
                                                              )

        except:
            self.printLog("Exception: setupIndicators", traceback.format_exc())

    def computeIndicators(self, data):
        try:
            '''
            Feed recent candle data to the indicators and compute signals
            :return: None
            '''

            signals = {}
            for name, indicator in self.indicators.items():
                if indicator:
                    #print("computeIndicatorsSize:" + str(len(data)))
                    signals[name] = indicator.compute(data)

            return signals

        except:
            self.printLog("Exception: computeIndicators", traceback.format_exc())
        # Used for test

    def updateTickData(self, candle, event_time):
        try:
            # print(f"\n\nUpdate from {candle.symbol} @{candle.close}")

            # Update local market state
            self.addCandleToMarketState(candle, self.btTimeframe)
            candles = self.market_state[candle.symbol]

            # Compute indicator signals
            signals = self.computeIndicators(candles)

            # Compute other combined signals
            conditions_r = self.checkEntryForRbuy(signals, candles)
            conditions_f = self.checkEntryForFbuy(signals, candles)
            conditions_s = self.checkEntryForSsell(signals, candles)

            if all(conditions_r):
                logger.debug(f'symbol: {candle.symbol} conditions_r: {conditions_r}')
            if all (conditions_s):
                logger.debug(f'symbol: {candle.symbol} conditions_s: {conditions_s}')

            # Update market state in DB
            self.updateMarketState(candle, signals, conditions_r, conditions_f, conditions_s)
            self.insertIndicatorLog(candle, signals, conditions_r, conditions_f, conditions_s, 0, 0, 0)

        except:
            self.printLog("Exception: updateTickData", traceback.format_exc())

    def onTick(self, candle, event_time):
        try:
            if not self.dataCollectorModeEnabled:
                # Run trading algorithm only on markets with enabled quote currency.
                quote_symbol = candle.symbol.split('-')[-1].lower()
                quote_symbol_qc_parameters = getattr(self, f'qc_parameters_{quote_symbol}', False)
                if quote_symbol_qc_parameters and quote_symbol_qc_parameters.tradeEnabled:
                    self.runTradingAlgorithm(candle, event_time)
            else:
                self.runDataCollector(candle, event_time)

        except:
            self.printLog("Exception: onTick", traceback.format_exc())

    def onTickBacktest(self, candle):
        try:
            # print(f"Update from {candle.symbol} @{candle.close}")
            if not self.backtestModeEnabled:
                return

            # Update local market state

            self.addCandleToMarketState(candle, self.btTimeframe)
            candles = self.market_state[(candle.symbol, self.btTimeframe)]

            # Compute indicator signals
            signals = self.computeIndicators(candles)

            # Compute other combined signals
            conditions_r = self.checkEntryForRbuy(signals, candles)
            conditions_f = self.checkEntryForFbuy(signals, candles)
            conditions_s = self.checkEntryForSsell(signals, candles)

            if all(conditions_r):
                logger.debug(f'symbol: {candle.symbol} conditions_r: {conditions_r}')
            if all (conditions_s):
                logger.debug(f'symbol: {candle.symbol} conditions_s: {conditions_s}')

            # Update market state in DB
            self.updateMarketState(candle, signals, conditions_r, conditions_f, conditions_s)

            rBuyTradeCount = 0
            fBuyTradeCount = 0
            sSellTradeCount = 0

            dnTrade = DNTrade()
            openTrades = dnTrade.listOpenTradeBySymbol(candle.symbol, self.backtestId)

            if openTrades:
                for trade in openTrades:
                    if trade.StrategyName == "R_Buy":
                        rBuyTradeCount = rBuyTradeCount + 1
                    if trade.StrategyName == "F_Buy":
                        fBuyTradeCount = fBuyTradeCount + 1
                    if trade.StrategyName == "S_Sell":
                        sSellTradeCount = sSellTradeCount + 1

            # insert indicator log to DB
            self.insertIndicatorLog(candle, signals, conditions_r, conditions_f, conditions_s, rBuyTradeCount, fBuyTradeCount, sSellTradeCount)

            if self.entryEnabled:
                if self.strategy_parameters.R_TradingEnabled and rBuyTradeCount == 0: # and sSellTradeCount == 0:
                    success = self.monitorEntry("R_Buy", conditions_r, candle)
                    if success:
                        rBuyTradeCount = rBuyTradeCount + 1

                #if self.strategy_parameters.F_TradingEnabled and fBuyTradeCount == 0: # and sSellTradeCount == 0:
                #    success = self.monitorEntry("F_Buy", conditions_f, candle)
                #    if success:
                #        fBuyTradeCount = fBuyTradeCount + 1

                if self.strategy_parameters.S_TradingEnabled and sSellTradeCount == 0: # and fBuyTradeCount == 0 and rBuyTradeCount == 0:
                    success = self.monitorEntry("S_Sell", conditions_s, candle)
                    if success:
                        sSellTradeCount = sSellTradeCount + 1

            if openTrades:
                for trade in openTrades:
                    self.monitorExit(trade, candle)

        except:
            self.printLog("Exception: onTickBacktest", traceback.format_exc())

    def runTradingAlgorithm(self, candle, event_time):
        try:
            #print(f"Update from {candle.symbol} @{candle.close}")


            # Get parameters of the current symbol
            self.strategy_parameters = self.selectStrategyParametersForSymbol(candle.symbol)
            self.setupIndicators(self.strategy_parameters)
            #print("Used SpId: " + str(self.strategy_parameters.StrategyParametersId))
            #print(self.strategy_parameters)

            # Update local market state
            self.addCandleToMarketState(candle, self.interval)
            candles = self.market_state[(candle.symbol, self.interval)]

            # Lock the strategy.
            if self.trading_lock.get(candle.symbol):
                logger.info(f'Trading {candle.symbol} is locked.')
                return
            logger.debug(f'Locking {candle.symbol}.')
            self.trading_lock[candle.symbol] = True

            # Compute indicator signals
            signals = self.computeIndicators(candles)

            # Compute other combined signals
            conditions_long = self.checkEntryForRbuy(signals, candles)
            conditions_f = self.checkEntryForFbuy(signals, candles)
            conditions_short = self.checkEntryForSsell(signals, candles)

            will_sell = False
            if all(conditions_long):
                logger.debug(f'symbol: {candle.symbol} conditions long: {conditions_long}')
            if all(conditions_short):
                will_sell = True
                logger.debug(f'symbol: {candle.symbol} conditions short: {conditions_short}')

            #if self.strategy_parameters.TREND_IndicatorEnabled:
            #	#dont trade btcusdt, just use its trend
            #	if candle.symbol == "BTCUSDT":
            #		self.btcTrending = conditions_r[2]
            #		self.btcTrendingPrev = self.btcTrending
            #		return
            #	if "UPUSDT" in candle.symbol:
            #		conditions_r[2] = self.btcTrending
            #	if "DOWNUSDT" in candle.symbol:
            #		conditions_r[2] = not self.btcTrending

            # Update market state in DB
            self.updateMarketState(candle, signals, conditions_long, conditions_f, conditions_short)

            long_buy_trade_count = 0
            fBuyTradeCount = 0
            short_sell_trade_count = 0

            dnTrade = DNTrade()
            openTrades = dnTrade.listOpenTradeBySymbol(candle.symbol, self.backtestId)

            if openTrades:
                for trade in openTrades:
                    # update the current price on open trades
                    if trade.Symbol == candle.symbol:
                        trade.CurrentPrice = candle.close
                        trade.ModifiedDate = datetime.now()
                        dnTrade.updateTrade(trade)

                    if trade.StrategyName == "R_Buy":
                        long_buy_trade_count = long_buy_trade_count + 1
                    if trade.StrategyName == "F_Buy":
                        fBuyTradeCount = fBuyTradeCount + 1
                    if trade.StrategyName == "S_Sell":
                        short_sell_trade_count = short_sell_trade_count + 1

            # insert indicator log to DB
            self.insertIndicatorLog(candle, signals, conditions_long, conditions_f, conditions_short, long_buy_trade_count, fBuyTradeCount, short_sell_trade_count)

            if self.entryEnabled:
                #if a sell signal comes from vstop, but the inverse pair
                #self.monitorEntryForInversePair("R_Buy", conditions_s, candle)

                # and not self.hasOppositeMarginTrade(candle.symbol, "R_Buy")
                if self.strategy_parameters.R_TradingEnabled and long_buy_trade_count == 0 and short_sell_trade_count == 0:
                    success = self.monitorEntry("R_Buy", conditions_long, candle)
                    if success:
                        long_buy_trade_count = long_buy_trade_count + 1

                #if self.strategy_parameters.F_TradingEnabled and fBuyTradeCount == 0 and sSellTradeCount == 0 and not self.hasOppositeMarginTrade(candle.symbol, "F_Buy"):
                #    success = self.monitorEntry("F_Buy", conditions_f, candle)
                #    if success:
                #        fBuyTradeCount = fBuyTradeCount + 1

                # and not self.hasOppositeMarginTrade(candle.symbol, "S_Sell")
                if will_sell:
                    logger.debug(f'Symbol: {candle.symbol}, S_TradingEnabled: {self.strategy_parameters.S_TradingEnabled}, short_sell_trade_count: {short_sell_trade_count}, long_buy_trade_count: {long_buy_trade_count}, fBuyTradeCount: {fBuyTradeCount}')
                if self.strategy_parameters.S_TradingEnabled and short_sell_trade_count == 0 and fBuyTradeCount == 0 and long_buy_trade_count == 0:
                    success = self.monitorEntry("S_Sell", conditions_short, candle)
                    if success:
                        short_sell_trade_count = short_sell_trade_count + 1
            else:
                pass
                #logger.debug(f'symbol: {candle.symbol}, Entry is disabled.')

            if openTrades:
                for trade in openTrades:
                    immediateExit = False
                    immediateEntry = False
                    if USE_CPD_TRADE_EXIT and check_trade_exit_on_cpd(candles, trade, CPD_PRICE_SOURCE, CPD_EXIT_PERCENT_LONG, CPD_EXIT_PERCENT_SHORT):
                        logger.info(f'CPD exit for {candle.symbol}')
                        immediateExit = True
                        immediateEntry = CPD_OPEN_OPPOSITE
                    self.monitorExit(trade, candle, immediateExit)
                    if immediateEntry and self.entryEnabled:
                        oposite_entry_conditions = [True] * len(conditions_long)
                        opposite_strategy = 'R_Buy' if trade.StrategyName == 'S_Sell' else 'S_Sell'
                        logger.info(f'CPD open opposite trade for {candle.symbol}')
                        self.monitorEntry(opposite_strategy, oposite_entry_conditions, candle, immediateEntry)

        except:
            self.printLog("Exception: runTradingAlgorithm", traceback.format_exc())
        finally:
            logger.debug(f'Unlocking {candle.symbol}.')  # TODO: Remove this log.
            self.trading_lock[candle.symbol] = False

    def hasOppositeMarginTrade(self, symbol, strategyName):
        if "UPUSDT" not in symbol and "DOWNUSDT" not in symbol:
            return False

        if "UPUSDT" in symbol:
            symbolOpposite = symbol.replace("UP", "DOWN")
        else:
            symbolOpposite = symbol.replace("DOWN", "UP")

        dnTrade = DNTrade()
        tradeList = dnTrade.listOpenTradeBySymbol(symbolOpposite)

        if not tradeList:
            return False

        for trade in tradeList:
            if (strategyName == "R_Buy" or strategyName == "F_Buy") and (trade.StrategyName == "R_Buy" or trade.StrategyName == "F_Buy"):
                #print(symbol + " " + strategyName + " trade is blocked because there is an open trade of " + symbolOpposite + " " + trade.StrategyName)
                return True
            if trade.StrategyName == "S_Sell" and strategyName == "S_Sell":
                #print(symbol + " " + strategyName + " trade is blocked because there is an open trade of " + symbolOpposite + " " + trade.StrategyName)
                return True

        return False

    def runDataCollector(self, candle, event_time):
        try:
            #if websocket fails
            if candle is None and event_time == -1:
                self.initClient()
                self.startWebSockets()
                return

            # print(f"Update from {candle.symbol} @{candle.close}")
            tickData = TickData()

            tickData.Symbol = candle.symbol
            tickData.Timeframe = candle.interval
            tickData.Close = candle.close
            tickData.Open = candle.open
            tickData.High = candle.high
            tickData.Low = candle.low
            tickData.OpenTime = datetime.fromtimestamp(candle.open_time / 1000, timezone('Etc/GMT0'))
            tickData.CloseTime = datetime.fromtimestamp(candle.close_time / 1000, timezone('Etc/GMT0'))
            tickData.NumTrades = candle.num_trades
            tickData.Volume = candle.volume
            tickData.QuoteAssetVolume = candle.quote_asset_volume
            tickData.TakerBuyBaseAssetVolume = candle.taker_buy_base_asset_volume
            tickData.TakerBuyQuoteAssetVolume = candle.taker_buy_quote_asset_volume
            tickData.EventTime = datetime.fromtimestamp(event_time / 1000, timezone('Etc/GMT0'))
            tickData.CreatedDate = datetime.now()

            dnTickData = DNTickData()
            dnTickData.insertTickData(tickData)

        except:
            self.printLog("Exception: runDataCollector", traceback.format_exc())


    def getPullbackEntrySignal(self, strategyName, candle):
        try:
            dateCurrent = self.getCurrentDateTime(candle) #datetime.now()
            dateFrom = dateCurrent - timedelta(seconds=self.PullbackEntryWaitTimeInSeconds)
            currentPrice = decimal.Decimal(candle.close)

            if strategyName == "R_Buy":
                targetPrice = self.addPercentageToPrice(currentPrice, self.PullbackEntryPercentage)
            else:
                targetPrice = self.subtractPercentageFromPrice(currentPrice, self.PullbackEntryPercentage)

            # if the current price is a pullback, return 1
            dnSignal = DNSignal()
            signals = dnSignal.listSignalForPullbackEntry(candle.symbol, strategyName, dateFrom, targetPrice, self.backtestId)
            if signals:
                # self.printLog("getPullbackEntrySignal:PullbackEntry. " + candle.symbol + ", " + strategyName + ", CP:" + self.decToStr(currentPrice) + ", TargetPrice:" + self.decToStr(targetPrice) + " , DateFrom:" + str(dateFrom))
                return 1

            # if there is no pullback, but the wait time is expired, and there was a signal between -waittime and -(waittime+10) seconds, return 2
            dateTo = dateCurrent - timedelta(seconds=self.PullbackEntryWaitTimeInSeconds)
            dateFrom = dateCurrent - timedelta(seconds=self.PullbackEntryWaitTimeInSeconds+10)

            signals = dnSignal.listSignalForExpiredPullbackWait(candle.symbol, strategyName, dateFrom, dateTo, self.backtestId)
            if signals:
                # self.printLog("getPullbackEntrySignal:ExpiredPullbackWait. " + candle.symbol + ", " + strategyName + ", TargetPrice:" + self.decToStr(targetPrice))
                return 2

            return 0

        except:
            self.printLog("Exception: getPullbackEntrySignal", traceback.format_exc())


    def convertBinanceDateToLocalDate(self, date):
        try:
            t1 = time.localtime()
            t2 = time.gmtime()
            gmtTimeDiffInHours = (time.mktime(t1) - time.mktime(t2)) / 60 / 60

            return date + timedelta(hours=gmtTimeDiffInHours)

        except:
            self.printLog("Exception: convertBinanceDateToLocalDate", traceback.format_exc())

    def convertLocalDateToBinanceDate(self, date):
        try:
            t1 = time.localtime()
            t2 = time.gmtime()
            gmtTimeDiffInHours = (time.mktime(t1) - time.mktime(t2)) / 60 / 60

            return date - timedelta(hours=gmtTimeDiffInHours)
        except:
            self.printLog("Exception: convertLocalDateToBinanceDate", traceback.format_exc())

    def getCurrentDateTime(self, candle):
        try:
            if not self.backtestModeEnabled:
                return datetime.now()
            else:
                #candle.eventtime normalde binance time,  ama bu func benim local time imi dondurmeli.
                # live modda opentime=localtime, backtest modda opentime=binancetime.sanirim.

                currentBinanceDate = datetime.fromtimestamp(int(candle.event_time) / 1000)
                return self.convertBinanceDateToLocalDate(currentBinanceDate)
                #return datetime.fromtimestamp(int(candle.event_time) / 1000)
        except:
            self.printLog("Exception: getCurrentDateTime", traceback.format_exc())

    def getCurrentDateTimeInSeconds(self, candle):
        try:
            if not self.backtestModeEnabled:
                return int(round(time.time()))
            else:
                return int(candle.event_time / 1000 / 1000)
        except:
            self.printLog("Exception: getCurrentDateTimeInSeconds", traceback.format_exc())

    def monitorEntryForInversePair(self, strategyName, conditions_s, candle):
        symbol = candle.symbol

        #is vstop is sell for the current pair, make a buy in the inverse pair..conditions_s[5]=VStop==-1
        if not conditions_s[5]:
            return

        if "UPUSDT" not in symbol and "DOWNUSDT" not in symbol:
            return

        if "UPUSDT" in symbol:
            symbolInverse = symbol.replace("UP", "DOWN")
        else:
            symbolInverse = symbol.replace("DOWN", "UP")

        dnTrade = DNTrade()
        openTrades = dnTrade.listOpenTradeBySymbol(symbolInverse, self.backtestId)

        if openTrades:
            return

        # make sure it will enter in monitorEntry
        conditions = [True] * 6

        dnMarket = DNMarket()
        market = dnMarket.getMarketBySymbol(symbolInverse)

        candleInverse = Candle()
        candleInverse.symbol = symbolInverse
        candleInverse.interval = candle.interval
        candleInverse.open_time = candle.open_time
        candleInverse.open = candle.open
        candleInverse.high = candle.high
        candleInverse.low = candle.low
        candleInverse.close = market.LastPrice
        candleInverse.volume = candle.volume
        candleInverse.close_time = candle.close_time
        candleInverse.quote_asset_volume = candle.quote_asset_volume
        candleInverse.num_trades = candle.num_trades
        candleInverse.taker_buy_base_asset_volume = candle.taker_buy_base_asset_volume
        candleInverse.taker_buy_quote_asset_volume = candle.taker_buy_quote_asset_volume
        candleInverse.ignore = True
        candleInverse.is_closed = candle.is_closed
        candleInverse.event_time = candle.event_time

        self.monitorEntry(strategyName, conditions, candleInverse)



    def monitorEntry(self, strategyName, conditions, candle, imediateEntry=False):
        try:

            success = False

            self.setTradeParameters(strategyName)

            #logger.debug(self.qc_parameters_btc)
            #logger.debug(self.qc_parameters_eth)

            dnTrade = DNTrade()

            #signaltest = all(conditions)
            #if signaltest:
            #    print("signaltest:" + str(signaltest))
            if not imediateEntry:
                # check if it is a rebuy. if so, ignore indicator signals/trade limits and enter immediately. rebuys are only used for r/f buys.
                ignoreIndicatorSignal = False
                reEntryNumber = 0
                signalCode = 0
                if self.RebuyPercentage > 0 and self.RebuyTimeInSeconds > 0:
                    if strategyName == "R_Buy" or strategyName == "F_Buy":
                        dateCurrent = self.getCurrentDateTime(candle)
                        dateFrom = dateCurrent - timedelta(seconds=self.RebuyTimeInSeconds)
                        rebuyLimit = 99999
                        if self.RebuyMaxLimit > 0:
                            rebuyLimit = self.RebuyMaxLimit

                        rebuyTrades = dnTrade.listRebuyTrade(candle.symbol, strategyName, dateFrom, rebuyLimit, self.backtestId)

                        if rebuyTrades:
                            if rebuyTrades[0].PLAmount > 0:
                                exitPrice = rebuyTrades[0].ExitPrice
                                rebuyEntryPrice = self.addPercentageToPrice(exitPrice, self.RebuyPercentage)
                                currentPrice = decimal.Decimal(candle.close)
                                if currentPrice >= rebuyEntryPrice:
                                    reEntryNumber = rebuyTrades[0].ReEntryNumber + 1
                                    # if rebuy conditions are met, we will ignore the current indicator signals.
                                    ignoreIndicatorSignal = True
                                    self.printLog(candle.symbol + ": Reentry." + "Strategy:" + strategyName + ", ReEntryNumber:" + str(reEntryNumber) + ", CP:" + self.decToStr(currentPrice) + ", PrevExitPrice:" + self.decToStr(exitPrice) + ", RebuyEntryPrice:" + self.decToStr(rebuyEntryPrice))

                # if it is not a rebuy entry
                if not ignoreIndicatorSignal:
                    ## if pullback entries are enabled, check for pullback entry signals. 1=pullback entry, 2=expired pullback wait. for 2, indicator signals should also be true.
                    #if self.PullbackEntryPercentage > 0 and (strategyName == "R_Buy" or strategyName == "F_Buy"):
                    #    signalCode = self.getPullbackEntrySignal(strategyName, candle)
                    #    signal = signalCode == 1 or (signalCode == 2 and all(conditions))
                    #else:

                    # Get Indicator signals
                    signal = all(conditions)

                    if not signal:
                        #logger.debug('No signal.')
                        return False

                    # check limit for all trades except for rebuys. dont enter if the trade limit is reached.
                    if not self.backtestModeEnabled:
                        openTrades = dnTrade.listOpenTrade(self.backtestId)
                        if openTrades and len(openTrades) >= self.bot_parameters.maxConcurrentTradeNumber:
                            logger.debug ('Max concurrent trades reached.')
                            return False

            # we enter a trade
            self.printLog("Entering trade: " + strategyName)
            entryPrice = decimal.Decimal(candle.close)

            tradeAmount, quoteAmount = self.computeTradeAmount(candle)
            self.printLog("Trade Amount: " + str(tradeAmount))

            if tradeAmount == -1:
                self.printLog(candle.symbol + ": Invalid balance. Cant enter trade.")
                return False

            tradeType = ""
            side = ""
            if strategyName == "R_Buy" or strategyName == "F_Buy":
                side = ENUM_ORDER_SIDE.BUY
                tradeType = "Buy"
            elif strategyName == "S_Sell":
                side = ENUM_ORDER_SIDE.SELL
                tradeType = "Sell"

            if not self.hasEnoughBalance(candle.symbol, tradeAmount, tradeType, "Entry"):
                self.printLog(candle.symbol + ": Insufficient balance or very small amount. Cant enter trade.")
                return False

            logger.debug(f'Entering trade for {candle.symbol}')
            response = self.sendTradeOrder(candle.symbol, side, tradeAmount)
            logger.debug(f'Trade entry response: {response}')

            if response.status == "FILLED":
                filledAmount = decimal.Decimal(response.executed_qty)
                commission = decimal.Decimal(response.commission)

                if not self.backtestModeEnabled:
                    avgPrice = decimal.Decimal(response.avg_price)
                else:
                    avgPrice = candle.close

                success = filledAmount > 0
            else:
                logger.warning(f'Entry order for {candle.symbol} was not filled.')

            # If trade couldn't be opened, return.
            if not success:
                self.printLog("Trade could not be opened.")
                logger.warning(f'Entering a trade for {candle.symbol} failed.')
                return False

            self.printLog(candle.symbol +  " Trade opened for " + strategyName + ": EP:" + self.decToStr(entryPrice))

            # If trade is successful, save it.

            trade = Trade()
            trade.Symbol = candle.symbol
            trade.TradeType = tradeType
            trade.StrategyName = strategyName
            trade.EntryDate = self.getCurrentDateTime(candle) #datetime.now()
            trade.EntryCandleDate = datetime.fromtimestamp(candle.open_time / 1000, timezone('Etc/GMT0'))
            trade.Amount = filledAmount
            trade.QuoteAmount = quoteAmount
            trade.EntryPrice = avgPrice
            trade.EntryTriggerPrice = entryPrice
            trade.IsOpen = True
            trade.EntryCommission = commission
            trade.ExitCommission = 0
            trade.ReEntryNumber = reEntryNumber
            trade.CurrentPrice = avgPrice
            trade.IsTslActivated = False
            trade.BacktestId = self.backtestId

            #temp to see which trade is cross-graph
            #if not candle.ignore and candle.ignore == True:
            #    trade.TargetPrice = 100000

            # if small profit target is enabled, compute the target price.
            """
            if self.TargetPercentage > 0:
                if strategyName == "R_Buy" or strategyName == "F_Buy":
                    trade.TargetPrice = self.addPercentageToPrice(trade.EntryPrice, self.TargetPercentage + self.CommissionPercentage)
                elif strategyName == "S_Sell":
                    trade.TargetPrice = self.subtractPercentageFromPrice(trade.EntryPrice, self.TargetPercentage + self.CommissionPercentage)
            """

            # set stoploss timer
            if self.SLTimerInMinutes > 0:
                currentTimeInSeconds = self.getCurrentDateTimeInSeconds(candle)  #int(round(time.time()))  # This can be local time. It is just a timer.
                trade.TimerInSeconds = currentTimeInSeconds + self.SLTimerInMinutes * 60

            # set stoploss
            if self.SL1Percentage > 0:
                if strategyName == "R_Buy" or strategyName == "F_Buy":
                    sl = self.subtractPercentageFromPrice(trade.EntryPrice, self.SL1Percentage)
                elif strategyName == "S_Sell":
                    sl = self.addPercentageToPrice(trade.EntryPrice, self.SL1Percentage)

                trade.StopLoss = sl


            tradeId = dnTrade.insertTrade(trade)
            trade.TradeId = tradeId

            if self.SL1Percentage > 0:
                self.printLog(str(tradeId) + ": SL update for " + strategyName + ": EP:" + self.decToStr(trade.EntryPrice) + ", SL1Perc:" + self.decToStr(self.SL1Percentage) + ", SL1:" + self.decToStr(sl))

            comment = ""
            if ignoreIndicatorSignal:
                comment = "Rebuy " + str(reEntryNumber)

            #temp to see which trade is cross-graph
            #if not candle.ignore and candle.ignore == True:
            #	comment = comment + "-CrossGraph"

            #elif signalCode == 1:
            #    comment = "Pullback"
            #elif signalCode == 2:
            #    comment = "Expired Pullback"

            self.insertTradeLog(trade, candle, trade.TradeType, comment)

            return success

        except:
            self.printLog("Exception: monitorEntry", traceback.format_exc())


    def manualBuy(self, symbol):
        if not self.isRunning:
            self.printLog("Bot is not running. Run before manual buy.")
            return False

        # we enter a trade
        strategyName = "R_Buy"
        self.printLog("Entering manual trade: " + strategyName)
        self.setTradeParameters(strategyName)

        dnMarket = DNMarket()
        market = dnMarket.getMarketBySymbol(symbol)

        if self.bot_parameters.minDailyVolume > 0 and market.DailyVolume < self.bot_parameters.minDailyVolume:
            self.printLog("Pair volume is lower than min daily volume. Cannot buy.")
            return False

        if self.bot_parameters.minPrice > 0 and market.DailyPrice < self.bot_parameters.minPrice:
            self.printLog("Pair price is lower than min daily price. Cannot buy.")
            return False

        entryPrice = decimal.Decimal(market.LastPrice)

        candle = Candle()
        candle.symbol = symbol
        candle.close = market.LastPrice

        tradeAmount, quoteAmount = self.computeTradeAmount(candle)
        self.printLog("Trade Amount: " + str(tradeAmount))

        if tradeAmount == -1:
            self.printLog(candle.symbol + ": Invalid balance. Cant enter trade.")
            return False

        tradeType = ""
        side = ENUM_ORDER_SIDE.BUY
        tradeType = "Buy"

        if not self.hasEnoughBalance(candle.symbol, tradeAmount, tradeType, "Entry"):
            self.printLog(candle.symbol + ": Insufficient balance or very small amount. Cant enter trade.")
            return False

        response = self.sendTradeOrder(candle.symbol, side, tradeAmount)
        print("Trade result: ", response)

        success = False
        if response.status and response.status == "FILLED":
            filledAmount = decimal.Decimal(response.executed_qty)
            commission = decimal.Decimal(response.commission)

            if not self.backtestModeEnabled:
                avgPrice = decimal.Decimal(response.avg_price)
            else:
                avgPrice = candle.close

            success = filledAmount > 0

        # If trade couldn't be opened, return.
        if not success:
            self.printLog("Trade could not be opened.")
            return False

        self.printLog(candle.symbol + " Trade opened for " + strategyName + ": EP:" + self.decToStr(entryPrice))

        # If trade is successful, save it.

        trade = Trade()
        trade.Symbol = candle.symbol
        trade.TradeType = tradeType
        trade.StrategyName = strategyName
        trade.EntryDate = self.getCurrentDateTime(candle)  # datetime.now()
        trade.EntryCandleDate = datetime.fromtimestamp(candle.open_time / 1000, timezone('Etc/GMT0'))
        trade.Amount = filledAmount
        trade.QuoteAmount = quoteAmount
        trade.EntryPrice = avgPrice
        trade.EntryTriggerPrice = entryPrice
        trade.IsOpen = True
        trade.EntryCommission = commission
        trade.ExitCommission = 0
        trade.ReEntryNumber = 1
        trade.CurrentPrice = avgPrice
        trade.IsTslActivated = False
        trade.BacktestId = self.backtestId

        # set stoploss timer
        if self.SLTimerInMinutes > 0:
            currentTimeInSeconds = self.getCurrentDateTimeInSeconds(candle)
            trade.TimerInSeconds = currentTimeInSeconds + self.SLTimerInMinutes * 60

        # set stoploss
        sl = 0
        if self.SL1Percentage > 0:
            sl = self.subtractPercentageFromPrice(trade.EntryPrice, self.SL1Percentage)

        trade.StopLoss = sl

        dnTrade = DNTrade()
        tradeId = dnTrade.insertTrade(trade)
        trade.TradeId = tradeId

        self.printLog(str(tradeId) + ": SL update for " + strategyName + ": EP:" + self.decToStr(
            trade.EntryPrice) + ", SL1Perc:" + self.decToStr(self.SL1Percentage) + ", SL1:" + self.decToStr(sl))

        comment = "Manual Buy"
        self.insertTradeLog(trade, candle, trade.TradeType, comment)

    def decToStr(self, value):
        value = round(value, 8)
        return str(value)


    def monitorExit(self, trade, candle, immediateExit=False):
        try:
            if trade is None or not trade.IsOpen:
                self.printLog("Trade doesn't exist or it is not open. Exiting...")
                return

            tradeIdStr = str(trade.TradeId)

            checkForExit = True
            #currentCandleDate = datetime.fromtimestamp(candle.open_time / 1000, timezone('Etc/GMT0'))
            #if trade.EntryCandleDate == currentCandleDate:
            #    self.printLog(tradeIdStr + ": " + "Trade entered in this candle. Wont check for exit: " + trade.StrategyName)
            #    checkForExit = False

            self.setTradeParameters(trade.StrategyName)
            dnTrade = DNTrade()

            currentPrice = decimal.Decimal(candle.close)
            currentPrice = round(currentPrice, 8)

            comment = ""
            success = False
            tpSlHitPrice = 0

            if trade.TradeType == "Buy":
                shouldExit = False

                # immediate exit by VStop only when we are in profit
                if immediateExit and trade.PLAmount > 0:
                    shouldExit = True
                    comment = "VStop Exit"
                    self.printLog(tradeIdStr + ": " + comment + " for " + trade.StrategyName + ", CP:" + self.decToStr(currentPrice))

                # exit by SL or TSL hit
                if checkForExit and trade.StopLoss != 0 and currentPrice <= trade.StopLoss:
                    shouldExit = True
                    if not trade.IsTslActivated:
                        comment = "SL Hit"
                    else:
                        comment = "TSL Hit"

                    tpSlHitPrice = trade.StopLoss
                    self.printLog(tradeIdStr + ": " + comment + " for " + trade.StrategyName + ": SL:" + self.decToStr(
                        trade.StopLoss) + ", CP:" + self.decToStr(currentPrice))

                # exit by small profit target hit. only exits if target is hit before tsl is activated.
                if checkForExit and not trade.IsTslActivated and trade.TargetPrice != 0 and currentPrice >= trade.TargetPrice:
                    shouldExit = True
                    comment = "Target Hit"

                    tpSlHitPrice = trade.TargetPrice
                    self.printLog(tradeIdStr + ": " + comment + " for " + trade.StrategyName + ": Target:" + self.decToStr(
                        trade.TargetPrice) + ", CP:" + self.decToStr(currentPrice))

                # exit if btcusdt trend has changed, and trade.IsTslActivated
                #if checkForExit and self.btcTrending != self.btcTrendingPrev and (("UPUSDT" in candle.symbol and not self.btcTrending) or ("DOWNUSDT" in candle.symbol and self.btcTrending)):
                #    shouldExit = True
                #    comment = "Btcusdt trend change"
                #    tpSlHitPrice = currentPrice
                #    self.printLog(tradeIdStr + ": " + comment + ", CurrentTrend: " + str(self.btcTrending) + ", PrevTrend: " + str(self.btcTrendingPrev) + ", CP:" + self.decToStr(currentPrice))



                if shouldExit:
                    trade.CurrentPrice = decimal.Decimal(currentPrice)
                    # compute exit amount based on banking rules.Applies only to the exits of Buy trades.
                    exitAmount = self.computeExitAmount(trade)

                    if not self.hasEnoughBalance(candle.symbol, trade.Amount, "Sell", "Exit"):
                        self.printLog(tradeIdStr + ": " + candle.symbol + ":" + "Insufficient balance or very small amount. Cant exit trade.")
                        #self.markTradeAsClosed(trade.TradeId, "Insufficient balance") # This part may change in the future
                        return

                    logger.debug(f'Exiting trade for {candle.symbol}')
                    response = self.sendTradeOrder(candle.symbol, ENUM_ORDER_SIDE.SELL, exitAmount)
                    logger.debug(f'Trade exit response: {response}')

                    if response.status == "FILLED":
                        filledAmount = decimal.Decimal(response.executed_qty)
                        commission = decimal.Decimal(response.commission)
                        if not self.backtestModeEnabled:
                            avgPrice = decimal.Decimal(response.avg_price)
                        else:
                            avgPrice = tpSlHitPrice
                            #avgPrice = currentPrice

                        success = filledAmount > 0
                    else:
                        logger.warning(f'Exit order for {candle.symbol} was not filled.')

                    if success:
                        self.printLog(tradeIdStr + ": " + "Close successful: " + trade.StrategyName)
                        trade.ExitPrice = decimal.Decimal(avgPrice)
                        trade.ExitTriggerPrice = decimal.Decimal(currentPrice)
                        trade.ExitDate = self.getCurrentDateTime(candle) #datetime.now()
                        trade.IsOpen = False
                        trade.ExitCommission = decimal.Decimal(commission)
                        trade.CurrentPrice = decimal.Decimal(avgPrice) # this is used for pl computation
                        trade = self.computePL(trade)
                        trade.ModifiedDate = self.getCurrentDateTime(candle)

                        dnTrade.updateTrade(trade)

                        self.insertTradeLog(trade, candle, "Close", comment)
                        return
                    else:
                        logger.warning(f'Exiting trade for {candle.symbol} was not succsessfull.')


                # If neither SL or Target is hit, continue with updates...

                tslActivationPrice = self.addPercentageToPrice(trade.EntryPrice, self.TSLActivationPercentage)

                # If TSL activation price is reached.
                if currentPrice >= tslActivationPrice:
                    tslPrice = self.subtractPercentageFromPrice(currentPrice, self.TSLTrailPercentage)
                    if not trade.IsTslActivated:
                        self.printLog(tradeIdStr + ": " + "TSL activation for " + trade.StrategyName + ": TSLA:" + self.decToStr(tslActivationPrice) + ", CP:" + self.decToStr(currentPrice))
                    trade.IsTslActivated = True

                    # If TSL price is greater than current SL, set SL=TSLPrice
                    if tslPrice > trade.StopLoss:
                        self.printLog(tradeIdStr + ": " + "TSL update for " + trade.StrategyName + ": TSL:" + self.decToStr(tslPrice) + ", OSL:" + self.decToStr(trade.StopLoss))
                        trade.StopLoss = tslPrice
                        trade.TimerInSeconds = 0
                        self.insertTradeLog(trade, candle, "Modify", "TSL Update")

                else:
                    if trade.TimerInSeconds > 0:
                        #currentTime = int(round(time.time()))
                        currentTime = self.getCurrentDateTimeInSeconds(candle)

                        # If the timer is expired
                        if currentTime > trade.TimerInSeconds:
                            #trade.TimerInSeconds = currentTime + self.SLTimerInMinutes * 60
                            trade.TimerInSeconds = 0

                            sl2 = self.subtractPercentageFromPrice(currentPrice, self.SL2Percentage)
                            self.printLog(tradeIdStr + ": " + trade.StrategyName + " timer expired. Updating to SL2: CP:" + self.decToStr(currentPrice) + ", SL2:" + self.decToStr(sl2))

                            if sl2 > trade.StopLoss:
                                self.printLog(tradeIdStr + ": " + "SL2 updated for " + trade.StrategyName + ": SL:" + self.decToStr(sl2) + ", OSL:" + self.decToStr(trade.StopLoss))
                                trade.StopLoss = sl2
                                self.insertTradeLog(trade, candle, "Modify", "SL Update")
                            else:
                                self.printLog(tradeIdStr + ": " + "Cant update to SL2 because SL > SL2")

                trade.CurrentPrice = currentPrice
                trade = self.computePL(trade)
                trade.ModifiedDate = self.getCurrentDateTime(candle)

                dnTrade.updateTrade(trade)

            if trade.TradeType == "Sell":
                shouldExit = False
                if checkForExit and trade.StopLoss != 0 and currentPrice >= trade.StopLoss:
                    shouldExit = True
                    if not trade.IsTslActivated:
                        comment = "SL Hit"
                    else:
                        comment = "TSL Hit"

                    tpSlHitPrice = trade.StopLoss
                    self.printLog(tradeIdStr + ": " + comment + " for " + trade.StrategyName + ": SL:" + self.decToStr(trade.StopLoss) + ", CP:" + self.decToStr(currentPrice))

                # exit by small profit target hit. only exits if target is hit before tsl is activated.
                if checkForExit and not trade.IsTslActivated and trade.TargetPrice != 0 and currentPrice <= trade.TargetPrice:
                    shouldExit = True
                    comment = "Target Hit"

                    tpSlHitPrice = trade.TargetPrice
                    self.printLog(tradeIdStr + ": " + comment + " for " + trade.StrategyName + ": Target:" + self.decToStr(trade.TargetPrice) + ", CP:" + self.decToStr(currentPrice))

                if shouldExit:
                    trade.CurrentPrice = decimal.Decimal(currentPrice)

                    if not self.hasEnoughBalance(candle.symbol, trade.Amount, "Buy", "Exit"):
                        self.printLog(tradeIdStr + ": " + candle.symbol + ":" + "Insufficient balance or very small amount. Cant exit trade.")
                        #self.markTradeAsClosed(trade.TradeId, "Insufficient balance")  # This part may change in the future
                        return

                    response = self.sendTradeOrder(candle.symbol, ENUM_ORDER_SIDE.BUY, trade.Amount)
                    if response.status == "FILLED":
                        filledAmount = decimal.Decimal(response.executed_qty)
                        commission = decimal.Decimal(response.commission)
                        if not self.backtestModeEnabled:
                            avgPrice = decimal.Decimal(response.avg_price)
                        else:
                            #avgPrice = currentPrice
                            avgPrice = tpSlHitPrice
                        success = filledAmount > 0

                    if success:
                        self.printLog(tradeIdStr + ": " + "Close successful: " + trade.StrategyName)
                        trade.ExitPrice = decimal.Decimal(avgPrice)
                        trade.ExitTriggerPrice = decimal.Decimal(currentPrice)
                        trade.ExitDate = self.getCurrentDateTime(candle) #datetime.now()
                        trade.IsOpen = False
                        trade.ExitCommission = decimal.Decimal(commission)
                        trade.CurrentPrice = decimal.Decimal(avgPrice) # this is used for pl computation
                        trade = self.computePL(trade)
                        trade.ModifiedDate = self.getCurrentDateTime(candle)

                        dnTrade.updateTrade(trade)

                        self.insertTradeLog(trade, candle, "Close", comment)
                        return

                # If neither SL or Target is hit, continue with updates...

                tslActivationPrice = self.subtractPercentageFromPrice(trade.EntryPrice, self.TSLActivationPercentage)

                # If TSL activation price is reached.
                if currentPrice <= tslActivationPrice:
                    tslPrice = self.addPercentageToPrice(currentPrice, self.TSLTrailPercentage)
                    if not trade.IsTslActivated:
                        self.printLog(tradeIdStr + ": " + "TSL activation for " + trade.StrategyName + ": TSLA:" + self.decToStr(tslActivationPrice) + ", CP:" + self.decToStr(currentPrice))
                    trade.IsTslActivated = True

                    # If TSL price is smaller than current SL, set SL=TSLPrice
                    if tslPrice < trade.StopLoss:
                        self.printLog(tradeIdStr + ": " + "TSL update for " + trade.StrategyName + ": TSL:" + self.decToStr(tslPrice) + ", OSL:" + self.decToStr(trade.StopLoss))
                        trade.StopLoss = tslPrice
                        trade.TimerInSeconds = 0
                        self.insertTradeLog(trade, candle, "Modify", "TSL Update")

                else:
                    # If a timer is set.
                    if trade.TimerInSeconds > 0:
                        currentTime = int(round(time.time()))

                        # If the timer is expired
                        if currentTime > trade.TimerInSeconds:
                            #trade.TimerInSeconds = currentTime + self.SLTimerInMinutes * 60
                            trade.TimerInSeconds = 0

                            sl2 = self.addPercentageToPrice(currentPrice, self.SL2Percentage)
                            self.printLog(trade.StrategyName + " timer expired. Updating to SL2: CP:" + self.decToStr(currentPrice) + ", SL2:" + self.decToStr(sl2))

                            if sl2 < trade.StopLoss:
                                self.printLog(tradeIdStr + ": " + "SL2 updated for " + trade.StrategyName + ": SL:" + self.decToStr(sl2) + ", OSL:" + self.decToStr(trade.StopLoss))
                                trade.StopLoss = sl2
                                self.insertTradeLog(trade, candle, "Modify", "SL Update")
                            else:
                                self.printLog(tradeIdStr + ": " + "Cant update to SL2 because SL < SL2")

                trade.CurrentPrice = currentPrice
                trade = self.computePL(trade)
                trade.ModifiedDate = self.getCurrentDateTime(candle)

                dnTrade.updateTrade(trade)

        except:
            self.printLog("Exception: monitorExit", traceback.format_exc())

    def computeTotalUsedAmountForQuoteAsset(self, assetName, side):
        try:
            dnTrade = DNTrade()
            totalUsedAmount = 0

            trades = dnTrade.listOpenTradeByQuoteAsset(assetName)

            if trades:
                for t in trades:
                    if t.TradeType == side:
                        totalUsedAmount = totalUsedAmount + t.QuoteAmount

            return totalUsedAmount
        except:
            self.printLog("Exception: computeTotalUsedAmountForQuoteAsset", traceback.format_exc())

    def computeTotalUsedAmountForBaseAsset(self, assetName, side):
        try:
            dnTrade = DNTrade()
            totalUsedAmount = 0

            trades = dnTrade.listOpenTradeByBaseAsset(assetName)

            if trades:
                for t in trades:
                    if t.TradeType == side:
                        totalUsedAmount = totalUsedAmount + t.Amount

            return totalUsedAmount
        except:
            self.printLog("Exception: computeTotalUsedAmountForBaseAsset", traceback.format_exc())

    def round_decimals_down(self, number, decimals: int = 2):
        """
        Returns a value rounded down to a specific number of decimal places.
        """
        if not isinstance(decimals, int):
            raise TypeError("decimal places must be an integer")
        elif decimals < 0:
            raise ValueError("decimal places has to be 0 or more")
        elif decimals == 0:
            return math.floor(number)

        factor = 10 ** decimals
        return math.floor(number * factor) / factor

    def computeTotalUsedBaseAmountForSymbol(self, symbol, side):
        try:
            dnTrade = DNTrade()
            totalUsedAmount = 0

            trades = dnTrade.listOpenTradeBySymbol(symbol)
            if trades:
                for t in trades:
                    if t.TradeType == side:
                        totalUsedAmount = totalUsedAmount + t.Amount

            return totalUsedAmount
        except:
            self.printLog("Exception: computeTotalUsedBaseAmountForSymbol", traceback.format_exc())

    # This is only used to compute banking, for exits in buy trades.
    def computeExitAmount(self, trade):
        try:
            if trade is None:
                self.printLog("computeExitAmount: trade is None")
                return 0

            # in backtest mode, dont do banking
            if self.backtestModeEnabled:
                return trade.Amount

            if trade.TradeType == "Sell":
                self.printLog("computeExitAmount: trade is Sell")
                return trade.Amount

            if self.bot_parameters is None:
                dnBotParameters = DNBotParameters()
                self.bot_parameters = dnBotParameters.getBotParameters()

            dnMarket = DNMarket()
            market = dnMarket.getMarketBySymbol(trade.Symbol)
            if market is None:
                self.printLog("computeExitAmount: market is None:" + trade.Symbol)
                return 0

            binanceBalance = self.getBalance(market.BaseAsset)
            if binanceBalance is None:
                self.printLog("computeExitAmount: binanceBalance is None:" + trade.Symbol)
                return 0

            baseBalance = decimal.Decimal(binanceBalance.free)
            baseBalance = self.roundDown(baseBalance, market.AmountDecimalDigits)
            self.printLog("computeExitAmount: RealBaseBalance: " + str(binanceBalance.free))
            self.printLog("computeExitAmount: RealBaseBalanceDecRound: " + str(baseBalance))

            #dnAsset = DNAsset()
            #asset = dnAsset.getAsset(market.BaseAsset)
            #if asset is None:
            #    self.printLog("computeExitAmount: asset is None:" + market.BaseAsset)
            #    return 0



            # if exiting with loss
            if trade.CurrentPrice < trade.EntryPrice:
                self.printLog("computeExitAmount: Trade is not profitable. Wont bank coins.")
                exitAmount = trade.Amount
                # if balance is lower than exit amount, we exit the full balance.
                if exitAmount * market.LastPrice >= market.MinAmountToTrade and exitAmount > baseBalance:
                    self.printLog("Updating ExitAmount to Balance: From " + str(exitAmount) + " to " + str(baseBalance))
                    exitAmount = baseBalance

                exitAmount = self.roundDown(exitAmount, market.AmountDecimalDigits)
                self.printLog("Rounding ExitAmount to: " + str(exitAmount))
                return exitAmount

            dnTrade = DNTrade()
            trades = dnTrade.listOpenTradeBySymbol(trade.Symbol)

            #Get all open Buy trades at the moment and compute the total of coins they use
            totalUsedAmount = 0
            totalOpenTradeNumber = 0
            if trades:
                for t in trades:
                    if t.TradeType == "Buy":
                        totalUsedAmount = totalUsedAmount + t.Amount
                        totalOpenTradeNumber = totalOpenTradeNumber + 1

            # Compute the average trade amount for buy
            avgUsedAmount = 0
            if totalOpenTradeNumber > 0:
                avgUsedAmount = totalUsedAmount / totalOpenTradeNumber

            totalUsedAmountForAsset = self.computeTotalUsedAmountForBaseAsset(market.BaseAsset, "Buy")

            # find the surplus of coins: all available coins - the total used for buys
            balanceAllocatedForSSell = baseBalance - totalUsedAmountForAsset

            baseBalance = self.roundDown(baseBalance, market.AmountDecimalDigits)
            totalUsedAmountForAsset = self.roundDown(totalUsedAmountForAsset, market.AmountDecimalDigits)
            avgUsedAmount = self.roundDown(avgUsedAmount, market.AmountDecimalDigits)
            balanceAllocatedForSSell = self.roundDown(balanceAllocatedForSSell, market.AmountDecimalDigits)

            # if the surplus is still small, then banking is enabled.
            bankingPercentage = self.bot_parameters.bankingPercentage / 100
            bankingBaseAmount = trade.Amount * decimal.Decimal(1-bankingPercentage)
            bankingBaseAmount = self.roundDown(bankingBaseAmount, market.AmountDecimalDigits)
            bankingQuoteAmount = bankingBaseAmount * market.LastPrice
            bankingEnabled = balanceAllocatedForSSell < avgUsedAmount and bankingQuoteAmount >= market.MinAmountToTrade

            # if we still have small amount of this coin, we will keep some buy exiting with a small sell, if no banking, we will exit with the regular amount
            if bankingEnabled:
                exitAmount = bankingBaseAmount
            else:
                exitAmount = trade.Amount

            # if balance is lower than exit amount, we exit the full balance.
            if exitAmount * market.LastPrice >= market.MinAmountToTrade and exitAmount > baseBalance:
                self.printLog("Updating ExitAmount to Balance: From " + str(exitAmount) + " to " + str(baseBalance))
                exitAmount = baseBalance

            exitAmount = self.roundDown(exitAmount, market.AmountDecimalDigits)
            bankingQuoteAmount = self.roundDown(bankingQuoteAmount, 8)

            self.printLog(
                "computeExitAmount: totalUsedAmountForAsset:" + str(totalUsedAmountForAsset) + ", avgUsedAmount:" + str(
                    avgUsedAmount) + ", baseBalance:" + str(baseBalance) + ", balanceAllocatedForSSell:" + str(
                    balanceAllocatedForSSell) + ", bankingEnabled:" + str(bankingEnabled) + ", tradeAmount:" + str(
                    trade.Amount) + ", exitAmount:" + str(exitAmount))

            self.printLog(
                "computeExitAmount: bankingBaseAmount:" + str(bankingBaseAmount) + ", bankingQuoteAmount:" + str(
                    bankingQuoteAmount) )

            return exitAmount

        except:
            self.printLog("Exception: computeExitAmount", traceback.format_exc())

    def roundDown(self, amount, digits):
        amount = decimal.Decimal(amount)
        roundedAmount = round(amount, digits)
        if roundedAmount <= amount:
            return roundedAmount

        minValue = 1 / pow(10, digits)

        roundedAmount = roundedAmount - decimal.Decimal(minValue)
        roundedAmount = round(roundedAmount, digits)
        return roundedAmount

    def subtractPercentageFromPrice(self, price, percentage):
        try:
            h = decimal.Decimal(100.0)
            result = price * (h - percentage) / h
            result = round(result, 8)

            # if a small percent is subtracted and it doesnt change the value, i subtract a minimum possible value to change the result.
            if round(price, 8) == result:
                result = result - decimal.Decimal(0.00000001)
                result = round(result, 8)

            return result
        except:
            self.printLog("Exception: subtractPercentageFromPrice", traceback.format_exc())

    def addPercentageToPrice(self, price, percentage):
        try:
            h = decimal.Decimal(100.0)
            result = price * (decimal.Decimal(1) + (percentage / h))
            result = round(result, 8)

            # if a small percent is added and it doesnt change the value, i add a minimum possible value to change the result.
            if round(price, 8) == result:
                result = result + decimal.Decimal(0.00000001)
                result = round(result, 8)

            return result
        except:
            self.printLog("Exception: addPercentageToPrice", traceback.format_exc())

    def computeTradeAmount(self, candle):
        try:
            if self.backtestModeEnabled:
                qcAmount = self.btTradeQuoteAmount
                baseAmount = qcAmount / candle.close
                return baseAmount, qcAmount

            currentPrice = candle.close
            symbol = candle.symbol

            #self.printLog("computeTradeAmount: " + candle.symbol)

            dnMarket = DNMarket()
            market = dnMarket.getMarketBySymbol(symbol)
            marketVolume = market.DailyVolume

            #self.printLog(symbol + ": DailyVolume: " + str(market.DailyVolume))

            balance = 0
            qcRange = None

            if market.QuoteAsset == "BTC":
                qcRange = self.qc_parameters_btc
                balanceBinance = self.client.get_asset_balance("BTC")
                balance = balanceBinance.free
            elif market.QuoteAsset == "USDT":
                qcRange = self.qc_parameters_usdt
                balanceBinance = self.client.get_asset_balance("USDT")
                balance = balanceBinance.free
            elif market.QuoteAsset == "ETH":
                qcRange = self.qc_parameters_eth
                balanceBinance = self.client.get_asset_balance("ETH")
                balance = balanceBinance.free
            elif market.QuoteAsset == "USD":
                qcRange = self.qc_parameters_bnb
                balanceBinance = self.client.get_asset_balance("USD")
                balance = balanceBinance.free

            if balance == 0:
                self.printLog(symbol + ": Balance is Zero")
                return -1,-1

            percentage = 0
            if float(qcRange.minVolume1) <= marketVolume <= float(qcRange.maxVolume1) and qcRange.perc1 > 0:
                percentage = qcRange.perc1
                self.printLog(symbol + ": Range 1 chosen.")
            elif float(qcRange.minVolume2) <= marketVolume <= float(qcRange.maxVolume2) and qcRange.perc2 > 0:
                percentage = qcRange.perc2
                self.printLog(symbol + ": Range 2 chosen.")
            elif float(qcRange.minVolume3) <= marketVolume <= float(qcRange.maxVolume3) and qcRange.perc3 > 0:
                percentage = qcRange.perc3
                self.printLog(symbol + ": Range 3 chosen.")
            elif float(qcRange.minVolume4) <= marketVolume <= float(qcRange.maxVolume4) and qcRange.perc4 > 0:
                percentage = qcRange.perc4
                self.printLog(symbol + ": Range 4 chosen.")
            elif float(qcRange.minVolume5) <= marketVolume <= float(qcRange.maxVolume5) and qcRange.perc5 > 0:
                percentage = qcRange.perc5
                self.printLog(symbol + ": Range 5 chosen.")
            elif float(qcRange.minVolume6) <= marketVolume <= float(qcRange.maxVolume6) and qcRange.perc6 > 0:
                percentage = qcRange.perc6
                self.printLog(symbol + ": Range 6 chosen.")
            else:
                percentage = qcRange.perc1
                #self.printLog(symbol + ": Error: No range is chosen. So chosing Range 1.")

            if percentage == 0:
                self.printLog(symbol + ": Percentage is Zero")
                return -1,-1

            if qcRange.dailySpendPerc == 0:
                self.printLog(symbol + ": DailySpendPerc is Zero")
                return -1,-1

            dailyPerc = qcRange.dailySpendPerc
            qcAmount = balance / 100 * float(dailyPerc)
            qcAmount = qcAmount / 100 * float(percentage)

            self.printLog(symbol + ": Balance: " + str(balance) + ", Percentage: " + str(percentage) + ", QcAmount: " + str(qcAmount))

            minTradeAmount = self.qc_parameters_usdt.rebuyTriggerAmount
            minTradeAmount = decimal.Decimal(minTradeAmount)

            if qcAmount < market.MinAmountToTrade or (symbol.endswith('USDT') and qcAmount < minTradeAmount):
                self.printLog("computeTradeAmount:" + symbol + ":" + "Amount smaller than MinAmountToTrade(Exchange) or MinTradeAmount(Qc Settings).")
                if symbol.endswith('USDT') and minTradeAmount > 0:
                    qcAmount = minTradeAmount
                else:
                    qcAmount = market.MinAmountToTrade * decimal.Decimal(1.2)

                qcAmount = round(qcAmount, 8)
                self.printLog("Updating quoteAmount to MinAmountToTrade: " + str(qcAmount))


            #if qcAmount >= market.MinAmountToTrade and qcAmount > balance:
            #    self.printLog("Updating quoteAmount to Balance: From " + str(qcAmount) + " to " + str(balance))
            #    qcAmount = balance

            # amount is the qc amount, now convert it to base amount

            baseAmount = float(qcAmount) / float(candle.close)
            baseAmount = round(baseAmount, market.AmountDecimalDigits)

            if baseAmount == 0:
                self.printLog(symbol + ": BaseAmountRound is Zero")
                return -1,-1

            return baseAmount, qcAmount
        except:
            self.printLog("Exception: computeTradeAmount", traceback.format_exc())
            return 0,0




    def insertTradeLog(self, trade, candle, action, comment):
        try:
            tradeLog = TradeLog()
            tradeLog.TradeId = trade.TradeId
            tradeLog.Symbol = trade.Symbol
            tradeLog.StrategyName = trade.StrategyName
            tradeLog.TradeType = trade.TradeType
            tradeLog.StopLoss = trade.StopLoss
            tradeLog.EntryPrice = trade.EntryPrice
            tradeLog.Amount = trade.Amount
            tradeLog.QuoteAmount = trade.QuoteAmount
            tradeLog.CreatedDate = self.getCurrentDateTime(candle) #datetime.now()
            tradeLog.PLPercentage = trade.PLPercentage
            tradeLog.PLAmount = trade.PLAmount
            tradeLog.EntryPrice = trade.EntryPrice
            tradeLog.CandleDate = trade.EntryCandleDate
            tradeLog.TargetPrice = trade.TargetPrice
            tradeLog.BacktestId = self.backtestId

            # for buy/sell/close, we assume currentprice is the executed avg price of the transaction. for everything else, it is the price from the websocket.
            if action == "Buy" or action == "Sell":
                tradeLog.CurrentPrice = trade.EntryPrice
            elif action == "Close":
                tradeLog.CurrentPrice = trade.ExitPrice
            elif candle is not None:
                tradeLog.CurrentPrice = candle.close
            else:
                tradeLog.CurrentPrice = trade.CurrentPrice

            tradeLog.Action = action
            tradeLog.Comment = comment
            tradeLog.Commission = trade.ExitCommission + trade.EntryCommission

            dnTradeLog = DNTradeLog()
            dnTradeLog.insertTradeLog(tradeLog)

        except:
            self.printLog("Exception: insertTradeLog", traceback.format_exc())

    def setTradeParameters(self, strategyName):
        try:
            sp = self.strategy_parameters

            if strategyName == "R_Buy":
                self.SL1Percentage = sp.R_SL1Percentage
                self.SL2Percentage = sp.R_SL2Percentage
                self.SLTimerInMinutes = sp.R_SLTimerInMinutes
                self.TSLActivationPercentage = sp.R_TSLActivationPercentage
                self.TSLTrailPercentage = sp.R_TSLTrailPercentage
            elif strategyName == "F_Buy":
                self.SL1Percentage = sp.F_SL1Percentage
                self.SL2Percentage = sp.F_SL2Percentage
                self.SLTimerInMinutes = sp.F_SLTimerInMinutes
                self.TSLActivationPercentage = sp.F_TSLActivationPercentage
                self.TSLTrailPercentage = sp.F_TSLTrailPercentage
            elif strategyName == "S_Sell":
                self.SL1Percentage = sp.S_SL1Percentage
                self.SL2Percentage = sp.S_SL2Percentage
                self.SLTimerInMinutes = sp.S_SLTimerInMinutes
                self.TSLActivationPercentage = sp.S_TSLActivationPercentage
                self.TSLTrailPercentage = sp.S_TSLTrailPercentage

            self.TargetPercentage = sp.TargetPercentage
            self.RebuyTimeInSeconds = sp.RebuyTimeInSeconds
            self.RebuyPercentage = sp.RebuyPercentage
            self.RebuyMaxLimit = sp.RebuyMaxLimit
            self.PullbackEntryPercentage = sp.PullbackEntryPercentage
            self.PullbackEntryWaitTimeInSeconds = sp.PullbackEntryWaitTimeInSeconds

        except:
            self.printLog("Exception: setTradeParameters", traceback.format_exc())

    def updateMarketState(self, candle, signals, conditions_r, conditions_f, conditions_s):
        try:
            roc: RocResult = signals[ENUM_INDICATOR.ROC].get_latest() if ENUM_INDICATOR.ROC in signals.keys() else None
            mpt_value = signals[ENUM_INDICATOR.MPT].get_latest().value if ENUM_INDICATOR.MPT in signals.keys() else None
            #trend_signal = signals[ENUM_INDICATOR.TREND].get_latest().signal if ENUM_INDICATOR.TREND in signals.keys() else None
            #emax_signal = signals[ENUM_INDICATOR.EMAX].get_latest().signal if ENUM_INDICATOR.EMAX in signals.keys() else None

            nv: NvResult = signals[ENUM_INDICATOR.NV].get_latest() if ENUM_INDICATOR.NV in signals.keys() else None
            rsi = signals[ENUM_INDICATOR.RSI].get_latest().value if ENUM_INDICATOR.RSI in signals.keys() else 0
            stoch = signals[ENUM_INDICATOR.STOCH].get_latest().slowk if ENUM_INDICATOR.STOCH in signals.keys() else 0

            market = Market()
            market.Symbol = candle.symbol

            market.LastPrice = candle.close
            market.R_ROC_Value = roc.change_r if roc and roc.change_r else 0
            market.R_ROC_Signal = conditions_r[0] #roc.signal_r if roc and roc.signal_r else 0
            market.R_MPT_Value = mpt_value if mpt_value else 0
            market.R_NV_BuyPercent = nv.buy_sell_percent if nv else 0
            market.R_NV_SellPercent = nv.sell_buy_percent if nv else 0
            market.R_NV_NetVolume = nv.net_volume if nv else 0
            market.R_ROC_MPT_Signal = conditions_r[1]

            market.Trend_Signal = conditions_r[2]
            market.R_NV_Signal = conditions_r[3]
            market.EMAX_Signal = conditions_r[4]
            market.VSTOP_Signal = conditions_r[5]
            market.ST_Signal = conditions_r[6]
            market.R_Signal = all(conditions_r)

            market.F_ROC_Value = roc.change_f if roc and roc.change_f else 0
            market.F_ROC_Signal = roc.signal_f if roc and roc.signal_f else False
            market.F_ROC_MPT_Signal = conditions_f[0]
            market.F_Signal = all(conditions_f)
            market.F_NV_Signal = conditions_f[2]

            market.S_ROC_Value = roc.change_s if roc and roc.change_s else 0
            market.S_Rsi_Value = float(rsi)
            market.S_Stoch_Value = float(stoch)
            market.S_ROC_Signal = conditions_s[0]
            market.S_Rsi_Signal = conditions_s[1]
            market.S_Stoch_Signal = conditions_s[2]
            market.S_Signal = all(conditions_s)
            market.ModifiedDate = datetime.now()

            dn_market = DNMarket()
            dn_market.updateMarketStats(market)

        except:
            self.printLog("Exception: updateMarketState", traceback.format_exc())


    """
    def insertTickData(self, candle, signals):
        try:

            market = Market()
            market.Symbol = candle.symbol
            market.LastPrice = candle.close
            market.R_ROC_Value = roc.change_r if roc and roc.change_r else 0
            market.R_ROC_Signal = roc.signal_r if roc and roc.signal_r else 0
            market.R_MPT_Value = mpt_value if mpt_value else 0
            market.R_NV_BuyPercent = nv.buy_sell_percent if nv else 0
            market.R_NV_SellPercent = nv.sell_buy_percent if nv else 0
            market.R_NV_NetVolume = nv.net_volume if nv else 0
            market.R_ROC_MPT_Signal = conditions_r[0]
            market.Trend_Signal = trend_signal if trend_signal else 0
            market.R_NV_Signal = conditions_r[2]
            market.R_Signal = all(conditions_r)
            market.F_ROC_Value = roc.change_f if roc and roc.change_f else 0
            market.F_ROC_Signal = roc.signal_f if roc and roc.signal_f else 0
            market.F_ROC_MPT_Signal = conditions_f[0]
            market.F_Signal = all(conditions_f)
            market.F_NV_Signal = conditions_f[2]
            market.S_ROC_Value = roc.change_s if roc and roc.change_s else 0
            market.S_Rsi_Value = float(rsi)
            market.S_Stoch_Value = float(stoch)
            market.S_ROC_Signal = conditions_s[0]
            market.S_Rsi_Signal = conditions_s[1]
            market.S_Stoch_Signal = conditions_s[2]
            market.S_Signal = all(conditions_s)
            market.ModifiedDate = datetime.now()

            dn_market = DNMarket()
            dn_market.updateMarketStats(market)

        except:
            self.printLog("Exception: updateMarketState", traceback.format_exc())
    """

    def insertIndicatorLog(self, candle: Candle, signals, conditions_r, conditions_f, conditions_s, rBuyTradeCount, fBuyTradeCount, sSellTradeCount):
        try:
            """
            print("\n")
            print(candle.open, candle.close, candle.high, candle.low)
            for name, result in signals.items():
                print(result)
            print(conditions_r)
            print(conditions_f)
            print(conditions_s)
            """

            #if self.backtestModeEnabled:
            #	return

            # Indicators: roc,mpt,trend,nv,emax,vstop

            roc: RocResult = signals[ENUM_INDICATOR.ROC].get_latest() if ENUM_INDICATOR.ROC in signals.keys() else None
            mpt_value = signals[ENUM_INDICATOR.MPT].get_latest().value if ENUM_INDICATOR.MPT in signals.keys() else None
            trend_signal = signals[ENUM_INDICATOR.TREND].get_latest().signal if ENUM_INDICATOR.TREND in signals.keys() else None
            nv: NvResult = signals[ENUM_INDICATOR.NV].get_latest() if ENUM_INDICATOR.NV in signals.keys() else None
            emax_signal = signals[ENUM_INDICATOR.EMAX].get_latest().signal if ENUM_INDICATOR.EMAX in signals.keys() else None
            st_signal = signals[ENUM_INDICATOR.ST].get_latest().signal if ENUM_INDICATOR.ST in signals.keys() else None
            vstop_signal = signals[ENUM_INDICATOR.VSTOP].get_latest().uptrend if ENUM_INDICATOR.VSTOP in signals.keys() else None
            rsi = signals[ENUM_INDICATOR.RSI].get_latest().value if ENUM_INDICATOR.RSI in signals.keys() else 0
            stoch = signals[ENUM_INDICATOR.STOCH].get_latest().slowk if ENUM_INDICATOR.STOCH in signals.keys() else 0

            log = IndicatorLog()
            log.Symbol = candle.symbol
            log.CreatedDate = self.getCurrentDateTime(candle)

            if not self.backtestModeEnabled:
                log.CandleDate = datetime.fromtimestamp(candle.open_time / 1000, timezone('Etc/GMT0'))
            else:
                log.CandleDate = datetime.fromtimestamp(candle.open_time / 1000)

            log.CurrentPrice = candle.close
            log.R_ROC_Value = roc.change_r if roc and roc.change_r else 0
            log.R_ROC_Signal = roc.signal_r if roc and roc.signal_r else 0
            log.R_MPT_Value = mpt_value if mpt_value else 0

            log.R_NV_BuyPercent = nv.buy_sell_percent if nv and nv.buy_sell_percent else 0
            log.R_NV_SellPercent = nv.sell_buy_percent if nv and nv.sell_buy_percent else 0
            log.R_NV_NetVolume = nv.net_volume if nv and nv.net_volume else 0
            log.R_NV_Signal = conditions_r[3]

            log.R_ROC_MPT_Signal = conditions_r[0]
            log.Trend_Signal = trend_signal if trend_signal else 0

            log.EMAX_Signal = conditions_r[4]
            log.VSTOP_Signal = conditions_r[5]
            log.ST_Signal = conditions_r[6]

            log.R_Signal = all(conditions_r)

            #log.F_ROC_Value = roc.change_f if roc and roc.change_f else 0
            #log.F_ROC_Signal = roc.signal_f if roc and roc.signal_f else 0
            #log.F_ROC_MPT_Signal = conditions_f[0]
            #log.F_Signal = all(conditions_f)
            #log.F_NV_Signal = conditions_f[2]

            log.S_ROC_Value = roc.change_s if roc and roc.change_s else 0
            log.S_Rsi_Value = float(rsi)
            log.S_Stoch_Value = float(stoch)
            log.S_ROC_Signal = conditions_s[0]
            log.S_Rsi_Signal = conditions_s[1]
            log.S_Stoch_Signal = conditions_s[2]
            log.S_Signal = all(conditions_s)

            log.R_Open_Count = rBuyTradeCount
            log.F_Open_Count = fBuyTradeCount
            log.S_Open_Count = sSellTradeCount

            log.BacktestId = self.backtestId

            dn_log = DNIndicatorLog()
            dn_log.insertIndicatorLog(log)

            if log.R_Signal or log.F_Signal or log.S_Signal:

                signal = Signal()
                signal.Symbol = log.Symbol
                signal.CurrentPrice = log.CurrentPrice
                signal.CreatedDate = log.CreatedDate
                signal.CandleDate = log.CandleDate
                signal.BacktestId = self.backtestId

                dnSignal = DNSignal()
                if log.R_Signal:
                    signal.StrategyName = "R_Buy"
                    dnSignal.insertSignal(signal)
                if log.F_Signal:
                    signal.StrategyName = "F_Buy"
                    dnSignal.insertSignal(signal)
                if log.S_Signal:
                    signal.StrategyName = "S_Sell"
                    dnSignal.insertSignal(signal)


        except:
            self.printLog("Exception: insertIndicatorLog", traceback.format_exc())

    def updateAssets(self):
        try:
            assets = self.client.get_asset_balances()
            if assets:
                dn_asset = DNAsset()
                dn_asset.resetAllAssets()
                dn_asset.updateAssets(assets)

        except:
            self.printLog("Exception: updateAssets", traceback.format_exc())

    def addCandleToMarketState(self, candle, timeframe):
        try:
            key = (candle.symbol, timeframe)
            if key not in self.market_state.keys() or not self.market_state[key]:
                # if empty
                self.market_state[key] = [candle]
            else:
                #print("Updating...." + str(len(self.market_state[key])))
                last_candle = self.market_state[key][-1]
                if candle.open_time == last_candle.open_time:
                    self.market_state[key][-1] = candle
                else:
                    self.market_state[key].append(candle)
        except:
            self.printLog("Exception: addCandleToMarketState", traceback.format_exc())

    def checkEntryForRbuy(self, signals, candles):
        try:
            # Indicators: roc,mpt,trend,nv,emax,vstop,st
            conditions = [False] * 7

            if not self.strategy_parameters.R_TradingEnabled:
                return conditions

            # conditions[0]: [ROC]
            if not self.strategy_parameters.ROC_IndicatorEnabled:
                conditions[0] = True
            else:
                roc_r = signals[ENUM_INDICATOR.ROC].get_latest().signal_r
                if roc_r is not None:
                    conditions[0] = roc_r == 1

            # conditions[1]: [MPT] price > MPT
            if not self.strategy_parameters.MPT_IndicatorEnabled:
                conditions[1] = True
            else:
                mpt = signals[ENUM_INDICATOR.MPT].get_latest().value
                price = candles[-1].close
                if mpt is not None:
                    conditions[1] = price > mpt

            # conditions[2]: [TREND] Are we in an up Trend = false (must be in a down trend)
            if not self.strategy_parameters.TREND_IndicatorEnabled:
                conditions[2] = True
            else:
                trend = signals[ENUM_INDICATOR.TREND].get_latest().signal
                if trend is not None:
                    conditions[2] = trend == 1

            # conditions[3]: [NV] NV must be bullish
            if not self.strategy_parameters.NV_IndicatorEnabled:
                conditions[3] = True
            else:
                nv: NvResult = signals[ENUM_INDICATOR.NV].get_latest()
                conditions[3] = nv.buy_sell_percent >= self.strategy_parameters.NV_IncreasePercentage and \
                                nv.net_volume >= self.strategy_parameters.NV_MinNetVolume

            # conditions[4]: [EMAX] if Bullish cross, then emax=1
            if not self.strategy_parameters.EMAX_IndicatorEnabled:
                conditions[4] = True
            else:
                emax = signals[ENUM_INDICATOR.EMAX].get_latest().signal
                if emax is not None:
                    conditions[4] = emax == 1

            # conditions[5]: [VSTOP]
            if not self.strategy_parameters.VSTOP_IndicatorEnabled:
                conditions[5] = True
            else:
                vstop = signals[ENUM_INDICATOR.VSTOP].get_latest().signals
                if vstop is not None:
                    conditions[5] = vstop == 1

            # conditions[6]: [ST]
            if not self.strategy_parameters.ST_IndicatorEnabled:
                conditions[6] = True
            else:
                st = signals[ENUM_INDICATOR.ST].get_latest().signal
                if ALWAYS_GENERATE_ST_LONG_BUY_SIGNAL:
                    st = 1
                if st is not None:
                    conditions[6] = st == 1
                    if st == 1:
                        logger.debug('ST signal')


            return conditions

        except:
            self.printLog("Exception: checkEntryForRbuy", traceback.format_exc())

    # def __check_entry_for_r_buy_test(self, roc_r, mpt, trend, nv, candle):
    #     try:
    #         conditions = [False] * 3
    #
    #         # if all indicators are off, don't enter a trade
    #         if not self.strategy_parameters.TREND_IndicatorEnabled and not self.strategy_parameters.NV_IndicatorEnabled and \
    #                 not (self.strategy_parameters.ROC_IndicatorEnabled and self.strategy_parameters.MPT_IndicatorEnabled):
    #             return conditions
    #
    #         # Condition-1: [ROC & MPY] Is current ROC price > MPT price (ROC & MPT)
    #         if not (self.strategy_parameters.ROC_IndicatorEnabled and self.strategy_parameters.MPT_IndicatorEnabled):
    #             conditions[0] = True
    #         else:
    #             price = candle.close
    #             if roc_r and mpt:
    #                 conditions[0] = roc_r == 1 and price > mpt
    #
    #         # Condition-2: [Trend] Are we in an up Trend = true (must be in an up trend)
    #         if not self.strategy_parameters.TREND_IndicatorEnabled:
    #             conditions[1] = True
    #         else:
    #             if trend:
    #                 conditions[1] = trend == 1
    #
    #         # Condition-3: [NV] NV must be bullish
    #         if not self.strategy_parameters.NV_IndicatorEnabled:
    #             conditions[2] = True
    #         else:
    #             if nv:
    #                 conditions[2] = nv == 1
    #
    #         return conditions
    #
    #     except:
    #         self.printLog("Exception: __check_entry_for_r_buy_test", traceback.format_exc())

    # not used anymore
    def checkEntryForFbuy(self, signals, candles):
        try:
            conditions = [False] * 3

            if not self.strategy_parameters.F_TradingEnabled:
                return conditions

            # Condition-1: [Roc & Mpt] Is current ROC price < MPT price (ROC & MPT)
            if not (self.strategy_parameters.ROC_IndicatorEnabled and self.strategy_parameters.MPT_IndicatorEnabled):
                conditions[0] = True
            else:
                roc_f = signals[ENUM_INDICATOR.ROC].get_latest().signal_f
                mpt = signals[ENUM_INDICATOR.MPT].get_latest().value
                price = candles[-1].close
                if roc_f is not None and mpt is not None:
                    conditions[0] = roc_f == 1 and price < mpt

            # Condition-2: [Trend] Are we in an up Trend = false (must be in a down trend)
            if not self.strategy_parameters.TREND_IndicatorEnabled:
                conditions[1] = True
            else:
                trend = signals[ENUM_INDICATOR.TREND].get_latest().signal
                if trend is not None:
                    conditions[1] = trend == 0

            # Condition-3: [NV]
            if not self.strategy_parameters.NV_IndicatorEnabled:
                conditions[2] = True
            else:
                nv: NvResult = signals[ENUM_INDICATOR.NV].get_latest()
                conditions[2] = nv.sell_buy_percent >= self.strategy_parameters.NV_IncreasePercentage and \
                                (-1*nv.net_volume) >= self.strategy_parameters.NV_MinNetVolume

            return conditions

        except:
            self.printLog("Exception: checkEntryForFbuy", traceback.format_exc())

    # def __check_entry_for_f_buy_test(self, roc_f, mpt, trend, candle):
    #     conditions = [False] * 2
    #
    #     # if all indicators are off, don't enter a trade
    #     if not (self.strategy_parameters.ROC_IndicatorEnabled and self.strategy_parameters.MPT_IndicatorEnabled) and \
    #             not self.strategy_parameters.TREND_IndicatorEnabled:
    #         return conditions
    #
    #     # Condition-1: [Roc & Mpt] Is current ROC price < MPT price (ROC & MPT)
    #     if not (self.strategy_parameters.ROC_IndicatorEnabled and self.strategy_parameters.MPT_IndicatorEnabled):
    #         conditions[0] = True
    #     else:
    #         price = candle.close
    #         if roc_f and mpt:
    #             conditions[0] = roc_f == 1 and price < mpt
    #
    #     # Condition-2: [Trend] Are we in an up Trend = false (must be in a down trend)
    #     if not self.strategy_parameters.TREND_IndicatorEnabled:
    #         conditions[1] = True
    #     else:
    #         if trend is not None:
    #             conditions[1] = trend == 0
    #
    #     return conditions

    def checkEntryForSsell(self, signals, candles):
        try:
            conditions = [False] * 7

            if not self.strategy_parameters.S_TradingEnabled:
                return conditions

            #if not self.strategy_parameters.SELL_IndicatorEnabled:
            #    return conditions

            # conditions[0]: [ROC]
            if not self.strategy_parameters.ROC_IndicatorEnabled:
                conditions[0] = True
            else:
                roc_s = signals[ENUM_INDICATOR.ROC].get_latest().signal_s
                if roc_s is not None:
                    conditions[0] = roc_s == 1

            # conditions[1]: [MPT] price < MPT
            if not self.strategy_parameters.MPT_IndicatorEnabled:
                conditions[1] = True
            else:
                mpt = signals[ENUM_INDICATOR.MPT].get_latest().value
                price = candles[-1].close
                if mpt is not None:
                    conditions[1] = price < mpt

            # conditions[2]: [TREND] Are we in an up Trend = false (must be in a down trend)
            if not self.strategy_parameters.TREND_IndicatorEnabled:
                conditions[2] = True
            else:
                trend = signals[ENUM_INDICATOR.TREND].get_latest().signal
                if trend is not None:
                    conditions[2] = trend == 0

            # conditions[3]: [NV]
            if not self.strategy_parameters.NV_IndicatorEnabled:
                conditions[3] = True
            else:
                nv: NvResult = signals[ENUM_INDICATOR.NV].get_latest()
                conditions[3] = nv.sell_buy_percent >= self.strategy_parameters.NV_IncreasePercentage and \
                                (-1*nv.net_volume) >= self.strategy_parameters.NV_MinNetVolume

            # conditions[4]: [EMAX] if Bearish cross, then emax=-1
            if not self.strategy_parameters.EMAX_IndicatorEnabled:
                conditions[4] = True
            else:
                emax = signals[ENUM_INDICATOR.EMAX].get_latest().signal
                if emax is not None:
                    conditions[4] = emax == -1

            # conditions[5]: [VSTOP]
            if not self.strategy_parameters.VSTOP_IndicatorEnabled:
                conditions[5] = True
            else:
                vstop = signals[ENUM_INDICATOR.VSTOP].get_latest().signals
                if vstop is not None:
                    conditions[5] = vstop == -1

                #vstop = not signals[ENUM_INDICATOR.VSTOP].get_latest().uptrend
                #if vstop is not None:
                #    conditions[5] = vstop

            # conditions[6]: [ST]
            if not self.strategy_parameters.ST_IndicatorEnabled:
                conditions[6] = True
            else:
                st = signals[ENUM_INDICATOR.ST].get_latest().signal
                if ALWAYS_GENERATE_ST_SHORT_SELL_SIGNAL:
                    st = -1
                if st is not None:
                    conditions[6] = st == -1

            # Condition-1
            #rsi = signals[ENUM_INDICATOR.RSI].get_latest().value
            #if rsi is not None:
            #    conditions[1] = utils.compare_floats(rsi, self.strategy_parameters.SELL_RSI_LowerLevel) < 0 or \
            #                    utils.compare_floats(rsi, self.strategy_parameters.SELL_RSI_UpperLevel) > 0

            # Condition-2
            #stoch = signals[ENUM_INDICATOR.STOCH].get_latest().slowk
            #if stoch is not None:
            #    conditions[2] = utils.compare_floats(stoch, self.strategy_parameters.SELL_Stoch_LowerLevel) < 0 or \
            #                    utils.compare_floats(stoch, self.strategy_parameters.SELL_Stoch_UpperLevel) > 0

            return conditions
        except:
            self.printLog("Exception: checkEntryForFbuy", traceback.format_exc())

    # def __check_entry_for_s_sell_test(self, roc_s, rsi, stoch):
    #     conditions = [False] * 3
    #
    #     if not self.strategy_parameters.SELL_IndicatorEnabled:
    #         return conditions
    #
    #     conditions[0] = roc_s
    #     conditions[1] = utils.compare_floats(rsi, self.strategy_parameters.SELL_RSI_LowerLevel) < 0 or \
    #                     utils.compare_floats(rsi, self.strategy_parameters.SELL_RSI_UpperLevel) > 0
    #     conditions[2] = utils.compare_floats(stoch, self.strategy_parameters.SELL_Stoch_LowerLevel) < 0 or \
    #                     utils.compare_floats(stoch, self.strategy_parameters.SELL_Stoch_UpperLevel) > 0
    #
    #     return conditions

    def initClient(self):
        if self.client is not None:
            print("No need to init binance")
            return

        dnBotParameters = DNBotParameters()
        bot_parameters = dnBotParameters.getBotParameters()
        self.client = ExchangeClient(self.exchange_type, bot_parameters.apiKey, bot_parameters.secretKey)

    def sendTradeOrder(self, symbol, side, tradeAmount) -> OrderResponse:
        response = None
        sideStr = ""
        if side == ENUM_ORDER_SIDE.BUY:
            sideStr = "Buy"
        elif side == ENUM_ORDER_SIDE.SELL:
            sideStr = "Sell"

        if symbol is None or symbol == "":
            self.printLog(symbol + ": " + "Symbol is invalid")
            return response
        if side is None or side == "":
            self.printLog(symbol + ": " + "Side is invalid")
            return response
        if tradeAmount is None or tradeAmount == 0:
            self.printLog(symbol + ": " + "TradeAmount is invalid")
            return response

        self.printLog("sendTradeOrder: " + symbol + ": " + sideStr + ", " + str(tradeAmount) + ", " + str(datetime.now()))

        # if backtesting
        try:
            if self.backtestModeEnabled:
                response = OrderResponse()
                response.status = "FILLED"
                response.executed_qty = tradeAmount
                response.commission = tradeAmount / 100 * self.CommissionPercentage
                return response
        except:
            self.printLog("Exception: sendTradeOrder", traceback.format_exc())

        #if client is not init
        if self.client is None:
            self.initClient()

        # try:
        if side == ENUM_ORDER_SIDE.BUY:
            if TEST_MODE:
                logger.info(f'Test mode is enabled. Ignoring BUY for {symbol}')
            else:
                logger.info(f'Creating BUY for {symbol}')
                response = self.client.buy_asset(symbol, float(tradeAmount))
                logger.info(f'BUY response for {symbol}: {response}')
        elif side == ENUM_ORDER_SIDE.SELL:
            if TEST_MODE:
                logger.info(f'Test mode is enabled. Ignoring SELL for {symbol}')
            else:
                logger.info(f'Creating SELL for {symbol}')
                response = self.client.sell_asset(symbol, float(tradeAmount))
                logger.info(f'SELL response for {symbol}: {response}')

        try:
            if response.status == 'FILLED':
                #self.printLog("Exchange order: " + symbol + ": " + sideStr + " " + str(tradeAmount), str(response))

                # After every successful transaction, update balance of both assets.
                dnMarket = DNMarket()
                market = dnMarket.getMarketBySymbol(symbol)
                if market is not None:
                    self.getBalance(market.BaseAsset)
                    self.getBalance(market.QuoteAsset)
            else:
                logger.warning(f'Response status is not FILLED: {response}')
        except:
            self.printLog("Exception: sendTradeOrder", traceback.format_exc())

        return response

    def insertBotLog(self, shortLog, longLog):
        try:
            if self.backtestModeEnabled:
                #print("backtest enabled")
                return

            dnBotLog = DNBotLog()
            botLog = BotLog()
            botLog.ShortLog = shortLog
            botLog.LongLog = longLog
            botLog.CreatedDate = datetime.now()
            dnBotLog.insertBotLog(botLog)

            if "Timestamp for this request was 1000ms" in shortLog or "recvWindow" in shortLog:
                self.swtUpdate.emit("PcClockOutOfSync")
                self.stop()

        except:
            self.printLog("Exception: insertBotLog", traceback.format_exc())

    def printLog(self, shortLog, longLog="", logToDb=True):
        try:
            #return

            print(shortLog, longLog)
            if logToDb:
                self.insertBotLog(shortLog, longLog)
        except:
            self.printLog("Exception: printLog", traceback.format_exc())

    def validateParameters(self):
        try:
            validated = True
            if self.bot_parameters is None:
                self.printLog("bot_parameters is None")
                validated = False
            if self.strategy_parameters is None:
                self.printLog("strategy_parameters is None")
                validated = False
            if self.strategy_parameters_default is None:
                self.printLog("strategy_parameters_default is None")
                validated = False
            if self.qc_parameters_btc is None:
                self.printLog("qc_parameters_btc is None")
                validated = False
            if self.qc_parameters_usdt is None:
                self.printLog("qc_parameters_usdt is None")
                validated = False
            if self.qc_parameters_eth is None:
                self.printLog("qc_parameters_eth is None")
                validated = False
            if self.qc_parameters_bnb is None:
                self.printLog("qc_parameters_usd is None")
                validated = False
            if self.bot_parameters.runOnSelectedMarkets == False and self.quoteAssets == "":
                self.printLog("No qc market selected to trade.")
                validated = False

            return validated

        except:
            self.printLog("Exception: validateParameters", traceback.format_exc())

    def computeMaxCandleNumber(self):
        try:
            maxCandleNumber = 1
            sp = self.strategy_parameters

            if sp.ROC_IndicatorEnabled:
                maxCandleNumber = max(maxCandleNumber, sp.ROC_Period_R)
                maxCandleNumber = max(maxCandleNumber, sp.ROC_Period_F)

            if sp.MPT_IndicatorEnabled:
                maxCandleNumber = max(maxCandleNumber, sp.MPT_ShortMAPeriod)
                maxCandleNumber = max(maxCandleNumber, sp.MPT_LongMAPeriod)

            if sp.TREND_IndicatorEnabled:
                maxCandleNumber = max(maxCandleNumber, sp.TREND_LongEmaPeriod)
                maxCandleNumber = max(maxCandleNumber, sp.TREND_ShortEmaPeriod)

            if sp.EMAX_IndicatorEnabled:
                maxCandleNumber = max(maxCandleNumber, sp.EMAX_LongEmaPeriod)
                maxCandleNumber = max(maxCandleNumber, sp.EMAX_ShortEmaPeriod)

            if sp.ST_IndicatorEnabled:
                maxCandleNumber = max(maxCandleNumber, sp.ST_AtrPeriod)

            if sp.VSTOP_IndicatorEnabled:
                maxCandleNumber = max(maxCandleNumber, sp.VSTOP_Period)

            if sp.SELL_IndicatorEnabled and sp.S_TradingEnabled:
                maxCandleNumber = max(maxCandleNumber, sp.SELL_Period)
                maxCandleNumber = max(maxCandleNumber, sp.SELL_RSI_Period)
                maxCandleNumber = max(maxCandleNumber, sp.SELL_Stoch_KPeriod)
                maxCandleNumber = max(maxCandleNumber, sp.SELL_Stoch_DPeriod)
                maxCandleNumber = max(maxCandleNumber, sp.SELL_Stoch_Slowing)
                maxCandleNumber = max(maxCandleNumber, sp.SELL_RSI_Period)
                maxCandleNumber = max(maxCandleNumber, sp.SELL_RSI_Period)

            maxCandleNumber = max(maxCandleNumber + 1, MAX_NUMBER_OF_CANDLES_AT_INITIALIZARION)

            return maxCandleNumber

        except:
            self.printLog("Exception: computeMaxCandleNumber", traceback.format_exc())


    def getBalance(self, assetName):
        try:
            print("GetBalance")

            if self.client is None:
                self.initClient()



            balance = self.client.get_asset_balance(assetName)
            if balance is None:
                self.printLog(assetName + ": getBalance:balance is None.")
                return

            dnAsset = DNAsset()
            asset = dnAsset.getAsset(assetName)

            update = False
            if asset is None:
                asset = Asset()
            else:
                update = True

            asset.AssetName = assetName
            asset.BalanceFree = balance.free
            asset.BalanceLocked = balance.locked
            asset.ModifiedDate = datetime.now()

            #self.printLog(assetName + ": getBalance:Updating balance.")
            if update:
                dnAsset.updateAsset(asset)
            else:
                dnAsset.insertAsset(asset)

            return balance

        except:
            self.printLog("Exception: getBalance", traceback.format_exc())


    def hasEnoughBalance(self, symbol, baseAmount, side, action):
        try:
            if self.backtestModeEnabled:
                return True

            dnMarket = DNMarket()
            market = dnMarket.getMarketBySymbol(symbol)

            # If no market, cant check for balance
            if market is None:
                self.printLog("hasEnoughBalance:market is None: " + symbol)
                return True

            if market.LastPrice is None or market.LastPrice == 0:
                self.printLog("hasEnoughBalance:market.LastPrice is None: " + symbol)
                return True

            isUsd = symbol.endswith('USD') or symbol.endswith('USDT')

            result = False
            dnAsset = DNAsset()
            baseAmount = decimal.Decimal(baseAmount)
            baseAmount = round(baseAmount,8)
            lockedBaseAmount = 0
            lockedQuoteAmount = 0
            lockedAmount = 0

            if side == "Buy":
                asset = dnAsset.getAsset(market.QuoteAsset)

                # Not created in db yet, get it from binance and update
                if asset is None or asset.BalanceFree == -1:
                    quoteBalance = self.getBalance(market.QuoteAsset).free
                else:
                    quoteBalance = asset.BalanceFree


                #quoteBalance = self.getBalance(market.QuoteAsset).free

                quoteBalance = decimal.Decimal(quoteBalance)
                quoteBalance = round(quoteBalance, market.AmountDecimalDigits)



                # for r/f entry check if there is any locked amount by s sells
                if action == "Entry":
                    lockedQuoteAmount = self.computeTotalUsedAmountForQuoteAsset(market.QuoteAsset, "Sell")
                    #self.printLog("hasEnoughBalance:lockedQuoteAmount: " + str(lockedQuoteAmount))
                #elif action == "Rebuy":
                #    lockedQuoteAmount = self.qc_parameters_usdt.rebuyTriggerAmount
                #self.printLog("hasEnoughBalance:min usdt amount to keep: " + str(lockedQuoteAmount))

                quoteAmount = baseAmount * market.LastPrice
                quoteAmount = round(quoteAmount, 8)

                minTradeAmount = self.qc_parameters_usdt.rebuyTriggerAmount
                minTradeAmount = decimal.Decimal(minTradeAmount)

                if quoteAmount < market.MinAmountToTrade or (isUsd and quoteAmount < minTradeAmount):
                    self.printLog("hasEnoughBalance:" + symbol + ":" + "Amount smaller than MinAmountToTrade(Exchange) or MinTradeAmount(Qc Settings).")
                    #if we are trading usdt, use self.qc_parameters_usdt.rebuyTriggerAmount amount for MinTradeAmount. The name is misleading.Needs to be renamed.

                    if isUsd and minTradeAmount > 0:
                        quoteAmount = minTradeAmount
                    else:
                        quoteAmount = market.MinAmountToTrade * decimal.Decimal(1.2)

                    quoteAmount = round(quoteAmount, 8)
                    self.printLog("Updating quoteAmount to MinAmountToTrade: " + str(quoteAmount))

                if quoteBalance - lockedQuoteAmount >= quoteAmount:
                    result = True

                # in exits, if balance is smaller than the trade amount, exit the whole balance. balance should also be above MinAmountToTrade
                if action == "Exit" and quoteAmount >= market.MinAmountToTrade and quoteBalance - lockedQuoteAmount >= market.MinAmountToTrade and quoteAmount > quoteBalance - lockedQuoteAmount:
                    self.printLog("Buy-Exit: Balance is smaller than ExitAmount. ExitAmount will be the full balance.")
                    result = True


                balance = quoteBalance
                totalNeeded = quoteAmount
                lockedAmount = lockedQuoteAmount

            elif side == "Sell":
                #asset = dnAsset.getAsset(market.BaseAsset)

                # Not created in db yet, get it from binance and update
                #if asset is None or asset.BalanceFree == -1:
                #    baseBalance = self.getBalance(market.BaseAsset).free
                #else:
                #    baseBalance = asset.BalanceFree

                baseBalance = self.getBalance(market.BaseAsset).free
                baseBalance = decimal.Decimal(baseBalance)

                #for ssell entry check if there is any locked amount by f and r buys
                if action == "Entry":
                    lockedBaseAmount = self.computeTotalUsedAmountForBaseAsset(market.BaseAsset, "Buy")
                    #self.printLog("hasEnoughBalance:lockedBaseAmount: " + str(lockedBaseAmount))

                baseAmount = round(baseAmount, 8)

                if baseBalance - lockedBaseAmount >= baseAmount:
                    result = True

                if baseAmount * market.LastPrice < market.MinAmountToTrade:
                    self.printLog("hasEnoughBalance:" + symbol + ":" + "Amount smaller than MinAmountToTrade.")
                    result = False

                # in exits, if balance is smaller than the trade amount, exit the whole balance. balance should also be above MinAmountToTrade
                if action == "Exit" and baseAmount * market.LastPrice >= market.MinAmountToTrade and (baseBalance - lockedBaseAmount) * market.LastPrice >= market.MinAmountToTrade and baseAmount > baseBalance - lockedBaseAmount :
                    self.printLog("Sell-Exit: Balance is smaller than ExitAmount. ExitAmount will be the full balance.")
                    result = True

                balance = baseBalance
                totalNeeded = baseAmount
                lockedAmount = lockedBaseAmount

            self.printLog("hasEnoughBalance:" + symbol + ", BaseAmount:" + str(baseAmount) + ", Locked:" + str(lockedAmount) + ", Price:" + str(
                market.LastPrice) + ", Side:" + side + ", TotalNeeded:" + str(totalNeeded) + ", MinNotional:" + str(
                market.MinAmountToTrade) + ", Balance:" + str(balance) + ", Result:" + str(result))

            return result

        except:
            self.printLog("Exception: hasEnoughBalance", traceback.format_exc())

    def markTradeAsClosed(self, tradeId, comment):
        try:
            dnTrade = DNTrade()
            trade = dnTrade.getTrade(tradeId)
            if trade is None:
                self.printLog("markTradeAsClosed:  trade is None: " + str(tradeId))
                return

            dnMarket = DNMarket()
            market = dnMarket.getMarketBySymbol(trade.Symbol)
            if market is None:
                self.printLog("markTradeAsClosed:  market is None: " + str(tradeId))
                return

            trade.IsOpen = False
            trade.ExitPrice = market.LastPrice
            trade.ExitTriggerPrice = 0
            trade.ExitDate = datetime.now()
            trade.CurrentPrice = market.LastPrice
            trade = self.computePL(trade)

            trade.ModifiedDate = datetime.now()
            dnTrade.updateTrade(trade)
            self.insertTradeLog(trade, None, "Close", comment)

        except:
            self.printLog("Exception: markTradeAsClosed", traceback.format_exc())


    def setEntryEnabled(self, value):
        self.entryEnabled = value

    def getEntryEnabled(self):
        return self.entryEnabled

    def setRunning(self, value):
        self.isRunning = value

    def isBotRunning(self):
        return self.isRunning

    def isDataCollectorRunning(self):
        return self.dataCollectorRunning

    def isBacktestRunning(self):
        return self.backtestRunning

    def isOptimizationsRunning(self):
        return self.optimizationRunning

    def setDataCollectorModeEnabled(self, value):
        self.dataCollectorModeEnabled = value

    def setBacktestModeEnabled(self, value):
        self.backtestModeEnabled = value

    def setUpdateMarketsForOptimizationModeEnabled(self, value):
        self.updateMarketsForOptimization = value

    def exitAllTrades(self):
        try:
            self.printLog("Exiting all trades.")

            dnTrade = DNTrade()
            openTrades = dnTrade.listOpenTrade(self.backtestId)
            if openTrades:
                for trade in openTrades:
                    self.exitTrade(trade.TradeId)

            self.swtUpdate.emit("ExitAllTradesFinished")

        except:
            self.printLog("Exception: exitAllTrades", traceback.format_exc())

    def exitAllMarginTrades(self):
        try:
            exitMarginType = "UPUSDT"
            if self.btcTrending:
                exitMarginType = "DOWNUSDT"

            self.printLog("Exiting all margin trades: " + exitMarginType)

            dnTrade = DNTrade()
            openTrades = dnTrade.listOpenTrade(self.backtestId)
            if openTrades:
                for trade in openTrades:
                    if exitMarginType in trade.Symbol:
                        self.exitTrade(trade.TradeId)


        except:
            self.printLog("Exception: exitAllMarginTrades", traceback.format_exc())

    def exitTrade(self, tradeId):
        try:
            dnTrade = DNTrade()
            trade = dnTrade.getTrade(tradeId)

            if trade is None or not trade.IsOpen:
                self.printLog("Trade doesn't exist or it is not open. Exiting...")
                return

            dnMarket = DNMarket()
            market = dnMarket.getMarketBySymbol(trade.Symbol)
            currentPrice = decimal.Decimal(market.LastPrice)
            comment = "Manual Close"

            if trade.TradeType == "Buy":
                oppositeTradeType = "Sell"
                oppositeEnumOrderSide = ENUM_ORDER_SIDE.SELL
                # compute exit amount based on banking rules.Applies to only Buy exits
                trade.CurrentPrice = decimal.Decimal(currentPrice)
                exitAmount = self.computeExitAmount(trade)
            else:
                oppositeTradeType = "Buy"
                oppositeEnumOrderSide = ENUM_ORDER_SIDE.BUY
                exitAmount = trade.Amount

            if not self.hasEnoughBalance(trade.Symbol, exitAmount, oppositeTradeType, "Exit"):
                self.printLog(trade.Symbol + ":" + str(trade.TradeId) + ":" + "Insufficient balance or very small amount. Cant exit trade.")
                #self.markTradeAsClosed(trade.TradeId, comment)  # This part may change in the future
                return

            response = self.sendTradeOrder(trade.Symbol, oppositeEnumOrderSide, exitAmount)
            success = False
            avgPrice = 0
            commission = 0
            if response.status == "FILLED":
                filledAmount = decimal.Decimal(response.executed_qty)
                commission = decimal.Decimal(response.commission)
                avgPrice = decimal.Decimal(response.avg_price)
                success = filledAmount > 0

            if success:
                self.printLog(str(trade.TradeId) + ": " + "Close successful: " + trade.StrategyName)
                trade.ExitPrice = decimal.Decimal(avgPrice)
                trade.ExitTriggerPrice = decimal.Decimal(currentPrice)
                trade.ExitDate = datetime.now()
                trade.IsOpen = False
                trade.CurrentPrice = decimal.Decimal(avgPrice)
                trade.ExitCommission = decimal.Decimal(commission)
                trade = self.computePL(trade)
                trade.ModifiedDate = datetime.now()

                dnTrade = DNTrade()
                dnTrade.updateTrade(trade)

                self.insertTradeLog(trade, None, "Close", comment)

        except:
            self.printLog("Exception: exitTrade", traceback.format_exc())


    def computePL(self, trade):
        try:
            if trade is None:
                return trade

            if trade.TradeType == "":
                self.printLog("computePL:  trade.TradeType is empty. Cant compute PL.")
                return trade

            if trade.EntryPrice == 0:
                self.printLog("computePL:  trade.EntryPrice = 0. Cant compute PL.")
                return trade

            if trade.CurrentPrice == 0:
                self.printLog("computePL:  trade.CurrentPrice = 0. Cant compute PL.")
                return trade

            if trade.Amount == 0:
                self.printLog("computePL:  trade.Amount = 0. Cant compute PL.")
                return trade

            if trade.TradeType == "Buy":
                trade.PLAmount = (trade.CurrentPrice - trade.EntryPrice) * trade.Amount
                trade.PLPercentage = (trade.CurrentPrice - trade.EntryPrice) / trade.EntryPrice * decimal.Decimal(100.0)
            elif trade.TradeType == "Sell":
                trade.PLAmount = (trade.CurrentPrice - trade.EntryPrice) * decimal.Decimal(-1) * trade.Amount
                trade.PLPercentage = (trade.CurrentPrice - trade.EntryPrice) * decimal.Decimal(-1) / trade.EntryPrice * decimal.Decimal(100.0)

            if trade.IsOpen:
                endDate = datetime.now()
            else:
                endDate = trade.ExitDate

            # compute daily margin fee perc for upusdt,downusdt pairs.
            dailyCommissionPercentageForMargin = self.ComputeMarginCommissionPercentage(trade.Symbol, trade.EntryDate, endDate)
            commissionAmount = trade.QuoteAmount / decimal.Decimal(100.0) * (self.CommissionPercentage + dailyCommissionPercentageForMargin)

            trade.PLAmount = trade.PLAmount - commissionAmount
            trade.PLPercentage = trade.PLPercentage - self.CommissionPercentage - dailyCommissionPercentageForMargin

            return trade

        except:
            self.printLog("Exception: computePL", traceback.format_exc())


    def makeQcBuys(self):
        try:
            self.printLog("Qc buys started.")

            if self.qc_parameters_usdt is None:
                self.printLog("qc_parameters_usdt is None. Cannot continue qc buys. Exiting.")
                return

            if self.qc_parameters_btc is not None and self.qc_parameters_btc.tradeEnabled:
                if self.qc_parameters_btc.rebuyTriggerAmount > 0 and self.qc_parameters_btc.rebuyAmount > 0:
                    balance = self.getBalance("BTC")
                    self.printLog("BTC Balance: " + str(balance))
                    if balance.free < self.qc_parameters_btc.rebuyTriggerAmount:
                        self.printLog("BTC Rebuy triggered.")
                        if not self.hasEnoughBalance("BTC-USD", self.qc_parameters_btc.rebuyAmount, "Buy", "Rebuy"):
                            self.printLog("Insufficient balance or very small amount for BTC Rebuy.")
                        else:
                            self.printLog("Buying BTC.")
                            self.sendTradeOrder("BTC-USD", ENUM_ORDER_SIDE.BUY, self.qc_parameters_btc.rebuyAmount)
                    else:
                        self.printLog("No need for BTC rebuy.")

            if self.qc_parameters_eth is not None and self.qc_parameters_eth.tradeEnabled:
                if self.qc_parameters_eth.rebuyTriggerAmount > 0 and self.qc_parameters_eth.rebuyAmount > 0:
                    balance = self.getBalance("ETH")
                    self.printLog("ETH Balance: " + str(balance))
                    if balance.free < self.qc_parameters_eth.rebuyTriggerAmount:
                        self.printLog("ETH Rebuy triggered.")
                        if not self.hasEnoughBalance("ETH-USD", self.qc_parameters_btc.qc_parameters_eth, "Buy", "Rebuy"):
                            self.printLog("Insufficient balance or very small amount for ETH Rebuy.")
                        else:
                            self.printLog("Buying ETH.")
                            self.sendTradeOrder("ETH-USD", ENUM_ORDER_SIDE.BUY, self.qc_parameters_eth.rebuyAmount)
                    else:
                        self.printLog("No need for ETH rebuy.")

            """
            if self.qc_parameters_bnb is not None:
                if self.qc_parameters_bnb.rebuyTriggerAmount > 0 and self.qc_parameters_bnb.rebuyAmount > 0:
                    balance = self.getBalance("BNB")
                    self.printLog("BNB Balance: " + str(balance))
                    if balance.free < self.qc_parameters_bnb.rebuyTriggerAmount:
                        self.printLog("BNB Rebuy triggered.")
                        if not self.hasEnoughBalance("BNBUSDT", self.qc_parameters_bnb.rebuyAmount, "Buy", "Rebuy"):
                            self.printLog("Insufficient balance or very small amount for BNB Rebuy.")
                        else:
                            self.printLog("Buying BNB.")
                            self.sendTradeOrder("BNBUSDT", ENUM_ORDER_SIDE.BUY, self.qc_parameters_bnb.rebuyAmount)
                    else:
                        self.printLog("No need for BNB rebuy.")
            """

            self.printLog("Qc buys ended.")

        except:
            self.printLog("Exception: makeQcBuys", traceback.format_exc())


    def computeBacktestStats(self, backtestId, durationInMinutes):
        try:
            dnBacktest = DNBacktest()
            backtest = dnBacktest.getBacktest(backtestId)

            if not backtest:
                return

            dnTrade = DNTrade()
            trades = dnTrade.listClosedTradeByBacktestId(backtestId)

            secondsDiff = (self.btEndDate - self.btStartDate).total_seconds()
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

            index = -1
            if backtest.Symbol.endswith('BTC'):
                index = 0
            elif backtest.Symbol.endswith('USDT'):
                index = 1
            elif backtest.Symbol.endswith('ETH'):
                index = 2
            elif backtest.Symbol.endswith('USD'):
                index = 3

            if trades:
                for t in trades:
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
                            avgTimeInTradeInMinutes[index] = avgTimeInTradeInMinutes[index] + decimal.Decimal(dateDiff.seconds / 60)

                dnMarket = DNMarket()
                if plAmount[0] > 0:
                    btcusdt = dnMarket.getMarketBySymbol("BTC-USD")
                    plUsd[0] = plAmount[0] * btcusdt.LastPrice
                if plAmount[2] > 0:
                    ethusdt = dnMarket.getMarketBySymbol("ETH-USD")
                    plUsd[2] = plAmount[2] * ethusdt.LastPrice
                if plAmount[3] > 0:
                    #bnbusdt = dnMarket.getMarketBySymbol("USDUSDT")
                    plUsd[3] = plAmount[3] #* bnbusdt.LastPrice

                for i in range(4):
                    if closedTradeCount[i] > 0:
                        avgPLTrade[i] = plAmount[i] / closedTradeCount[i]
                        avgTradeAmount[i] = avgTradeAmount[i] / closedTradeCount[i]
                        avgTimeInTradeInMinutes[i] = avgTimeInTradeInMinutes[i] / closedTradeCount[i]
                        avgPLPercentage[i] = plPercentage[i] / closedTradeCount[i]

                    if avgTimeInTradeInMinutes[i] > 0:
                        tradeCountPerHour[i] = closedTradeCount[i] / dateDiffInHours
                        plAmountPerHour[i] = plAmount[i] / dateDiffInHours

            backtest.DurationInMinutes = durationInMinutes
            backtest.TotalTrades = totalTradeCount[index]
            backtest.TotalTradesPerHour = tradeCountPerHour[index]
            backtest.PLPercentage = plPercentage[index]
            backtest.PLAmount = plAmount[index]
            backtest.PLAmountPerHour = plAmountPerHour[index]
            backtest.PLUsd = plUsd[index]
            backtest.AvgPLTrade= avgPLTrade[index]
            backtest.AvgPLPercentage = avgPLPercentage[index]
            backtest.AvgTradeAmount = avgTradeAmount[index]

            backtest.AvgTimeInTradeInMinutes = avgTimeInTradeInMinutes[index]
            dnBacktest.updateBacktest(backtest)

        except:
            self.printLog("Exception: initStatsDatagrid", traceback.format_exc())

    def getLosingParameter(self, sp, spPrev):

        print("getLosingParameter: " + str(sp.StrategyParametersId) + "    " + str(spPrev.StrategyParametersId))
        dnStrategyParameters = DNStrategyParameters()

        if sp.PLPercentage < spPrev.PLPercentage:
            losingSp = dnStrategyParameters.set(sp, False)
        else:
            losingSp = dnStrategyParameters.set(spPrev, False)

        propertyName = "ROC_IndicatorEnabled"
        if getattr(sp, propertyName) != getattr(spPrev, propertyName):
            return propertyName, getattr(losingSp, propertyName)

        propertyName = "ROC_AppliedPrice_R"
        if getattr(sp, propertyName) != getattr(spPrev, propertyName):
            print(getattr(sp, propertyName))
            print(getattr(spPrev, propertyName))
            return propertyName, getattr(losingSp, propertyName)

        propertyName = "ROC_AppliedPrice_F"
        if getattr(sp, propertyName) != getattr(spPrev, propertyName):
            return propertyName, getattr(losingSp, propertyName)

        propertyName = "ROC_Period_R"
        if getattr(sp, propertyName) != getattr(spPrev, propertyName):
            return propertyName, getattr(losingSp, propertyName)

        propertyName = "ROC_Period_F"
        if getattr(sp, propertyName) != getattr(spPrev, propertyName):
            return propertyName, getattr(losingSp, propertyName)

        propertyName = "ROC_R_BuyIncreasePercentage"
        if getattr(sp, propertyName) != getattr(spPrev, propertyName):
            return propertyName, getattr(losingSp, propertyName)

        propertyName = "ROC_F_BuyDecreasePercentage"
        if getattr(sp, propertyName) != getattr(spPrev, propertyName):
            return propertyName, getattr(losingSp, propertyName)

        propertyName = "MPT_IndicatorEnabled"
        if getattr(sp, propertyName) != getattr(spPrev, propertyName):
            return propertyName, getattr(losingSp, propertyName)
        propertyName = "MPT_AppliedPrice"
        if getattr(sp, propertyName) != getattr(spPrev, propertyName):
            return propertyName, getattr(losingSp, propertyName)
        propertyName = "MPT_ShortMAPeriod"
        if getattr(sp, propertyName) != getattr(spPrev, propertyName):
            return propertyName, getattr(losingSp, propertyName)
        propertyName = "MPT_LongMAPeriod"
        if getattr(sp, propertyName) != getattr(spPrev, propertyName):
            return propertyName, getattr(losingSp, propertyName)

        propertyName = "NV_IndicatorEnabled"
        if getattr(sp, propertyName) != getattr(spPrev, propertyName):
            return propertyName, getattr(losingSp, propertyName)
        propertyName = "NV_IncreasePercentage"
        if getattr(sp, propertyName) != getattr(spPrev, propertyName):
            return propertyName, getattr(losingSp, propertyName)
        propertyName = "NV_MinNetVolume"
        if getattr(sp, propertyName) != getattr(spPrev, propertyName):
            return propertyName, getattr(losingSp, propertyName)

        propertyName = "TREND_IndicatorEnabled"
        if getattr(sp, propertyName) != getattr(spPrev, propertyName):
            return propertyName, getattr(losingSp, propertyName)
        propertyName = "TREND_AppliedPrice"
        if getattr(sp, propertyName) != getattr(spPrev, propertyName):
            return propertyName, getattr(losingSp, propertyName)
        propertyName = "TREND_LongEmaPeriod"
        if getattr(sp, propertyName) != getattr(spPrev, propertyName):
            return propertyName, getattr(losingSp, propertyName)
        propertyName = "TREND_ShortEmaPeriod"
        if getattr(sp, propertyName) != getattr(spPrev, propertyName):
            return propertyName, getattr(losingSp, propertyName)

        propertyName = "EMAX_IndicatorEnabled"
        if getattr(sp, propertyName) != getattr(spPrev, propertyName):
            return propertyName, getattr(losingSp, propertyName)
        propertyName = "EMAX_AppliedPrice"
        if getattr(sp, propertyName) != getattr(spPrev, propertyName):
            return propertyName, getattr(losingSp, propertyName)
        propertyName = "EMAX_LongEmaPeriod"
        if getattr(sp, propertyName) != getattr(spPrev, propertyName):
            return propertyName, getattr(losingSp, propertyName)
        propertyName = "EMAX_ShortEmaPeriod"
        if getattr(sp, propertyName) != getattr(spPrev, propertyName):
            return propertyName, getattr(losingSp, propertyName)

        propertyName = "ST_IndicatorEnabled"
        if getattr(sp, propertyName) != getattr(spPrev, propertyName):
            return propertyName, getattr(losingSp, propertyName)
        propertyName = "ST_AppliedPrice"
        if getattr(sp, propertyName) != getattr(spPrev, propertyName):
            return propertyName, getattr(losingSp, propertyName)
        propertyName = "ST_AtrPeriod"
        if getattr(sp, propertyName) != getattr(spPrev, propertyName):
            return propertyName, getattr(losingSp, propertyName)
        propertyName = "ST_AtrMultiplier"
        if getattr(sp, propertyName) != getattr(spPrev, propertyName):
            return propertyName, getattr(losingSp, propertyName)
        propertyName = "ST_UseWicks"
        if getattr(sp, propertyName) != getattr(spPrev, propertyName):
            return propertyName, getattr(losingSp, propertyName)

        propertyName = "VSTOP_IndicatorEnabled"
        if getattr(sp, propertyName) != getattr(spPrev, propertyName):
            return propertyName, getattr(losingSp, propertyName)
        propertyName = "VSTOP_AppliedPrice"
        if getattr(sp, propertyName) != getattr(spPrev, propertyName):
            return propertyName, getattr(losingSp, propertyName)
        propertyName = "VSTOP_Period"
        if getattr(sp, propertyName) != getattr(spPrev, propertyName):
            return propertyName, getattr(losingSp, propertyName)
        propertyName = "VSTOP_Factor"
        if getattr(sp, propertyName) != getattr(spPrev, propertyName):
            return propertyName, getattr(losingSp, propertyName)

        propertyName = "SELL_IndicatorEnabled"
        if getattr(sp, propertyName) != getattr(spPrev, propertyName):
            return propertyName, getattr(losingSp, propertyName)
        propertyName = "SELL_DecreasePercentage"
        if getattr(sp, propertyName) != getattr(spPrev, propertyName):
            return propertyName, getattr(losingSp, propertyName)
        propertyName = "SELL_Period"
        if getattr(sp, propertyName) != getattr(spPrev, propertyName):
            return propertyName, getattr(losingSp, propertyName)
        propertyName = "SELL_RSI_AppliedPrice"
        if getattr(sp, propertyName) != getattr(spPrev, propertyName):
            return propertyName, getattr(losingSp, propertyName)
        propertyName = "SELL_RSI_Period"
        if getattr(sp, propertyName) != getattr(spPrev, propertyName):
            return propertyName, getattr(losingSp, propertyName)
        propertyName = "SELL_RSI_UpperLevel"
        if getattr(sp, propertyName) != getattr(spPrev, propertyName):
            return propertyName, getattr(losingSp, propertyName)
        propertyName = "SELL_RSI_LowerLevel"
        if getattr(sp, propertyName) != getattr(spPrev, propertyName):
            return propertyName, getattr(losingSp, propertyName)
        propertyName = "SELL_Stoch_KPeriod"
        if getattr(sp, propertyName) != getattr(spPrev, propertyName):
            return propertyName, getattr(losingSp, propertyName)
        propertyName = "SELL_Stoch_DPeriod"
        if getattr(sp, propertyName) != getattr(spPrev, propertyName):
            return propertyName, getattr(losingSp, propertyName)
        propertyName = "SELL_Stoch_Slowing"
        if getattr(sp, propertyName) != getattr(spPrev, propertyName):
            return propertyName, getattr(losingSp, propertyName)
        propertyName = "SELL_Stoch_UpperLevel"
        if getattr(sp, propertyName) != getattr(spPrev, propertyName):
            return propertyName, getattr(losingSp, propertyName)
        propertyName = "SELL_Stoch_LowerLevel"
        if getattr(sp, propertyName) != getattr(spPrev, propertyName):
            return propertyName, getattr(losingSp, propertyName)


        propertyName = "R_TradingEnabled"
        if getattr(sp, propertyName) != getattr(spPrev, propertyName):
            return propertyName, getattr(losingSp, propertyName)
        propertyName = "R_SL1Percentage"
        if getattr(sp, propertyName) != getattr(spPrev, propertyName):
            return propertyName, getattr(losingSp, propertyName)
        propertyName = "R_SL2Percentage"
        if getattr(sp, propertyName) != getattr(spPrev, propertyName):
            return propertyName, getattr(losingSp, propertyName)
        propertyName = "R_SLTimerInMinutes"
        if getattr(sp, propertyName) != getattr(spPrev, propertyName):
            return propertyName, getattr(losingSp, propertyName)
        propertyName = "R_TSLActivationPercentage"
        if getattr(sp, propertyName) != getattr(spPrev, propertyName):
            return propertyName, getattr(losingSp, propertyName)
        propertyName = "R_TSLTrailPercentage"
        if getattr(sp, propertyName) != getattr(spPrev, propertyName):
            return propertyName, getattr(losingSp, propertyName)
        propertyName = "F_TradingEnabled"
        if getattr(sp, propertyName) != getattr(spPrev, propertyName):
            return propertyName, getattr(losingSp, propertyName)
        propertyName = "F_SL1Percentage"
        if getattr(sp, propertyName) != getattr(spPrev, propertyName):
            return propertyName, getattr(losingSp, propertyName)
        propertyName = "F_SL2Percentage"
        if getattr(sp, propertyName) != getattr(spPrev, propertyName):
            return propertyName, getattr(losingSp, propertyName)
        propertyName = "F_SLTimerInMinutes"
        if getattr(sp, propertyName) != getattr(spPrev, propertyName):
            return propertyName, getattr(losingSp, propertyName)
        propertyName = "F_TSLActivationPercentage"
        if getattr(sp, propertyName) != getattr(spPrev, propertyName):
            return propertyName, getattr(losingSp, propertyName)
        propertyName = "F_TSLTrailPercentage"
        if getattr(sp, propertyName) != getattr(spPrev, propertyName):
            return propertyName, getattr(losingSp, propertyName)

        propertyName = "S_TradingEnabled"
        if getattr(sp, propertyName) != getattr(spPrev, propertyName):
            return propertyName, getattr(losingSp, propertyName)
        propertyName = "S_SL1Percentage"
        if getattr(sp, propertyName) != getattr(spPrev, propertyName):
            return propertyName, getattr(losingSp, propertyName)
        propertyName = "S_SL2Percentage"
        if getattr(sp, propertyName) != getattr(spPrev, propertyName):
            return propertyName, getattr(losingSp, propertyName)
        propertyName = "S_SLTimerInMinutes"
        if getattr(sp, propertyName) != getattr(spPrev, propertyName):
            return propertyName, getattr(losingSp, propertyName)
        propertyName = "S_TSLActivationPercentage"
        if getattr(sp, propertyName) != getattr(spPrev, propertyName):
            return propertyName, getattr(losingSp, propertyName)
        propertyName = "S_TSLTrailPercentage"
        if getattr(sp, propertyName) != getattr(spPrev, propertyName):
            return propertyName, getattr(losingSp, propertyName)

        propertyName = "TargetPercentage"
        if getattr(sp, propertyName) != getattr(spPrev, propertyName):
            return propertyName, getattr(losingSp, propertyName)

        propertyName = "RebuyTimeInSeconds"
        if getattr(sp, propertyName) != getattr(spPrev, propertyName):
            return propertyName, getattr(losingSp, propertyName)
        propertyName = "RebuyPercentage"
        if getattr(sp, propertyName) != getattr(spPrev, propertyName):
            return propertyName, getattr(losingSp, propertyName)
        propertyName = "RebuyMaxLimit"
        if getattr(sp, propertyName) != getattr(spPrev, propertyName):
            return propertyName, getattr(losingSp, propertyName)
        propertyName = "PullbackEntryPercentage"
        if getattr(sp, propertyName) != getattr(spPrev, propertyName):
            return propertyName, getattr(losingSp, propertyName)
        propertyName = "PullbackEntryWaitTimeInSeconds"
        if getattr(sp, propertyName) != getattr(spPrev, propertyName):
            return propertyName, getattr(losingSp, propertyName)

        return "",0



    def ComputeMarginCommissionPercentage(self, symbol, dateFrom, dateTo):
        if "UPUSDT" not in symbol and "DOWNUSDT" not in symbol:
            return 0

        difference = dateTo - dateFrom
        diffInDays = difference.days + 1
        return diffInDays * decimal.Decimal(0.1)

    def test_signals(self):
        import pandas as pd
        df = pd.read_csv('../BL/bot/output.csv', sep=';', encoding='utf-16', index_col='Date', parse_dates=True)

        candles = self.market_state[('BTC-USD',self.interval)]
        # print(*candles, sep="\n")

        # Compute indicator signals
        signals = self.computeIndicators(candles)

        r=[]
        for i in range(len(candles)):
            c: Candle = candles[i]
            date = datetime.fromtimestamp(c.open_time / 1000)
            if date in df.index:
                roc_r = signals[ENUM_INDICATOR.ROC].signal_r[i]
                roc_f = signals[ENUM_INDICATOR.ROC].signal_f[i]
                roc_s = signals[ENUM_INDICATOR.ROC].signal_s[i]

                mpt = signals[ENUM_INDICATOR.MPT].value[i]
                trend = 0  # signals[ENUM_INDICATOR.TREND].signal[i]
                nv = 0  # signals[ENUM_INDICATOR.NV].signal[i]

                rsi = signals[ENUM_INDICATOR.RSI].value[i]
                stoch = signals[ENUM_INDICATOR.STOCH].slowk[i]

                conditions_r = self.__check_entry_for_r_buy_test(roc_r, mpt, trend, nv, c)
                conditions_f = self.__check_entry_for_f_buy_test(roc_f, mpt, trend, c)
                conditions_s = self.__check_entry_for_s_sell_test(roc_s, rsi, stoch)

                r1 = int((df.loc[date, 'SwT-Signal_1']))
                r2 = int(all(conditions_r))
                f1 = int((df.loc[date, 'SwT-Signal_2']))
                f2 = int(all(conditions_f))
                s1 = int((df.loc[date, 'SwT-Signal_3']))
                s2 = int(all(conditions_s))

                # r.append([date,
                #           'MPT',
                #           # df.loc[date,'High'], c.high,
                #           '{:.3f}'.format(df.loc[date,'MPT_1']), '{:.3f}'.format(signals[ENUM_INDICATOR.MPT].value[i]), # OK
                #           ])
                # r.append([date,
                #           'TREND',
                #           # df.loc[date, 'Low'], c.low,
                #           '{:.3f}'.format(df.loc[date, 'Trend_1']), '{:.3f}'.format(signals[ENUM_INDICATOR.TREND].short[i]), # OK
                #           '{:.3f}'.format(df.loc[date, 'Trend_2']), '{:.3f}'.format(signals[ENUM_INDICATOR.TREND].long[i]), # NOT OK
                #           '{:.3f}'.format(df.loc[date, 'Trend_4']), '{:.3f}'.format(signals[ENUM_INDICATOR.TREND].signal[i]), # OK
                #           ])
                # r.append([date,
                #           'ROC',
                #           df.loc[date, 'High'], c.high,
                #           df.loc[date, 'Low'], c.low,
                #           df.loc[date, 'Close'], c.close,
                #           '{:.3f}'.format(df.loc[date, 'ROC_1']), '{:.3f}'.format(signals[ENUM_INDICATOR.ROC].change_r[i]), # ok
                #           '{:.3f}'.format(df.loc[date, 'ROC_2']), '{:.3f}'.format(signals[ENUM_INDICATOR.ROC].change_f[i]), # ok
                #           '{:.3f}'.format(df.loc[date, 'ROC_3']), '{:.3f}'.format(signals[ENUM_INDICATOR.ROC].signal_r[i]), # ok
                #           '{:.3f}'.format(df.loc[date, 'ROC_4']), '{:.3f}'.format(signals[ENUM_INDICATOR.ROC].signal_f[i]), # ok
                #           ])
                r.append([date,
                          str(r1), str(r2), str(r1==r2),
                          str(f1), str(f2), str(f1 == f2),
                          str(s1), str(s2), str(s1 == s2),
                          "*********************************************" if s1!=s2 or f1!=f2 or r1!=r2 else ""
                          ])


        print(*r,sep='\n')
