import os
import sys

sys.path.insert(0, os.path.join(os.path.dirname(os.path.abspath(__file__)), "vendor"))
import makefun_bars


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
        # 1. Round trip tracking
        is_holding = "CBBTC" in state.positions
        if not is_holding and self.prev_had_position:
            self.completed_round_trips += 1
            self.last_exit_seq = state.seq
        self.prev_had_position = is_holding

        # 2. Track every CBBTC close (int) in a list, in batch order
        close = state.close("CBBTC")
        if close is not None:
            self.closes.append(close)

        # Never order while warming up or on the last batch
        if state.warming_up or state.seq >= 1439:
            return []

        if close is None:
            return []

        # Derive indicators each batch
        prev_close = self.closes[-2] if len(self.closes) >= 2 else None
        high420 = max(self.closes[-420:]) if len(self.closes) >= 420 else None
        low420 = min(self.closes[-420:]) if len(self.closes) >= 420 else None
        sma90 = (sum(self.closes[-90:]) / 90.0) if len(self.closes) >= 90 else None
        ret60 = (
            (close - self.closes[-61]) / float(self.closes[-61])
            if len(self.closes) >= 61
            else None
        )

        # EXIT (only when holding)
        if is_holding:
            holding = state.positions["CBBTC"]
            mark = state.value("CBBTC", holding.qty)
            cost = holding.cost
            self.peak_mark = max(self.peak_mark, mark)

            take_profit = mark >= cost * 1.012
            stop_loss = mark <= cost * 0.992
            trailing_stop = mark <= self.peak_mark * 0.99
            max_hold = (state.seq - self.entry_seq) >= 480

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

        # ENTRY (only when flat)
        can_enter = (
            len(self.closes) >= 420
            and high420 is not None
            and ((high420 - close) / float(high420)) >= 0.012
            and prev_close is not None
            and close > prev_close
            and sma90 is not None
            and close >= sma90
            and ret60 is not None
            and ret60 > -0.05
            and (self.last_exit_seq is None or (state.seq - self.last_exit_seq) >= 10)
            and self.completed_round_trips < 8
            and low420 is not None
            and close >= low420 * 1.005
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

        # FALLBACK: if no buy has ever been sent AND state.seq >= 1260
        if not self.buy_sent and state.seq >= 1260:
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
