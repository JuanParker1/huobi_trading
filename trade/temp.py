from test import Trader
import time
from huobi.privateconfig import p_api_key, p_secret_key
from huobi.client.trade import TradeClient
from huobi.client.market import MarketClient
from huobi.client.wallet import WalletClient
from huobi.client.account import AccountClient
from huobi.constant import *
from decimal import *
import pickle
import os

if __name__ == '__main__':
    t = Trader()
    while True:
        order_obj = t.trade_client.get_order(order_id=204610773149465)
        print(order_obj.state)
        if order_obj.state == "filled":
            sell_amount = (Decimal(order_obj.filled_amount) - Decimal(
                order_obj.filled_fees)).quantize(Decimal('.0001'), rounding=ROUND_DOWN)
            sell_price = Decimal("440").quantize(
                Decimal('.0001'), rounding=ROUND_DOWN)
            sell_order_id = t.trade_client.create_order("btc3lusdt", t.account_id, OrderType.SELL_LIMIT,
                                                        sell_amount, sell_price, source=OrderSource.API, client_order_id=10009)
            break
        time.sleep(5)
