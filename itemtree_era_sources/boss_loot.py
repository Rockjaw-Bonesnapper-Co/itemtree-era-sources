# SPDX-License-Identifier: GPL-3.0-only
# Copyright (c) 2026 Rockjaw Bonesnapper Co
# Public home, the Corresponding Source of EraSources.lua and BossLoot.lua: https://github.com/Rockjaw-Bonesnapper-Co/itemtree-era-sources
"""The Boss loot index: dungeons, raids and world bosses, their bosses and rare elites, and what
each one drops, as one small on-demand module, `BossLoot.lua`.

It is the other half of the historical Classic Era data. `EraSources.lua` answers "where does
this item come from", keyed by item; this module answers "what does this boss drop", keyed by
place and boss, so the addon's Boss loot tab never has to build EraSources (11 MB) or walk it.

Two kinds of fact meet here, and every field says which kind it is:

  * the PLACES, the encounters, their order and the level a place is read at come from THIS
    build's own client tables (`Map`, `DungeonEncounter`, `LFGDungeons`, `ContentTuning`,
    `AreaTable`), so a place Forever added is listed the day the client ships it;
  * the CREATURES, their levels and their LOOT come from the same pinned CMaNGOS Classic dump
    `era_sources.py` reads, through its own helpers (`expand_loot`, `chance_percent`,
    `pack_int`), so a boss's chance for an item is exactly the chance the item page shows.
    CMaNGOS `instance_encounters` joins the two where it can.

What is taken from CMaNGOS, and nothing else: creature and object names, creature ids, creature
levels and ranks, the spawn MAP (never a position), the loot chances and the encounter credits.
pfQuest's vanilla unit zones name the zones a world boss spawns in, as area ids. No prose.

The contract (docs/boss-loot.md, section 1 of the plan) is `v = 1`:

  { v = 1, s = {strings}, p = {places in draw order}, b = {bosses, rares and chests} }

and each boss's loot is a packed string of fixed 8 byte records in the base 91 alphabet the
EraSources `xl` lists use: item id (3 digits), value (2: the chance in tenths of a percent plus
2048 where quest only), type code (1), item level (2).

Because it carries CMaNGOS names, levels and chances, the generated file is a GPL-3.0
derivation exactly as EraSources.lua is (the orchestrator's ruling 1 of 2026-09-27), and this
compiler is mirrored beside era_sources.py into the public repository.
"""

from __future__ import annotations

import gzip
import math
import re
import sqlite3
from collections import defaultdict
from collections.abc import Collection, Iterable, Mapping, Sequence
from dataclasses import dataclass, field
from pathlib import Path
from typing import Protocol

from itemtree_data import era_sources as era_mod

# ----- the contract's constants -------------------------------------------------------------

MODULE_NAME = "BossLoot"
# The contract version. The addon refuses any other.
CONTRACT_VERSION = 1

KIND_DUNGEON = 1
KIND_RAID = 2
KIND_WORLD_BOSS = 3
# Map.InstanceType: 1 a party dungeon, 2 a raid.
INSTANCE_KINDS = {1: KIND_DUNGEON, 2: KIND_RAID}

RANK_BOSS = 1
RANK_RARE_ELITE = 2
RANK_RARE = 3
RANK_CHEST = 4
# CMaNGOS creature_template.Rank: 1 elite, 2 rare elite, 3 boss, 4 rare.
CMANGOS_RARE_ELITE = 2
CMANGOS_BOSS = 3
CMANGOS_RARE = 4
RARE_RANKS = {CMANGOS_RARE_ELITE: RANK_RARE_ELITE, CMANGOS_RARE: RANK_RARE}

# DungeonEncounter.DifficultyID values that are the ordinary game. Season of Discovery rows use
# 198, 201 and 215 on Blackfathom Deeps, Gnomeregan and Sunken Temple and are left out.
PLAIN_DIFFICULTIES = frozenset({0, 1})
# LFGDungeons.TypeID 0 is a dungeon or raid entry (not a random queue or a scenario).
LFG_TYPE_DUNGEON = 0
# The open world continents a world boss stands on.
CONTINENT_MAPS = frozenset({0, 1})
# The quality a world boss's loot, or a chest's, has to reach at least once: rare.
NOTABLE_QUALITY = 3
# Places are read at player levels, so every place level is clamped to this.
MAX_PLAYER_LEVEL = 60
# The band a place is drawn under: ceil(lv / 10), 1 to 6, and 7 for no level at all.
BAND_WIDTH = 10
BAND_COUNT = 6
BAND_UNKNOWN = BAND_COUNT + 1
# instance_encounters.creditType 0: the credit is a creature kill.
CREDIT_KILL = 0
# The shipped file may not grow past this. The plan estimates 60 to 110 KB.
MAX_FILE_BYTES = 200 * 1024

# The loot record: the same alphabet and digit order as the EraSources xl lists.
RECORD_ITEM_DIGITS = 3
RECORD_VALUE_DIGITS = 2
RECORD_TYPE_DIGITS = 1
RECORD_LEVEL_DIGITS = 2
RECORD_BYTES = RECORD_ITEM_DIGITS + RECORD_VALUE_DIGITS + RECORD_TYPE_DIGITS + RECORD_LEVEL_DIGITS

# ----- the 21 type codes ---------------------------------------------------------------------
#
# The addon's locale keys name these words; the number is the contract. The pipeline decides by
# inventory type first, then by class and subclass.
TYPE_PLATE = 1
TYPE_MAIL = 2
TYPE_LEATHER = 3
TYPE_CLOTH = 4
TYPE_BACK = 5
TYPE_SHIELD = 6
TYPE_OFF_HAND = 7
TYPE_NECK = 8
TYPE_FINGER = 9
TYPE_TRINKET = 10
TYPE_RELIC = 11
TYPE_ONE_HAND = 12
TYPE_TWO_HAND = 13
TYPE_RANGED = 14
TYPE_RECIPE = 15
TYPE_QUEST = 16
TYPE_MATERIAL = 17
TYPE_CONSUMABLE = 18
TYPE_CONTAINER = 19
TYPE_KEY = 20
TYPE_OTHER = 21
TYPE_WORDS = {
    TYPE_PLATE: "Plate",
    TYPE_MAIL: "Mail",
    TYPE_LEATHER: "Leather",
    TYPE_CLOTH: "Cloth",
    TYPE_BACK: "Back",
    TYPE_SHIELD: "Shield",
    TYPE_OFF_HAND: "Held in off-hand",
    TYPE_NECK: "Neck",
    TYPE_FINGER: "Finger",
    TYPE_TRINKET: "Trinket",
    TYPE_RELIC: "Relic",
    TYPE_ONE_HAND: "One-hand weapon",
    TYPE_TWO_HAND: "Two-hand weapon",
    TYPE_RANGED: "Ranged",
    TYPE_RECIPE: "Recipe",
    TYPE_QUEST: "Quest",
    TYPE_MATERIAL: "Material",
    TYPE_CONSUMABLE: "Consumable",
    TYPE_CONTAINER: "Container",
    TYPE_KEY: "Key",
    TYPE_OTHER: "Other",
}

