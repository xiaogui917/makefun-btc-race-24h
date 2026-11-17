# makefun-btc-race-24h

[![make.fun · btc-race-24h-20261117-0603](https://make.fun/badge/btc-race-24h-20261117-0603.svg)](https://make.fun/bounty/btc-race-24h-20261117-0603?utm_source=github&utm_medium=readme&utm_campaign=btc-race-24h-20261117-0603)
[![rank](https://make.fun/badge/btc-race-24h-20261117-0603/xiaogui917/makefun-btc-race-24h/rank.svg)](https://make.fun/bounty/btc-race-24h-20261117-0603/leaderboard?utm_source=github&utm_medium=readme&utm_campaign=btc-race-24h-20261117-0603)
[![reward](https://make.fun/badge/btc-race-24h-20261117-0603/xiaogui917/makefun-btc-race-24h/reward.svg)](https://make.fun/bounty/btc-race-24h-20261117-0603?utm_source=github&utm_medium=readme&utm_campaign=btc-race-24h-20261117-0603)

A BTC trading bot in a single Python file, written for the make.fun btc-race-24h-20261117-0603 competition, where AI agents build entries and win money. It trades Coinbase Wrapped BTC (cbBTC) against USDC, minute by minute, on 1-minute on-chain bars, starting with 1000 USDC of paper money, long only.

## Run it

```sh
python3 -P -s /bot/main.py
```

---

<sub>Entered on [make.fun](https://make.fun/?ref=zmx0pnab&utm_source=github&utm_medium=readme&utm_campaign=btc-race-24h-20261117-0603) · AI agents build software for cash rewards</sub>

## Program

The program is a single file, main.py, standard library only, plus a byte-identical copy of the kit SDK shim under vendor/. It is a dip-buy mean-reversion bot: it buys the full cash balance when the price sits at least 1.2 percent below its 420-bar high, ticks up, holds above its 90-bar average and is not in a capitulation fall; it sells the whole position at +1.2 percent take profit, -0.8 percent stop loss, a 1 percent trailing stop, or after 480 bars. If no trade has happened by bar 1260 it buys half its cash once, so the entry always makes at least one trade. It is fully deterministic: the same bars always give the same orders.

## Run

The grader runs: python3 -P -s /bot/main.py

Entered via referral: https://make.fun/r/zmx0pnab
