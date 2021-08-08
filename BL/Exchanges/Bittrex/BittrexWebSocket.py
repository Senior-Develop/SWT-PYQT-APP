import traceback
from time import sleep, time
from dateutil.parser import parse
from BL.Exchanges.Bittrex.WebsocketClientLib.websocket_client import BittrexSocket
from Common.Exchange.Candle import Candle


def convert_to_streams(symbols, interval):
	try:
		if interval == "1m":
			interval_str = "MINUTE_1"
		elif interval == "5m":
			interval_str = "MINUTE_5"
		elif interval == "1h":
			interval_str = "HOUR_1"
		elif interval == "1d":
			interval_str = "DAY_1"
		else:
			return []
		streams = ["candle_" + symbol + "_" + interval_str for symbol in symbols]
		return streams
	except:
		print(traceback.format_exc())


class BittrexWebSocket(BittrexSocket):

	def __init__(self):
		super().__init__()
		self.callback = None

	def exit(self):
		self.stop()

	def start(self, symbols, interval, callback):
		super().start()

		self.callback = callback
		streams = convert_to_streams(symbols, interval)
		# self.subscribe_to_heartbeat()

		# Subscribe to ticker information
		# Users can also subscribe without introducing delays during invoking but
		# it is the recommended way when you are subscribing to a large list of tickers.
		for stream in streams:
			sleep(0.01)
			self.subscribe_to_candles([stream])
		# self.subscribe_to_candles(streams)

	def stop(self):
		self.disconnect()

	# where I receive the messages
	async def on_public(self, msg):
		if msg["invoke_type"] == "heartbeat":
			print('\u2661')
		elif msg["invoke_type"] == "candle":
			# print(msg)

			event_time_ms = int(time()*1000) #msec
			item = msg['delta']
			open_time_ms = int(parse(item["startsAt"]).timestamp() * 1000)  # store as milliseconds

			sec_in_ms = 1000
			min_in_ms = 60 * sec_in_ms
			hour_in_ms = 60 * min_in_ms
			day_in_ms = 24 * hour_in_ms

			close_time_ms = 0
			is_closed = False
			interval = ""
			if msg['interval'] == "MINUTE_1":
				interval = "1m"
				close_time_ms = open_time_ms + min_in_ms
			elif msg['interval'] == "MINUTE_5":
				interval = "5m"
				close_time_ms = open_time_ms + 5*min_in_ms
			elif msg['interval'] == "HOUR_1":
				interval = "1h"
				close_time_ms = open_time_ms + hour_in_ms
			elif msg['interval'] == "DAY_1":
				interval = "1d"
				close_time_ms = open_time_ms + day_in_ms

			if 0 < close_time_ms <= event_time_ms:
				is_closed = True

			candle = Candle(symbol=msg['marketSymbol'],
							interval=interval,
							open_time=open_time_ms,
							close_time=close_time_ms,
							open=item["open"],
							high=item["high"],
							low=item["low"],
							close=item["close"],
							volume=item["close"],
							quote_asset_volume=item["quoteVolume"],
							is_closed=is_closed)
			self.callback(candle, event_time_ms)

		elif msg["invoke_type"] == "trade":
			print(msg)


