#!/usr/bin/env python
#
# Solver for Hearthstone Barrens Mystery "Hunter Puzzle"
# MIT License
# Copyright (c) 2021 Laszlo Makk
#

import collections
from collections import defaultdict, deque
import enum
from enum import IntEnum
import random
import sys
import time
from typing import Dict, List, Tuple, Set, Type, Sequence, Mapping, Optional


class Item(IntEnum):
    GOLD = enum.auto()
    HEALING_POTION = enum.auto()       # 2g
    GOLDEN_GOBLET = enum.auto()        # (5xHA=10g) (4xHP=8g)
    JADE_LOCKET = enum.auto()          # (2xLB=6g) (4xSC=8g)
    ALLIANCE_MACE = enum.auto()        # (14xSC=28g) (3xGG=24g) (3xCD=45g)
    DRAUGHT_OF_ANGELS = enum.auto()    # (3xCD=45g) (1xAC=60g) (9xGG=72g)
    GILNEAN_DAGGER = enum.auto()       # (2xSG=54g) (49xHP=98g) (2xSW=28g) (1xRC=33g)
    LOYAL_PET_WHISTLE = enum.auto()    # (4xEOV=12g) (7xID=7g)
    IRON_DAGGER = enum.auto()          # 1g
    RUBY_CROWN = enum.auto()           # (22xHA=44g) (3xCP=33g)
    SPHERE_OF_WISDOM = enum.auto()     # (4xPON=104g) (10xGG=80g)
    SHADOWY_GEM = enum.auto()          # (3xGS=36g) (9xEOV=27g)
    SAPPHIRE_WAND = enum.auto()        # (2xLPW=14g) (15xSC=30g) (5xVNH=20g)
    HAND_AXE = enum.auto()             # 2g
    CUTE_DOLL = enum.auto()            # (5xLB=15g)
    ARCANE_SCROLL = enum.auto()        # 25g (8xVNH=32g)
    POTION_OF_NIGHT = enum.auto()      # (5xJL=30g) (13xSC=26g)
    EVERBURNING_CANDLE = enum.auto()   # (4xGFP=32g) (1xAM=24g)
    TIGER_AMULET = enum.auto()         # (5xCP=55g) (3xAS=75g) (4xGS=48g)
    CAPTIVATING_PIPES = enum.auto()    # 11g (7xHP=14g)
    LINEN_BANDAGE = enum.auto()        # (1xEOV=3g)
    GNOMISH_SHIELD = enum.auto()       # (12xID=12g)
    VERY_NICE_HAT = enum.auto()        # (2xHA=4g)
    ANGRY_CRYSTAL = enum.auto()        # (20xEOV=60g) (5xCD=75g)
    ELIXIR_OF_VIGOR = enum.auto()      # 3g
    GOBLIN_FISHING_POLE = enum.auto()  # (4xHA=8g) (5xSC=10g)
    STORMWIND_CHEDDAR = enum.auto()    # 2g

    def goldvalue(self) -> int:
        return GOLDVALUE_OF_ITEM[self]

GOLDVALUE_OF_ITEM = {Item.GOLD: 1, }  # type: Dict[Item, int]
# which trade to use to achieve best value for crafting item:
BESTTRADE_TO_CRAFT_ITEM = {Item.GOLD: None, }  # type: Dict[Item, Optional[Type['TopLineTrade']]]

STARTING_GOLD = 10


class _TradeMeta(type):
    def __str__(self):
        return f"{self.__name__}" \
               f"(get {self.WE_GET_COUNT}x{self.WE_GET_ITEM.name} " \
               f"for {self.THEY_GET_COUNT}x{self.THEY_GET_ITEM.name})"

    def __repr__(self):
        return f"<{str(self)}>"


class Trade(metaclass=_TradeMeta):
    WE_GET_ITEM: Item
    WE_GET_COUNT: int
    THEY_GET_ITEM: Item
    THEY_GET_COUNT: int
    IS_BOTTOM_LINE: bool

    _CACHED_TRADE_BALANCE = None
    @classmethod
    def delta_balance(cls) -> int:
        """Returns the change of inventory-value after executing the trade.
        ret_val > 0 trades are GOOD,
        ret_val == 0 trades are NEUTRAL,
        ret_val < 0 trades are BAD.
        """
        if cls._CACHED_TRADE_BALANCE is None:
            cls._CACHED_TRADE_BALANCE = cls.invalue() - cls.outvalue()
        return cls._CACHED_TRADE_BALANCE

    _CACHED_OUTVALUE = None
    @classmethod
    def outvalue(cls) -> int:
        """Returns the overall value of items needed for the trade.
        This is the value THEY get FROM us.
        ~outflow of value
        ~capital requirements (min inventory-value needed) to make trade
        """
        if cls._CACHED_OUTVALUE is None:
            cls._CACHED_OUTVALUE = cls.THEY_GET_ITEM.goldvalue() * cls.THEY_GET_COUNT
        return cls._CACHED_OUTVALUE

    _CACHED_INVALUE = None
    @classmethod
    def invalue(cls) -> int:
        """Returns the overall value of items WE GET from the trade."""
        if cls._CACHED_INVALUE is None:
            cls._CACHED_INVALUE = cls.WE_GET_ITEM.goldvalue() * cls.WE_GET_COUNT
        return cls._CACHED_INVALUE


