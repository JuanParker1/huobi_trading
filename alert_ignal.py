from huobi.privateconfig import p_api_key, p_secret_key
from huobi.client.trade import TradeClient
from huobi.client.market import MarketClient
from huobi.client.wallet import WalletClient
from huobi.client.account import AccountClient
import tkinter
from tkinter import messagebox
import time
from huobi.constant import *
from huobi.utils import *

def alert(msg: str):
    root = tkinter.Tk()
    root.withdraw()
    root.lift()
    messagebox.showinfo("Title", msg)


class Trader:
    def __init__(self):
        self.cash = 0
        self.stock = 0
        self.history_data = []
        self.open_prices = []
        self.log_file = "trade_log.txt"
        self.account_id = 1037218
        self.trade_client = TradeClient(
            api_key=p_api_key, secret_key=p_secret_key, init_log=True)
        self.market_client = MarketClient()
        self.wallet_client = WalletClient(
            api_key=p_api_key, secret_key=p_secret_key)
        self.account_client = AccountClient(api_key=p_api_key,
                                            secret_key=p_secret_key)

    def run(self):
        while True:
            if self.check_buy_condition():
                self.buy()
            time.sleep(25)

    def check_buy_condition(self):
        interval = CandlestickInterval.MIN1
        symbol = "btc3lusdt"
        length = 30
        list_obj = self.market_client.get_candlestick(
            symbol, interval, length+1)
        price_sum = 0

        for candlestick in list_obj[1:]:
            price_sum += candlestick.close
        price_sum_average = price_sum / length
        print(price_sum_average,list_obj[0].close)
        if list_obj[0].close < price_sum_average*0.95:
            return True
        else:
            return False

def listen(market_client,listen_prices,symbol="ethusdt"):
    i=0
    while True:
        i+=1
        interval = CandlestickInterval.MIN1
        list_obj = market_client.get_candlestick(symbol, interval, 1)
        cur=list_obj[0]
        for price in listen_prices:
            if cur.low<=price<=cur.high:
                alert(f"{symbol} reaches {price:.2f}")
                return
        if i%20==0:
            print(cur.low, cur.high)
        time.sleep(30)

def check():
    t= Trader()
    while True:
        if t.check_buy_condition():
            alert("buy!!")
        time.sleep(2)

if __name__ == "__main__":
    check()