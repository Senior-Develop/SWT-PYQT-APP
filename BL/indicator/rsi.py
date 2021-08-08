from Common.Constant import ENUM_APPLIED_PRICE
import talib
import numpy
from datetime import datetime
from Common.Constant import ENUM_INDICATOR
from Utils import utils


class RsiResult:
    def __init__(self, timestamp, value):
        self.timestamp = timestamp
        self.value = value

    def get_latest(self):
        return RsiResult(self.timestamp, self.value[-1])

    def __str__(self):
        return "RSI {}".format(self.value[-1])

    def __repr__(self):
        return self.__str__()

class Rsi:
    name = ENUM_INDICATOR.RSI.value

    def __init__(self,
                 applied_price=ENUM_APPLIED_PRICE.PRICE_CLOSE,
                 time_period=14
                 ):

        self.applied_price = applied_price
        self.time_period = int(time_period)

    ''' Assumption: data[0] contains oldest data point '''
    def compute(self, candles):
        price = [candle.get_price(self.applied_price) for candle in candles]
        if self.time_period > 1:
            rsi = list(talib.RSI(numpy.array(price), self.time_period))
        else:
            rsi = price

        return RsiResult(datetime.now(), rsi)