class TopLineTrade(Trade):
    """Trades with MERCHANTS/VENDORS.
    These trades can be executed arbitrarily many times.
    Only "max buys" are allowed.
      - E.g. consider trade where we can BUY 1xHEALING_POTION for a cost of 2xGOLD.
        if we had 9xGOLD, after executing the trade we would have 4xHEALING_POTION and 1xGOLD.
        It is not allowed to buy fewer HEALING_POTIONs.
    """
    IS_BOTTOM_LINE = False
    WE_GET_COUNT   = 1

class BottomLineTrade(Trade):
    """Trades with ADVENTURERS.
    Each of these trades can only be executed once.
    The objective/goal of the game is to execute ALL of these trades once.
    Adventurers offer us GOLD for non-GOLD items.
    """
    IS_BOTTOM_LINE = True
    WE_GET_ITEM = Item.GOLD


#########################

class TradeTop11(TopLineTrade):
    WE_GET_ITEM    = Item.HEALING_POTION
    THEY_GET_ITEM  = Item.GOLD
    THEY_GET_COUNT = 2
class TradeTop12(TopLineTrade):
    WE_GET_ITEM    = Item.GOLDEN_GOBLET
    THEY_GET_ITEM  = Item.HAND_AXE
    THEY_GET_COUNT = 5
class TradeTop13(TopLineTrade):
    WE_GET_ITEM    = Item.JADE_LOCKET
    THEY_GET_ITEM  = Item.LINEN_BANDAGE
    THEY_GET_COUNT = 2
class TradeTop14(TopLineTrade):
    WE_GET_ITEM    = Item.ALLIANCE_MACE
    THEY_GET_ITEM  = Item.STORMWIND_CHEDDAR
    THEY_GET_COUNT = 14
class TradeTop15(TopLineTrade):
    WE_GET_ITEM    = Item.DRAUGHT_OF_ANGELS
    THEY_GET_ITEM  = Item.CUTE_DOLL
    THEY_GET_COUNT = 3
class TradeTop16(TopLineTrade):
    WE_GET_ITEM    = Item.GILNEAN_DAGGER
    THEY_GET_ITEM  = Item.SHADOWY_GEM
    THEY_GET_COUNT = 2
class TradeTop17(TopLineTrade):
    WE_GET_ITEM    = Item.LOYAL_PET_WHISTLE
    THEY_GET_ITEM  = Item.ELIXIR_OF_VIGOR
    THEY_GET_COUNT = 4

class TradeTop21(TopLineTrade):
    WE_GET_ITEM    = Item.IRON_DAGGER
    THEY_GET_ITEM  = Item.GOLD
    THEY_GET_COUNT = 1
class TradeTop22(TopLineTrade):
    WE_GET_ITEM    = Item.JADE_LOCKET
    THEY_GET_ITEM  = Item.STORMWIND_CHEDDAR
    THEY_GET_COUNT = 4
class TradeTop23(TopLineTrade):
    WE_GET_ITEM    = Item.GOLDEN_GOBLET
    THEY_GET_ITEM  = Item.HEALING_POTION
    THEY_GET_COUNT = 4
class TradeTop24(TopLineTrade):
    WE_GET_ITEM    = Item.RUBY_CROWN
    THEY_GET_ITEM  = Item.HAND_AXE
    THEY_GET_COUNT = 22
class TradeTop25(TopLineTrade):
    WE_GET_ITEM    = Item.SPHERE_OF_WISDOM
    THEY_GET_ITEM  = Item.POTION_OF_NIGHT
    THEY_GET_COUNT = 4
class TradeTop26(TopLineTrade):
    WE_GET_ITEM    = Item.SHADOWY_GEM
    THEY_GET_ITEM  = Item.GNOMISH_SHIELD
    THEY_GET_COUNT = 3
class TradeTop27(TopLineTrade):
    WE_GET_ITEM    = Item.SAPPHIRE_WAND
    THEY_GET_ITEM  = Item.LOYAL_PET_WHISTLE
    THEY_GET_COUNT = 2

class TradeTop31(TopLineTrade):
    WE_GET_ITEM    = Item.HAND_AXE
    THEY_GET_ITEM  = Item.GOLD
    THEY_GET_COUNT = 2
class TradeTop32(TopLineTrade):
    WE_GET_ITEM    = Item.CUTE_DOLL
    THEY_GET_ITEM  = Item.LINEN_BANDAGE
    THEY_GET_COUNT = 5
class TradeTop33(TopLineTrade):
    WE_GET_ITEM    = Item.ARCANE_SCROLL
    THEY_GET_ITEM  = Item.VERY_NICE_HAT
    THEY_GET_COUNT = 8
class TradeTop34(TopLineTrade):
    WE_GET_ITEM    = Item.DRAUGHT_OF_ANGELS
    THEY_GET_ITEM  = Item.ANGRY_CRYSTAL
    THEY_GET_COUNT = 1
class TradeTop35(TopLineTrade):
    WE_GET_ITEM    = Item.POTION_OF_NIGHT
    THEY_GET_ITEM  = Item.JADE_LOCKET
    THEY_GET_COUNT = 5
class TradeTop36(TopLineTrade):
    WE_GET_ITEM    = Item.EVERBURNING_CANDLE
    THEY_GET_ITEM  = Item.GOBLIN_FISHING_POLE
    THEY_GET_COUNT = 4
