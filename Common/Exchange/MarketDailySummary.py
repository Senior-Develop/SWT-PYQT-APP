class MarketDailySummary:
    def __init__(self, symbol="", price_change=0.0, price_change_percent=0.0,
                 weighted_avg_price=0.0, prev_close_price=0.0,
                 last_price=0.0, last_qty=0.0,
                 bid_price=0.0, bid_qty=0.0,
                 ask_price=0.0, ask_qty=0.0,
                 open_price=0.0, high_price=0.0, low_price=0.0,
                 volume=0.0, quote_volume=0.0, open_time=0, close_time=0,
                 first_id=0, last_id=0, count=0):
        self.symbol = symbol
        self.price_change = float(price_change)
        self.price_change_percent = float(price_change_percent)
        self.weighted_avg_price = float(weighted_avg_price)
        self.prev_close_price = float(prev_close_price)
        self.last_price = float(last_price)
        self.last_qty = float(last_qty)
        self.bid_price = float(bid_price)
        self.bid_qty = float(bid_qty)
        self.ask_price = float(ask_price)
        self.ask_qty = float(ask_qty)
        self.open_price = float(open_price)
        self.high_price = float(high_price)
        self.low_price = float(low_price)
        self.volume = float(volume)
        self.quote_volume = float(quote_volume)
        self.open_time = int(open_time)
        self.close_time = int(close_time)
        self.first_id = int(first_id)
        self.last_id = int(last_id)
        self.count = int(count)

    def __str__(self):
        return str(self.__dict__)

    def __repr__(self):
        return self.__str__()