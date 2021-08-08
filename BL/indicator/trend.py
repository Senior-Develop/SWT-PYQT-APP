from Common.Constant import ENUM_APPLIED_PRICE
import talib
import numpy
from datetime import datetime
from Common.Constant import ENUM_INDICATOR
from Utils import utils


class TrendResult:
    def __init__(self, timestamp, short, long, signal):
        self.timestamp = timestamp
        self.short = short
        self.long = long
        self.signal = signal

    def get_latest(self):
        return TrendResult(self.timestamp,
                           self.short[-1],
                           self.long[-1],
                           self.signal[-1])

    def __str__(self):
        return "TREND {} {} {}".format(self.short[-1], self.long[-1], self.signal[-1])

    def __repr__(self):
        return self.__str__()


class Trend:
    name = ENUM_INDICATOR.TREND.value

    def __init__(self,
                 applied_price=ENUM_APPLIED_PRICE.PRICE_LOW,
                 short_ema_period=1,  # EMA length
                 long_ema_period=3,  # ZLWMA period
                 ):
        # assert short_ema_period >= 1, "shortEmaPeriod cannot be smaller than 1."
        # assert long_ema_period >= 1, "longEmaPeriod cannot be smaller than 1."

        self.applied_price = applied_price
        self.short_ema_period = int(short_ema_period)
        self.long_ema_period = int(long_ema_period)

    ''' Assumption: data[0] contains oldest data point '''
    def compute(self, candles):
        # price = numpy.array(self.get_column(data, self.applied_price.value))
        # x_lag = round((self.long_ema_period - 1) / 2)
        # x_ema_data = price + (price - price[x_lag])
        # long = talib.EMA(x_ema_data, self.long_ema_period)
        # print(self.applied_price, self.short_ema_period, self.long_ema_period)
        # print(candles)

        price = [candle.get_price(self.applied_price) for candle in candles]
#        price_close = [candle.get_price(ENUM_APPLIED_PRICE.PRICE_CLOSE) for candle in candles]
        price_close = [candle.get_price(self.applied_price) for candle in candles]

        if self.short_ema_period > 1:
            short = list(talib.EMA(numpy.array(price), self.short_ema_period))
        else:
            short = price_close

        lag = int((self.long_ema_period - 2) / 2)   # int((self.long_ema_period - 1) / 2)
        ema_data = [price[i] * 2 - price[i - lag] if (i - lag > 0) else price[i] for i in range(len(price))]
        if self.long_ema_period > 1:
            long = list(talib.EMA(numpy.array(ema_data), self.long_ema_period))
        else:
            ema_data_close = [price_close[i] * 2 - price_close[i - lag] if (i - lag > 0) else price_close[i] for i in range(len(price_close))]
            long = ema_data_close

        signal = list(map(lambda x, y: 0 if utils.compare_floats(x, y) == 1 else 1, long, short)) # if long is greater than short 0, else 1

        #print(short)
        #print(long)
        #print(signal)

        # print(signal[-1], short[-1], long[-1])
        return TrendResult(datetime.now(), short, long, signal)