class TradeTop37(TopLineTrade):
    WE_GET_ITEM    = Item.TIGER_AMULET
    THEY_GET_ITEM  = Item.CAPTIVATING_PIPES
    THEY_GET_COUNT = 5

class TradeTop41(TopLineTrade):
    WE_GET_ITEM    = Item.CAPTIVATING_PIPES
    THEY_GET_ITEM  = Item.GOLD
    THEY_GET_COUNT = 11
class TradeTop42(TopLineTrade):
    WE_GET_ITEM    = Item.LINEN_BANDAGE
    THEY_GET_ITEM  = Item.ELIXIR_OF_VIGOR
    THEY_GET_COUNT = 1
class TradeTop43(TopLineTrade):
    WE_GET_ITEM    = Item.GILNEAN_DAGGER
    THEY_GET_ITEM  = Item.HEALING_POTION
    THEY_GET_COUNT = 49
class TradeTop44(TopLineTrade):
    WE_GET_ITEM    = Item.GNOMISH_SHIELD
    THEY_GET_ITEM  = Item.IRON_DAGGER
    THEY_GET_COUNT = 12
class TradeTop45(TopLineTrade):
    WE_GET_ITEM    = Item.POTION_OF_NIGHT
    THEY_GET_ITEM  = Item.STORMWIND_CHEDDAR
    THEY_GET_COUNT = 13
class TradeTop46(TopLineTrade):
    WE_GET_ITEM    = Item.TIGER_AMULET
    THEY_GET_ITEM  = Item.ARCANE_SCROLL
    THEY_GET_COUNT = 3
class TradeTop47(TopLineTrade):
    WE_GET_ITEM    = Item.ALLIANCE_MACE
    THEY_GET_ITEM  = Item.GOLDEN_GOBLET
    THEY_GET_COUNT = 3

class TradeTop51(TopLineTrade):
    WE_GET_ITEM    = Item.ARCANE_SCROLL
    THEY_GET_ITEM  = Item.GOLD
    THEY_GET_COUNT = 25
class TradeTop52(TopLineTrade):
    WE_GET_ITEM    = Item.VERY_NICE_HAT
    THEY_GET_ITEM  = Item.HAND_AXE
    THEY_GET_COUNT = 2
class TradeTop53(TopLineTrade):
    WE_GET_ITEM    = Item.CAPTIVATING_PIPES
    THEY_GET_ITEM  = Item.HEALING_POTION
    THEY_GET_COUNT = 7
class TradeTop54(TopLineTrade):
    WE_GET_ITEM    = Item.ANGRY_CRYSTAL
    THEY_GET_ITEM  = Item.ELIXIR_OF_VIGOR
    THEY_GET_COUNT = 20
class TradeTop55(TopLineTrade):
    WE_GET_ITEM    = Item.GILNEAN_DAGGER
    THEY_GET_ITEM  = Item.SAPPHIRE_WAND
    THEY_GET_COUNT = 2
class TradeTop56(TopLineTrade):
    WE_GET_ITEM    = Item.SPHERE_OF_WISDOM
    THEY_GET_ITEM  = Item.GOLDEN_GOBLET
    THEY_GET_COUNT = 10
class TradeTop57(TopLineTrade):
    WE_GET_ITEM    = Item.SAPPHIRE_WAND
    THEY_GET_ITEM  = Item.STORMWIND_CHEDDAR
    THEY_GET_COUNT = 15

class TradeTop61(TopLineTrade):
    WE_GET_ITEM    = Item.ELIXIR_OF_VIGOR
    THEY_GET_ITEM  = Item.GOLD
    THEY_GET_COUNT = 3
class TradeTop62(TopLineTrade):
    WE_GET_ITEM    = Item.GOBLIN_FISHING_POLE
    THEY_GET_ITEM  = Item.HAND_AXE
    THEY_GET_COUNT = 4
class TradeTop63(TopLineTrade):
    WE_GET_ITEM    = Item.SAPPHIRE_WAND
    THEY_GET_ITEM  = Item.VERY_NICE_HAT
    THEY_GET_COUNT = 5
class TradeTop64(TopLineTrade):
    WE_GET_ITEM    = Item.EVERBURNING_CANDLE
    THEY_GET_ITEM  = Item.ALLIANCE_MACE
    THEY_GET_COUNT = 1
class TradeTop65(TopLineTrade):
    WE_GET_ITEM    = Item.ANGRY_CRYSTAL
    THEY_GET_ITEM  = Item.CUTE_DOLL
    THEY_GET_COUNT = 5
class TradeTop66(TopLineTrade):
    WE_GET_ITEM    = Item.RUBY_CROWN
    THEY_GET_ITEM  = Item.CAPTIVATING_PIPES
    THEY_GET_COUNT = 3
class TradeTop67(TopLineTrade):
    WE_GET_ITEM    = Item.DRAUGHT_OF_ANGELS
    THEY_GET_ITEM  = Item.GOLDEN_GOBLET
    THEY_GET_COUNT = 9

class TradeTop71(TopLineTrade):
    WE_GET_ITEM    = Item.STORMWIND_CHEDDAR
    THEY_GET_ITEM  = Item.GOLD
    THEY_GET_COUNT = 2
