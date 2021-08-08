from enum import Enum


class ENUM_APPLIED_PRICE(Enum):
    PRICE_HIGH = 'High'
    PRICE_LOW = 'Low'
    PRICE_OPEN = 'Open'
    PRICE_CLOSE = 'Close'

    def get_price(p):
        if p.lower() == ENUM_APPLIED_PRICE.PRICE_HIGH.value.lower(): return ENUM_APPLIED_PRICE.PRICE_HIGH
        if p.lower() == ENUM_APPLIED_PRICE.PRICE_LOW.value.lower(): return ENUM_APPLIED_PRICE.PRICE_LOW
        if p.lower() == ENUM_APPLIED_PRICE.PRICE_OPEN.value.lower(): return ENUM_APPLIED_PRICE.PRICE_OPEN
        if p.lower() == ENUM_APPLIED_PRICE.PRICE_CLOSE.value.lower(): return ENUM_APPLIED_PRICE.PRICE_CLOSE
        return None


class ENUM_ORDER_SIDE(Enum):
    SELL = 'Sell'
    BUY = 'Buy'


class ENUM_INDICATOR(Enum):
    ROC = 'ROC'
    MPT = 'MPT'
    TREND = 'Trend'
    NV = 'NV'
    RSI = 'RSI'
    STOCH = 'Stoch'
    STOCHRSI = 'StochRsi'
    EMAX = 'EMAX'
    VSTOP = 'VSTOP'


# class INTERVAL(Enum):
#     MINUTE_1 = '1m'
#     MINUTE_5 = '5m'
#     MINUTE_15 = '15m'
#     MINUTE_30 = '30m'
#     HOUR_1 = '1h'
#     HOUR_2 = '2h'
#     HOUR_4 = '4h'
#     DAY_1 = '1d'
