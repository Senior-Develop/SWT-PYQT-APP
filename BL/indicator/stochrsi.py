from Common.Constant import ENUM_APPLIED_PRICE
import talib
import numpy
from datetime import datetime
from Common.Constant import ENUM_INDICATOR
from Utils import utils


class StochRsiResult:
    def __init__(self, timestamp, fastk, fastd):
        self.timestamp = timestamp
        self.fastk = fastk
        self.fastd = fastd

    def get_latest(self):
        return StochRsiResult(self.timestamp,
                              self.fastk[-1],
                              self.fastd[-1])


class StochRsi:
    name = ENUM_INDICATOR.STOCHRSI.value
    
    def __init__(self,
                 applied_price=ENUM_APPLIED_PRICE.PRICE_CLOSE,
                 time_period=14,
                 fastk_period=5,
                 fastd_period=3
                 ):
        self.applied_price = applied_price
        self.time_period = int(time_period)
        self.fastk_period = int(fastk_period)
        self.fastd_period = int(fastd_period)

    ''' Assumption: data[0] contains latest data point '''
    def compute(self, candles):
        price = [candle.get_price(self.applied_price) for candle in candles]
        fastk, fastd = list(talib.STOCHRSI(numpy.array(price),
                                        self.time_period,
                                        self.fastk_period,
                                        self.fastd_period))
        # return StochRsiResult(datetime.now(), fastk[-1], fastd[-1])
        return StochRsiResult(datetime.now(), fastk, fastd)