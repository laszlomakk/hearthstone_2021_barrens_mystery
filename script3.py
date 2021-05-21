#!/usr/bin/env python
#
# Solver for Hearthstone Barrens Mystery "Hunter Puzzle"
# MIT License
# Copyright (c) 2021 Laszlo Makk
#
# Depth-first search
# Each edge is a full craft-sequence required for, and including, a bottom-line trade.
# Heuristic: craft sequences for bottom-line trades are atomic.

import sys
import time

import hsutil
from hsutil import BOTTOM_LINE_TRADES
from hsutil import GameState


if __name__ == '__main__':
    # main code starts.
    print(f"=====")
    print(f">>> main code starts...")
    gs = GameState()
    trade_idx = 0  # next action to try
    iter_count = 0
    time_start = time.monotonic()

    while not gs.is_complete():
        iter_count += 1
        if iter_count % 100_000 == 0:
            print(f"-----")
            print(f"iters done: {iter_count//1000} k")
            gs.print_diagnostic_data()
            print(f"Time taken: {time.monotonic() - time_start:.3f} seconds.")

        for trade in BOTTOM_LINE_TRADES[trade_idx:]:
            if gs.chaincraft_bltrade(trade):
                trade_idx = 0
                break
        else:
            trade_idx = gs.undo_last_chaincraft() + 1

    print(f"=====")
    gs.print_diagnostic_data()
    print(f"DONE!")
    print(f"Total time taken: {time.monotonic()-time_start:.3f} seconds.")
    gs.print_readable_history()
