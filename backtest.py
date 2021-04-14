import requests
import json
from scipy.stats import norm
import pandas as pd
import numpy as np
import matplotlib.pyplot as plt
import pickle
from tqdm import tqdm
from gplearn.genetic import SymbolicClassifier


def get_prices(name: str) -> pd.DataFrame:
    # load a pkl file into a dataframe
    # columns: high low open close amount count vol timestamp
    with open(name, "rb") as f:
        df: pd.DataFrame = pickle.load(f)
    df.dropna(inplace=True)
    df["timestamp"] = pd.to_datetime(df["id"], unit="s")
    df = df.set_index(df["timestamp"])
    df = df.drop(columns=["id"])
    return df


def make_return_series(prices, actions, init_cash, fee=0):
    """return the accumulated returns and each time unit return

    Args:
        prices (list[float]): the close price
        fee (float): transaction fee rate
        actions (list[float]): the holding stocks at close, trade at close
        init_cash (float): total cash at the beginning of trading

    Returns:
        (list[float]): accumulated returns of each time unit
        (list[float]): returns of each time unit
    """
    prev_assets = init_cash
    cur_stocks = 0
    cur_cash = init_cash
    cur_assets = init_cash
    R_series = np.empty_like(actions)
    R_single_series = np.empty_like(actions)
    num_actions = len(actions)
    for i in tqdm(range(num_actions)):
        transaction_cost = abs(cur_stocks - actions[i]) * prices[i] * fee
        cur_cash = cur_cash + (cur_stocks - actions[i]) * prices[i] - transaction_cost
        # update assets & stocks
        prev_assets = cur_assets
        cur_assets = actions[i] * prices[i] + cur_cash
        cur_stocks = actions[i]
        # assert(cur_stocks >= 0 and cur_assets >= 0)
        # save to result
        R_single_series[i] = (cur_assets - prev_assets) / prev_assets
        R_series[i] = (cur_assets - init_cash) / init_cash
    return pd.Series(R_series), pd.Series(R_single_series)


def get_sharpe_from_minute(R_single_series: pd.Series) -> float:
    if R_single_series.sum()==0:
        return 0
    return R_single_series.mean() / R_single_series.std() * (365 * 24 * 60)**0.5


def get_turnover(prices: pd.Series, actions: pd.Series) -> float:
    return (abs(actions.diff().fillna(actions)).values * prices.values).sum()


def plot_result(prices, actions, R_series, R_single_series, init_cash=1, need_actions=True, diff_sharpe=True):
    """plot actions and returns of each time unit

    Args:
        prices (list[float]): prices at close
        actions (list[float]): actions at close
        R_series (list[float]): returns at close
    """
    fig = plt.figure(figsize=(12, 8), dpi=100, facecolor="w", edgecolor="k")
    ax = fig.add_subplot(111)
    ax.plot(prices.index.values, R_series, label="Returns")
    if need_actions:
        ax2 = ax.twinx()
        ax2.plot(prices.index.values, actions, label="action", color="orange")
    turnover = get_turnover(prices, actions)
    pnl_over_turnover = R_series.iloc[-1] * init_cash / turnover * 1000
    # net earn = 1 - turnover/pnl * fee%
    if diff_sharpe:
        plt.title(f"sharpe: {get_sharpe_from_minute(R_series.diff())}, pot: {pnl_over_turnover}")
    else:
        plt.title(f"sharpe: {get_sharpe_from_minute(R_single_series)}, pot: {pnl_over_turnover}")
    plt.xlabel("Date")
    plt.ylabel("Returns")
    plt.grid()
    plt.legend(loc="upper right")
    plt.show()


def plot_return_distribution(return_series: pd.Series):
    # usage: df[:]["close"].pct_change()
    return_series = return_series.copy()
    return_series.dropna(inplace=True)
    # Create figure
    plt.figure(figsize=(12, 8), dpi=100, facecolor="w", edgecolor="k")
    bins = int(np.ceil(np.sqrt(len(return_series))))
    plt.hist(return_series, bins=bins, density=True)
    plt.grid()
    # Plot the PDF, Fit a normal distribution to the data:
    mu, std = norm.fit(return_series)
    xmin, xmax = plt.xlim()
    x = np.linspace(xmin, xmax, 100)
    p = norm.pdf(x, mu, std)
    plt.plot(x, p, "k", linewidth=2)
    title = f"norm fit: mean: {100 * mu:.4f}%, standard deviation: {100 * std:.4f}% "
    plt.title(title)
    plt.show()


def plot_upper_lower_series(series: pd.Series, mean_period=5, std_period=60):
    # usage: df['close']
    series = series.copy()
    plt.figure(figsize=(12, 8), dpi=100, facecolor="w", edgecolor="k")
    plt.plot(series, label="price")
    plt.plot(series.rolling(mean_period).mean() + 2 * series.rolling(std_period).std(), label="upper")
    plt.plot(series.rolling(mean_period).mean() - 2 * series.rolling(std_period).std(), label="lower")
    plt.grid()
    plt.legend()
    plt.show()


def multi_trade_backtest(name: str, func, need_actions=False):
    df = get_prices(name)["2021-3-1":]

    df_train = df.copy()
    prices = df_train["close"].copy()
    init_cash = prices[0] * 11

    actions = func(df_train)
    R_series, R_single_series = make_return_series(prices, actions, init_cash, fee=0)
    plot_result(prices, actions, R_series, R_single_series, init_cash=init_cash,
                need_actions=need_actions)


def single_trade_backtest(name: str, func, need_actions=False):
    df = get_prices(name)

    df_train = df.copy()
    prices = df_train["close"].copy()
    init_cash = prices[0]

    actions = func(df_train)
    R_series, R_single_series = make_return_series(prices, actions, init_cash, fee=0)
    plot_result(prices, actions, R_series, R_single_series, init_cash=init_cash,
                need_actions=need_actions)


def strategy_to_sharpe(name: str, func):
    fee = 0.002
    df = get_prices(name)

    df_train = df.copy()
    prices = df_train["close"].copy()
    init_cash = prices[0]

    actions = func(df_train)
    R_series, R_single_series = make_return_series(prices, actions, init_cash, fee)
    return get_sharpe_from_minute(R_series.diff())


if __name__ == "__main__":
    from strategy import low_close_rolling60_strategy as strategy
    NAME = "data/btc3lusdt_2021_04_13_08_43_03.pkl"
    multi_trade_backtest(NAME, strategy, need_actions=True)
