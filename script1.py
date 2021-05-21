#!/usr/bin/env python
#
# Solver for Hearthstone Barrens Mystery "Hunter Puzzle"
# MIT License
# Copyright (c) 2021 Laszlo Makk
#
# Depth-first search
# Each edge is a trade, either top-line or bottom-line.
#
# optimisation ideas
# - idea1: note that these scenarios are identical:
#           - scenario1:
#             <TradeTop32(get 1xCUTE_DOLL for 5xLINEN_BANDAGE)>
#             <TradeBottom2CD(get 18xGOLD for 1xCUTE_DOLL)>
#             <TradeTop21(get 1xIRON_DAGGER for 1xGOLD)>
#           - scenario2:
#             <TradeTop32(get 1xCUTE_DOLL for 5xLINEN_BANDAGE)>
#             <TradeTop21(get 1xIRON_DAGGER for 1xGOLD)>
#             <TradeBottom2CD(get 18xGOLD for 1xCUTE_DOLL)>
#             <TradeTop21(get 1xIRON_DAGGER for 1xGOLD)>
#      - store a set of all states visited
#        - if encountering an already visited state, then cut DFS
#        - a state is: hash((bottomlinetrades_done, inventory))
#          - a 16 byte hash might be long enough... e.g. sha256(x)[:16]

import sys
import time

import hsutil
from hsutil import ALL_GOOD_TRADES
from hsutil import GameState


if __name__ == '__main__':
    # main code starts.
    print(f"=====")
    print(f">>> main code starts...")
    gs = GameState()
    trade_idx = 0  # next action to try
    iter_count = 0
    time_start = time.monotonic()

    # allow specifying where to start searching for first move:
    if len(sys.argv) > 1:
        trade_idx = int(sys.argv[1])

    while not gs.is_complete():
        iter_count += 1
        if iter_count % 100_000 == 0:
            print(f"-----")
            print(f"iters done: {iter_count//1000} k")
            gs.print_diagnostic_data()
            print(f"Time taken: {time.monotonic() - time_start:.3f} seconds.")

        for trade in ALL_GOOD_TRADES[trade_idx:]:
            if gs.do_trade(trade):
                trade_idx = 0
                break
        else:
            trade_idx = gs.undo_last_trade() + 1

    print(f"=====")
    gs.print_diagnostic_data()
    print(f"DONE!")
    print(f"Total time taken: {time.monotonic()-time_start:.3f} seconds.")
    gs.print_readable_history()