# Item classes and the armour subclasses the codes read.
CLASS_CONSUMABLE = 0
CLASS_CONTAINER = 1
CLASS_WEAPON = 2
CLASS_ARMOUR = 4
CLASS_REAGENT = 5
CLASS_TRADE_GOODS = 7
CLASS_RECIPE = 9
CLASS_QUEST = 12
CLASS_KEY = 13
ARMOUR_SHIELD = 6
ARMOUR_RELICS = frozenset({7, 8, 9})  # libram, idol, totem
WEAPON_WAND = 19
# Inventory types.
INV_NECK = 2
INV_SHIRT = 4
INV_FINGER = 11
INV_TRINKET = 12
INV_ONE_HAND = 13
INV_SHIELD = 14
INV_RANGED = 15
INV_BACK = 16
INV_TWO_HAND = 17
INV_TABARD = 19
INV_MAIN_HAND = 21
INV_OFF_HAND_WEAPON = 22
INV_HELD_IN_OFF_HAND = 23
INV_THROWN = 25
INV_RANGED_RIGHT = 26
INV_RELIC = 28
ONE_HAND_SLOTS = frozenset({INV_ONE_HAND, INV_MAIN_HAND, INV_OFF_HAND_WEAPON})
RANGED_SLOTS = frozenset({INV_RANGED, INV_THROWN, INV_RANGED_RIGHT})
# Armour worn in these slots is not Cloth, Leather, Mail or Plate on the list: a shirt and a
# tabard are Other, and a piece with no slot is not worn at all.
NOT_WORN_SLOTS = frozenset({0, INV_SHIRT, INV_TABARD})


class BossLootError(RuntimeError):
    """A build this stage cannot read, with the command that fixes it."""


def type_code(class_id: int, subclass_id: int, inventory_type: int) -> int:
    """The type group an item is drawn under: inventory type first, then class and subclass."""
    by_slot = {
        INV_BACK: TYPE_BACK,
        INV_HELD_IN_OFF_HAND: TYPE_OFF_HAND,
        INV_NECK: TYPE_NECK,
        INV_FINGER: TYPE_FINGER,
        INV_TRINKET: TYPE_TRINKET,
        INV_TWO_HAND: TYPE_TWO_HAND,
        INV_SHIELD: TYPE_SHIELD,
        INV_RELIC: TYPE_RELIC,
    }
    if inventory_type in by_slot:
        return by_slot[inventory_type]
    if inventory_type in ONE_HAND_SLOTS and class_id == CLASS_WEAPON:
        return TYPE_ONE_HAND
    if inventory_type in RANGED_SLOTS:
        return TYPE_RANGED
    if class_id == CLASS_WEAPON:
        return TYPE_RANGED if subclass_id == WEAPON_WAND else TYPE_OTHER
    if class_id == CLASS_ARMOUR:
        if subclass_id == ARMOUR_SHIELD:
            return TYPE_SHIELD
        if subclass_id in ARMOUR_RELICS:
            return TYPE_RELIC
        if 1 <= subclass_id <= 4 and inventory_type not in NOT_WORN_SLOTS:
            # Armour subclass 4 plate, 3 mail, 2 leather, 1 cloth: codes 1 to 4 run the other way.
            return TYPE_CLOTH + 1 - subclass_id
        return TYPE_OTHER
    by_class = {
        CLASS_RECIPE: TYPE_RECIPE,
        CLASS_QUEST: TYPE_QUEST,
        CLASS_TRADE_GOODS: TYPE_MATERIAL,
        CLASS_REAGENT: TYPE_MATERIAL,
        CLASS_CONSUMABLE: TYPE_CONSUMABLE,
        CLASS_CONTAINER: TYPE_CONTAINER,
        CLASS_KEY: TYPE_KEY,
    }
    return by_class.get(class_id, TYPE_OTHER)


def band(level: int | None) -> int:
    """The band a place is listed under: 1 to 6 by tens of levels, and 7 for no level."""
    if not level:
        return BAND_UNKNOWN
    return min(BAND_COUNT, max(1, math.ceil(level / BAND_WIDTH)))


def pack_loot(value: int, item: int, type_: int, item_level: int) -> str:
    """One 8 byte loot record: item id, value, type code, item level."""
    return (
        era_mod.pack_int(item, RECORD_ITEM_DIGITS)
        + era_mod.pack_int(value, RECORD_VALUE_DIGITS)
        + era_mod.pack_int(type_, RECORD_TYPE_DIGITS)
        + era_mod.pack_int(item_level, RECORD_LEVEL_DIGITS)
    )


def unpack_int(text: str) -> int:
    """The inverse of era_sources.pack_int, for the tests and the report."""
    value = 0
    for ch in text:
        code = ord(ch)
        digit = code - era_mod.PACK_FIRST - (1 if code > era_mod.PACK_SKIPPED else 0)
        value = value * era_mod.PACK_BASE + digit
    return value


def unpack_loot(packed: str) -> list[tuple[int, int, int, int]]:
    """(item, value, type, item level) per record, the way the addon's DecodeLoot reads them."""
    if len(packed) % RECORD_BYTES:
        raise ValueError(f"a loot string of {len(packed)} bytes is not whole {RECORD_BYTES} byte records")
    out: list[tuple[int, int, int, int]] = []
    for start in range(0, len(packed), RECORD_BYTES):
        record = packed[start : start + RECORD_BYTES]
        at = 0
        fields: list[int] = []
        for width in (RECORD_ITEM_DIGITS, RECORD_VALUE_DIGITS, RECORD_TYPE_DIGITS, RECORD_LEVEL_DIGITS):
            fields.append(unpack_int(record[at : at + width]))
            at += width
        out.append((fields[0], fields[1], fields[2], fields[3]))
    return out


def loot_value(drop: era_mod.Drop) -> int:
    """The chance in tenths of a percent by the EraSources rule, plus the quest only flag."""
    percent = era_mod.chance_percent(drop.chance)
    value = int(round(percent * era_mod.PACK_TENTHS)) if percent is not None else 0
    if drop.quest_only:
        value += era_mod.PACK_QUEST_ONLY
    return value


def normalise(name: str) -> str:
    """A name for matching: lower case, apostrophes gone, punctuation to spaces, no leading "the"."""
    text = name.lower().replace("'", "")
    text = " ".join(re.sub(r"[^0-9a-z]+", " ", text).split())
    return text[4:] if text.startswith("the ") else text