class TradeTop72(TopLineTrade):
    WE_GET_ITEM    = Item.GOBLIN_FISHING_POLE
    THEY_GET_ITEM  = Item.STORMWIND_CHEDDAR
    THEY_GET_COUNT = 5
class TradeTop73(TopLineTrade):
    WE_GET_ITEM    = Item.LOYAL_PET_WHISTLE
    THEY_GET_ITEM  = Item.IRON_DAGGER
    THEY_GET_COUNT = 7
class TradeTop74(TopLineTrade):
    WE_GET_ITEM    = Item.SHADOWY_GEM
    THEY_GET_ITEM  = Item.ELIXIR_OF_VIGOR
    THEY_GET_COUNT = 9
class TradeTop75(TopLineTrade):
    WE_GET_ITEM    = Item.GILNEAN_DAGGER
    THEY_GET_ITEM  = Item.RUBY_CROWN
    THEY_GET_COUNT = 1
class TradeTop76(TopLineTrade):
    WE_GET_ITEM    = Item.TIGER_AMULET
    THEY_GET_ITEM  = Item.GNOMISH_SHIELD
    THEY_GET_COUNT = 4
class TradeTop77(TopLineTrade):
    WE_GET_ITEM    = Item.ALLIANCE_MACE
    THEY_GET_ITEM  = Item.CUTE_DOLL
    THEY_GET_COUNT = 3


#########################

class TradeBottom1HA(BottomLineTrade):
    WE_GET_COUNT   = 10
    THEY_GET_ITEM  = Item.HAND_AXE
    THEY_GET_COUNT = 6
class TradeBottom1GFP(BottomLineTrade):
    WE_GET_COUNT   = 18
    THEY_GET_ITEM  = Item.GOBLIN_FISHING_POLE
    THEY_GET_COUNT = 2
class TradeBottom1AC(BottomLineTrade):
    WE_GET_COUNT   = 60
    THEY_GET_ITEM  = Item.ANGRY_CRYSTAL
    THEY_GET_COUNT = 1
class TradeBottom1AS(BottomLineTrade):
    WE_GET_COUNT   = 138
    THEY_GET_ITEM  = Item.ARCANE_SCROLL
    THEY_GET_COUNT = 6
class TradeBottom1SOW(BottomLineTrade):
    WE_GET_COUNT   = 205
    THEY_GET_ITEM  = Item.SPHERE_OF_WISDOM
    THEY_GET_COUNT = 3

class TradeBottom2CD(BottomLineTrade):
    WE_GET_COUNT   = 18
    THEY_GET_ITEM  = Item.CUTE_DOLL
    THEY_GET_COUNT = 1
class TradeBottom2SC(BottomLineTrade):
    WE_GET_COUNT   = 25
    THEY_GET_ITEM  = Item.STORMWIND_CHEDDAR
    THEY_GET_COUNT = 10
class TradeBottom2GFP(BottomLineTrade):
    WE_GET_COUNT   = 120
    THEY_GET_ITEM  = Item.GOBLIN_FISHING_POLE
    THEY_GET_COUNT = 10
class TradeBottom2RC(BottomLineTrade):
    WE_GET_COUNT   = 92
    THEY_GET_ITEM  = Item.RUBY_CROWN
    THEY_GET_COUNT = 4
class TradeBottom2PON(BottomLineTrade):
    WE_GET_COUNT   = 240
    THEY_GET_ITEM  = Item.POTION_OF_NIGHT
    THEY_GET_COUNT = 8

class TradeBottom3LB(BottomLineTrade):
    WE_GET_COUNT   = 13
    THEY_GET_ITEM  = Item.LINEN_BANDAGE
    THEY_GET_COUNT = 3
class TradeBottom3VNH(BottomLineTrade):
    WE_GET_COUNT   = 14
    THEY_GET_ITEM  = Item.VERY_NICE_HAT
    THEY_GET_COUNT = 4
class TradeBottom3DOA(BottomLineTrade):
    WE_GET_COUNT   = 30
    THEY_GET_ITEM  = Item.DRAUGHT_OF_ANGELS
    THEY_GET_COUNT = 1
class TradeBottom3AC(BottomLineTrade):
    WE_GET_COUNT   = 150
    THEY_GET_ITEM  = Item.ANGRY_CRYSTAL
    THEY_GET_COUNT = 3
class TradeBottom3CD(BottomLineTrade):
    WE_GET_COUNT   = 166
    THEY_GET_ITEM  = Item.CUTE_DOLL
    THEY_GET_COUNT = 9

class TradeBottom4JL(BottomLineTrade):
    WE_GET_COUNT   = 11
    THEY_GET_ITEM  = Item.JADE_LOCKET
    THEY_GET_COUNT = 1
class TradeBottom4CP(BottomLineTrade):
    WE_GET_COUNT   = 42
    THEY_GET_ITEM  = Item.CAPTIVATING_PIPES
    THEY_GET_COUNT = 6
class TradeBottom4RC(BottomLineTrade):
    WE_GET_COUNT   = 72
    THEY_GET_ITEM  = Item.RUBY_CROWN
    THEY_GET_COUNT = 2
class TradeBottom4TA(BottomLineTrade):
    WE_GET_COUNT   = 114
    THEY_GET_ITEM  = Item.TIGER_AMULET
    THEY_GET_COUNT = 2
