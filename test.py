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


class Trader:
    def __init__(self):
        self.cash = 0
        self.stock = 0
        self.history_data = []
        self.active_buy_orders = {}
        # Dict: order_id: order_id, client_order_id, order_price, time.time()
        self.client_order_id = 6
        self.config_file = "config.pkl"
        self.order_price = Decimal(0)
        self.symbol = "btc3lusdt"
        self.trade_log_file = "trade_log.txt"
        self.run_log_file = "run_log.txt"
        self.error_log_file = "error_log.txt"
        self.account_id = 1037218
        self.last_buy_time = 0
        self.buy_cooling_time = 20  # second
        self.trade_client = TradeClient(
            api_key=p_api_key, secret_key=p_secret_key, init_log=True)
        self.market_client = MarketClient()
        self.account_client = AccountClient(api_key=p_api_key,
                                            secret_key=p_secret_key)

        if os.path.exists(self.config_file):
            with open(self.config_file, 'rb') as f:
                self.client_order_id, self.active_buy_orders = pickle.load(f)

    def run(self):
        while True:
            try:
                if self.check_buy_condition():
                    self.buy()
            except Exception as e:
                self.error_log(str(e))
            try:
                self.update_orders()
            except Exception as e:
                self.error_log(str(e))
            time.sleep(5)

    def check_buy_condition(self):
        if time.time() < self.last_buy_time + self.buy_cooling_time:
            self.trade_log(f"TRY BUYING but in COLDTIME at {self.order_price:0.4f}")
            return False
        interval = CandlestickInterval.MIN1
        length = 30
        list_obj = self.market_client.get_candlestick(
            self.symbol, interval, length+1)
        price_sum = 0

        for candlestick in list_obj[1:]:
            price_sum += candlestick.close
        price_sum_average = price_sum / length

        self.run_log(f"{self.client_order_id} {self.active_buy_orders} {list_obj[0].close:0.4f} {price_sum_average:0.4f} {price_sum_average*0.95:0.4f}")

        if list_obj[0].close < price_sum_average*0.95:
            self.order_price = Decimal(list_obj[0].close)
            return True
        else:
            return False

    def buy(self):
        division = Decimal(10)
        usdt_balance = Decimal(self.get_currency_balance("usdt"))
        min_order = Decimal(6)
        if usdt_balance < min_order:
            self.trade_log(f"TRY BUYING but NO ENOUGH MONEY at {self.order_price:0.4f}")
            return
        total_balance = Decimal(self.get_balance())
        buy_amount_usdt = max(min_order, min(
            total_balance/division, usdt_balance))
        buy_amount = (
            buy_amount_usdt/self.order_price).quantize(Decimal('.0001'), rounding=ROUND_DOWN)

        cur_timestamp = int(time.time())
        self.last_buy_time = cur_timestamp
        self.client_order_id += 1
        order_id = self.trade_client.create_order(self.symbol, self.account_id, OrderType.BUY_LIMIT,
                                                  buy_amount, self.order_price, source=OrderSource.API,
                                                  client_order_id=str(self.client_order_id))
        self.trade_log(
            f"{order_id}: BUY ORDERED.   BUY {buy_amount} at {self.order_price}")
        self.active_buy_orders[order_id] = [
            order_id, self.client_order_id, self.order_price, cur_timestamp]

    def update_orders(self):
        cur_timestamp = time.time()
        waiting_limit = 60*5
        for order_id in list(self.active_buy_orders):
            _, _, order_price, order_cur_timestamp = self.active_buy_orders[order_id]
            order_obj = self.trade_client.get_order(order_id=order_id)
            order_state = order_obj.state
            if order_state == "filled":
                sell_amount = (Decimal(
                    order_obj.filled_amount) - Decimal(order_obj.filled_fees)).quantize(Decimal('.0001'), rounding=ROUND_DOWN)
                sell_price = (order_price*Decimal(1.03)
                              ).quantize(Decimal('.0001'), rounding=ROUND_DOWN)

                self.trade_log(
                    f"{order_id}: BUY SUCCEEDED. BUY {sell_amount} at {order_price}")
                self.client_order_id += 1
                sell_order_id = self.trade_client.create_order(self.symbol, self.account_id, OrderType.SELL_LIMIT,
                                                               sell_amount, sell_price, source=OrderSource.API,
                                                               client_order_id=str(
                                                                   self.client_order_id))

                self.trade_log(
                    f"{sell_order_id}: SELL ORDERED.  SELL {sell_amount} at {sell_price}")
                del self.active_buy_orders[order_id]

            elif cur_timestamp - order_cur_timestamp > waiting_limit:
                self.trade_client.cancel_order(self.symbol, order_id)
                del self.active_buy_orders[order_id]

        with open(self.config_file, 'wb') as f:
            pickle.dump((self.client_order_id, self.active_buy_orders), f)

    def get_currency_balance(self, currency: str) -> str:
        balances = self.account_client.get_balance(self.account_id)
        for balance in balances:
            if balance.currency == currency and balance.type == "trade":
                return balance.balance

    def get_balance(self) -> str:
        asset_valuation = self.account_client.get_account_asset_valuation(
            account_type="spot", valuation_currency="usd")
        return asset_valuation.balance

    def trade_log(self, msg):
        cur_time = time.strftime(r"%Y%m%d_%H%M%S")
        print(cur_time, msg)
        with open(self.trade_log_file, "a+") as f:
            f.write(f"{cur_time} {msg}\n")

    def run_log(self, msg):
        cur_time = time.strftime(r"%Y%m%d_%H%M%S")
        print(cur_time, msg)
        with open(self.run_log_file, "a+") as f:
            f.write(f"{cur_time} {msg}\n")

    def error_log(self, msg):
        cur_time = time.strftime(r"%Y%m%d_%H%M%S")
        print(cur_time, msg)
        with open(self.error_log_file, "a+") as f:
            f.write(f"{cur_time} {msg}\n")



if __name__ == "__main__":
    trader = Trader()
    trader.run()
