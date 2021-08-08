from Common.Constant import ENUM_APPLIED_PRICE
from Common.Constant import ENUM_INDICATOR
from datetime import datetime


class MptResult:
    def __init__(self, timestamp, value):
        self.timestamp = timestamp
        self.value = value

    def get_latest(self):
        return MptResult(self.timestamp, self.value[-1])

    def __str__(self):
        return "MPT {}".format(self.value[-1])

    def __repr__(self):
        return self.__str__()

class Mpt:
    name = ENUM_INDICATOR.MPT.value

    def __init__(self,
                 applied_price=ENUM_APPLIED_PRICE.PRICE_HIGH,
                 short_ma_length=4,
                 long_ma_length=40):

        # assert short_ma_length < long_ma_length, "Short_MA_Length cannot be larger than Long_MA_Length."

        self.applied_price = applied_price
        self.short_ma_length = int(short_ma_length)
        self.long_ma_length = int(long_ma_length)

    ''' Assumption: data[0] contains oldest data point '''
    def compute(self, candles):
        r1 = self.long_ma_length / (self.long_ma_length - self.short_ma_length)
        r2 = self.short_ma_length / (self.long_ma_length - self.short_ma_length)
        result = [None]*len(candles)
        for i in range(self.long_ma_length, len(candles)):
            price_short = candles[i-self.short_ma_length].get_price(self.applied_price)
            price_long = candles[i-self.long_ma_length].get_price(self.applied_price)
            # print("i:",i,data[i][self.applied_price.value],price_short,price_long)
            result[i] = r1 * price_short - r2 * price_long

        return MptResult(datetime.now(), result)