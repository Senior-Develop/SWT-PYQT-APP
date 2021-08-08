from Common.Binance.Balance import Balance


class AccountInfo:
    def __init__(self, maker_commission=0, taker_commission=0,
                 buyer_commission=0, seller_commission=0,
                 can_trade=False, can_withdraw=False, can_deposit=False,
                 update_time=0, account_type="", balances=None, permissions=None):
        self.maker_commission = int(maker_commission)
        self.taker_commission = int(taker_commission)
        self.buyer_commission = int(buyer_commission)
        self.seller_commission = int(seller_commission)
        self.can_trade = bool(can_trade)
        self.can_withdraw = bool(can_withdraw)
        self.can_deposit = bool(can_deposit)
        self.update_time = int(update_time)
        self.account_type = account_type
        self.balances = [Balance(*balance.values()) for balance in balances] if balances else []
        self.permissions = permissions if permissions else []

    def __str__(self):
        return str(self.__dict__)

    def __repr__(self):
        return self.__str__()