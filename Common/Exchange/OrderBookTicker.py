class OrderBookTicker:
    def __init__(self, symbol="",
                 bid_price=0.0, bid_qty=0.0,
                 ask_price=0.0, ask_qty=0.0):
        self.symbol = symbol
        self.bid_price = float(bid_price)
        self.bid_qty = float(bid_qty)
        self.ask_price = float(ask_price)
        self.ask_qty = float(ask_qty)

    def __str__(self):
        return str(self.__dict__)

    def __repr__(self):
        return self.__str__()