class TradeBottom4SW(BottomLineTrade):
    WE_GET_COUNT   = 125
    THEY_GET_ITEM  = Item.SAPPHIRE_WAND
    THEY_GET_COUNT = 10

class TradeBottom5ID(BottomLineTrade):
    WE_GET_COUNT   = 6
    THEY_GET_ITEM  = Item.IRON_DAGGER
    THEY_GET_COUNT = 3
class TradeBottom5GD(BottomLineTrade):
    WE_GET_COUNT   = 70
    THEY_GET_ITEM  = Item.GILNEAN_DAGGER
    THEY_GET_COUNT = 1
class TradeBottom5CP(BottomLineTrade):
    WE_GET_COUNT   = 50
    THEY_GET_ITEM  = Item.CAPTIVATING_PIPES
    THEY_GET_COUNT = 4
class TradeBottom5AM(BottomLineTrade):
    WE_GET_COUNT   = 125
    THEY_GET_ITEM  = Item.ALLIANCE_MACE
    THEY_GET_COUNT = 5
class TradeBottom5SG(BottomLineTrade):
    WE_GET_COUNT   = 166
    THEY_GET_ITEM  = Item.SHADOWY_GEM
    THEY_GET_COUNT = 7

class TradeBottom6EOV(BottomLineTrade):
    WE_GET_COUNT   = 15
    THEY_GET_ITEM  = Item.ELIXIR_OF_VIGOR
    THEY_GET_COUNT = 10
class TradeBottom6GS(BottomLineTrade):
    WE_GET_COUNT   = 25
    THEY_GET_ITEM  = Item.GNOMISH_SHIELD
    THEY_GET_COUNT = 2
class TradeBottom6GG(BottomLineTrade):
    WE_GET_COUNT   = 65
    THEY_GET_ITEM  = Item.GOLDEN_GOBLET
    THEY_GET_COUNT = 7
class TradeBottom6AM(BottomLineTrade):
    WE_GET_COUNT   = 70
    THEY_GET_ITEM  = Item.ALLIANCE_MACE
    THEY_GET_COUNT = 4
class TradeBottom6EC(BottomLineTrade):
    WE_GET_COUNT   = 180
    THEY_GET_ITEM  = Item.EVERBURNING_CANDLE
    THEY_GET_COUNT = 7

class TradeBottom7HP(BottomLineTrade):
    WE_GET_COUNT   = 10
    THEY_GET_ITEM  = Item.HEALING_POTION
    THEY_GET_COUNT = 8
class TradeBottom7LPW(BottomLineTrade):
    WE_GET_COUNT   = 22
    THEY_GET_ITEM  = Item.LOYAL_PET_WHISTLE
    THEY_GET_COUNT = 3
class TradeBottom7AS(BottomLineTrade):
    WE_GET_COUNT   = 70
    THEY_GET_ITEM  = Item.ARCANE_SCROLL
    THEY_GET_COUNT = 2
class TradeBottom7GS(BottomLineTrade):
    WE_GET_COUNT   = 60
    THEY_GET_ITEM  = Item.GNOMISH_SHIELD
    THEY_GET_COUNT = 7
class TradeBottom7DOA(BottomLineTrade):
    WE_GET_COUNT   = 204
    THEY_GET_ITEM  = Item.DRAUGHT_OF_ANGELS
    THEY_GET_COUNT = 4

#########################
# Compute best value of items based on top-line trades.

TOP_LINE_TRADES_ANY = tuple(TopLineTrade.__subclasses__())  # type: Sequence[Type[TopLineTrade]]

while True:
    updated_anything = False
    for item in Item.__members__.values():
        for trade in TOP_LINE_TRADES_ANY:
            assert trade.WE_GET_COUNT == 1
            if trade.WE_GET_ITEM != item:
                continue
            price = GOLDVALUE_OF_ITEM.get(trade.THEY_GET_ITEM, None)
            if price is None:
                continue
            price *= trade.THEY_GET_COUNT

            old_besttrade = BESTTRADE_TO_CRAFT_ITEM.get(item)
            old_goldval = GOLDVALUE_OF_ITEM.get(item, float("inf"))
            if price < old_goldval:
                GOLDVALUE_OF_ITEM[item] = price
                BESTTRADE_TO_CRAFT_ITEM[item] = trade
                updated_anything = True
            elif price == old_goldval and trade != old_besttrade:
                assert False, "found multiple optimal paths to craft item!"
    if not updated_anything:
        break


#########################

BOTTOM_LINE_TRADES = tuple(BottomLineTrade.__subclasses__())  # type: Sequence[Type[BottomLineTrade]]
TOP_LINE_TRADES_ONLY_GOOD = tuple(cls for cls in TOP_LINE_TRADES_ANY if cls.delta_balance() >= 0)  # type: Sequence[Type[TopLineTrade]]
ALL_GOOD_TRADES = tuple(trade for trade in (list(BOTTOM_LINE_TRADES) + list(TOP_LINE_TRADES_ONLY_GOOD)))  # type: Sequence[Type[Trade]]

INVERSEMAP_BOTTOMLINETRADES = {trade: idx for idx, trade in enumerate(BOTTOM_LINE_TRADES)}  # type: Mapping[Type[BottomLineTrade], int]
INVERSEMAP_ALLTRADES        = {trade: idx for idx, trade in enumerate(ALL_GOOD_TRADES)}  # type: Mapping[Type[Trade], int]

