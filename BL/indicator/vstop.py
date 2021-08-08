from Common.Constant import ENUM_APPLIED_PRICE
import talib
import numpy
from datetime import datetime
from Common.Constant import ENUM_INDICATOR
from Utils import utils


class VstopResult:
    def __init__(self, timestamp, stop, uptrend, signals):
        self.timestamp = timestamp
        self.stop = stop
        self.uptrend = uptrend
        self.signals = signals

    def get_latest(self):
        return VstopResult(self.timestamp, self.stop[-1], self.uptrend[-1], self.signals[-1])

    def __str__(self):
        return "Vstop {}; Uptrend {}; Signal {}".format(self.stop[-1], self.uptrend[-1], self.signals[-1])

    def __repr__(self):
        return self.__str__()

class Vstop:
    name = ENUM_INDICATOR.VSTOP.value

    def __init__(self,
                 applied_price=ENUM_APPLIED_PRICE.PRICE_CLOSE,
                 high_price=ENUM_APPLIED_PRICE.PRICE_HIGH,
                 low_price=ENUM_APPLIED_PRICE.PRICE_LOW,
                 time_period=8,
                 atr_factor=0.75,
                 ema_1_period=1,
                 ema_2_period=2
                 ):

        #print("applied_price")
        #print(applied_price)

        self.applied_price = applied_price
        self.high_price = high_price
        self.low_price = low_price
        self.time_period = int(time_period)
        self.atr_factor = float(atr_factor)
        self.ema_1_period = int(ema_1_period)
        self.ema_2_period = int(ema_2_period)

    def vstop(self, high, low, close, atr_period, atr_factor, ema_1_period, ema_2_period):
        if len(close) > 1:
            max_price = close[1]
            min_price = close[1]
        else:
            max_price = close[0]
            min_price = close[0]

        uptrend = [True]
        stop = [0]

        atr_indicator = talib.ATR(high, low, close, atr_period) * atr_factor
        tr_indicator = talib.TRANGE(high, low, close)

        # talib can't calculate EMA with period 1 because it is the same as the input (close)

        #print(close)
        #print("ema_1_period")
        #print(ema_1_period)

        ema_1 = close if ema_1_period == 1 else talib.EMA(close, ema_1_period)
        ema_2 = talib.EMA(close, ema_2_period)

        for price, atr, tr in list(zip(close, atr_indicator, tr_indicator))[1:]:
            atr = tr if numpy.isnan(atr) else atr
            max_price = max(max_price, price)
            min_price = min(min_price, price)
            stop.append(max(stop[-1], max_price - atr) if uptrend[-1] else min(stop[-1], min_price + atr))
            uptrend.append(price - stop[-1] >= 0)
            if uptrend[-1] != uptrend[-2]:
                max_price = price
                min_price = price
                stop[-1] = max_price - atr if uptrend[-1] else min_price + atr

        signals = [None]
        is_long = False
        is_short = False

        for i in range(1, len(close)):
            e_up = ema_1[i] > ema_2[i] and ema_1[i-1] < ema_2[i-1]
            e_down = ema_1[i] < ema_2[i] and ema_1[i-1] > ema_2[i-1]

            #version 1
            #buy_signal = e_up and uptrend[i] and uptrend[i-1] and not is_long
            #sell_signal = e_down and not uptrend[i] and not uptrend[i-1] and not is_short

            #version 2
            buy_signal = e_up and uptrend[i] and not is_long
            sell_signal = e_down and not uptrend[i] and not is_short



            if buy_signal:
                is_long = True
                is_short = False
                signals.append(1)
            elif sell_signal:
                is_long = False
                is_short = True
                signals.append(-1)
            else:
                signals.append(0)

        return stop, uptrend, signals

    ''' Assumption: data[0] contains oldest data point '''
    def compute(self, candles):

        close = [candle.get_price(self.applied_price) for candle in candles]
        high = [candle.get_price(self.high_price) for candle in candles]
        low = [candle.get_price(self.low_price) for candle in candles]

        highArr = numpy.array(high)
        lowArr = numpy.array(low)
        closeArr = numpy.array(close)

        if self.time_period > 1:
            vstop, uptrend, signals = self.vstop(highArr, lowArr, closeArr, self.time_period, self.atr_factor, self.ema_1_period, self.ema_2_period)
        else:
            # TODO: Are the defaults correct?
            vstop = 0
            uptrend = True
            signals = None

        return VstopResult(datetime.now(), vstop, uptrend, signals)
