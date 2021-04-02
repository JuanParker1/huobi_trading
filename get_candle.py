from huobi.client.market import MarketClient
from huobi.constant import *
from huobi.exception.huobi_api_exception import HuobiApiException
import pandas as pd
import pickle
import time

SYMBOLS = ["btcusdt"]

for SYMBOL in SYMBOLS:
    save = []

    def callback(candlestick_req: 'CandlestickReq'):
        save.extend(candlestick_req.data)

    def error(e: 'HuobiApiException'):
        print(e.error_code + e.error_message)

    sub_client = MarketClient(init_log=True)
    timestamp = int(time.time())
    PERIOD = 24 * 60 * 60 * 180
    for i in range(timestamp - PERIOD, timestamp, 300 * 60):
        sub_client.req_candlestick(SYMBOL, CandlestickInterval.MIN1, callback, from_ts_second=i, end_ts_second=i + 299 * 60, error_handler=error)
        print(i)
        time.sleep(1)
    # sub_client.req_candlestick("btcusdt", CandlestickInterval.MIN1, callback, from_ts_second=1571124360, end_ts_second=1571124361)
    #sub_client.request_candlestick_event("btcusdt", CandlestickInterval.MIN1, callback, from_ts_second=1569361140, end_ts_second=0)
    #sub_client.request_candlestick_event("btcusdt", CandlestickInterval.MIN1, callback, from_ts_second=1569379980)
    # sub_client.req_candlestick("btcusdt", CandlestickInterval.MIN1, callback)

    time.sleep(60 * 2)
    cur = time.strftime(r"%Y_%m_%d_%H_%M_%S")
    print(len(save))
    sorted_save = sorted(save, key=lambda x: x.id)
    print(save[0].id)
    df = pd.DataFrame([vars(f) for f in sorted_save])
    with open(f'data/{SYMBOL}_{cur}.pkl', 'wb') as f:
        pickle.dump(df, f)

    print(f"{SYMBOL} saved")
