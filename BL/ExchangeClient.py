from enum import Enum
import traceback

from BL.Exchanges.Binance.BinanceClient import BinanceClient
from BL.Exchanges.Binance.BinanceWebSocket import BinanceWebSocket
from BL.Exchanges.Bittrex.BittrexClient import BittrexClient
from BL.Exchanges.ClientInterface import ClientInterface


class ExchangeType(Enum):
	BINANCE = 1
	BITTREX = 2


class ExchangeClient(ClientInterface):
	def __init__(self, exchange_type, api_key, api_secret):
		try:
			self.client = None

			self.exchange_type = exchange_type
			if self.exchange_type == ExchangeType.BINANCE:
				self.client = BinanceClient(api_key, api_secret)
			if self.exchange_type == ExchangeType.BITTREX:
				self.client = BittrexClient(api_key, api_secret)
		except:
			print(traceback.format_exc())

	# Client interface implementations
	def get_server_time(self):
		return self.client.get_server_time()

	def get_asset_balances(self):
		return self.client.get_asset_balances()

	def get_asset_balance(self, asset):
		return self.client.get_asset_balance(asset)

	def get_markets(self, quote_assets=[]):
		return self.client.get_markets(quote_assets)

	def get_market_daily_summary(self, symbol):
		return self.client.get_market_daily_summary(symbol)

	def get_candles(self, symbol, interval, limit=500):
		return self.client.get_candles(symbol, interval, limit)

	def get_candles_historical(self, symbol, interval, start_time=None, end_time=None):
		return self.client.get_candles_historical(symbol, interval, start_time, end_time)

	def buy_asset(self, symbol, amount):
		return self.client.buy_asset(symbol, amount)

	def sell_asset(self, symbol, amount):
		return self.client.sell_asset(symbol, amount)



	# Websocket methods
	def exit_websocket(self):
		self.client.exit_websocket()

	def start_websocket(self, symbols, interval, callback):
		self.client.start_websocket(symbols, interval, callback)

	def stop_websocket(self):
		self.client.stop_websocket()