BOTTOM_LINE_TRADES_DONE_BITMAP = (1 << len(BOTTOM_LINE_TRADES)) - 1

#########################
# Note that we only ever need
#   - 1 GILNEAN_DAGGER
#   - 5 DRAUGHT_OF_ANGELS
#   - 3 SPHERE_OF_WISDOM, ...
# This can be extended to not only include "end/final items" but intermediate ingredients.
# This exploits that the "item-crafting graph" is a tree; i.e. to craft an item for
# its best price, there is only one path.
# note: ITEMS_OVERALL_NEEDED_FOR_GOAL does not account for STARTING_GOLD,
#       as gamestate.items_crafted_ever does not include it either.

ITEMS_OVERALL_NEEDED_FOR_GOAL = defaultdict(int)  # type: Dict[Item, int]
_crafting_queue = deque()  # type: collections.deque[Tuple[Item, int]]
for trade in BOTTOM_LINE_TRADES:
    _crafting_queue.append((trade.THEY_GET_ITEM, trade.THEY_GET_COUNT))
while len(_crafting_queue) > 0:
    to_craft_item, to_craft_count = _crafting_queue.popleft()
    ITEMS_OVERALL_NEEDED_FOR_GOAL[to_craft_item] += to_craft_count
    if to_craft_item == Item.GOLD:
        continue
    trade = BESTTRADE_TO_CRAFT_ITEM[to_craft_item]
    _crafting_queue.append((trade.THEY_GET_ITEM, trade.THEY_GET_COUNT * to_craft_count))

del _crafting_queue

#########################

CRAFTING_TRADECHAIN_FOR_ITEM = defaultdict(list)  # type: Dict[Item, Sequence[Tuple[Type[TopLineTrade], int]]]
CRAFTING_ITEMCHAIN_FOR_ITEM = defaultdict(list)  # type: Dict[Item, Sequence[Tuple[Item, int]]]
for item in Item.__members__.values():
    ingredient = item
    multiplier = 1
    while ingredient != Item.GOLD:
        CRAFTING_ITEMCHAIN_FOR_ITEM[item].append((ingredient, multiplier))
        CRAFTING_TRADECHAIN_FOR_ITEM[item].append((BESTTRADE_TO_CRAFT_ITEM[ingredient], multiplier))
        multiplier *= BESTTRADE_TO_CRAFT_ITEM[ingredient].THEY_GET_COUNT
        ingredient = BESTTRADE_TO_CRAFT_ITEM[ingredient].THEY_GET_ITEM
    CRAFTING_ITEMCHAIN_FOR_ITEM[item].append((ingredient, multiplier))
    CRAFTING_TRADECHAIN_FOR_ITEM[item] = tuple(CRAFTING_TRADECHAIN_FOR_ITEM[item])
    CRAFTING_ITEMCHAIN_FOR_ITEM[item] = tuple(CRAFTING_ITEMCHAIN_FOR_ITEM[item])

CRAFTING_TRADECHAIN_FOR_TRADE = defaultdict(list)  # type: Dict[Type[BottomLineTrade], Sequence[Type[TopLineTrade]]]
for trade in BOTTOM_LINE_TRADES:
    CRAFTING_TRADECHAIN_FOR_TRADE[trade] = tuple(tr for tr, mult in CRAFTING_TRADECHAIN_FOR_ITEM[trade.THEY_GET_ITEM][::-1])


#########################

def list_enabled_bits(x: int) -> Sequence[int]:
    """example: 35==0b100011 -> (0, 1, 5)"""
    rev_bin = reversed(bin(x)[2:])
    return tuple(i for i, b in enumerate(rev_bin) if b == '1')


#########################

