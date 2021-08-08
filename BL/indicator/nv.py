from Common.Exchange.Candle import Candle
from typing import List
from datetime import datetime


class NvResult:
    def __init__(self, timestamp, buy_sell_percent, sell_buy_percent, net_volume):
        self.timestamp = timestamp
        self.buy_sell_percent = buy_sell_percent
        self.sell_buy_percent = sell_buy_percent
        self.net_volume = net_volume

    def get_latest(self):
        return NvResult(self.timestamp, self.buy_sell_percent[-1], self.sell_buy_percent[-1], self.net_volume[-1])

    def __str__(self):
        return "NV {} {} {}".format(self.buy_sell_percent[-1], self.sell_buy_percent[-1], self.net_volume[-1])

    def __repr__(self):
        return self.__str__()

class Nv:
    name = "NV"

    # def __init__(self, min_buy_sell_volume_percent, min_net_volume):
    #     self.min_buy_sell_volume_percent = float(min_buy_sell_volume_percent)
    #     self.min_net_volume = float(min_net_volume)

    ''' Assumption: data[0] contains oldest data point '''
    def compute(self, candles: List[Candle]):
        # signal = [None] * len(candles)
        # total_percent = [None] * len(candles)
        buy_sell_percent = [0] * len(candles)
        sell_buy_percent = [0] * len(candles)
        net_volume = [0] * len(candles)

        for i in range(len(candles)):
            curr = candles[i]
            curr_total_volume = curr.volume
            curr_buy_volume = curr.taker_buy_base_asset_volume
            curr_sell_volume = curr_total_volume - curr_buy_volume
            curr_net_volume = curr_buy_volume - curr_sell_volume

            # prev = candles[i-1]
            # prev_total_volume = prev.volume
            # prev_buy_volume = prev.taker_buy_base_asset_volume
            # prev_sell_volume = prev_total_volume - prev_buy_volume

            net_volume[i] = curr_net_volume

            if curr_buy_volume > curr_sell_volume:
                if curr_sell_volume != 0:
                    buy_sell_percent[i] = ((curr_buy_volume - curr_sell_volume) / curr_sell_volume) * 100
                else:
                    buy_sell_percent[i] = curr_buy_volume
            else:
                if curr_buy_volume != 0:
                    sell_buy_percent[i] = ((curr_sell_volume - curr_buy_volume) / curr_buy_volume) * 100
                else:
                    sell_buy_percent[i] = curr_sell_volume

        return NvResult(datetime.now(), buy_sell_percent, sell_buy_percent, net_volume)
