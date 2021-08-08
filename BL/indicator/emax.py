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
                 applied_price=ENUM_APPLIED_PRICE.PRICE_HIGH,
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
        price_close = [candle.get_price(ENUM_APPLIED_PRICE.PRICE_CLOSE) for candle in candles]
        price_open = [candle.get_price(ENUM_APPLIED_PRICE.PRICE_OPEN) for candle in candles]

        if self.short_ema_period > 1:
            ema = list(talib.EMA(numpy.array(price), self.short_ema_period))
        else:
            ema = price

        signals = [0]
        is_long = False
        is_short = False
        for i in range(1, len(ema)):
            if not ema[i-1]:
                signals.append(0)
                continue

            emaXup = ema[i] < price[i] and ema[i-1] >= price[i-1]
            emaXdn = ema[i] > price[i] and ema[i-1] <= price[i-1]
            body = (price_close[i] - price_open[i])

            if body and emaXup and not is_long:
                signal = 1
                is_long = True
                is_short = False
            elif body and emaXdn and not is_short:
                signal = -1
                is_long = False
                is_short = True
            else:
                signal = 0

            signals.append(signal)

        return EmaxResult(datetime.now(), ema, ema, signals)