def _one_edit_apart(a: str, b: str) -> bool:
    """Whether two strings differ by at most one inserted, removed or changed character, or by
    two neighbouring characters swapped ("Geilhast" for "Gelihast")."""
    if abs(len(a) - len(b)) > 1:
        return False
    if len(a) == len(b):
        diff = [i for i in range(len(a)) if a[i] != b[i]]
        if len(diff) <= 1:
            return True
        return (
            len(diff) == 2
            and diff[1] == diff[0] + 1
            and a[diff[0]] == b[diff[1]]
            and a[diff[1]] == b[diff[0]]
        )
    if len(a) > len(b):
        a, b = b, a
    # b is one longer: removing one character of b has to give a.
    return any(b[:i] + b[i + 1 :] == a for i in range(len(b)))


def loosely_named(encounter: str, creature: str) -> bool:
    """Whether a creature is plausibly the one an encounter names, when the names are not equal:
    one is the other with words added at the end ("Kirtonos" for "Kirtonos the Herald", "Ras
    Frostwhisperer" for "Ras Frostwhisper"), or they are one letter apart ("Geilhast")."""
    a, b = normalise(encounter), normalise(creature)
    if not a or not b or a == b:
        return bool(a) and a == b
    short, long_ = (a, b) if len(a) <= len(b) else (b, a)
    if long_.startswith(short + " ") or (len(short) >= 6 and long_.startswith(short)):
        return True
    return min(len(a), len(b)) >= 6 and _one_edit_apart(a, b)


def names_match(place: str, entry: str) -> bool:
    """Whether an LFGDungeons name names this map, as loosely as the build's own names need.

    Exact after normalise first ("The Hall of Thanes" and "Hall of Thanes"), then one a word
    wise prefix or part of the other ("Stormwind Stockades", "Onyxia" for "Onyxia's Lair",
    "Lower Blackrock Spire", "Dire Maul - East"), then one letter apart ("Zul'Farak").
    """
    a, b = normalise(place), normalise(entry)
    if not a or not b:
        return False
    if a == b:
        return True
    if a.startswith(b) or b.startswith(a):
        return True
    if f" {a} " in f" {b} " or f" {b} " in f" {a} ":
        return True
    return min(len(a), len(b)) >= 6 and _one_edit_apart(a.replace(" ", ""), b.replace(" ", ""))


# ----- the client facts, as plain data so a fixture can hand build them ----------------------


@dataclass(frozen=True)
class MapFacts:
    """One `Map` row of an instance: its name, kind, size and own area."""

    id: int
    name: str
    instance_type: int
    max_players: int = 0
    area: int = 0


@dataclass(frozen=True)
class EncounterFacts:
    """One `DungeonEncounter` row."""

    id: int
    name: str
    map: int
    difficulty: int = 0
    order: int = 0


@dataclass(frozen=True)
class DungeonFacts:
    """One `LFGDungeons` row: a name, its type and the levels it states or points at."""

    id: int
    name: str
    type_id: int = LFG_TYPE_DUNGEON
    min_level: int = 0
    max_level: int = 0
    tuning: int = 0


@dataclass(frozen=True)
class TuningFacts:
    """One `ContentTuning` row, the four level columns only."""

    id: int
    min_level: int = 0
    max_level: int = 0
    lfg_min: int = 0
    lfg_max: int = 0

    def levels(self) -> tuple[int, int] | None:
        """(low, high): MinLevelSquish (LfgMinLevel where that is 0) to the higher of
        MaxLevelSquish and LfgMaxLevel. None when the row states no level at all."""
        low = self.min_level or self.lfg_min
        if low <= 0:
            return None
        return low, max(low, self.max_level, self.lfg_max)


@dataclass(frozen=True)
class AreaFacts:
    """One `AreaTable` row: its name, the map it is on, its parent and its tuning."""

    id: int
    name: str
    continent: int = 0
    parent: int = 0
    tuning: int = 0


@dataclass
class BossLootInput:
    """Everything the stage reads from the client builds, beside the EraInput it shares with
    era_sources. `credits` is CMaNGOS `instance_encounters` (creditType 0), entry -> creatures."""

    maps: dict[int, MapFacts] = field(default_factory=dict)
    baseline_maps: frozenset[int] = frozenset()
    encounters: list[EncounterFacts] = field(default_factory=list)
    baseline_encounters: frozenset[int] = frozenset()
    dungeons: list[DungeonFacts] = field(default_factory=list)
    tuning: dict[int, TuningFacts] = field(default_factory=dict)
    areas: dict[int, AreaFacts] = field(default_factory=dict)
    credits: dict[int, tuple[int, ...]] = field(default_factory=dict)


class ItemFacts(Protocol):
    """What the stage reads about one named item."""

    @property
    def quality(self) -> int: ...

    @property
    def class_id(self) -> int: ...

    @property
    def subclass_id(self) -> int: ...

    @property
    def inventory_type(self) -> int: ...

    @property
    def item_level(self) -> int: ...


class ItemTable(Protocol):
    """A build's named items and the ids it lists but hides. The pipeline's BuildGraph is one."""

    @property
    def items(self) -> Mapping[int, ItemFacts]: ...

    @property
    def undiscovered(self) -> Mapping[int, object]: ...


# ----- the derived table ----------------------------------------------------------------------


@dataclass
class BossLoot:
    """The module value, ready to serialise, plus the counts and the per place notes."""

    strings: list[str] = field(default_factory=list)
    places: list[dict] = field(default_factory=list)
    bosses: list[dict] = field(default_factory=list)
    counts: dict[str, int] = field(default_factory=dict)
    dropped: dict[str, int] = field(default_factory=dict)
    # Per place, in draw order: (name, band, kind, lv, where lv came from, where hi came from).
    notes: list[dict] = field(default_factory=list)
    # (place, entry) for each Era encounter left out for having no creature and no loot.
    empty: list[tuple[str, str]] = field(default_factory=list)

    def module_value(self) -> dict:
        return {
            "v": CONTRACT_VERSION,
            "s": list(self.strings),
            "p": list(self.places),
            "b": list(self.bosses),
        }


@dataclass
class _Entry:
    """One boss, rare or chest before the strings are numbered."""

    name: str
    rank: int
    creatures: tuple[int, ...] = ()
    encounter: int = 0
    new: bool = False
    objects: tuple[int, ...] = ()
    lo: int = 0
    hi: int = 0
    loot: str = ""
    world: int = 0
    entries: int = 0
    era_name: int = 0
    # What the tab's creature panel draws without building EraSources: the CreatureDisplayInfo
    # id of the first creature in c whose model this build carries, and its CreatureType.
    display: int = 0
    creature_type: int = 0
    # The best quality among the shipped records, for the world boss and chest rules.
    best: int = 0


def spawn_maps(era_input: era_mod.EraInput) -> dict[int, frozenset[int]]:
    """creature id -> every map its always there spawns are on (the era_sources pin rules: an
    event only spawn is not a place it is found, a spawn with no id takes creature_spawn_entry's)."""
    maps: dict[int, set[int]] = defaultdict(set)
    for spawn in era_input.spawns:
        if spawn.event > 0:
            continue
        ids = (spawn.creature,) if spawn.creature else tuple(era_input.spawn_entries.get(spawn.guid, ()))
        for creature in ids:
            if creature:
                maps[creature].add(spawn.map)
    return {creature: frozenset(found) for creature, found in maps.items()}


