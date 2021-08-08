from Common.Exchange.Balance import Balance
from Common.Exchange.MarketDailySummary import MarketDailySummary
from Common.Exchange.OrderResponse import OrderResponse


class ClientInterface:

	def get_server_time(self) -> int:
		pass

	def get_asset_balances(self) -> list:
		pass

	def get_asset_balance(self, symbol) -> Balance:
		pass

	def get_markets(self, quote_assets=[]) -> list:
		pass

	def get_market_daily_summary(self, symbol) -> MarketDailySummary:
		pass

	def buy_asset(self, symbol, amount) -> OrderResponse:
		pass

	def sell_asset(self, symbol, amount) -> OrderResponse:
		pass

	def get_candles(self, symbol, interval, limit=500):
		pass

	def get_candles_historical(self, symbol, interval, start_time, end_time):
		pass

	def start_websocket(self, symbols, interval, callback):
		pass

	def stop_websocket(self):
		pass

	def exit_websocket(self):
		pass
