import traceback
from binance.client import Client
from datetime import datetime
from math import log

from BL.BinanceWebSocket import BinanceWebSocket
from Common.Binance.AccountInfo import AccountInfo
from Common.Binance.Balance import Balance
from Common.Binance.Trade import Trade
from Common.Binance.Candle import Candle
from Common.Binance.OrderBookTicker import OrderBookTicker
from Common.Binance.PriceTicker import PriceTicker
from Common.Binance.PriceTicker24 import PriceTicker24
from Common.Market import Market
from Common.QcParameters import QcParameters


class BinanceLibrary:
    url_base = "https://api.binance.com/api/v3/klines?symbol={}&interval={}&limit={}"

    def __init__(self, api_key, api_secret):
        try:
            self.client = Client(api_key, api_secret)
            self.ws = None
        except:
            print(traceback.format_exc())

    def exit(self):
        try:
            if self.ws:
                self.ws.exit()
        except:
            print(traceback.format_exc())

    def get_candles(self, symbol, interval, limit=500, start_time=None, end_time=None):
        candles = None
        try:
            data = self.client.get_klines(symbol=symbol, interval=interval, limit=limit, startTime=start_time, endTime=end_time)
            candles = [Candle(symbol,interval,*d) for d in data]
        except:
            print(traceback.format_exc())
        return candles

    def get_markets(self, quote_assets):
        markets = []
        try:
            symbols = self.client.get_exchange_info()['symbols']
            #print(*symbols,sep='\n')
            for symbol in symbols:
                if symbol['status'] != 'TRADING':
                    continue
                if not quote_assets or (symbol['quoteAsset'] in quote_assets):
                    market = Market(Symbol=symbol['symbol'], BaseAsset=symbol['baseAsset'], QuoteAsset=symbol['quoteAsset'])
                    if symbol['filters']:
                        for filter in symbol['filters']:
                            if filter['filterType'] == 'MIN_NOTIONAL':
                                market.MinAmountToTrade = float(filter['minNotional'])
                            if filter['filterType'] == 'LOT_SIZE':
                                market.AmountDecimalDigits = round(-log(float(filter['stepSize']),10))
                                market.MinQuantity = float(filter['minQty'])
                    markets.append(market)
        except:
            print(traceback.format_exc())
        return markets

    def get_account_info(self):
        info = None
        try:
            info = AccountInfo(*self.client.get_account(recvWindow=59000).values())
        except:
            print(traceback.format_exc())
        return info

    def get_asset_balance(self, asset):
        balance = None
        try:
            balance = Balance(*self.client.get_asset_balance(asset=asset, recvWindow=59000).values())
        except:
            print(traceback.format_exc())
        return balance

    def get_server_time(self):
        server_time = None
        try:
            server_time = int(self.client.get_server_time()["serverTime"])
        except:
            print(traceback.format_exc())
        return server_time

    def get_orderbook(self):
        order_book = None
        try:
            order_book = [OrderBookTicker(*ticker) for ticker in self.client.get_orderbook_tickers()]
        except:
            print(traceback.format_exc())
        return order_book

    def get_price_ticker(self, symbol):
        price_ticker = None
        try:
            result = self.client.get_symbol_ticker(symbol=symbol)
            price_ticker = PriceTicker(*result.values())
        except:
            print(traceback.format_exc())
        return price_ticker

    def get_price_ticker_24(self, symbol):
        price_ticker_24 = None
        try:
            result = self.client.get_ticker(symbol=symbol)
            price_ticker_24 = PriceTicker24(*result.values())
        except:
            print(traceback.format_exc())
        return price_ticker_24

    def get_trades(self, symbol):
        trades = None
        try:
            result = self.client.get_my_trades(symbol=symbol, recvWindow=59000)
            trades = [Trade(*trade.values()) for trade in result]
        except:
            print(traceback.format_exc())
        return trades

    def buy_asset(self, symbol, amount):
        try:
            return self.client.order_market_buy(
                    symbol=symbol,
                    quantity=amount, recvWindow=59000)
        except:
            print(traceback.format_exc())

    def sell_asset(self, symbol, amount):
        try:
            return self.client.order_market_sell(
                    symbol=symbol,
                    quantity=amount, recvWindow=59000)
        except:
            print(traceback.format_exc())

    def __convert_to_stream_names(self, symbols, interval):
        try:
            stream_names = []
            for symbol in symbols:
                stream_names.append("{}@kline_{}".format(symbol.lower(), interval))
            return stream_names
        except:
            print(traceback.format_exc())

    ''' 
    input:
        inverval: str
        markets: list of market objects
    '''
    def start_web_socket(self, symbols, interval, callback):
        try:
            print("start_web_socket")
            streams = self.__convert_to_stream_names(symbols, interval)
            self.ws = BinanceWebSocket(self.client)
            self.ws.start(streams, callback)
        except:
            print(traceback.format_exc())

    def stop_web_socket(self):
        try:
            if self.ws:
                self.ws.stop()
        except:
            print(traceback.format_exc())


