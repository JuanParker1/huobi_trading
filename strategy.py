import pandas as pd
import numpy as np


def drop_buy_strategy(df: pd.DataFrame, max_holding: int = 10):
    """return the actions at close, trade at close

    Args:
        df (df[float]): high low open close amount count vol timestamp
        max_holding (float): the maximum holding amount

    Returns:
        list[float]: the holding at close
    """
    PERIOD = 30
    INIT_COLD = 1
    INIT_COLD_SELL = 0
    RETURN_RATE = 1.03
    prices = df["close"]
    actions = pd.Series(np.zeros_like(prices))
    cold_time = INIT_COLD
    cur_stocks = 0
    open_price = []
    trade_cnt = 0

    prices_mean = prices.rolling(PERIOD).mean()
    for i in range(PERIOD, prices.shape[0]):
        while cur_stocks and prices[i] > open_price[-1] * RETURN_RATE:
            # if reaches RETURN_RATE, try sell
            cur_stocks -= 1
            trade_cnt += 1
            open_price.pop()
            cold_time = INIT_COLD_SELL

        if cold_time == 0 and cur_stocks < max_holding and prices[i] < prices_mean[i] * 0.97:
            cur_stocks += 1
            cold_time = INIT_COLD
            open_price.append(prices[i])

        actions[i] = cur_stocks
        cold_time = max(cold_time - 1, 0)
        open_price.sort(reverse=True)
    return actions


def test_strategy(df: pd.DataFrame):
    """return the actions at close, trade at close

    Args:
        df (df[float]): high low open close amount count vol timestamp

    Returns:
        list[float]: the holding at close
    """
    PERIOD = 1
    close_rolling5 = df["close"].rolling(5).mean()
    close_rolling10 = df["close"].rolling(10).mean()
    close_rolling30 = df["close"].rolling(30).mean()
    close_rolling60 = df["close"].rolling(60).mean()
    close_rolling120 = df["close"].rolling(120).mean()
    close_rolling180 = df["close"].rolling(180).mean()
    close = df["close"]
    count = df["count"]
    for col in df.columns:
        # print(f"{col}=df['{col}']")
        exec(f"{col}=df['{col}']", globals(), locals())
    div = np.divide
    add = np.add
    sub = np.subtract
    mul = np.multiply
    actions = div(div(div(sub(close_rolling30, close),
                          add(div(div(close_rolling120, close_rolling10),
                                  div(close_rolling30, count)), count)), close), close_rolling10)
    actions = actions.replace([np.inf, -np.inf, np.nan], 0)*100000
    # if df["open"][i] > df["close"][i]:
    #     actions[i] = 1
    # else:
    #     actions[i] = -1

    return actions
