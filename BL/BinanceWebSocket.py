import atexit

from binance.websockets import BinanceSocketManager
from twisted.internet import reactor
import traceback

from Common.Binance.Candle import Candle


class BinanceWebSocket:
    PrevHighPrice = 0
    PrevLowPrice = 0
    PrevClosePrice = 0
    CurrHighPrice = 0
    CurrLowPrice = 0
    CurrClosePrice = 0
    callback = None
    conn_key = None
    is_started = False

    def __init__(self, client):
        self.bsm = BinanceSocketManager(client)

    def exit(self):
        print("WebSocket exit called")
        self.stop()
        reactor.callFromThread(reactor.stop)

    def start(self, streams, callback):
        try:
            self.callback = callback
            self.conn_key = self.bsm.start_multiplex_socket(streams, self.websocket_callback)

            if not self.is_started:
                print("Start bsm")
                self.bsm.start()
                self.is_started = True

        except:
            print(traceback.format_exc())

    def stop(self):
        #print("Stop websocket")
        try:
            if self.bsm:
                if self.conn_key:
                    print("Stop websocket")
                    self.bsm.stop_socket(self.conn_key)
                self.bsm.close()
        except:
            print(traceback.format_exc())

    def websocket_callback(self, msg):
        """
        Each time bot receives an update, it will convert the message to a candle and call given callback func
        :return:
        """
        try:

            if not msg:
                print("Error: websocket_callback msg is null")
                self.callback(None, -1)
                return

            # print("msg: ", msg['data'])
            k = msg['data']['k']
            event_time = int(msg['data']['E']) #msec
            candle = Candle(k['s'], k['i'],
                            k['t'], k['o'], k['h'], k['l'], k['c'], k['v'],
                            k['T'], k['q'], k['n'], k['V'], k['Q'], None, k['x'])
            self.callback(candle, event_time)
        except:
            print(traceback.format_exc())
            # somtimes this function crashes. msg["data"] becomes null
            self.callback(None, -1)