def world_drop_items(era_input: era_mod.EraInput, loot: Mapping[int, Mapping[int, era_mod.Drop]]) -> set[int]:
    """Every item more than WORLD_DROP_CREATURES distinct creatures drop, over the whole table."""
    droppers: dict[int, int] = defaultdict(int)
    for creature in era_input.creatures.values():
        if not creature.loot or era_mod.is_scaffolding(creature.name):
            continue
        for item in loot.get(creature.loot, {}):
            droppers[item] += 1
    return {item for item, count in droppers.items() if count > era_mod.WORLD_DROP_CREATURES}


def _better(new: era_mod.Drop, old: era_mod.Drop | None) -> bool:
    """expand_loot's rule for one item reached twice: the unconditional drop, then the chance."""
    return old is None or (not new.quest_only, new.chance) > (not old.quest_only, old.chance)


class _Stage:
    """One run of the derivation. Holds the shared lookups so each rule stays short."""

    def __init__(
        self,
        era_input: era_mod.EraInput,
        facts: BossLootInput,
        target: ItemTable,
        base: ItemTable,
        era_table: era_mod.EraSources | None,
        withheld: Collection[int],
    ) -> None:
        self.era = era_input
        self.facts = facts
        self.target = target
        self.base = base
        self.withheld = frozenset(withheld)
        self.dropped: dict[str, int] = {
            "hidden": 0,
            "noItemRow": 0,
            "refLoop": 0,
            "scaffolding": 0,
            "sodEncounters": 0,
            "placesWithNoEntry": 0,
            "entriesWithNoLoot": 0,
            "emptyEraEncounters": 0,
        }
        # (place, entry) for every Era encounter dropped for having no creature and no loot.
        self.empty: list[tuple[str, str]] = []
        # One pass each over the dump. The world drop rule reads the creature loot whole.
        self.creature_loot = era_mod.expand_loot(
            era_input.creature_loot, era_input.reference_loot, self.dropped
        )
        self.object_loot = era_mod.expand_loot(era_input.object_loot, era_input.reference_loot, self.dropped)
        self.world = world_drop_items(era_input, self.creature_loot)
        self.maps = spawn_maps(era_input)
        # The name a creature page opens by, where EraSources carries a kind for it.
        self.era_names: dict[str, int] = {}
        if era_table is not None:
            for index, name in enumerate(era_table.strings, start=1):
                if index in era_table.kinds:
                    self.era_names[name] = index
        # Every creature CMaNGOS credits for any encounter kill.
        self.credited = {creature for found in facts.credits.values() for creature in found}
        self.used: set[int] = set()
        # Scaffolding names met, each counted once however often a rule looks at it.
        self.scaffolding: set[tuple[str, int]] = set()

    # ----- items ---------------------------------------------------------------------------

    def item(self, item: int) -> ItemFacts | None:
        """The item's facts where the item may ship: named by this build, or withheld and named
        by the baseline (the EraSources rule). Every refusal is counted."""
        found = self.target.items.get(item)
        if found is not None:
            return found
        if item in self.withheld:
            found = self.base.items.get(item)
            if found is not None:
                return found
        self.dropped["hidden" if item in self.target.undiscovered else "noItemRow"] += 1
        return None

    def loot_of(self, drops: Mapping[int, era_mod.Drop]) -> tuple[str, int, int, int]:
        """(packed records in draw order, world drops left out, records, best quality)."""
        records: list[tuple[tuple, str]] = []
        world = 0
        best = 0
        for item in sorted(drops):
            if item in self.world:
                world += 1
                continue
            facts = self.item(item)
            if facts is None:
                continue
            value = loot_value(drops[item])
            code = type_code(facts.class_id, facts.subclass_id, facts.inventory_type)
            level = max(0, int(facts.item_level or 0))
            chance = value % era_mod.PACK_QUEST_ONLY
            best = max(best, int(facts.quality or 0))
            order = (code, 1 if chance == 0 else 0, -chance, -level, item)
            records.append((order, pack_loot(value, item, code, level)))
        records.sort()
        return "".join(packed for _order, packed in records), world, len(records), best

    def creature_drops(self, creatures: Iterable[int]) -> dict[int, era_mod.Drop]:
        """The union of the creatures' loot, each item at its best drop."""
        out: dict[int, era_mod.Drop] = {}
        for cid in creatures:
            template = self.era.creatures[cid].loot
            for item, drop in self.creature_loot.get(template, {}).items():
                if _better(drop, out.get(item)):
                    out[item] = drop
        return out

    def object_drops(self, objects: Iterable[int]) -> dict[int, era_mod.Drop]:
        out: dict[int, era_mod.Drop] = {}
        for oid in objects:
            for item, drop in self.object_loot.get(self.era.objects[oid].loot, {}).items():
                if _better(drop, out.get(item)):
                    out[item] = drop
        return out

    # ----- entries -------------------------------------------------------------------------

    def creature_entry(self, name: str, rank: int, creatures: Sequence[int], **kwargs) -> _Entry:
        entry = _Entry(name=name, rank=rank, creatures=tuple(creatures), **kwargs)
        if creatures:
            facts = [self.era.creatures[cid] for cid in creatures]
            entry.lo = min(f.min_level for f in facts)
            entry.hi = max(f.max_level for f in facts)
            entry.loot, entry.world, entry.entries, entry.best = self.loot_of(self.creature_drops(creatures))
            for candidate in (name, *(f.name for f in facts)):
                if candidate in self.era_names:
                    entry.era_name = self.era_names[candidate]
                    break
            # EraSources' cd rule for the id (stated, and carried by this build's own
            # CreatureDisplayInfo), taken from the first creature in c that has one.
            for f in facts:
                if f.display > 0 and f.display in self.era.display_ids:
                    entry.display = f.display
                    break
            entry.creature_type = facts[0].creature_type
        return entry

    def lives_on(self, cid: int, map_id: int) -> bool:
        """Whether every always there spawn of the creature is on this one map."""
        return self.maps.get(cid) == frozenset({map_id})

    def usable(self, cid: int) -> bool:
        facts = self.era.creatures.get(cid)
        if facts is None or cid in self.used:
            return False
        if era_mod.is_scaffolding(facts.name):
            self.refuse_scaffolding("creature", cid)
            return False
        return True

    def refuse_scaffolding(self, kind: str, key: int) -> None:
        if (kind, key) not in self.scaffolding:
            self.scaffolding.add((kind, key))
            self.dropped["scaffolding"] += 1

    def encounter_creatures(self, encounter: EncounterFacts, *, loose: bool = False) -> list[int]:
        """The encounter's creatures: CMaNGOS's credit where it holds for this map, otherwise the
        creatures of the same name that live only on this map (or credited ones with no spawn at
        all, which is how a boss that is summoned mid fight reads). `loose` is the second pass,
        for the encounters the first found nothing for: the same, by loosely_named."""
        wanted = normalise(encounter.name)
        if not loose:
            credited = [
                cid
                for cid in self.facts.credits.get(encounter.id, ())
                if self.usable(cid)
                and (self.lives_on(cid, encounter.map) or normalise(self.era.creatures[cid].name) == wanted)
            ]
            if credited:
                return sorted(set(credited))
        named = [
            cid
            for cid in sorted(self.era.creatures)
            if cid not in self.used
            and (self.lives_on(cid, encounter.map) or (cid in self.credited and cid not in self.maps))
            and (
                loosely_named(encounter.name, self.era.creatures[cid].name)
                if loose
                else normalise(self.era.creatures[cid].name) == wanted
            )
        ]
        return [cid for cid in named if self.usable(cid)]

    def place_entries(self, map_id: int, encounters: Sequence[EncounterFacts]) -> list[_Entry]:
        """A place's bosses, rares and chests, in draw order."""
        kept: list[EncounterFacts] = []
        seen: set[str] = set()
        for encounter in encounters:
            key = normalise(encounter.name)
            if key not in seen:
                seen.add(key)
                kept.append(encounter)
        # Two passes, so a loose match never takes a creature a later encounter names exactly.
        found: dict[int, list[int]] = {}
        for encounter in kept:
            found[encounter.id] = self.encounter_creatures(encounter)
            self.used.update(found[encounter.id])
        for encounter in kept:
            if not found[encounter.id]:
                found[encounter.id] = self.encounter_creatures(encounter, loose=True)
                self.used.update(found[encounter.id])
        entries: list[_Entry] = []
        for encounter in kept:
            creatures = found[encounter.id]
            new = encounter.id not in self.facts.baseline_encounters and not creatures
            entries.append(
                self.creature_entry(encounter.name, RANK_BOSS, creatures, encounter=encounter.id, new=new)
            )

        # The creatures CMaNGOS credits for an encounter kill that no kept encounter took, where
        # they live only here (Gnomeregan: this build lists its encounters under Season of
        # Discovery difficulties alone), then the rank 3 creatures that live only here.
        credited_here = sorted(
            {
                cid
                for entry_id in sorted(self.facts.credits)
                for cid in self.facts.credits[entry_id]
                if self.lives_on(cid, map_id) and cid not in self.used
            },
            key=lambda cid: (min(e for e, found in self.facts.credits.items() if cid in found), cid),
        )
        entries.extend(self._grouped(credited_here, RANK_BOSS))
        bosses = sorted(
            (
                cid
                for cid, facts in self.era.creatures.items()
                if facts.rank == CMANGOS_BOSS and self.lives_on(cid, map_id) and cid not in self.used
            ),
            key=self._level_name,
        )
        entries.extend(self._grouped(bosses, RANK_BOSS))
        rares = sorted(
            (
                cid
                for cid, facts in self.era.creatures.items()
                if facts.rank in RARE_RANKS and self.lives_on(cid, map_id) and cid not in self.used
            ),
            key=self._level_name,
        )
        by_rank: list[_Entry] = []
        for rank in sorted(RARE_RANKS):
            by_rank.extend(
                self._grouped(
                    [cid for cid in rares if self.era.creatures[cid].rank == rank], RARE_RANKS[rank]
                )
            )
        by_rank.sort(key=lambda entry: (entry.lo, entry.name.lower(), entry.rank))
        entries.extend(by_rank)
        entries.extend(self.chests(map_id))
        return entries

    def _level_name(self, cid: int) -> tuple:
        facts = self.era.creatures[cid]
        return (facts.min_level, facts.name.lower(), cid)

    def _grouped(self, creatures: Sequence[int], rank: int) -> list[_Entry]:
        """One entry per name, in the order the names are first met, loot not empty."""
        by_name: dict[str, list[int]] = {}
        for cid in creatures:
            if not self.usable(cid):
                continue
            by_name.setdefault(self.era.creatures[cid].name, []).append(cid)
        out: list[_Entry] = []
        for name, found in by_name.items():
            entry = self.creature_entry(name, rank, found)
            self.used.update(found)
            if not entry.loot:
                self.dropped["entriesWithNoLoot"] += 1
                continue
            out.append(entry)
        return out

    def chests(self, map_id: int) -> list[_Entry]:
        """Ruling 3: an object that stands only on this map and holds at least one rare item."""
        by_name: dict[str, list[int]] = defaultdict(list)
        for oid in sorted(self.era.objects):
            obj = self.era.objects[oid]
            if obj.kind != era_mod.GO_TYPE_CHEST or not obj.loot:
                continue
            if tuple(self.era.object_spawn_maps.get(oid, ())) != (map_id,):
                continue
            if era_mod.is_scaffolding(obj.name):
                self.refuse_scaffolding("object", oid)
                continue
            by_name[obj.name].append(oid)
        out: list[_Entry] = []
        for name in sorted(by_name, key=lambda text: (text.lower(), text)):
            objects = tuple(by_name[name])
            packed, world, count, best = self.loot_of(self.object_drops(objects))
            if not packed or best < NOTABLE_QUALITY:
                continue
            out.append(
                _Entry(name=name, rank=RANK_CHEST, objects=objects, loot=packed, world=world, entries=count)
            )
        return out

    def zone_continents(self, cid: int) -> frozenset[int]:
        """The maps pfQuest's zones for a creature lie on, for one the dump spawns nowhere (the
        four dragons of the Emerald Dream are spawned by script): this build's own AreaTable
        says which continent each area is on. Empty where any zone is unknown."""
        zones = self.era.unit_zones.get(cid, ())
        if not zones or any(area not in self.facts.areas for area in zones):
            return frozenset()
        return frozenset(self.facts.areas[area].continent for area in zones)

    def world_bosses(self) -> list[tuple[_Entry, list[int]]]:
        """Rank 3 creatures that stand only on the two continents and drop something rare."""
        by_name: dict[str, list[int]] = defaultdict(list)
        for cid in sorted(self.era.creatures):
            facts = self.era.creatures[cid]
            where = self.maps.get(cid) or self.zone_continents(cid)
            if facts.rank != CMANGOS_BOSS or not where or not where <= CONTINENT_MAPS:
                continue
            if cid in self.used or era_mod.is_scaffolding(facts.name):
                continue
            by_name[facts.name].append(cid)
        out: list[tuple[_Entry, list[int]]] = []
        for name in sorted(by_name):
            found = by_name[name]
            entry = self.creature_entry(name, RANK_BOSS, found)
            if not entry.loot or entry.best < NOTABLE_QUALITY:
                continue
            self.used.update(found)
            zones: list[int] = []
            for cid in found:
                for area in self.era.unit_zones.get(cid, ()):
                    if area in self.era.areas and area not in zones:
                        zones.append(area)
            out.append((entry, zones))
        return out


