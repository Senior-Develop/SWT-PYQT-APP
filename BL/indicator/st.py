from Common.Constant import ENUM_APPLIED_PRICE
import talib
import numpy
from datetime import datetime
from Common.Constant import ENUM_INDICATOR
from Utils import utils
from loguru import logger

logger.add('debug_logs/st-{time}.log')

class SuperTrendResult:
    def __init__(self, timestamp, short_stop, long_stop, signal):
        self.timestamp = timestamp
        self.short_stop = short_stop
        self.long_stop = long_stop
        self.signal = signal

    def get_latest(self):
        return SuperTrendResult(self.timestamp,
                                self.short_stop[-1],
                                self.long_stop[-1],
                                self.signal[-1])

    def __str__(self):
        return "SUPER_TREND {} {} {}".format(self.short_stop[-1], self.long_stop[-1], self.signal[-1])

    def __repr__(self):
        return self.__str__()

class SuperTrend:
    name = ENUM_INDICATOR.ST.value

    def __init__(self,
                 applied_price=ENUM_APPLIED_PRICE.PRICE_LOW,
                 atr_period=85,
                 atr_multiplier=9,
                 atr_use_wicks=True
                 ):

        self.applied_price = applied_price
        self.atr_period = int(atr_period)
        self.atr_multiplier = float(atr_multiplier)
        self.atr_use_wicks = atr_use_wicks

    ''' Assumption: data[0] contains oldest data point '''
    def compute(self, candles):

        # price = numpy.array([candle.get_price(self.applied_price) for candle in candles])
        price_close = numpy.array([candle.get_price(ENUM_APPLIED_PRICE.PRICE_CLOSE) for candle in candles])
        price_open = numpy.array([candle.get_price(ENUM_APPLIED_PRICE.PRICE_OPEN) for candle in candles])
        price_high = numpy.array([candle.get_price(ENUM_APPLIED_PRICE.PRICE_HIGH) for candle in candles])
        price_low = numpy.array([candle.get_price(ENUM_APPLIED_PRICE.PRICE_LOW) for candle in candles])

        if self.applied_price == ENUM_APPLIED_PRICE.HL2:
            atr_price_source = (price_high + price_low) / 2
        elif self.applied_price == ENUM_APPLIED_PRICE.HLC3:
            atr_price_source = (price_high + price_low + price_close) / 3
        else:
            atr_price_source = numpy.array([candle.get_price(self.applied_price) for candle in candles])

        atr = self.atr_multiplier * talib.ATR(price_high, price_low, price_close, self.atr_period)
        long_stop = atr_price_source - atr
        short_stop = atr_price_source + atr

        high_price = price_high if self.atr_use_wicks else price_close
        low_price = price_low if self.atr_use_wicks else price_close

        signals = [0]
        direction = [1]
        for i in range(1, len(atr)):
            if not atr[i-1]:
                signals.append(0)
                direction.append(1)
                continue

            doji4price = price_open[i] == price_close[i] and price_open[i] == price_low[i] and price_open[i] == price_high[i]

            if long_stop[i] > 0:
                if doji4price:
                    long_stop[i] = long_stop[i-1]
                else:
                    long_stop[i] = max(long_stop[i], long_stop[i-1]) if low_price[i-1] > long_stop[i-1] else long_stop[i]
            else:
                long_stop[i] = long_stop[i-1]

            if short_stop[i] > 0:
                if doji4price:
                    short_stop[i] = short_stop[i-1]
                else:
                    short_stop[i] = min(short_stop[i], short_stop[i-1]) if high_price[i-1] < short_stop[i-1] else short_stop[i]
            else:
                short_stop[i] = short_stop[i-1]


            if price_high[i] > short_stop[i-1]:
                direction.append(1)
            elif price_low[i] < long_stop[i-1]:
                direction.append(-1)
            else:
                direction.append(direction[-1])

            buy_st = direction[i] == 1 and direction[i-1] != 1
            sell_st = direction[i] == -1 and direction[i-1] != -1

            st_u = long_stop[i] if buy_st else None
            st_d = short_stop[i] if sell_st else None

            if price_close[i] > price_open[i] and st_u:
                signal = 1
            elif price_close[i] < price_open[i] and st_d:
                signal = -1
            else:
                signal = 0

            signals.append(signal)

        #logger.debug(f'{signals[-5:]}\nshort_stop:{short_stop[-5:]}\nlong_stop:{long_stop[-5:]}')


        return SuperTrendResult(datetime.now(), short_stop, long_stop, signals)
