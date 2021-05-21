#!/usr/bin/env python
#
# Solver for Hearthstone Barrens Mystery "Hunter Puzzle"
# MIT License
# Copyright (c) 2021 Laszlo Makk
#
# Greedy approach.
# Look ahead k steps (depth=k), choose next step towards best state seen.

import sys
import time
from typing import Tuple, Sequence, Type, Optional

import hsutil
from hsutil import ALL_GOOD_TRADES
from hsutil import BOTTOM_LINE_TRADES
from hsutil import GameState
from hsutil import Trade

SCORING_HEURISTIC = 1
LOOKAHEAD_DEPTH = 15

if SCORING_HEURISTIC == 1:
    def score_gamestate(gs: GameState) -> Sequence[int]:
        num_bottomtradesdone = bin(gs.bottomlinetrades_done)[2:].count("1")
        return num_bottomtradesdone, gs.cur_inventory_goldvalue
elif SCORING_HEURISTIC == 2:
    def score_gamestate(gs: GameState) -> Sequence[int]:
        bltrades_done = hsutil.list_enabled_bits(gs.bottomlinetrades_done)
        positive_bltrades_done = [
            idx for idx in bltrades_done
            if BOTTOM_LINE_TRADES[idx].delta_balance() > 0]
        return len(positive_bltrades_done), len(bltrades_done), gs.cur_inventory_goldvalue
elif SCORING_HEURISTIC == 3:
    def score_gamestate(gs: GameState) -> Sequence[int]:
        bltrades_done = hsutil.list_enabled_bits(gs.bottomlinetrades_done)
        total_gold_collected = sum([
            BOTTOM_LINE_TRADES[idx].delta_balance() for idx in bltrades_done
            if BOTTOM_LINE_TRADES[idx].delta_balance() > 0])
        return total_gold_collected, len(bltrades_done), gs.cur_inventory_goldvalue, -gs.get_cur_inventory_num_itemtypes_excl_gold()
elif SCORING_HEURISTIC == 4:
    def score_gamestate(gs: GameState) -> Sequence[int]:
        num_bottomtradesdone = bin(gs.bottomlinetrades_done)[2:].count("1")
        return num_bottomtradesdone, -gs.get_cur_inventory_num_itemtypes_excl_gold(), gs.cur_inventory_goldvalue


if __name__ == '__main__':
    # main code starts.
    print(f"=====")
    print(f">>> main code starts...")
    gs = GameState()
    time_start = time.monotonic()

    # XXXXX testing
    # gs.do_trade(hsutil.TradeTop61)

    while not gs.is_complete():
        print(f"-----")
        print(f"OUTER LOOP iter. ({LOOKAHEAD_DEPTH=}, {SCORING_HEURISTIC=})")
        print(f"- history({len(gs.history)}) state: {gs.dump_history_trade_idx_ints()}")
        if gs.history:
            print(f"- last trade: {gs.history[-1]}")
        print(f"Time taken: {time.monotonic() - time_start:.3f} seconds.")
        greedy_steps_done = len(gs.history)
        best_score = (0, )  # type: Sequence[int]
        best_trade = None  # type: Optional[Type[Trade]]
        trade_idx = 0  # next action to try
        while not gs.is_complete():
            # print(f"INNER LOOP iter.")
            # print(f"- history state: {gs.dump_history_trade_idx_ints()}")
            if len(gs.history) == greedy_steps_done + LOOKAHEAD_DEPTH:
                score = score_gamestate(gs)
                if score > best_score:
                    best_score = score
                    best_trade = gs.history[greedy_steps_done][0]
                trade_idx = gs.undo_last_trade() + 1
            for trade in ALL_GOOD_TRADES[trade_idx:]:
                if gs.do_trade(trade):
                    trade_idx = 0
                    break
            else:
                if len(gs.history) == greedy_steps_done:
                    break
                trade_idx = gs.undo_last_trade() + 1

        if gs.is_complete():
            break
        assert len(gs.history) == greedy_steps_done
        if best_trade is None:
            raise Exception("no solution")
        gs.do_trade(best_trade)

    print(f"=====")
    gs.print_diagnostic_data()
    print(f"DONE!")
    print(f"Total time taken: {time.monotonic()-time_start:.3f} seconds.")
    gs.print_readable_history()