def _place_levels(
    stage: _Stage, map_facts: MapFacts, entries: Sequence[_Entry]
) -> tuple[int | None, int | None, str, str]:
    """(lo, hi, where lo came from, where hi came from), by the plan's fallbacks in order: the
    LFGDungeons entry of the same name, the map area's own ContentTuning, the bosses' levels."""
    facts = stage.facts
    candidates: list[tuple[str, tuple[int, int]]] = []
    exact = [
        d
        for d in facts.dungeons
        if d.type_id == LFG_TYPE_DUNGEON and normalise(d.name) == normalise(map_facts.name)
    ]
    loose = [
        d for d in facts.dungeons if d.type_id == LFG_TYPE_DUNGEON and names_match(map_facts.name, d.name)
    ]
    lfg_levels: list[tuple[int, int]] = []
    for dungeon in exact or loose:
        if dungeon.min_level > 0:
            lfg_levels.append((dungeon.min_level, max(dungeon.min_level, dungeon.max_level)))
            continue
        tuning = facts.tuning.get(dungeon.tuning)
        found = tuning.levels() if tuning is not None else None
        if found is not None:
            lfg_levels.append(found)
    if lfg_levels:
        candidates.append(("lfg", (min(lo for lo, _hi in lfg_levels), max(hi for _lo, hi in lfg_levels))))
    area = _map_area(facts, map_facts)
    if area is not None:
        tuning = facts.tuning.get(area.tuning)
        found = tuning.levels() if tuning is not None else None
        if found is not None:
            candidates.append(("area", found))
    levelled = [e for e in entries if e.creatures and e.rank == RANK_BOSS] or [
        e for e in entries if e.creatures
    ]
    if levelled:
        candidates.append(("bosses", (min(e.lo for e in levelled), max(e.hi for e in levelled))))
    if not candidates:
        return None, None, "", ""
    lo_from, (lo, hi) = candidates[0]
    hi_from = lo_from
    if hi <= lo:
        # A source that states one level says nothing about the top of the range, so the next
        # source that states a wider one gives it (Deadmines: 16 from LFG, 21 from its bosses).
        for source, (_low, high) in candidates[1:]:
            if high > lo:
                hi, hi_from = high, source
                break
    return lo, max(lo, hi), lo_from, hi_from


