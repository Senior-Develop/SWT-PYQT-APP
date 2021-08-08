import decimal
import traceback
from datetime import datetime
from math import log

from binance.client import Client
from binance.exceptions import BinanceAPIException

from BL.Exchanges.Binance.BinanceWebSocket import BinanceWebSocket
from BL.Exchanges.ClientInterface import ClientInterface
from Common.Exchange.AccountInfo import AccountInfo
from Common.Exchange.Balance import Balance
from Common.Exchange.Candle import Candle
from Common.Exchange.MarketDailySummary import MarketDailySummary
from Common.Asset import Asset
from Common.Exchange.OrderResponse import OrderResponse
from Common.Market import Market


class BinanceClient(ClientInterface):
	url_base = "https://api.binance.com/api/v3/klines?symbol={}&interval={}&limit={}"

	def __init__(self, api_key, api_secret):
		try:
			self.client = Client(api_key, api_secret)
			self.ws = BinanceWebSocket(self.client)
		except:
			print(traceback.format_exc())

	def get_server_time(self):
		server_time = None
		try:
			server_time = int(self.client.get_server_time()["serverTime"])
		except:
			print(traceback.format_exc())
		return server_time

	def get_asset_balances(self):
		assets = None
		try:
			account = AccountInfo(*self.client.get_account(recvWindow=59000).values())

			if account and account.balances:
				assets = []
				for balance in account.balances:
					assets.append(Asset(AssetName=balance.asset,
										BalanceFree=balance.free,
										BalanceLocked=balance.locked,
										ModifiedDate=datetime.now()))

		except:
			print(traceback.format_exc())
		return assets

	def get_asset_balance(self, asset):
		balance = None
		try:
			balance = Balance(*self.client.get_asset_balance(asset=asset, recvWindow=59000).values())
		except:
			print(traceback.format_exc())
		return balance

	def get_markets(self, quote_assets):
		markets = []
		try:
			symbols = self.client.get_exchange_info()['symbols']
			# print(*symbols,sep='\n')
			for symbol in symbols:
				if symbol['status'] != 'TRADING':
					continue
				if not quote_assets or (symbol['quoteAsset'] in quote_assets):
					market = Market(Symbol=symbol['symbol'],
									BaseAsset=symbol['baseAsset'],
									QuoteAsset=symbol['quoteAsset'])
					if symbol['filters']:
						for asset_filter in symbol['filters']:
							if asset_filter['filterType'] == 'MIN_NOTIONAL':
								market.MinAmountToTrade = float(asset_filter['minNotional'])
							if asset_filter['filterType'] == 'LOT_SIZE':
								market.AmountDecimalDigits = round(-log(float(asset_filter['stepSize']), 10))
								market.MinQuantity = float(asset_filter['minQty'])
					markets.append(market)
		except:
			print(traceback.format_exc())
		return markets

	def get_market_daily_summary(self, symbol):
		daily_summary = None
		try:
			result = self.client.get_ticker(symbol=symbol)
			daily_summary = MarketDailySummary(*result.values())
		except:
			print(traceback.format_exc())
		return daily_summary

	def buy_asset(self, symbol, amount):
		return self._make_trade_order("BUY", symbol, amount)

	def sell_asset(self, symbol, amount):
		return self._make_trade_order("SELL", symbol, amount)

	def _make_trade_order(self, side, symbol, amount):
		order_response = OrderResponse(direction=side,
									   order_type="MARKET",
									   symbol=symbol,
									   requested_qty=amount,
									   executed_time=datetime.now())
		try:
			response = None
			if side == "BUY":
				response = self.client.order_market_buy(
					symbol=symbol,
					quantity=amount, recvWindow=59000)
			elif side == "SELL":
				response = self.client.order_market_sell(
					symbol=symbol,
					quantity=amount, recvWindow=59000)

			if response is None:
				order_response.status = "Exchange Response is None"
			else:
				# Compute avg_price and total commission
				filledAmount = decimal.Decimal(response['executedQty'])
				totalCommission = 0
				avgPrice = 0
				for fill in response['fills']:
					totalCommission = totalCommission + decimal.Decimal(fill['commission'])
					avgPrice = avgPrice + decimal.Decimal(fill['qty']) * decimal.Decimal(fill['price'])
				if filledAmount != 0:
					avgPrice = avgPrice / filledAmount

				order_response.status = response['status']
				order_response.executed_qty = response['executedQty']
				order_response.avg_price = avgPrice
				order_response.commission = totalCommission
		except BinanceAPIException as ex:
			order_response.status = '(' + str(ex.code) + ') ' + ex.message
		except Exception as ex:
			order_response.status = '(' + str(ex.code) + ') ' + ex.message
			print(traceback.format_exc())
		return order_response

	def get_candles(self, symbol, interval, limit=500):
		candles = None
		try:
			data = self.client.get_klines(symbol=symbol, interval=interval, limit=limit)
			candles = [Candle(symbol, interval, *d, is_closed=True) for d in data]
		except:
			print(traceback.format_exc())
		return candles

	def get_candles_historical(self, symbol, interval, start_time, end_time):
		candles = None
		try:
			data = self.client.get_klines(symbol=symbol,
										  interval=interval,
										  limit=1000,
										  startTime=start_time,
										  endTime=end_time)
			candles = [Candle(symbol, interval, *d, is_closed=True) for d in data]
		except:
			print(traceback.format_exc())
		return candles

	def start_websocket(self, symbols, interval, callback):
		try:
			print("start_web_socket")
			self.ws.start(symbols, interval, callback)
		except:
			print(traceback.format_exc())

	def stop_websocket(self):
		try:
			if self.ws:
				self.ws.stop()
		except:
			print(traceback.format_exc())

	def exit_websocket(self):
		try:
			if self.ws:
				self.ws.exit()
		except:
			print(traceback.format_exc())


	# NOT USED
	# def get_trades(self, symbol):
	# 	trades = None
	# 	try:
	# 		result = self.client.get_my_trades(symbol=symbol, recvWindow=59000)
	# 		trades = [Trade(*trade.values()) for trade in result]
	# 	except:
	# 		print(traceback.format_exc())
	# 	return trades

	# NOT USED
	# def get_price_ticker(self, symbol):
	# 	price_ticker = None
	# 	try:
	# 		result = self.client.get_symbol_ticker(symbol=symbol)
	# 		price_ticker = PriceTicker(*result.values())
	# 	except:
	# 		print(traceback.format_exc())
	# 	return price_ticker

	# NOT USED
	# def get_orderbook(self):
	# 	order_book = None
	# 	try:
	# 		order_book = [OrderBookTicker(*ticker) for ticker in self.client.get_orderbook_tickers()]
	# 	except:
	# 		print(traceback.format_exc())
	# 	return order_book