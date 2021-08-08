from Common.Constant import ENUM_APPLIED_PRICE
import talib
import numpy
from datetime import datetime
from Common.Constant import ENUM_INDICATOR
from Utils import utils


class EmaxResult:
    def __init__(self, timestamp, short, long, signal):
        self.timestamp = timestamp
        self.short = short
        self.long = long
        self.signal = signal

    def get_latest(self):
        #if not self.signal:
        #    return None
        #print("len")
        #print(len(self.signal))
        return EmaxResult(self.timestamp,
                           self.short[-1],
                           self.long[-1],
                           self.signal[-1])

    def __str__(self):
        return "EMAX {} {} {}".format(self.short[-1], self.long[-1], self.signal[-1])

    def __repr__(self):
        return self.__str__()


class Emax:
    name = ENUM_INDICATOR.EMAX.value

    def __init__(self,
                 applied_price=ENUM_APPLIED_PRICE.PRICE_LOW,
                 short_ema_period=1,
                 long_ema_period=3,
                 ):
        # assert short_ema_period >= 1, "shortEmaPeriod cannot be smaller than 1."
        # assert long_ema_period >= 1, "longEmaPeriod cannot be smaller than 1."

        self.applied_price = applied_price
        self.short_ema_period = int(short_ema_period)
        self.long_ema_period = int(long_ema_period)
        #print("self.short_ema_period")
        #print(self.short_ema_period)

        #print("self.long_ema_period")
        #print(self.long_ema_period)

        #print("self.applied_price")
        #print(self.applied_price)

    ''' Assumption: data[0] contains oldest data point '''
    def compute(self, candles):

        price = [candle.get_price(self.applied_price) for candle in candles]
#        price_close = [candle.get_price(ENUM_APPLIED_PRICE.PRICE_CLOSE) for candle in candles]
        price_close = [candle.get_price(self.applied_price) for candle in candles]

        if self.short_ema_period > 1:
            short = list(talib.EMA(numpy.array(price), self.short_ema_period))
        else:
            short = price_close

        if self.long_ema_period > 1:
            long = list(talib.EMA(numpy.array(price), self.long_ema_period))
        else:
            long = price_close

        signal = [None] * len(candles)
        #signal = []
        for i in range(len(long)):
            if i == 0:
                continue

            s = 0
            if short[i-1] < long[i-1] and short[i] > long[i]:
                s = 1
            elif short[i-1] > long[i-1] and short[i] < long[i]:
                s = -1

            signal.append(s)

        #signal = 0
        #if short[1] < long[1] and short[0] > long[1]:
        #    signal = 1
        #elif short[1] > long[1] and short[0] < long[1]:
        #    signal = -1

        #print("EMAX:")
        #if short[-1] > 30000:

        #print(signal[-1], short[-1], long[-1])

        return EmaxResult(datetime.now(), short, long, signal)