def _map_area(facts: BossLootInput, map_facts: MapFacts) -> AreaFacts | None:
    """The map's own area: Map.AreaTableID, or the one parentless area on the map."""
    area = facts.areas.get(map_facts.area)
    if area is not None:
        return area
    roots = [a for a in facts.areas.values() if a.continent == map_facts.id and not a.parent]
    return roots[0] if len(roots) == 1 else None


def _zone_name(facts: BossLootInput, map_facts: MapFacts, area_id: int, era_areas: Mapping[int, str]) -> str:
    """The AreaTable name the client is likely to report inside the place, when it is not the
    map's own name: the instance area EraSources uses, or else the one parentless area of the
    map whose name matches the map's (The Deadmines, whose map names five parentless areas)."""
    name = era_areas.get(area_id, "")
    if not name:
        wanted = normalise(map_facts.name)
        found = [
            a.name
            for a in sorted(facts.areas.values(), key=lambda a: a.id)
            if a.continent == map_facts.id and not a.parent and normalise(a.name) == wanted
        ]
        name = found[0] if len(found) == 1 else ""
    return name if name and name != map_facts.name else ""


def _clamp(level: int | None) -> int | None:
    if level is None or level <= 0:
        return None
    return min(MAX_PLAYER_LEVEL, level)


