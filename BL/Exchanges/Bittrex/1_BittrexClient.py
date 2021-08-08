import hmac
import json
import queue
from datetime import datetime
from dateutil.relativedelta import relativedelta
from dateutil.parser import parse
import time
import traceback
import hashlib
from urllib.parse import urlparse
import requests
from queue import Queue

from BL.Exchanges.Bittrex.BittrexWebSocket import BittrexWebSocket
from BL.Exchanges.ClientInterface import ClientInterface
from Common.Asset import Asset
from Common.Exchange.Balance import Balance
from Common.Exchange.Candle import Candle
from Common.Exchange.MarketDailySummary import MarketDailySummary
from Common.Exchange.OrderResponse import OrderResponse
from Common.Market import Market


def compute_prev_date(interval, date: datetime):
    if interval == "1m" or interval == "5m":
        return date + relativedelta(days=-1)
    elif interval == "1h":
        return date + relativedelta(months=-1)
    elif interval == "1d":
        return date + relativedelta(years=-1)
    else:
        return


def create_get_candles_url(symbol, interval, date: datetime):
    if interval == "1m":
        candle_interval = "MINUTE_1"
        date_str = f"{date.year}/{date.month}/{date.day}"
    elif interval == "5m":
        candle_interval = "MINUTE_5"
        date_str = f"{date.year}/{date.month}/{date.day}"
    elif interval == "1h":
        candle_interval = "HOUR_1"
        date_str = f"{date.year}/{date.month}"
    elif interval == "1d":
        candle_interval = "DAY_1"
        date_str = f"{date.year}"
    else:
        return
    url = f"/markets/{symbol}/candles/{candle_interval}/"

    now = datetime.utcnow()
    if date.year == now.year and date.month == now.month and date.day == now.day:
        url = url + "recent"
    else:
        url = url + f"historical/{date_str}"
    return url


def merge_candles(set1, set2):
    for item in set2:
        if [1 for c in set1 if c.open_time == item.open_time]:
            continue
        set1.append(item)
    return set1


def extract_candles(response, symbol, interval):
    candles = []
    if response is None or len(response) == 0:
        return candles

    # response = response[::-1]

    now_ms = int(time.time()*1000)
    sec_in_ms = 1000
    min_in_ms = 60*sec_in_ms
    hour_in_ms = 60*min_in_ms
    day_in_ms = 24*hour_in_ms
    for item in response:
        #timestamp = int(datetime .strptime(item["startsAt"], "%Y-%m-%dT%H:%M:%SZ").timestamp()) * 1000
        open_time_ms = int(parse(item["startsAt"]).timestamp()*1000) # store as milliseconds

        close_time_ms = 0
        is_closed = False
        if interval == "1m":
            close_time_ms = open_time_ms + min_in_ms
        elif interval == "5m":
            close_time_ms = open_time_ms + 5*min_in_ms
        elif interval == "1h":
            close_time_ms = open_time_ms + hour_in_ms
        elif interval == "1d":
            close_time_ms = open_time_ms + day_in_ms

        if 0 < close_time_ms <= now_ms:
            is_closed = True

        candle = Candle(symbol=symbol,
                        interval=interval,
                        open_time=open_time_ms,
                        close_time=close_time_ms,
                        open=item["open"],
                        high=item["high"],
                        low=item["low"],
                        close=item["close"],
                        volume=item["close"],
                        quote_asset_volume=item["quoteVolume"],
                        is_closed=is_closed)
        candles.append(candle)
    return candles


