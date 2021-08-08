class Trade:
    def __init__(self, symbol="", id=0, order_id=0, order_list_id=0,
                 price=0.0, qty=0.0, quote_qty=0.0,
                 commission=0.0, commission_asset="", time=0,
                 is_buyer=False, is_maker=False, is_best_match=False):
        self.symbol = symbol
        self.id = int(id)
        self.order_id = int(order_id)
        self.order_list_id = int(order_list_id)
        self.price = float(price)
        self.qty = float(qty)
        self.quote_qty = float(quote_qty)
        self.commission = float(commission)
        self.commission_asset = commission_asset
        self.time = int(time)
        self.is_buyer = bool(is_buyer)
        self.is_maker = bool(is_maker)
        self.is_best_match = bool(is_best_match)

    def __str__(self):
        return str(self.__dict__)

    def __repr__(self):
        return self.__str__()