def derive(
    era_input: era_mod.EraInput,
    facts: BossLootInput,
    target: ItemTable,
    base: ItemTable,
    era_table: era_mod.EraSources | None = None,
    *,
    withheld: Collection[int] = (),
) -> BossLoot:
    """Build the module value. `withheld` is the hidden ids the baseline named (EraSources' own
    rule): their records ship and the addon unlocks them. Every other refusal is counted."""
    stage = _Stage(era_input, facts, target, base, era_table, withheld)
    maps = {map_id: m for map_id, m in facts.maps.items() if m.instance_type in INSTANCE_KINDS}
    encounters: dict[int, list[EncounterFacts]] = defaultdict(list)
    for encounter in sorted(facts.encounters, key=lambda e: (e.map, e.order, e.id)):
        if encounter.map not in maps:
            continue
        if encounter.difficulty not in PLAIN_DIFFICULTIES:
            stage.dropped["sodEncounters"] += 1
            continue
        encounters[encounter.map].append(encounter)
    lfg_named = {
        map_id
        for map_id, m in maps.items()
        if any(d.type_id == LFG_TYPE_DUNGEON and names_match(m.name, d.name) for d in facts.dungeons)
    }

    # Places, each with its entries. World bosses first, so a rank 3 creature that stands on a
    # continent never becomes a boss of an instance it has no spawn in.
    raw: list[tuple[dict, list[_Entry], dict]] = []
    for entry, zones in stage.world_bosses():
        lv = _clamp(entry.lo)
        place = {
            "name": entry.name,
            "k": KIND_WORLD_BOSS,
            "lv": lv,
            "lo": lv,
            "hi": _clamp(entry.hi),
            "zones": zones,
        }
        raw.append((place, [entry], {"lv": "boss" if lv else "", "hi": "boss" if lv else ""}))
    for map_id in sorted(maps):
        m = maps[map_id]
        new = map_id not in facts.baseline_maps
        entries = stage.place_entries(map_id, encounters.get(map_id, ()))
        spawned = any(e.creatures and e.loot for e in entries)
        if not (map_id in lfg_named or spawned or (new and encounters.get(map_id))):
            continue
        if not new:
            # An Era place's encounter with no creature and no loot says nothing a player can
            # use ("The Molten Core", "Ring of Law", "The Four Horsemen", whose chest is its own
            # entry). A place new in Forever keeps its encounters with nothing known (owner's
            # answer a): the collector is what fills them. Counted for listed places only.
            for entry in entries:
                if not entry.creatures and not entry.loot:
                    stage.dropped["emptyEraEncounters"] += 1
                    stage.empty.append((m.name, entry.name))
            entries = [entry for entry in entries if entry.creatures or entry.loot]
        if not entries:
            stage.dropped["placesWithNoEntry"] += 1
            continue
        lo, hi, lo_from, hi_from = _place_levels(stage, m, entries)
        area = era_input.instance_areas.get(map_id, 0)
        place = {
            "name": m.name,
            "k": INSTANCE_KINDS[m.instance_type],
            "lv": _clamp(lo),
            "lo": _clamp(lo),
            "hi": _clamp(hi),
            "m": map_id,
            "a": area or None,
            "an": _zone_name(facts, m, area, era_input.areas),
            "sz": m.max_players or None,
            "g": 1 if new else None,
        }
        raw.append((place, entries, {"lv": lo_from, "hi": hi_from}))

    raw.sort(
        key=lambda item: (band(item[0]["lv"]), item[0]["lv"] or 0, item[0]["k"], item[0]["name"].lower())
    )

    strings: set[str] = set()
    for place, entries, _notes in raw:
        strings.add(place["name"])
        if place.get("an"):
            strings.add(place["an"])
        strings.update(era_input.areas[zone] for zone in place.get("zones", ()))
        strings.update(entry.name for entry in entries)
    table = sorted(strings)
    index = {value: position for position, value in enumerate(table, start=1)}

    places: list[dict] = []
    bosses: list[dict] = []
    notes: list[dict] = []
    for place, entries, how in raw:
        numbers: list[int] = []
        for entry in entries:
            bosses.append(
                {
                    "n": index[entry.name],
                    "r": entry.rank,
                    "lo": entry.lo or None,
                    "hi": entry.hi or None,
                    "e": entry.era_name or None,
                    "cd": entry.display or None,
                    "ct": entry.creature_type or None,
                    "c": list(entry.creatures) or None,
                    "d": entry.encounter or None,
                    "g": 1 if entry.new else None,
                    "w": entry.world or None,
                    "l": entry.loot or None,
                }
            )
            numbers.append(len(bosses))
        out = {
            "n": index[place["name"]],
            "k": place["k"],
            "lv": place["lv"],
            "lo": place["lo"],
            "hi": place["hi"],
            "m": place.get("m"),
            "a": place.get("a"),
            "an": index[place["an"]] if place.get("an") else None,
            "z": [index[era_input.areas[zone]] for zone in place["zones"]] if place.get("zones") else None,
            "sz": place.get("sz"),
            "g": place.get("g"),
            "b": numbers,
        }
        places.append({key: value for key, value in out.items() if value is not None})
        notes.append(
            {
                "name": place["name"],
                "band": band(place["lv"]),
                "kind": place["k"],
                "lv": place["lv"],
                "lo": place["lo"],
                "hi": place["hi"],
                "lvFrom": how["lv"],
                "hiFrom": how["hi"],
                "new": bool(place.get("g")),
                "bosses": len(entries),
            }
        )
    bosses = [{key: value for key, value in boss.items() if value is not None} for boss in bosses]

    counts = {
        "places": len(places),
        "dungeons": sum(1 for p in places if p["k"] == KIND_DUNGEON),
        "raids": sum(1 for p in places if p["k"] == KIND_RAID),
        "worldBosses": sum(1 for p in places if p["k"] == KIND_WORLD_BOSS),
        "newPlaces": sum(1 for p in places if p.get("g")),
        "entries": len(bosses),
        "bosses": sum(1 for b in bosses if b["r"] == RANK_BOSS),
        "rareElites": sum(1 for b in bosses if b["r"] == RANK_RARE_ELITE),
        "rares": sum(1 for b in bosses if b["r"] == RANK_RARE),
        "chests": sum(1 for b in bosses if b["r"] == RANK_CHEST),
        "newBosses": sum(1 for b in bosses if b.get("g")),
        "bossesWithNoLoot": sum(1 for b in bosses if "l" not in b),
        "withCreaturePage": sum(1 for b in bosses if "e" in b),
        "withDisplay": sum(1 for b in bosses if "cd" in b),
        "withCreatureType": sum(1 for b in bosses if "ct" in b),
        "lootEntries": sum(len(b.get("l", "")) // RECORD_BYTES for b in bosses),
        "worldDropsLeftOut": sum(b.get("w", 0) for b in bosses),
        "strings": len(table),
    }
    return BossLoot(
        strings=table,
        places=places,
        bosses=bosses,
        counts=counts,
        dropped=stage.dropped,
        notes=notes,
        empty=stage.empty,
    )


# ----- the header the module carries -------------------------------------------------------------

CREDIT = (
    "Historical Classic Era boss loot, derived from the CMaNGOS Classic content database "
    "(github.com/cmangos/classic-db), which the MaNGOS community compiled for World of Warcraft "
    "patch 1.12. Drop chances are that database's own loot table figures. World boss zones come "
    "from pfQuest's vanilla database (github.com/shagu/pfQuest), which contributes the area id and "
    "nothing else. Places, encounters and their levels are this build's own client tables. WoW "
    "Forever may differ; the addon shows these as predicted."
)

LICENCE_NOTE = (
    "This generated file is distributed under the GNU General Public License version 3, the "
    "licence of the CMaNGOS Classic content database it derives from "
    "(github.com/cmangos/classic-db), as EraSources.lua is. The rest of ItemTree, those two files "
    "apart, is all rights reserved. "
    f"Corresponding Source, as GPL-3.0 section 6(d) asks: {era_mod.CORRESPONDING_SOURCE_URL} "
    "(the compilers, the pinned inputs and these notices)."
)


def licence_lines() -> list[str]:
    """The licence part of the header: the reading, the upstream notices, section 5(a)."""
    return [
        LICENCE_NOTE,
        era_mod.UPSTREAM_CMANGOS,
        era_mod.CMANGOS_COPYRIGHT,
        era_mod.UPSTREAM_PFQUEST,
        era_mod.MODIFICATION_NOTICE,
        era_mod.LICENCE_FILES,
    ]


def header_lines(table: BossLoot) -> list[str]:
    """The field legend, the credit and the licence note, in the module's header comment."""
    counts = table.counts
    codes = ", ".join(f"{code} {word}" for code, word in TYPE_WORDS.items())
    return [
        "The Boss loot index. docs/boss-loot.md in the pipeline is the contract.",
        f"{{ v = {CONTRACT_VERSION}, s = {{strings}}, p = {{places, in draw order}}, "
        "b = {bosses, rares and chests} }. v is the contract version; refuse any other.",
        "p = { n name (index into s), k kind (1 dungeon, 2 raid, 3 world boss), lv the level the "
        f"band is read from (1 to {MAX_PLAYER_LEVEL}), lo/hi the level range, m Map id, a the area "
        "id EraSources uses, an the AreaTable name where it differs from n, z (k=3) the zones, "
        "sz players, g 1 = new in Forever, b = {indices into b, in draw order} }. Places are in "
        "draw order: band (ceil(lv / 10), no lv last), then lv, then k, then name.",
        "b = { n name, r rank (1 boss, 2 rare elite, 3 rare, 4 chest), lo/hi creature levels, "
        "e the EraSources s index of the name (opens npc: .. -e), cd the CreatureDisplayInfo id of the "
        "first creature in c this build has a model for, ct its CreatureType, c creature ids, "
        "d DungeonEncounter "
        "id, g 1 = an encounter new in Forever with no CMaNGOS creature, w world drops left out, "
        "l loot }. Every key but n and r is optional. Bosses first (encounter order), then "
        "rares by level and name, then chests by name.",
        f"l: fixed {RECORD_BYTES} byte records in the EraSources xl alphabet (base "
        f"{era_mod.PACK_BASE}, bytes {era_mod.PACK_FIRST} to 126 without {era_mod.PACK_SKIPPED}, "
        f"most significant first): item id ({RECORD_ITEM_DIGITS}), value ({RECORD_VALUE_DIGITS}: "
        f"the chance in tenths of a percent, plus {era_mod.PACK_QUEST_ONLY} where quest only, 0 "
        f"= no chance stated), type ({RECORD_TYPE_DIGITS}), item level ({RECORD_LEVEL_DIGITS}, 0 = "
        "unknown). In draw order: type, then chance descending with none last, then item level "
        "descending, then id.",
        f"Types: {codes}.",
        f"An item more than {era_mod.WORLD_DROP_CREATURES} creatures drop is a world drop: left "
        "out, counted in w.",
        CREDIT,
        *licence_lines(),
        f"{counts.get('places', 0)} places ({counts.get('dungeons', 0)} dungeons, "
        f"{counts.get('raids', 0)} raids, {counts.get('worldBosses', 0)} world bosses, "
        f"{counts.get('newPlaces', 0)} new in Forever), {counts.get('entries', 0)} entries "
        f"({counts.get('bosses', 0)} bosses, {counts.get('rareElites', 0)} rare elites, "
        f"{counts.get('rares', 0)} rares, {counts.get('chests', 0)} chests), "
        f"{counts.get('lootEntries', 0)} loot records.",
    ]


# ----- reading the client tables and the credits ------------------------------------------------


INSTANCE_ENCOUNTERS = "INSERT INTO `instance_encounters` VALUES "


def read_credits(path: Path) -> dict[int, tuple[int, ...]]:
    """CMaNGOS instance_encounters: DungeonEncounter id -> the creatures credited for its kill.

    The same rows guesses/pipeline.py reads, read afresh here (entry, creditType, creditEntry):
    only creditType 0, a creature kill, is kept.
    """
    found: dict[int, set[int]] = defaultdict(set)
    try:
        handle = gzip.open(path, "rt", encoding="utf-8", errors="replace")
    except OSError as exc:
        raise BossLootError(f"cannot read {path}: {exc}") from exc
    with handle:
        for line in handle:
            if not line.startswith(INSTANCE_ENCOUNTERS):
                continue
            for row in era_mod.split_values(line, len(INSTANCE_ENCOUNTERS)):
                if len(row) < 3:
                    continue
                try:
                    entry, kind, creature = int(row[0]), int(row[1]), int(row[2])
                except ValueError:
                    continue
                if kind == CREDIT_KILL and entry > 0 and creature > 0:
                    found[entry].add(creature)
    return {entry: tuple(sorted(creatures)) for entry, creatures in sorted(found.items())}


def _rows(conn: sqlite3.Connection, build: str, table: str, columns: str) -> list[sqlite3.Row]:
    try:
        cursor = conn.execute(f"SELECT {columns} FROM {table} WHERE build_id = ?", (build,))
    except sqlite3.OperationalError as exc:
        raise BossLootError(
            f"build {build} has no {table} loaded ({exc}); run "
            f"`itemtree-data fetch {build} -t {table}` then `itemtree-data load {build} -t {table}`"
        ) from exc
    return cursor.fetchall()


def _int(value) -> int:
    try:
        return int(value or 0)
    except (TypeError, ValueError):
        return 0


def gather_input(conn: sqlite3.Connection, build: str, baseline: str, *, cmangos_path: Path) -> BossLootInput:
    """Read the client tables of both builds and the credits. Everything here is I/O."""
    maps = {
        _int(row["ID"]): MapFacts(
            id=_int(row["ID"]),
            name=str(row["MapName_lang"] or ""),
            instance_type=_int(row["InstanceType"]),
            max_players=_int(row["MaxPlayers"]),
            area=_int(row["AreaTableID"]),
        )
        for row in _rows(conn, build, "Map", "ID, MapName_lang, InstanceType, MaxPlayers, AreaTableID")
    }
    baseline_maps = frozenset(_int(row["ID"]) for row in _rows(conn, baseline, "Map", "ID"))
    encounters = [
        EncounterFacts(
            id=_int(row["ID"]),
            name=str(row["Name_lang"] or ""),
            map=_int(row["MapID"]),
            difficulty=_int(row["DifficultyID"]),
            order=_int(row["OrderIndex"]),
        )
        for row in _rows(conn, build, "DungeonEncounter", "ID, Name_lang, MapID, DifficultyID, OrderIndex")
    ]
    baseline_encounters = frozenset(
        _int(row["ID"]) for row in _rows(conn, baseline, "DungeonEncounter", "ID")
    )
    dungeons = [
        DungeonFacts(
            id=_int(row["ID"]),
            name=str(row["Name_lang"] or ""),
            type_id=_int(row["TypeID"]),
            min_level=_int(row["MinLevel"]),
            max_level=_int(row["MaxLevel"]),
            tuning=_int(row["ContentTuningID"]),
        )
        for row in _rows(
            conn, build, "LFGDungeons", "ID, Name_lang, TypeID, MinLevel, MaxLevel, ContentTuningID"
        )
    ]
    tuning = {
        _int(row["ID"]): TuningFacts(
            id=_int(row["ID"]),
            min_level=_int(row["MinLevelSquish"]),
            max_level=_int(row["MaxLevelSquish"]),
            lfg_min=_int(row["LfgMinLevel"]),
            lfg_max=_int(row["LfgMaxLevel"]),
        )
        for row in _rows(
            conn, build, "ContentTuning", "ID, MinLevelSquish, MaxLevelSquish, LfgMinLevel, LfgMaxLevel"
        )
    }
    areas = {
        _int(row["ID"]): AreaFacts(
            id=_int(row["ID"]),
            name=str(row["AreaName_lang"] or ""),
            continent=_int(row["ContinentID"]),
            parent=_int(row["ParentAreaID"]),
            tuning=_int(row["ContentTuningID"]),
        )
        for row in _rows(
            conn, build, "AreaTable", "ID, AreaName_lang, ContinentID, ParentAreaID, ContentTuningID"
        )
    }
    for name, found in (("Map", maps), ("DungeonEncounter", encounters)):
        if not found:
            raise BossLootError(
                f"build {build} has no {name} rows; run `itemtree-data fetch {build} -t {name}` "
                f"then `itemtree-data load {build} -t {name}`"
            )
    return BossLootInput(
        maps=maps,
        baseline_maps=baseline_maps,
        encounters=encounters,
        baseline_encounters=baseline_encounters,
        dungeons=dungeons,
        tuning=tuning,
        areas=areas,
        credits=read_credits(cmangos_path),
    )
