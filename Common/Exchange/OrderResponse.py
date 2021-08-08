class OrderResponse:
    def __init__(self,
                 status="",
                 direction="",
                 order_type="",
                 symbol="",
                 requested_qty=0,
                 executed_qty=0,
                 avg_price=0.0,
                 commission=0.0,
                 executed_time=None):
        self.status = status
        self.direction = direction
        self.order_type = order_type
        self.symbol = symbol
        self.requested_qty = requested_qty
        self.executed_qty = executed_qty
        self.avg_price = avg_price
        self.commission = commission
        self.executed_time = executed_time

    def __str__(self):
        return str(self.__dict__)

    def __repr__(self):
        return self.__str__()


# response['status'] = "FILLED"
# response['executedQty'] = str(tradeAmount)
# response['totalCommission'] = str(tradeAmount / 100 * self.CommissionPercentage)
# response['transactTime'] = datetime.now()
# response['avgPrice'] = "0"
# response['fills']
#
# for f in response['fills']:
#     totalCommission = totalCommission + decimal.Decimal(f['commission'])
#     avgPrice = avgPrice + decimal.Decimal(f['qty']) * decimal.Decimal(f['price'])