from Common.Constant import ENUM_APPLIED_PRICE
import talib
import numpy
from datetime import datetime
from Common.Constant import ENUM_INDICATOR
from Utils import utils


class StochResult:
    def __init__(self, timestamp, slowk, slowd):
        self.timestamp = timestamp
        self.slowk = slowk
        self.slowd = slowd

    def get_latest(self):
        return StochResult(self.timestamp,
                           self.slowk[-1],
                           self.slowd[-1])

    def __str__(self):
        return "STOCH {} {}".format(self.slowk[-1], self.slowd[-1])

    def __repr__(self):
        return self.__str__()

class Stoch:
    name = ENUM_INDICATOR.STOCH.value

    def __init__(self,
                 fastk_period=5,
                 slowk_period=3,
                 slowd_period=3
                 ):
        self.fastk_period = int(fastk_period)
        self.slowk_period = int(slowk_period)
        self.slowd_period = int(slowd_period)

    ''' Assumption: data[0] contains latest data point '''
    def compute(self, candles):
        high = [candle.get_price(ENUM_APPLIED_PRICE.PRICE_HIGH) for candle in candles]
        low = [candle.get_price(ENUM_APPLIED_PRICE.PRICE_LOW) for candle in candles]
        close = [candle.get_price(ENUM_APPLIED_PRICE.PRICE_CLOSE) for candle in candles]
        slowk, slowd = list(talib.STOCH(numpy.array(high),
                                        numpy.array(low),
                                        numpy.array(close),
                                        self.fastk_period,
                                        self.slowk_period,
                                        0,
                                        self.slowd_period,
                                        0))
        slowk = numpy.where(numpy.isnan(slowk), 0, slowk)
        slowd = numpy.where(numpy.isnan(slowd), 0, slowd)
        # return StochResult(datetime.now(), slowk[-1], slowd[-1])
        return StochResult(datetime.now(), slowk, slowd)
