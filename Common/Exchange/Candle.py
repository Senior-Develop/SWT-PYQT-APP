from Common.Constant import ENUM_APPLIED_PRICE


class Candle:
    def __init__(self,
                 symbol="",
                 interval="",
                 open_time=0,
                 open=0,
                 high=0,
                 low=0,
                 close=0,
                 volume=0,
                 close_time=0,
                 quote_asset_volume=0,
                 num_trades=0,
                 taker_buy_base_asset_volume=0,
                 taker_buy_quote_asset_volume=0,
                 ignore=None,
                 is_closed=False,
                 event_time=None

                 ):
        self.symbol = symbol
        self.interval = interval
        self.open_time = int(open_time)
        self.close_time = int(close_time)
        self.open = float(open)
        self.high = float(high)
        self.low = float(low)
        self.close = float(close)
        self.volume = float(volume)
        self.num_trades = int(num_trades)
        self.quote_asset_volume = float(quote_asset_volume)
        self.taker_buy_base_asset_volume = float(taker_buy_base_asset_volume)
        self.taker_buy_quote_asset_volume = float(taker_buy_quote_asset_volume)
        self.ignore = ignore
        self.is_closed = is_closed
        self.event_time = event_time

    def __str__(self):
        return str(self.__dict__)

    def __repr__(self):
        return self.__str__()

    def get_price(self, price_type):
        if price_type == ENUM_APPLIED_PRICE.PRICE_OPEN: return float(self.open)
        if price_type == ENUM_APPLIED_PRICE.PRICE_CLOSE: return float(self.close)
        if price_type == ENUM_APPLIED_PRICE.PRICE_HIGH: return float(self.high)
        if price_type == ENUM_APPLIED_PRICE.PRICE_LOW: return float(self.low)
        return None
