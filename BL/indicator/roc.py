from Common.Constant import ENUM_APPLIED_PRICE
from Common.Constant import ENUM_INDICATOR
import math
from datetime import datetime
from Utils import utils


class RocResult:
    def __init__(self, timestamp, change_r, change_f, change_s, signal_r, signal_f, signal_s):
        self.timestamp = timestamp
        self.change_r = change_r
        self.change_f = change_f
        self.change_s = change_s
        self.signal_r = signal_r
        self.signal_f = signal_f
        self.signal_s = signal_s

    def get_latest(self):
        return RocResult(self.timestamp,
                         self.change_r[-1],
                         self.change_f[-1],
                         self.change_s[-1],
                         self.signal_r[-1],
                         self.signal_f[-1],
                         self.signal_s[-1])

    def __str__(self):
        return "ROC {} {} {} {} {} {}".format(self.change_r[-1], self.change_f[-1], self.change_s[-1],
                                              self.signal_r[-1], self.signal_f[-1], self.signal_s[-1])

    def __repr__(self):
        return self.__str__()

    #def _del_(self):
    #    del self.value;

class Roc:
    name = ENUM_INDICATOR.ROC.value
    precision = 0.01

    def __init__(self,
                 applied_price_r=ENUM_APPLIED_PRICE.PRICE_LOW,
                 applied_price_f=ENUM_APPLIED_PRICE.PRICE_LOW,
                 applied_price_s=ENUM_APPLIED_PRICE.PRICE_LOW,
                 roc_period_r=3,
                 roc_period_f=3,
                 roc_period_s=3,
                 r_buy_increase_percentage=0,
                 f_buy_decrease_percentage=0,
                 s_sell_decrease_percentage=0,
                 roc_smoothing_r=1,
                 roc_smoothing_s=1,



                 ):

        # assert roc_period_r >= 1 and \
        #        roc_period_f >= 1 and \
        #        roc_period_s >= 1, "RocPeriod cannot be smaller than 1."
        # assert r_buy_increase_percentage >= 0, "R_Buy_Increase_Percentage cannot be smaller than 0."
        # assert f_buy_decrease_percentage >= 0, "F_Buy_Decrease_Percentage cannot be smaller than 0."
        # assert s_sell_decrease_percentage >= 0, "S_Sell_Decrease_Percentage cannot be smaller than 0."

        self.applied_price_r = applied_price_r
        self.applied_price_f = applied_price_f
        self.applied_price_s = applied_price_s
        self.roc_period_r = int(roc_period_r)
        self.roc_period_f = int(roc_period_f)
        self.roc_period_s = int(roc_period_s)
        self.r_buy_increase_percentage = float(r_buy_increase_percentage)
        self.f_buy_decrease_percentage = float(f_buy_decrease_percentage)
        self.s_sell_decrease_percentage = float(s_sell_decrease_percentage)
        self.roc_smoothing_r = int(roc_smoothing_r)
        self.roc_smoothing_s = int(roc_smoothing_s)

        #self.roc_period_r = max(self.roc_period_r, 5)

    # def __get_column(self, candles, column):
    #     return [candle[column] for candle in candles]

    #def _del_(self):
    #    del self.value;

    ''' Assumption: data[0] contains oldest data point '''
    def __calculate(self, candles, price_type, period, smoothing):
        result = [None]*len(candles)
        smoothresult = [None] * len(candles)

        for i in range(period, len(candles)):
            #curr = candles[i].get_price(ENUM_APPLIED_PRICE.PRICE_CLOSE)

            curr = candles[i].get_price(price_type)
            prev = candles[i-period].get_price(price_type)
            result[i] = 100 * (curr - prev) / prev
            if smoothing > 1:
                avg = 0
                for j in range(smoothing):
                    if i - j >= 0 and result[i-j] is not None:
                        avg = avg + result[i-j]
                smoothresult[i] = avg / smoothing

        if smoothing <= 1:
            return result
        else:
            return smoothresult


    def compute(self, candles):
        #print(str(self.applied_price_r) + "   " + str(self.roc_period_r) + "   " + str(self.roc_smoothing_r) + "   ")
        #print(str(self.applied_price_s) + "   " + str(self.roc_period_s) + "   " + str(self.roc_smoothing_s) + "   ")

        change_r = self.__calculate(candles, self.applied_price_r, self.roc_period_r, self.roc_smoothing_r)
        #print(change_r)
        #print(len(candles))

        change_f = self.__calculate(candles, self.applied_price_f, self.roc_period_f, 1)
        change_s = self.__calculate(candles, self.applied_price_s, self.roc_period_s, self.roc_smoothing_s)
        signal_r = [None if not d else
                    1 if utils.compare_floats(abs(d), self.r_buy_increase_percentage, self.precision) == 1 #utils.compare_floats(d, 0, self.precision) == 1 and
                    else 0 for d in change_r]

        #original version: r_buy_increase_percentage > change_r olmali
        #signal_r = [None if not d else
        #            1 if utils.compare_floats(d, 0, self.precision) == 1 and
        #                 utils.compare_floats(abs(d), self.r_buy_increase_percentage, self.precision) == 1
        #            else 0 for d in change_r]
        signal_f = [None if not d else
                    1 if utils.compare_floats(d, 0, self.precision) == -1 and
                         utils.compare_floats(abs(d), self.f_buy_decrease_percentage, self.precision) == 1
                    else 0 for d in change_f]
        signal_s = [None if not d else
                    1 if utils.compare_floats(d, 0, self.precision) == -1 and
                         utils.compare_floats(d, self.s_sell_decrease_percentage, self.precision) == -1
                    else 0 for d in change_s]

        # entry_point = self.__calculate_entry_price(candles, signal_r, signal_f)
        # return RocResult(datetime.now(), change_r[-1], change_f[-1], change_s[-1], signal_r[-1], signal_f[-1], signal_s[-1])
        return RocResult(datetime.now(), change_r, change_f, change_s, signal_r, signal_f, signal_s)

    # def __calculate_entry_price_for_r(self, candles):
    #     results = [None]*len(candles)
    #     for i,d in enumerate(candles):
    #         if i < self.roc_period_r:
    #             continue
    #
    #         perc_diff = 0
    #         price = 0
    #         open_price = d.get_price(ENUM_APPLIED_PRICE.PRICE_OPEN)
    #         prev_price = candles[i - self.roc_period_r].get_price(self.applied_price_r)
    #         price_change_percentage_at_open = ((open_price - prev_price) / prev_price) * 100
    #
    #         if utils.compare_floats(price_change_percentage_at_open, 0) == 1:
    #             if utils.compare_floats(price_change_percentage_at_open, self.r_buy_increase_percentage) == 1:
    #                 price = open_price
    #             else:
    #                 perc_diff = self.r_buy_increase_percentage - abs(price_change_percentage_at_open)
    #         else:
    #             perc_diff = self.r_buy_increase_percentage + abs(price_change_percentage_at_open)
    #
    #         if perc_diff != 0:
    #             price = open_price * (1 + (perc_diff/100.0))
    #
    #         # print(open_price, price_change_percentage_at_open, self.r_buy_increase_percentage, perc_diff, price)
    #         results[i] = price
    #     return results
    #
    # def __calculate_entry_price_for_f(self, candles):
    #     results = [None]*len(candles)
    #     for i,d in enumerate(candles):
    #         if i < self.roc_period_f:
    #             continue
    #
    #         perc_diff = 0
    #         price = 0
    #         open_price = d.get_price(ENUM_APPLIED_PRICE.PRICE_OPEN)
    #         prev_price = candles[i - self.roc_period_f].get_price(self.applied_price_f)
    #         price_change_percentage_at_open = ((open_price - prev_price) / prev_price) * 100
    #
    #         if utils.compare_floats(price_change_percentage_at_open, 0) == -1:
    #             if utils.compare_floats(abs(price_change_percentage_at_open), self.f_buy_decrease_percentage) == 1:
    #                 price = open_price
    #             else:
    #                 perc_diff = self.f_buy_decrease_percentage - abs(price_change_percentage_at_open)
    #         else:
    #             perc_diff = self.f_buy_decrease_percentage + abs(price_change_percentage_at_open)
    #
    #         if perc_diff != 0:
    #             price = open_price * ((100.0 - perc_diff)/100.0)
    #
    #         # print(open_price, price_change_percentage_at_open, self.f_buy_decrease_percentage, perc_diff, price)
    #         results[i] = price
    #     return results
    #
    # def __calculate_entry_price(self, candles, signal_r, signal_f):
    #     entry_r = self.__calculate_entry_price_for_r(candles)
    #     entry_f = self.__calculate_entry_price_for_f(candles)
    #     results = [entry_r[i] if signal_r[i] == 1 else entry_f[i] if signal_f[i] == 1 else 0 for i in range(len(candles))]
    #     return results