class GameState:

    def __init__(self):
        self.cur_inventory = defaultdict(int)  # type: Dict[Item, int]
        self.cur_inventory[Item.GOLD] = STARTING_GOLD
        self.cur_inventory_goldvalue = STARTING_GOLD  # assuming every item was converted to gold
        self.cur_inventory_num_itemtypes = 1  # how many different types of items we have currently
        self.items_crafted_ever = defaultdict(int)  # type: Dict[Item, int]
        # each history item is a trade already executed, coupled with a multiplier
        self.history = []  # type: List[Tuple[Type[Trade], int]]
        self._chaincraft_undo_history = []  # type: List[int]
        self.bottomlinetrades_done = 0  # type: int  # bitmap for indices of BOTTOM_LINE_TRADES
        # keep account of remaining trades that can increase cur_inventory_goldvalue
        self.sum_of_rem_balancepositive_trades = sum(trade.delta_balance() for trade in BOTTOM_LINE_TRADES
                                                     if trade.delta_balance() > 0)
        self._recalc_max_rem_outval_trade()

    def _recalc_max_rem_outval_trade(self):
        try:
            self.max_rem_outval_trade = max(trade.outvalue() for trade in BOTTOM_LINE_TRADES
                                            if not (self.bottomlinetrades_done & (1 << INVERSEMAP_BOTTOMLINETRADES[trade])))
        except ValueError:  # no trades left
            self.max_rem_outval_trade = -float("inf")

    def do_trade(self, trade: Type[Trade]) -> bool:
        """Returns whether the trade was executed."""
        # bottom-line trades can only be executed once
        if trade.IS_BOTTOM_LINE and bool(self.bottomlinetrades_done & (1 << INVERSEMAP_BOTTOMLINETRADES[trade])):
            return False
        multiplier = self.cur_inventory[trade.THEY_GET_ITEM] // trade.THEY_GET_COUNT
        # check if we have required items for trade
        if multiplier == 0:
            return False
        if trade.IS_BOTTOM_LINE:
            multiplier = 1
        # we precalculated counts for each item we will ever need to craft;
        # make sure that is not exceeded.
        if (self.items_crafted_ever[trade.WE_GET_ITEM] + multiplier * trade.WE_GET_COUNT
                > ITEMS_OVERALL_NEEDED_FOR_GOAL[trade.WE_GET_ITEM]):
            return False
        # we have now decided to execute the trade.
        if self.cur_inventory[trade.WE_GET_ITEM] == 0:
            self.cur_inventory_num_itemtypes += 1
        self.cur_inventory[trade.THEY_GET_ITEM] -= multiplier * trade.THEY_GET_COUNT
        self.cur_inventory[trade.WE_GET_ITEM] += multiplier * trade.WE_GET_COUNT
        if self.cur_inventory[trade.THEY_GET_ITEM] == 0:
            self.cur_inventory_num_itemtypes -= 1
        self.items_crafted_ever[trade.WE_GET_ITEM] += multiplier * trade.WE_GET_COUNT
        self.cur_inventory_goldvalue += multiplier * trade.delta_balance()
        self.history.append((trade, multiplier))
        if trade.IS_BOTTOM_LINE:
            self.bottomlinetrades_done += 1 << INVERSEMAP_BOTTOMLINETRADES[trade]
            if trade.delta_balance() > 0:
                self.sum_of_rem_balancepositive_trades -= trade.delta_balance()
            if trade.outvalue() == self.max_rem_outval_trade:
                self._recalc_max_rem_outval_trade()
        # now check the sanity of the new state; if fails, we undo the trade
        if not self.sanity_check_current_state():
            self.undo_last_trade()
            return False
        return True

    def undo_last_trade(self) -> int:
        """Returns index of trade undone."""
        if not self.history:
            raise Exception("no solution")
        trade, multiplier = self.history.pop()
        if self.cur_inventory[trade.THEY_GET_ITEM] == 0:
            self.cur_inventory_num_itemtypes += 1
        self.cur_inventory[trade.THEY_GET_ITEM] += multiplier * trade.THEY_GET_COUNT
        self.cur_inventory[trade.WE_GET_ITEM] -= multiplier * trade.WE_GET_COUNT
        if self.cur_inventory[trade.WE_GET_ITEM] == 0:
            self.cur_inventory_num_itemtypes -= 1
        self.items_crafted_ever[trade.WE_GET_ITEM] -= multiplier * trade.WE_GET_COUNT
        self.cur_inventory_goldvalue -= multiplier * trade.delta_balance()
        if trade.IS_BOTTOM_LINE:
            self.bottomlinetrades_done -= 1 << INVERSEMAP_BOTTOMLINETRADES[trade]
            if trade.delta_balance() > 0:
                self.sum_of_rem_balancepositive_trades += trade.delta_balance()
            if trade.outvalue() > self.max_rem_outval_trade:
                self._recalc_max_rem_outval_trade()
        return INVERSEMAP_ALLTRADES[trade]

    def has_enough_to_chaincraft_bltrade(self, trade: Type[BottomLineTrade]) -> bool:
        """Returns whether we can execute the given bottom-line-trade (sell to adventurer),
        including crafting the required items (doing potentially many top-line-trades, but
        without doing other bottom-line-trades).
        """
        # >>> hsutil.CRAFTING_ITEMCHAIN_FOR_ITEM[hsutil.Item.EVERBURNING_CANDLE]
        # ((<Item.EVERBURNING_CANDLE: 18>, 1), (<Item.ALLIANCE_MACE: 5>, 1), (<Item.GOLDEN_GOBLET: 3>, 3), (<Item.HEALING_POTION: 2>, 12), (<Item.GOLD: 1>, 24))
        our_relevant_inventory_value = 0
        itemchain = CRAFTING_ITEMCHAIN_FOR_ITEM[trade.THEY_GET_ITEM]
        for item, count_needed in itemchain:
            our_relevant_inventory_value += self.cur_inventory[item] * item.goldvalue()
        gold_needed = itemchain[-1][1] * trade.THEY_GET_COUNT
        return our_relevant_inventory_value >= gold_needed

    def chaincraft_bltrade(self, trade: Type[BottomLineTrade]) -> bool:
        """Execute the given bottom-line-trade (sell to adventurer),
        including crafting the required items (doing potentially many top-line-trades, but
        without doing other bottom-line-trades).
        Returns whether the chaincraft was executed.
        """
        # shortcut (duplicated from "do_trade"): bottom-line trades can only be executed once
        if self.bottomlinetrades_done & (1 << INVERSEMAP_BOTTOMLINETRADES[trade]):
            return False
        if not self.has_enough_to_chaincraft_bltrade(trade):
            return False
        self._chaincraft_undo_history.append(len(self.history))
        for toplinetrade in CRAFTING_TRADECHAIN_FOR_TRADE[trade]:
            # note: The first few trades might not execute (return False),
            #       if they are unnecessary. This is fine.
            self.do_trade(toplinetrade)
        # now execute the bottom-line trade. if this fails, we need to undo everything
        if not self.do_trade(trade):
            self.undo_last_chaincraft()
            return False
        return True

    def undo_last_chaincraft(self) -> Optional[int]:
        """Returns index of the undone bottom-line-trade-chaincrafted.
        Might return None, but only if undoing a partially-executed chaincraft.
        """
        if not self._chaincraft_undo_history:
            raise Exception("no solution")
        hist_idx = self._chaincraft_undo_history.pop()
        if not self.history:  # the chaincraft was only partially-executed
            return None
        assert len(self.history) >= hist_idx
        final_trade = self.history[-1][0]
        if final_trade.IS_BOTTOM_LINE:
            bottomlinetrade_idx = INVERSEMAP_BOTTOMLINETRADES[final_trade]
        else:  # the chaincraft was only partially-executed
            bottomlinetrade_idx = None
        for _ in range(len(self.history) - hist_idx):
            self.undo_last_trade()
        return bottomlinetrade_idx

    def sanity_check_current_state(self) -> bool:
        """Returns whether current state is SANE.
        If False, we need to undo last trade.
        """
        # if current inventory value plus sum of remaining positive-val BL-trades
        # is less than remaining max outval BL-trade, then cut DFS
        if self.cur_inventory_goldvalue + self.sum_of_rem_balancepositive_trades < self.max_rem_outval_trade:
            return False
        # if we have too many different cards in hand, then cut DFS
        if self.cur_inventory_num_itemtypes > 10:
            return False
        return True

    def is_complete(self) -> bool:
        return self.bottomlinetrades_done == BOTTOM_LINE_TRADES_DONE_BITMAP

    def get_cur_inventory_num_itemtypes_excl_gold(self) -> int:
        if self.cur_inventory[Item.GOLD] == 0:
            return self.cur_inventory_num_itemtypes
        else:
            return self.cur_inventory_num_itemtypes - 1

    def print_readable_history(self) -> None:
        for idx, action in enumerate(self.history):
            trade = action[0]
            assert issubclass(trade, Trade)
            print(f"idx={idx}. action={action}.")

    def print_diagnostic_data(self) -> None:
        print(f"- history state: {self.dump_history_trade_idx_ints()}")
        print(f"- invvalue-changes: {[trade.delta_balance() for trade, mult in self.history]}")
        inventory = self.get_nonzero_inventory()
        print(f"- {len(self.history)=}. inventory({len(inventory)})={inventory}")
        print(f"- {self.cur_inventory_goldvalue=}. {self.sum_of_rem_balancepositive_trades=}. {self.max_rem_outval_trade=}")
        print(f"- bottom trades bitmap: {bin(self.bottomlinetrades_done)}")
        print(f"- bottom trades done: {[str(trade) for trade, mult in self.history if trade.IS_BOTTOM_LINE]}")

    def get_nonzero_inventory(self) -> Dict[Item, int]:
        return {
            item: count for (item, count) in self.cur_inventory.items()
            if count > 0
        }

    def dump_history_trade_idx_ints(self) -> Sequence[int]:
        return [INVERSEMAP_ALLTRADES[trade] for trade, mult in self.history]


