"""make.fun btc-race-24h trading bot.
Dip-buy mean-reversion strategy on CBBTC/USDC minute bars.
"""

import os
import sys

sys.path.insert(0, os.path.join(os.path.dirname(os.path.abspath(__file__)), "vendor"))
import makefun_bars

DIP = 0.012
TP = 0.012
SL = 0.008
TRAIL = 0.01
BOUNCE = 0.005
LOOKBACK = 420
SMA_WIN = 90
RET_WIN = 60
CAP = 0.05
MAX_HOLD = 480
COOLDOWN = 10
MAX_TRIPS = 8
FALLBACK_BAR = 1260


class DipBuyStrategy:
    def __init__(self):
        self.closes = []
        self.entry_seq = -1
        self.peak_mark = 0
        self.last_exit_seq = None
        self.completed_round_trips = 0
        self.prev_had_position = False
        self.buy_sent = False

    def on_batch(self, state, batch):
        is_holding = "CBBTC" in state.positions
        if not is_holding and self.prev_had_position:
            self.completed_round_trips += 1
            self.last_exit_seq = state.seq
        self.prev_had_position = is_holding

        close = state.close("CBBTC")
        if close is not None:
            self.closes.append(close)

        if state.warming_up or state.seq >= 1439 or close is None:
            return []

        prev_close = self.closes[-2] if len(self.closes) >= 2 else None
        high420 = max(self.closes[-LOOKBACK:]) if len(self.closes) >= LOOKBACK else None
        low420 = min(self.closes[-LOOKBACK:]) if len(self.closes) >= LOOKBACK else None
        sma90 = (sum(self.closes[-SMA_WIN:]) / float(SMA_WIN)) if len(self.closes) >= SMA_WIN else None
        ret60 = (
            (close - self.closes[-(RET_WIN + 1)]) / float(self.closes[-(RET_WIN + 1)])
            if len(self.closes) >= RET_WIN + 1
            else None
        )
        # EXIT (only when holding)
        if is_holding:
            holding = state.positions["CBBTC"]
            mark = state.value("CBBTC", holding.qty)
            cost = holding.cost
            self.peak_mark = max(self.peak_mark, mark)

            take_profit = mark >= cost * (1.0 + TP)
            stop_loss = mark <= cost * (1.0 - SL)
            trailing_stop = mark <= self.peak_mark * (1.0 - TRAIL)
            max_hold = (state.seq - self.entry_seq) >= MAX_HOLD

            if take_profit or stop_loss or trailing_stop or max_hold:
                return [
                    {
                        "side": "sell",
                        "symbol": "CBBTC",
                        "qty": holding.qty,
                        "max_slippage_bps": 100,
                    }
                ]
            return []

        # ENTRY condition
        can_enter = (
            len(self.closes) >= LOOKBACK
            and high420 is not None
            and ((high420 - close) / float(high420)) >= DIP
            and prev_close is not None
            and close > prev_close
            and sma90 is not None
            and close >= sma90
            and ret60 is not None
            and ret60 > -CAP
            and (self.last_exit_seq is None or (state.seq - self.last_exit_seq) >= COOLDOWN)
            and self.completed_round_trips < MAX_TRIPS
            and low420 is not None
            and close >= low420 * (1.0 + BOUNCE)
        )
        if can_enter:
            self.entry_seq = state.seq
            self.peak_mark = 0
            self.buy_sent = True
            return [
                {
                    "side": "buy",
                    "symbol": "CBBTC",
                    "notional_quote_units": state.cash,
                    "max_slippage_bps": 100,
                }
            ]

        # FALLBACK: if no buy has ever been sent AND state.seq >= FALLBACK_BAR
        if not self.buy_sent and state.seq >= FALLBACK_BAR:
            self.entry_seq = state.seq
            self.peak_mark = 0
            self.buy_sent = True
            return [
                {
                    "side": "buy",
                    "symbol": "CBBTC",
                    "notional_quote_units": state.cash // 2,
                    "max_slippage_bps": 100,
                }
            ]

        return []


if __name__ == "__main__":
    bot = DipBuyStrategy()
    makefun_bars.run(bot.on_batch)