class BittrexClient(ClientInterface):
    url_base = "https://api.bittrex.com/v3"
    call_queue = Queue()

    def __init__(self, api_key, api_secret):
        self.api_key = api_key.encode('utf-8')
        self.api_secret = api_secret.encode('utf-8')
        self.session = requests.Session()
        self.ws = BittrexWebSocket()

    # GET https://api.bittrex.com/v3/ping
    def get_server_time(self) -> int:
        response = self._make_api_call("/ping", method="GET")
        return response["serverTime"]

    # GET AUTH https://api.bittrex.com/v3/balances
    def get_asset_balances(self) -> list:
        balances = self._make_api_call_auth("/balances", method="GET")
        assets = []
        if balances:
            for balance in balances:
                assets.append(Asset(AssetName=balance["currencySymbol"],
                                    BalanceFree=balance["available"],
                                    BalanceLocked=(float(balance["total"]) - float(balance["available"])),
                                    ModifiedDate=datetime.now()))
        return assets

    # GET AUTH https://api.bittrex.com/v3/balances/{currencySymbol}
    def get_asset_balance(self, asset) -> Balance:
        balance = Balance()
        try:
            response = self._make_api_call_auth("/balances/" + asset, method="GET")
            if response:
                balance = Balance(asset=response["currencySymbol"],
                                  free=response["available"],
                                  locked=(float(response["total"]) - float(response["available"])))
        except:
            print(traceback.format_exc())
        return balance

    # GET https://api.bittrex.com/v3/markets
    def get_markets(self, quote_assets=[]) -> list:
        markets = []
        try:
            market_list = self._make_api_call("/markets", method="GET")
            for market in market_list:
                if market['status'] != 'ONLINE':
                    continue
                if not quote_assets or (market['quoteCurrencySymbol'] in quote_assets):
                    m = Market(Symbol=market['symbol'],
                               BaseAsset=market['baseCurrencySymbol'],
                               QuoteAsset=market['quoteCurrencySymbol'])
                    m.MinAmountToTrade = 0
                    if m.QuoteAsset == "BTC":
                        m.MinAmountToTrade = 0.0001
                    if m.QuoteAsset == "ETH":
                        m.MinAmountToTrade = 0.005
                    if m.QuoteAsset == "USDT":
                        m.MinAmountToTrade = 10
                    m.AmountDecimalDigits = market["precision"]

                    markets.append(m)
        except:
            print(traceback.format_exc())
        return markets

    # GET https://api.bittrex.com/v3/markets/summaries -> volume
    # GET https://api.bittrex.com/v3/markets/tickers -> last price
    def get_market_daily_summary(self, symbol):
        daily_summary = None
        try:
            ticker = self._make_api_call("/markets/" + symbol + "/ticker", method="GET")
            summary = self._make_api_call("/markets/" + symbol + "/summary", method="GET")
            daily_summary = MarketDailySummary(
                symbol=symbol,
                volume=summary["volume"],
                quote_volume=summary["quoteVolume"],
                low_price=summary["low"],
                high_price=summary["high"],
                last_price=ticker["lastTradeRate"]
            )
        except:
            print(traceback.format_exc())
        return daily_summary

    # POST AUTH https://api.bittrex.com/v3/orders
    def buy_asset(self, symbol, amount):
        return self._make_trade_order("BUY", symbol, amount)

    # POST AUTH https://api.bittrex.com/v3/orders
    def sell_asset(self, symbol, amount):
        return self._make_trade_order("SELL", symbol, amount)

    def _make_trade_order(self, side, symbol, amount):
        order_response = OrderResponse(direction=side,
                                       order_type="MARKET",
                                       symbol=symbol,
                                       requested_qty=amount,
                                       executed_time=datetime.now())
        try:
            new_order = {
                "marketSymbol": symbol,
                "direction": side,
                "type": "MARKET",
                "quantity": amount,
                "timeInForce": "IMMEDIATE_OR_CANCEL",
            }
            response = self._make_api_call_auth("/orders", method="POST", payload=new_order)
            order_response.commission = float(response["commission"])
            order_response.executed_qty = float(response["fillQuantity"])
            order_response.avg_price = float(response["proceeds"]) / float(response["fillQuantity"])
            order_response.status = response["status"]
            if order_response.requested_qty == order_response.executed_qty:
                order_response.status = "FILLED"
        except TypeError as e:
            print(traceback.format_exc())
            print("Response:", response)
            order_response.status = str(e)
        except Exception as ex:
            print(traceback.format_exc())
            print("Response:", response)
            order_response.status = '(' + str(ex.code) + ') ' + ex.message

        return order_response

    # GET /markets/{marketSymbol}/candles/{candleType}/{candleInterval}/recent
    # GET / markets / {marketSymbol} / candles / {candleType} / {candleInterval} / historical / {year} / {month} / {day}
    def get_candles(self, symbol, interval, limit=300):
        candles = []
        current_date = datetime.utcnow()
        while len(candles) < limit:
            url = create_get_candles_url(symbol, interval, current_date)
            print(url)
            response = self._make_api_call(url, "GET")
            new_candles = extract_candles(response, symbol, interval)
            if len(new_candles) == 0:
                break
            candles = merge_candles(new_candles, candles)

            current_date = compute_prev_date(interval, current_date)
            # time.sleep(1.5)
        return candles[:limit]

    # GET /markets/{marketSymbol}/candles/{candleType}/{candleInterval}/recent
    # GET / markets / {marketSymbol} / candles / {candleType} / {candleInterval} / historical / {year} / {month} / {day}
    def get_candles_historical(self, symbol, interval, start_time, end_time):
        candles = []
        current_date = datetime.utcfromtimestamp(end_time/1000)
        while True:
            url = create_get_candles_url(symbol, interval, current_date)
            if not url:
                print("Cant get candles for: ", symbol, interval)
                break
            response = self._make_api_call(url, "GET")
            new_candles = extract_candles(response, symbol, interval)
            if len(new_candles) == 0:
                break
            candles = merge_candles(new_candles, candles)

            if candles[0].open_time <= start_time:
                break

            current_date = compute_prev_date(interval, current_date)
            # time.sleep(1.5)

        return [candle for candle in candles if start_time <= candle.open_time < end_time]


    def _make_api_call(self, path, method):
        url = self.url_base + path
        return self._make_request(url, method=method)

    def _make_api_call_auth(self, path, method, payload={}):
        url = self.url_base + path
        if not payload:
            payload = ""
        else:
            payload = json.dumps(payload, separators=(',', ':'))
        content_hash = hashlib.sha512(payload.encode('utf-8')).hexdigest()
        timestamp = str(int(time.time() * 1000))
        presign = timestamp + url + method + content_hash
        # signature = hashlib.sha512(presign, self.api_secret).hexdigest()
        signature = hmac.new(self.api_secret, presign.encode('utf-8'), digestmod=hashlib.sha512).hexdigest()
        headers = {
            "Api-Key": self.api_key,
            "Api-Timestamp": timestamp,
            "Api-Content-Hash": content_hash,
            "Api-Signature": signature,
        }
        response = self._make_request(url, method=method, headers=headers, payload=payload)
        return response

    def _make_request(self, url, method="GET", headers={}, num_retries=5, payload=None):
        headers = {
            **headers,
            "Connection": "keep-alive",
            "Accept": "text/html,application/xhtml+xml,application/xml;q=0.9,image/webp,image/apng,*/*;q=0.8,application/signed-exchange;v=b3;q=0.9",
            "Accept-Encoding": "gzip,deflate",
            "Accept-Language": "tr-TR,tr;q=0.9,en-US;q=0.8,en;q=0.7",
            "Content-Type": "application/json;charset=UTF-8",
            "Cache-Control": "no-cache",
            "Pragma": "no-cache",
            "Sec-Fetch-Dest": "document",
            "Sec-Fetch-Mode": "navigate",
            "Sec-Fetch-Site": "none",
            "Sec-Fetch-User": "?1",
            "Upgrade-Insecure-Requests": "1",
            "User-Agent": "Mozilla/5.0 (Windows NT 5.1; rv:41.0) Gecko/20100101 Firefox/41.0",
        }

        uri = urlparse(url)
        headers["host"] = uri.netloc
        headers["scheme"] = uri.scheme
        headers["origin"] = uri.scheme + "://" + uri.netloc
        headers["referrer"] = uri.scheme + "://" + uri.netloc

        try:
            #print("Downloading: ", url)

            q = BittrexClient.call_queue

            time.sleep(0.5)

            # check number of recent api calls to avoid getting blocked
            cutoff = datetime.now() - relativedelta(seconds=60)
            while q.qsize() > 0 and q.queue[0] < cutoff:
                q.get()
            if q.qsize() == 55:
                # 55 api calls within last 60 seconds
                elapsed_time = q.queue[0] - cutoff
                sleep_time = elapsed_time.total_seconds()
                print("55 calls within last 60 seconds. Sleeping for", sleep_time, "seconds")
                time.sleep(sleep_time)
            q.put(datetime.now())

            if method == "POST":
                response = self.session.post(url, headers=headers, data=payload, allow_redirects=True)
            else:
                response = self.session.get(url, headers=headers)

            if response.status_code != 200 and response.status_code != 201:
                print("Download error: ", response.status_code)
                print("Response: ", response.text)
                if num_retries > 0 and 500 <= response.status_code < 600:
                    print("Trying again for code: ", response.status_code)
                    time.sleep(1.5)
                    return self._make_request(url, method, headers, num_retries - 1, payload)
                return

            return response.json()
        except requests.exceptions.RequestException as e:
            print("Download error: ", e.response)
            return

    def start_websocket(self, symbols, interval, callback):
        try:
            print("start_web_socket")
            self.ws.start(symbols, interval, callback)
        except:
            print(traceback.format_exc())

    def stop_websocket(self):
        try:
            if self.ws:
                self.ws.stop()
        except:
            print(traceback.format_exc())

    def exit_websocket(self):
        try:
            if self.ws:
                self.ws.exit()
        except:
            print(traceback.format_exc())