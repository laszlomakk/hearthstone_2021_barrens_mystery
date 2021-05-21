# Solving the Hearthstone Barrens Mystery "Hunter Puzzle" (2021)

```
Language: Python >= 3.8
License: MIT
Author: Laszlo MAKK
```

This repository contains multiple scripts trying to find a solution to the
"Hunter Puzzle" ("The Bazaar") that was released as part of the Barrens Mystery update (May 2021)
to Hearthstone (card game by Blizzard).

## Problem statement (puzzle description)

- The player has an inventory that can hold items.
- We start with `10xGOLD` (and we will consider `GOLD` too as an item).
- There are seven merchants/vendors offering trades (e.g. selling `1xHEALING_POTION` for `2xGOLD`,
  or selling `1xGOLDEN_GOBLET` for `5xHAND_AXE`). Each merchant has seven different trade options.
- There are seven adventurers offering trades (e.g. buying `6xHAND_AXE` for `10xGOLD`).
  Each adventurer has five different trade options.
  All of these trades offer `GOLD` for (some pieces of) a non-GOLD item.
- Trades with merchants can be repeated arbitrarily many times, however trades with adventurers
  can only be executed a single time.
- Trades cannot be executed partially.
  (e.g. if adventurer wants to buy `8xPOTION_OF_NIGHT` for `240xGOLD`;
  we CANNOT sell `4xPOTION_OF_NIGHT` for `120xGOLD`)
- Each trade offers a certain number of one type of item for a certain number of another type of item.
- The trades can be done in any order: any of the (7x7=)49 merchant trades, and any of the
  not-yet-executed (7x5=)35 adventurer trades can be done at any time, as long as the
  player inventory contains the required items for that trade.
- Merchants only offer "max-buys". E.g. if they sell `1xHEALING_POTION` for `2xGOLD`, and the
  player has `9xGOLD` in their inventory; executing the trade leads to having `4xHEALING_POTION`
  and `1xGOLD`. This rule is not applicable to adventurers as their trades can only be executed once.
- The goal of the puzzle is to execute all 35 trades offered by the adventurers.

See `screenshots/` for the list of trades offered.
(Merchants are in the top line, and adventurers are in the bottom line.)

## Motivation

There is a "community solution" circulating online (`docs/fiufa_solution_found_online.pdf`).
However, that is just a list of trades to execute; without any explanation.

Here, we demonstrate how to solve the puzzle from scratch.

## Solution

### Observations made to help the solver

- Observation 1 (conjecture): "10 items max"
  
  the player inventory cannot contain more than 10 different items at any given time.
  (and `GOLD` counts as an item too)
  - this is because the items are cards from the point of view of the Hearthstone game engine,
    and the player usually cannot have more than 10 cards
    
- Observation 2: "the optimal item-crafting graph is a tree"
  
  - As adventurers only give us gold, and we start with only having gold, the only way to get items
    is to trade with merchants. To obtain certain items, we often need to execute multiple trades.
    Consider this "item-crafting graph". This graph has 27 nodes (`GOLD` and 26 other items), and
    49 edges (trades offered by merchants).
  - Note that all items can be assigned a gold value.
    - e.g. there are two ways to buy ("craft") a `GOLDEN_GOBLET`: 
      - (`2xGOLD` -> `1xHEALING_POTION`), (`4xHEALING_POTION` -> `GOLDEN_GOBLET`), spending 8 gold
      - (`2xGOLD` -> `1xHAND_AXE`), (`5xHAND_AXE` -> `GOLDEN_GOBLET`), spending 10 gold
      
      We assign a value of 8 gold (the minimum) to a `GOLDEN_GOBLET`, and refer to the
      corresponding sequence of trades to craft the item for the cheapest cost as
      the optimal trade-sequence.
  - Note that there is never a tie of optimal trade-sequences. That is, even if there are
    multiple ways to craft an item, there is only ever a single trade-sequence that can craft it
    for its gold value.
  - If we prune the "item-crafting graph" by removing the edges (trades) that are not part of
    any optimal trade-sequence, we get a tree. The item-crafting tree has 27 nodes and 26 edges.
  - Just like we assigned gold values to items, we can assign "balance deltas" to trades.
    The value of the player inventory is the sum of gold values of items in the inventory.
    The balance delta of a trade is the change of inventory-value after executing the trade.
  - The balance delta of each of the 26 trades/edges of the item-crafting tree are zero,
    while the balance delta of the other 23 edges of the original graph are negative.
    Due to the way we defined the gold value of items, there is no merchant-trade where
    the balance delta is positive.
    