#########################
#########################

# > observation
# We must execute all bottom-line trades exactly once, and given the best price of items,
# the overall balance change after doing all these trades is zero:
balance = 0
for trade in BOTTOM_LINE_TRADES:
    balance += trade.delta_balance()
print(f"balance-change after executing all bottom-line trades once: {balance} gold")
# hence from the top-line trades, we can exclude all "bad trades" (which would reduce our inventory-value)
trades_by_deltabal = defaultdict(list)
for trade in TOP_LINE_TRADES_ANY:
    bal_change = trade.delta_balance()
    if bal_change > 0: bal_change = 1
    if bal_change < 0: bal_change = -1
    trades_by_deltabal[bal_change].append(trade)
print(f"good TL-trades: {len(trades_by_deltabal[+1])}, "
      f"neutral TL-trades: {len(trades_by_deltabal[0])}, "
      f"bad TL-trades: {len(trades_by_deltabal[-1])}")
print(f"=====")

# > observation
# Now that all the top-line trades are neutral value, note that
# some of the bottom-line trades are negative, some neutral, some positive.
# Consider the max inventory-value we can achieve at any given time.
# For that, we would need to execute all the positive-value bottom-line trades
# and none of the negative ones at the start of the game.
# Note that some bottom-line trades require a very large inventory-value (e.g. 3xSPHERE_OF_WISDOM -> 240g).
valsum_of_positive_trades = 0
for trade in BOTTOM_LINE_TRADES:
    if trade.delta_balance() > 0:
        valsum_of_positive_trades += trade.delta_balance()
print(f"value sum of all positive delta bottom-line trades: {valsum_of_positive_trades}; "
      f"plus starting gold: {STARTING_GOLD}")
print(f"max value-outflow (cost) during a bottom-line trade: {max(trade.outvalue() for trade in BOTTOM_LINE_TRADES)}")
print(f"=====")

# print some derived stats
print(f"best gold price of items: {GOLDVALUE_OF_ITEM}")
print(f"items overall needed for goal: {ITEMS_OVERALL_NEEDED_FOR_GOAL}")
print(f"=====")
