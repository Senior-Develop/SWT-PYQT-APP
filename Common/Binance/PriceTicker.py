class PriceTicker:
    def __init__(self, symbol="", price=0.0):
        self.symbol = symbol
        self.price = float(price)

    def __str__(self):
        return str(self.__dict__)

    def __repr__(self):
        return self.__str__()