- Observation 3: "the adventurer-trades sum to zero"
  
  - The goal of the puzzle is to execute each of the 35 adventurer-trades.
  - Note that some of these trades have negative balance deltas, some are neutral,
    and some are positive.
  - Note that the sum of the balance-deltas of all 35 adventurer-trades is zero.
- Observation 4 (conjecture): "we can prune the negative balance delta merchant-trades"
  - We start out with 10 gold. The sum of all adventurer-trades is zero.
  - There are no positive balance delta merchant-trades, only neutral and negative ones.
  - This means that after executing (the full trade sequence that makes up) any
    potential solution, the player inventory value cannot be greater than 10 gold.
  - When looking for a solution, we make the assumption that we never need to execute
    negative balance delta merchant-trades, i.e. the final inventory value will be
    exactly 10 gold.
  - This assumption greatly simplifies the search space, however it might exclude otherwise
    valid solutions.
  - This means that for any given item, there is a single sequence of trades to craft that item.
    This optimal trade-sequence is how we "craft" an item.
    
- Observation 5 (conjecture): "we know the ever-crafted-count for each item"
  
  - By summing up the items required for all adventurer-trades, and considering how to craft them,
    we can count how many of each item we will ever need.
  - We will not explore game states where for any item the ever-crafted-count is higher.
  - Note that this uses another simplifying assumption that not only will we have an inventory value
    of 10 gold at the end of a solution, but we will have exactly `10xGOLD` (as opposed to other items
    making up the value). Due to the "max buy" rule, there could be solutions where
    this is not the case, and e.g. we finish with `8xGOLD`+`1xHEALING_POTION`.
  - It would be easy to remove this assumption if the program execution resulted in "no solution",
    however we try with it first as it is an easy speedup.
    
- Observation 6: "keep track of max capital requirements for unexecuted trades"
  
  - At a given game state, consider the sum of the not-yet-executed positive balance delta
    adventurer-trades. This, summed with our current inventory-value, gives an upper bound
    of the max inventory-value we can still achieve during that game.
  - Now note that adventurer-trades have "capital requirements": the gold value of items
    needed for the trade.
  - For any game state (that is part of a solution) the following must hold:
    
    `(max inventory-value we can still achieve) >= (max capital req of not-yet-executed adventurer-trades)`

- Observation 7 (conjecture): "craft-items-needed for adventurer-trade, do trade; atomically"
  
  - It would greatly reduce the search-space to only consider adventurer-trades,
    that is, craft the items needed for an adventurer-trade and then execute the trade, atomically.
  - So we do not want to e.g. craft some items for adventurer-trade1,
    craft some items for adventurer-trade2, then execute adventurer-trade2,
    then execute adventurer-trade1.
  - This assumption immensely simplifies the problem, but it might exclude many potential solutions.
  - Still, note that due to the "max buy" rule, when crafting the items for and executing
    an adventurer-trade, often we will inadvertently also craft some items
    needed for other adventurer-trades.
  - (Note that the community solution (`docs/fiufa_solution_found_online.pdf`)
    violates this simplifying assumption.)

### Algorithms

We try to model the problem as a graph search.
Each node of the graph is a game state, and each edge is a state transition.

- `script1.py` is a depth-first search.
  - Each edge is a single trade, either a merchant-trade or an adventurer-trade.
  - Observations 1-6 are used.
  - This is too slow. After 50+ CPU hours, the program did not finish executing.
- `script2.py` is a greedy approach.
  - Each edge/step is a single trade, either a merchant-trade or an adventurer-trade.
  - It looks ahead k steps (depth=k), evaluates the states seen using some heuristics,
    and then greedily chooses the (single) next step towards the best state seen.
  - Multiple different (combination of) heuristics are tried, such as
    - maximising the number of adventurer-trades done,
    - maximising the inventory-value,
    - minimising the number of item-types in the inventory
  - Observations 1-6 are used.
  - With a lookahead of > ~20, this was too slow, and with a lookahead of < ~20,
    the program terminated with "no solution".
- `script3.py` is a depth-first search.
  - Each edge is a full craft-sequence required for, and including, an adventurer-trade
    (i.e. using observation 7)
  - Observations 1-7 are used.
  - This program manages to find a solution and terminate in ~12 minutes.

Solution found by `script3.py`:
```
- history state: [38, 20, 53, 44, 36, 15, 53, 44, 10, 53, 44, 42, 5, 41, 0, 41, 54, 1, 38, 45, 26, 57, 6, 38, 58, 31, 38, 58, 40, 51, 21, 53, 50, 2, 35, 39, 27, 48, 32, 43, 56, 17, 41, 54, 7, 35, 39, 47, 23, 53, 44, 42, 14, 35, 39, 47, 55, 29, 53, 44, 42, 37, 34, 57, 46, 9, 35, 39, 52, 4, 53, 59, 24, 53, 50, 13, 48, 3, 38, 58, 40, 19, 38, 45, 33, 43, 22, 38, 45, 60, 18, 43, 56, 8, 35, 39, 47, 28, 43, 16, 53, 44, 42, 37, 12, 53, 25, 41, 49, 11, 35, 30]
- invvalue-changes: [0, 3, 0, 0, 0, 5, 0, 0, 4, 0, 0, 0, 3, 0, -2, 0, 0, 2, 0, 0, 1, 0, 5, 0, 0, 1, 0, 0, 0, 0, 42, 0, 0, 0, 0, 0, 9, 0, 20, 0, 0, 6, 0, 0, 40, 0, 0, 0, 5, 0, 0, 0, 31, 0, 0, 0, 0, 12, 0, 0, 0, 0, 24, 0, 0, 32, 0, 0, 0, -35, 0, 0, -23, 0, 0, -30, 0, -12, 0, 0, 0, -15, 0, 0, -24, 0, 6, 0, 0, 0, 18, 0, 0, -40, 0, 0, 0, -26, 0, -24, 0, 0, 0, 0, -15, 0, -15, 0, 0, -2, 0, -6]
- len(self.history)=112. inventory(1)={<Item.GOLD: 1>: 10}
- self.cur_inventory_goldvalue=10. self.sum_of_rem_balancepositive_trades=0. self.max_rem_outval_trade=-inf
- bottom trades bitmap: 0b11111111111111111111111111111111111
- bottom trades done: ['TradeBottom5ID(get 6xGOLD for 3xIRON_DAGGER)', 'TradeBottom4JL(get 11xGOLD for 1xJADE_LOCKET)', 'TradeBottom3LB(get 13xGOLD for 3xLINEN_BANDAGE)', 'TradeBottom2CD(get 18xGOLD for 1xCUTE_DOLL)', 'TradeBottom1HA(get 10xGOLD for 6xHAND_AXE)', 'TradeBottom1GFP(get 18xGOLD for 2xGOBLIN_FISHING_POLE)', 'TradeBottom6GS(get 25xGOLD for 2xGNOMISH_SHIELD)', 'TradeBottom2SC(get 25xGOLD for 10xSTORMWIND_CHEDDAR)', 'TradeBottom7LPW(get 22xGOLD for 3xLOYAL_PET_WHISTLE)', 'TradeBottom5GD(get 70xGOLD for 1xGILNEAN_DAGGER)', 'TradeBottom1AC(get 60xGOLD for 1xANGRY_CRYSTAL)', 'TradeBottom6GG(get 65xGOLD for 7xGOLDEN_GOBLET)', 'TradeBottom7AS(get 70xGOLD for 2xARCANE_SCROLL)', 'TradeBottom4RC(get 72xGOLD for 2xRUBY_CROWN)', 'TradeBottom2GFP(get 120xGOLD for 10xGOBLIN_FISHING_POLE)', 'TradeBottom5AM(get 125xGOLD for 5xALLIANCE_MACE)', 'TradeBottom3CD(get 166xGOLD for 9xCUTE_DOLL)', 'TradeBottom6EC(get 180xGOLD for 7xEVERBURNING_CANDLE)', 'TradeBottom7DOA(get 204xGOLD for 4xDRAUGHT_OF_ANGELS)', 'TradeBottom2PON(get 240xGOLD for 8xPOTION_OF_NIGHT)', 'TradeBottom1SOW(get 205xGOLD for 3xSPHERE_OF_WISDOM)', 'TradeBottom5SG(get 166xGOLD for 7xSHADOWY_GEM)', 'TradeBottom3AC(get 150xGOLD for 3xANGRY_CRYSTAL)', 'TradeBottom1AS(get 138xGOLD for 6xARCANE_SCROLL)', 'TradeBottom4SW(get 125xGOLD for 10xSAPPHIRE_WAND)', 'TradeBottom7GS(get 60xGOLD for 7xGNOMISH_SHIELD)', 'TradeBottom5CP(get 50xGOLD for 4xCAPTIVATING_PIPES)', 'TradeBottom4TA(get 114xGOLD for 2xTIGER_AMULET)', 'TradeBottom2RC(get 92xGOLD for 4xRUBY_CROWN)', 'TradeBottom6AM(get 70xGOLD for 4xALLIANCE_MACE)', 'TradeBottom4CP(get 42xGOLD for 6xCAPTIVATING_PIPES)', 'TradeBottom3DOA(get 30xGOLD for 1xDRAUGHT_OF_ANGELS)', 'TradeBottom6EOV(get 15xGOLD for 10xELIXIR_OF_VIGOR)', 'TradeBottom3VNH(get 14xGOLD for 4xVERY_NICE_HAT)', 'TradeBottom7HP(get 10xGOLD for 8xHEALING_POTION)']
DONE!
Total time taken: 709.484 seconds.
idx=0. action=(<TradeTop21(get 1xIRON_DAGGER for 1xGOLD)>, 10).
idx=1. action=(<TradeBottom5ID(get 6xGOLD for 3xIRON_DAGGER)>, 1).
idx=2. action=(<TradeTop61(get 1xELIXIR_OF_VIGOR for 3xGOLD)>, 2).
idx=3. action=(<TradeTop42(get 1xLINEN_BANDAGE for 1xELIXIR_OF_VIGOR)>, 2).
idx=4. action=(<TradeTop13(get 1xJADE_LOCKET for 2xLINEN_BANDAGE)>, 1).
idx=5. action=(<TradeBottom4JL(get 11xGOLD for 1xJADE_LOCKET)>, 1).
idx=6. action=(<TradeTop61(get 1xELIXIR_OF_VIGOR for 3xGOLD)>, 3).
idx=7. action=(<TradeTop42(get 1xLINEN_BANDAGE for 1xELIXIR_OF_VIGOR)>, 3).
idx=8. action=(<TradeBottom3LB(get 13xGOLD for 3xLINEN_BANDAGE)>, 1).
idx=9. action=(<TradeTop61(get 1xELIXIR_OF_VIGOR for 3xGOLD)>, 5).
idx=10. action=(<TradeTop42(get 1xLINEN_BANDAGE for 1xELIXIR_OF_VIGOR)>, 5).
idx=11. action=(<TradeTop32(get 1xCUTE_DOLL for 5xLINEN_BANDAGE)>, 1).
idx=12. action=(<TradeBottom2CD(get 18xGOLD for 1xCUTE_DOLL)>, 1).
idx=13. action=(<TradeTop31(get 1xHAND_AXE for 2xGOLD)>, 9).
idx=14. action=(<TradeBottom1HA(get 10xGOLD for 6xHAND_AXE)>, 1).
idx=15. action=(<TradeTop31(get 1xHAND_AXE for 2xGOLD)>, 5).
idx=16. action=(<TradeTop62(get 1xGOBLIN_FISHING_POLE for 4xHAND_AXE)>, 2).
idx=17. action=(<TradeBottom1GFP(get 18xGOLD for 2xGOBLIN_FISHING_POLE)>, 1).
idx=18. action=(<TradeTop21(get 1xIRON_DAGGER for 1xGOLD)>, 18).
idx=19. action=(<TradeTop44(get 1xGNOMISH_SHIELD for 12xIRON_DAGGER)>, 2).
idx=20. action=(<TradeBottom6GS(get 25xGOLD for 2xGNOMISH_SHIELD)>, 1).
idx=21. action=(<TradeTop71(get 1xSTORMWIND_CHEDDAR for 2xGOLD)>, 12).
idx=22. action=(<TradeBottom2SC(get 25xGOLD for 10xSTORMWIND_CHEDDAR)>, 1).
idx=23. action=(<TradeTop21(get 1xIRON_DAGGER for 1xGOLD)>, 26).
idx=24. action=(<TradeTop73(get 1xLOYAL_PET_WHISTLE for 7xIRON_DAGGER)>, 3).
idx=25. action=(<TradeBottom7LPW(get 22xGOLD for 3xLOYAL_PET_WHISTLE)>, 1).
idx=26. action=(<TradeTop21(get 1xIRON_DAGGER for 1xGOLD)>, 22).
idx=27. action=(<TradeTop73(get 1xLOYAL_PET_WHISTLE for 7xIRON_DAGGER)>, 4).
idx=28. action=(<TradeTop27(get 1xSAPPHIRE_WAND for 2xLOYAL_PET_WHISTLE)>, 2).
idx=29. action=(<TradeTop55(get 1xGILNEAN_DAGGER for 2xSAPPHIRE_WAND)>, 1).
idx=30. action=(<TradeBottom5GD(get 70xGOLD for 1xGILNEAN_DAGGER)>, 1).
idx=31. action=(<TradeTop61(get 1xELIXIR_OF_VIGOR for 3xGOLD)>, 23).
idx=32. action=(<TradeTop54(get 1xANGRY_CRYSTAL for 20xELIXIR_OF_VIGOR)>, 1).
idx=33. action=(<TradeBottom1AC(get 60xGOLD for 1xANGRY_CRYSTAL)>, 1).
idx=34. action=(<TradeTop11(get 1xHEALING_POTION for 2xGOLD)>, 30).
idx=35. action=(<TradeTop23(get 1xGOLDEN_GOBLET for 4xHEALING_POTION)>, 7).
idx=36. action=(<TradeBottom6GG(get 65xGOLD for 7xGOLDEN_GOBLET)>, 1).
idx=37. action=(<TradeTop51(get 1xARCANE_SCROLL for 25xGOLD)>, 2).
idx=38. action=(<TradeBottom7AS(get 70xGOLD for 2xARCANE_SCROLL)>, 1).
idx=39. action=(<TradeTop41(get 1xCAPTIVATING_PIPES for 11xGOLD)>, 7).
idx=40. action=(<TradeTop66(get 1xRUBY_CROWN for 3xCAPTIVATING_PIPES)>, 2).
idx=41. action=(<TradeBottom4RC(get 72xGOLD for 2xRUBY_CROWN)>, 1).
idx=42. action=(<TradeTop31(get 1xHAND_AXE for 2xGOLD)>, 40).
idx=43. action=(<TradeTop62(get 1xGOBLIN_FISHING_POLE for 4xHAND_AXE)>, 10).
idx=44. action=(<TradeBottom2GFP(get 120xGOLD for 10xGOBLIN_FISHING_POLE)>, 1).
idx=45. action=(<TradeTop11(get 1xHEALING_POTION for 2xGOLD)>, 60).
idx=46. action=(<TradeTop23(get 1xGOLDEN_GOBLET for 4xHEALING_POTION)>, 15).
idx=47. action=(<TradeTop47(get 1xALLIANCE_MACE for 3xGOLDEN_GOBLET)>, 5).
idx=48. action=(<TradeBottom5AM(get 125xGOLD for 5xALLIANCE_MACE)>, 1).
idx=49. action=(<TradeTop61(get 1xELIXIR_OF_VIGOR for 3xGOLD)>, 42).
idx=50. action=(<TradeTop42(get 1xLINEN_BANDAGE for 1xELIXIR_OF_VIGOR)>, 45).
idx=51. action=(<TradeTop32(get 1xCUTE_DOLL for 5xLINEN_BANDAGE)>, 9).
idx=52. action=(<TradeBottom3CD(get 166xGOLD for 9xCUTE_DOLL)>, 1).
idx=53. action=(<TradeTop11(get 1xHEALING_POTION for 2xGOLD)>, 83).
idx=54. action=(<TradeTop23(get 1xGOLDEN_GOBLET for 4xHEALING_POTION)>, 21).
idx=55. action=(<TradeTop47(get 1xALLIANCE_MACE for 3xGOLDEN_GOBLET)>, 7).
idx=56. action=(<TradeTop64(get 1xEVERBURNING_CANDLE for 1xALLIANCE_MACE)>, 7).
idx=57. action=(<TradeBottom6EC(get 180xGOLD for 7xEVERBURNING_CANDLE)>, 1).
idx=58. action=(<TradeTop61(get 1xELIXIR_OF_VIGOR for 3xGOLD)>, 60).
idx=59. action=(<TradeTop42(get 1xLINEN_BANDAGE for 1xELIXIR_OF_VIGOR)>, 60).
idx=60. action=(<TradeTop32(get 1xCUTE_DOLL for 5xLINEN_BANDAGE)>, 12).
idx=61. action=(<TradeTop15(get 1xDRAUGHT_OF_ANGELS for 3xCUTE_DOLL)>, 4).
idx=62. action=(<TradeBottom7DOA(get 204xGOLD for 4xDRAUGHT_OF_ANGELS)>, 1).
idx=63. action=(<TradeTop71(get 1xSTORMWIND_CHEDDAR for 2xGOLD)>, 102).
idx=64. action=(<TradeTop45(get 1xPOTION_OF_NIGHT for 13xSTORMWIND_CHEDDAR)>, 8).
idx=65. action=(<TradeBottom2PON(get 240xGOLD for 8xPOTION_OF_NIGHT)>, 1).
idx=66. action=(<TradeTop11(get 1xHEALING_POTION for 2xGOLD)>, 120).
idx=67. action=(<TradeTop23(get 1xGOLDEN_GOBLET for 4xHEALING_POTION)>, 30).
idx=68. action=(<TradeTop56(get 1xSPHERE_OF_WISDOM for 10xGOLDEN_GOBLET)>, 3).
idx=69. action=(<TradeBottom1SOW(get 205xGOLD for 3xSPHERE_OF_WISDOM)>, 1).
idx=70. action=(<TradeTop61(get 1xELIXIR_OF_VIGOR for 3xGOLD)>, 68).
idx=71. action=(<TradeTop74(get 1xSHADOWY_GEM for 9xELIXIR_OF_VIGOR)>, 7).
idx=72. action=(<TradeBottom5SG(get 166xGOLD for 7xSHADOWY_GEM)>, 1).
idx=73. action=(<TradeTop61(get 1xELIXIR_OF_VIGOR for 3xGOLD)>, 55).
idx=74. action=(<TradeTop54(get 1xANGRY_CRYSTAL for 20xELIXIR_OF_VIGOR)>, 3).
idx=75. action=(<TradeBottom3AC(get 150xGOLD for 3xANGRY_CRYSTAL)>, 1).
idx=76. action=(<TradeTop51(get 1xARCANE_SCROLL for 25xGOLD)>, 6).
idx=77. action=(<TradeBottom1AS(get 138xGOLD for 6xARCANE_SCROLL)>, 1).
idx=78. action=(<TradeTop21(get 1xIRON_DAGGER for 1xGOLD)>, 140).
idx=79. action=(<TradeTop73(get 1xLOYAL_PET_WHISTLE for 7xIRON_DAGGER)>, 20).
idx=80. action=(<TradeTop27(get 1xSAPPHIRE_WAND for 2xLOYAL_PET_WHISTLE)>, 10).
idx=81. action=(<TradeBottom4SW(get 125xGOLD for 10xSAPPHIRE_WAND)>, 1).
idx=82. action=(<TradeTop21(get 1xIRON_DAGGER for 1xGOLD)>, 125).
idx=83. action=(<TradeTop44(get 1xGNOMISH_SHIELD for 12xIRON_DAGGER)>, 10).
idx=84. action=(<TradeBottom7GS(get 60xGOLD for 7xGNOMISH_SHIELD)>, 1).
idx=85. action=(<TradeTop41(get 1xCAPTIVATING_PIPES for 11xGOLD)>, 5).
idx=86. action=(<TradeBottom5CP(get 50xGOLD for 4xCAPTIVATING_PIPES)>, 1).
idx=87. action=(<TradeTop21(get 1xIRON_DAGGER for 1xGOLD)>, 55).
idx=88. action=(<TradeTop44(get 1xGNOMISH_SHIELD for 12xIRON_DAGGER)>, 5).
idx=89. action=(<TradeTop76(get 1xTIGER_AMULET for 4xGNOMISH_SHIELD)>, 2).
idx=90. action=(<TradeBottom4TA(get 114xGOLD for 2xTIGER_AMULET)>, 1).
idx=91. action=(<TradeTop41(get 1xCAPTIVATING_PIPES for 11xGOLD)>, 10).
idx=92. action=(<TradeTop66(get 1xRUBY_CROWN for 3xCAPTIVATING_PIPES)>, 4).
idx=93. action=(<TradeBottom2RC(get 92xGOLD for 4xRUBY_CROWN)>, 1).
idx=94. action=(<TradeTop11(get 1xHEALING_POTION for 2xGOLD)>, 48).
idx=95. action=(<TradeTop23(get 1xGOLDEN_GOBLET for 4xHEALING_POTION)>, 12).
idx=96. action=(<TradeTop47(get 1xALLIANCE_MACE for 3xGOLDEN_GOBLET)>, 4).
idx=97. action=(<TradeBottom6AM(get 70xGOLD for 4xALLIANCE_MACE)>, 1).
idx=98. action=(<TradeTop41(get 1xCAPTIVATING_PIPES for 11xGOLD)>, 6).
idx=99. action=(<TradeBottom4CP(get 42xGOLD for 6xCAPTIVATING_PIPES)>, 1).
idx=100. action=(<TradeTop61(get 1xELIXIR_OF_VIGOR for 3xGOLD)>, 15).
idx=101. action=(<TradeTop42(get 1xLINEN_BANDAGE for 1xELIXIR_OF_VIGOR)>, 15).
idx=102. action=(<TradeTop32(get 1xCUTE_DOLL for 5xLINEN_BANDAGE)>, 3).
idx=103. action=(<TradeTop15(get 1xDRAUGHT_OF_ANGELS for 3xCUTE_DOLL)>, 1).
idx=104. action=(<TradeBottom3DOA(get 30xGOLD for 1xDRAUGHT_OF_ANGELS)>, 1).
idx=105. action=(<TradeTop61(get 1xELIXIR_OF_VIGOR for 3xGOLD)>, 10).
idx=106. action=(<TradeBottom6EOV(get 15xGOLD for 10xELIXIR_OF_VIGOR)>, 1).
idx=107. action=(<TradeTop31(get 1xHAND_AXE for 2xGOLD)>, 8).
idx=108. action=(<TradeTop52(get 1xVERY_NICE_HAT for 2xHAND_AXE)>, 4).
idx=109. action=(<TradeBottom3VNH(get 14xGOLD for 4xVERY_NICE_HAT)>, 1).
idx=110. action=(<TradeTop11(get 1xHEALING_POTION for 2xGOLD)>, 7).
idx=111. action=(<TradeBottom7HP(get 10xGOLD for 8xHEALING_POTION)>, 1).
```
