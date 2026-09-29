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
import json
import math
import re
import sqlite3
import unicodedata
from collections import defaultdict
from collections.abc import Collection, Iterable, Mapping, Sequence
from dataclasses import dataclass, field
from pathlib import Path
from typing import Protocol

from itemtree_data import creaturecache as cache_mod
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
# The UiMap types the location chain reads, as the client's Enum.UIMapType names them: a
# continent (2), a zone (3), a dungeon (4) and an orphan (6).
UI_MAP_CONTINENT = 2
UI_MAP_ZONE = 3
UI_MAP_DUNGEON = 4
UI_MAP_ORPHAN = 6
# Where a place is, as words (brief BL13a): the source each place's ez and ec came from.
WHERE_UI_MAP = "a"
WHERE_ENTRANCE = "b"
WHERE_AREA = "c"
WHERE_NONE = ""
# The entrance position's tie break: how many of pfQuest's nearest zoned spawns vote.
NEAREST_SPAWNS = 9
# pfQuest lists a spawn it cannot place in one zone in both (every creature of Blackrock
# Mountain is in Searing Gorge AND Burning Steppes), and the two copies land within a yard or
# two of each other. A spawn with another zone's spawn this close says nothing and is dropped.
SHARED_SPAWN_YARDS = 4.0
# A same name outdoor area is matched only where the shorter of the two names is this long, so
# "The Den" never names Starfall Barrow Den and "The Maul" is not read as Dire Maul.
NAMESAKE_MIN_CHARS = 6
# The entrance pin (brief W16): a position on a zone map in tenths of a percent, 0 to this.
ENTRANCE_SCALE = 1000
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


def folded(name: str) -> str:
    """A name with its diacritics dropped and its curly apostrophes made straight, so that
    "Rath’mäel" and "Rath'mael" normalise alike."""
    text = unicodedata.normalize("NFKD", name)
    text = "".join(ch for ch in text if not unicodedata.combining(ch))
    return text.replace("\u2019", "'").replace("\u2018", "'").replace("`", "'")


def _kill_form(text: str) -> str | None:
    """The name a "Kill <name>" text names, or None where the text does not read that way."""
    text = folded(text).strip()
    return text[5:] if text.casefold().startswith("kill ") else None


def criteria_key(text: str) -> str:
    """The matching key of an achievement text or an encounter name: folded, "Kill " dropped
    from the front, then normalise (so "Kill Rathmael" and "Rath'mael" meet)."""
    killed = _kill_form(text)
    return normalise(killed if killed is not None else folded(text))


def criteria_index(criteria: Iterable[KillCriterion]) -> dict[str, frozenset[int]]:
    """Matching key -> every creature a kill criterion names under it. A criterion's own tree
    texts count as the name or "Kill <name>"; a parent's text counts only in the "Kill" form,
    since a parent is otherwise an achievement or a place ("Novice Spelunker")."""
    found: dict[str, set[int]] = defaultdict(set)
    for criterion in criteria:
        if criterion.creature <= 0:
            continue
        keys = {criteria_key(text) for text in criterion.texts}
        keys.update(normalise(killed) for text in criterion.parents if (killed := _kill_form(text)))
        for key in keys - {""}:
            found[key].add(criterion.creature)
    return {key: frozenset(ids) for key, ids in found.items()}


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
    # Where a ghost is put back when it releases, which is outside the entrance: the continent
    # map (-1 for none) and the world position on it (0, 0 where the row states none).
    corpse_map: int = -1
    corpse_x: float = 0.0
    corpse_y: float = 0.0
    # The map the world map draws this one under (-1 for none), which on this build is the
    # continent for three places new in Forever.
    cosmetic_parent: int = -1


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


@dataclass(frozen=True)
class UiMapFacts:
    """One `UiMap` row: its localised name, its parent map and its type."""

    id: int
    name: str
    parent: int = 0
    type: int = 0


@dataclass(frozen=True)
class Location:
    """Where a place is, as words: its entrance zone, its continent and the source (a, b, c or
    none) they came from. Either name may be empty."""

    zone: str = ""
    continent: str = ""
    source: str = WHERE_NONE


@dataclass(frozen=True)
class NewBossRow:
    """One row of curated/new_bosses.json that passed its checks: a community named creature
    for an encounter new in Forever, with the pages it rests on."""

    encounter: int
    name: str
    creature: int
    display: int = 0
    sources: tuple[tuple[str, str], ...] = ()


@dataclass(frozen=True)
class KillCriterion:
    """One `Criteria` row of Type 0 (kill a creature, `Asset` the creature id) with the
    `Description_lang` of each `CriteriaTree` row that holds it (`texts`) and of each such
    row's parent (`parents`): "Shade of the Archmage" under "Kill Shade of the Archmage"."""

    id: int
    creature: int
    texts: tuple[str, ...] = ()
    parents: tuple[str, ...] = ()


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
    # The UiMap chain (brief BL13a, source a): every UiMap row, and (UiMap id, map id) for every
    # UiMapAssignment row, which is what ties a UiMap to the map it draws.
    ui_maps: dict[int, UiMapFacts] = field(default_factory=dict)
    ui_map_assignments: tuple[tuple[int, int], ...] = ()
    # The client's creature cache (brief BL15a): every creature a player has seen, merged from
    # the client's own file and the testers' files, and how many files were read.
    cached_creatures: dict[int, cache_mod.CachedCreature] = field(default_factory=dict)
    cache_files: int = 0
    # The build's own encounter models, where a table states them: encounter id -> (display id,
    # creature id or 0), and the source that answered ("" for none).
    client_models: dict[int, tuple[int, int]] = field(default_factory=dict)
    client_source: str = ""
    # The build's achievement kill criteria (Criteria Type 0 with their CriteriaTree texts),
    # the client's own word on which creature a name is.
    kill_criteria: list[KillCriterion] = field(default_factory=list)
    # curated/new_bosses.json, the rows that passed: encounter id -> the row.
    curated_bosses: dict[int, NewBossRow] = field(default_factory=dict)
    # Every cache file left out, cache disagreement and curated row refused, for the summary.
    notes: list[str] = field(default_factory=list)


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
    # Per new encounter named, in draw order: {encounter, name, creature, provenance}.
    naming: list[dict] = field(default_factory=list)
    # Criteria conflicts and curated rows refused while naming, for the summary.
    naming_notes: list[str] = field(default_factory=list)

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
        # pfQuest's zoned spawns as world positions, built the first time a tie needs them.
        self.points: list[tuple[int, float, float, int]] | None = None
        # The creatures the cache or the curated file gave a new encounter, and how many each.
        self.cache_used: set[int] = set()
        self.named: dict[str, int] = {
            "namedByClient": 0,
            "modelsByClient": 0,
            "namedByCriteria": 0,
            "namedByCache": 0,
            "namedByCurated": 0,
            "criteriaConflicts": 0,
        }
        self.criteria = criteria_index(facts.kill_criteria)
        # Which input named each new encounter, and what naming refused, for the summary.
        self.naming: list[dict] = []
        self.naming_notes: list[str] = []

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

    def cached_display(self, cid: int) -> int:
        """The first display id the client cached for the creature that this build carries."""
        found = self.facts.cached_creatures.get(cid)
        for display in found.displays if found else ():
            if display > 0 and display in self.era.display_ids:
                return display
        return 0

    def cached_named(self, name: str) -> cache_mod.CachedCreature | None:
        """The cached creature an encounter names: exactly, then case folded; the lowest entry
        id where several share the name. A creature the dump knows, or one already taken, is
        never offered: the index already has it."""
        offered = [
            c
            for cid, c in sorted(self.facts.cached_creatures.items())
            if cid not in self.era.creatures and cid not in self.cache_used
        ]
        for same in (lambda c: c.name == name, lambda c: c.name.casefold() == name.casefold()):
            for creature in offered:
                if same(creature):
                    return creature
        return None

    def name_new_boss(self, entry: _Entry) -> None:
        """c, cd and ct for an encounter new in Forever that nothing else named: the build's own
        encounter models first (cd, and c where the table gives a creature), then the client's
        the build's achievement kill criteria, then the creature cache, then
        curated/new_bosses.json. The entry stays new (g = 1)."""
        display, creature = self.facts.client_models.get(entry.encounter, (0, 0))
        display = display if display in self.era.display_ids else 0
        if creature > 0 and creature not in self.era.creatures and creature not in self.cache_used:
            self.cache_used.add(creature)
            entry.creatures = (creature,)
            seen = self.facts.cached_creatures.get(creature)
            entry.creature_type = seen.creature_type if seen else 0
            entry.display = display or self.cached_display(creature)
            self.named["namedByClient"] += 1
            self._record(entry, PROVENANCE_CLIENT)
            return
        if display:
            self.named["modelsByClient"] += 1
        if not self._name_from_criteria(entry):
            self._name_from_cache_or_curated(entry)
        if display:
            entry.display = display

    def _record(self, entry: _Entry, provenance: str) -> None:
        self.naming.append(
            {
                "encounter": entry.encounter,
                "name": entry.name,
                "creature": entry.creatures[0],
                "provenance": provenance,
            }
        )

    def _name_from_criteria(self, entry: _Entry) -> bool:
        """The creature a kill criterion names under the encounter's name, where exactly one
        does. Two or more is a conflict: none is taken, and the summary lists it."""
        found = self.criteria.get(criteria_key(entry.name), frozenset())
        if len(found) > 1:
            self.named["criteriaConflicts"] += 1
            ids = ", ".join(str(cid) for cid in sorted(found))
            self.naming_notes.append(
                f"criteria conflict: encounter {entry.encounter} ({entry.name}) is named by "
                f"creatures {ids}; none taken"
            )
            return False
        if not found:
            return False
        (creature,) = found
        if creature in self.era.creatures or creature in self.cache_used:
            return False
        self.cache_used.add(creature)
        entry.creatures = (creature,)
        entry.display = self.cached_display(creature)
        seen = self.facts.cached_creatures.get(creature)
        entry.creature_type = seen.creature_type if seen else 0
        row = self.facts.curated_bosses.get(entry.encounter)
        if row is not None and row.creature != creature:
            self.naming_notes.append(
                f"new bosses: encounter {entry.encounter} ({entry.name}): the row names creature "
                f"{row.creature}, the client's achievement criteria {creature}; the row is refused"
            )
        elif row is not None and not entry.display and row.display in self.era.display_ids:
            entry.display = row.display
        self.named["namedByCriteria"] += 1
        self._record(entry, PROVENANCE_CRITERIA)
        return True

    def _name_from_cache_or_curated(self, entry: _Entry) -> None:
        cached = self.cached_named(entry.name)
        if cached is not None:
            self.cache_used.add(cached.id)
            entry.creatures = (cached.id,)
            entry.display = self.cached_display(cached.id)
            entry.creature_type = cached.creature_type
            self.named["namedByCache"] += 1
            self._record(entry, PROVENANCE_CACHE)
            return
        row = self.facts.curated_bosses.get(entry.encounter)
        if row is None or row.creature in self.era.creatures or row.creature in self.cache_used:
            return
        self.cache_used.add(row.creature)
        entry.creatures = (row.creature,)
        entry.display = self.cached_display(row.creature)
        if not entry.display and row.display in self.era.display_ids:
            entry.display = row.display
        seen = self.facts.cached_creatures.get(row.creature)
        entry.creature_type = seen.creature_type if seen else 0
        self.named["namedByCurated"] += 1
        self._record(entry, PROVENANCE_CURATED)

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
            entry = self.creature_entry(encounter.name, RANK_BOSS, creatures, encounter=encounter.id, new=new)
            if new:
                self.name_new_boss(entry)
            entries.append(entry)

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

    # ----- where a place is ------------------------------------------------------------------

    def location(self, map_facts: MapFacts, area_id: int) -> Location:
        """A place's entrance zone and continent, from the first source that answers: a the
        UiMap chain, b the entrance position inside exactly one zone's corners, c the AreaTable
        (which has to agree with the corners where the Map row states a position), b again with
        the nearest pfQuest spawns breaking the tie, and last the continent alone, from
        CorpseMapID or CosmeticParentMapID."""
        facts = self.facts
        found = location_from_ui_map(facts, map_facts.id)
        if found is not None:
            return found
        candidates = entrance_zones(map_facts, self.era.map_bounds)
        corpse_continent = continent_name(facts, map_facts.corpse_map)
        if len(candidates) == 1 and candidates[0] in facts.ui_maps:
            return Location(facts.ui_maps[candidates[0]].name, corpse_continent, WHERE_ENTRANCE)
        zone = zone_from_area(facts, map_facts, area_id)
        if zone is not None and (not candidates or self.era.area_maps.get(zone.id) in candidates):
            return Location(zone.name, continent_name(facts, zone.continent), WHERE_AREA)
        if len(candidates) > 1:
            if self.points is None:
                self.points = zoned_points(self.era)
            nearest = nearest_zone(map_facts, candidates, self.points)
            if nearest in facts.ui_maps:
                return Location(facts.ui_maps[nearest].name, corpse_continent, WHERE_ENTRANCE)
        continent = corpse_continent or continent_name(facts, map_facts.cosmetic_parent)
        if continent:
            return Location("", continent, WHERE_ENTRANCE)
        return Location()

    def world_boss_continent(self, zones: Sequence[int]) -> str:
        """The continent every one of a world boss's zones lies on, by this build's AreaTable,
        or "" where one is unknown or they differ."""
        continents = {self.facts.areas[z].continent for z in zones if z in self.facts.areas}
        if not zones or len(continents) != 1 or any(z not in self.facts.areas for z in zones):
            return ""
        return continent_name(self.facts, next(iter(continents)))

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
    # A new encounter the creature cache or the curated file named has no level: left out.
    levelled = [e for e in entries if e.creatures and not e.new and e.rank == RANK_BOSS] or [
        e for e in entries if e.creatures and not e.new
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


# ----- where a place is, as words (brief BL13a) ---------------------------------------------------


def continent_name(facts: BossLootInput, map_id: int) -> str:
    """The localised `Map` name of an open world continent (Eastern Kingdoms, Kalimdor), or ""."""
    found = facts.maps.get(map_id)
    if map_id not in CONTINENT_MAPS or found is None:
        return ""
    return found.name


def location_from_ui_map(facts: BossLootInput, map_id: int) -> Location | None:
    """Source a: the place's own UiMap (a dungeon or an orphan map assigned to its map id), whose
    parent is a zone map, whose parent is a continent map. None unless exactly one answer."""
    answers: set[tuple[str, str]] = set()
    for ui_map, assigned in facts.ui_map_assignments:
        own = facts.ui_maps.get(ui_map)
        if assigned != map_id or own is None or own.type not in (UI_MAP_DUNGEON, UI_MAP_ORPHAN):
            continue
        zone = facts.ui_maps.get(own.parent)
        if zone is None or zone.type != UI_MAP_ZONE:
            continue
        continent = facts.ui_maps.get(zone.parent)
        if continent is None or continent.type != UI_MAP_CONTINENT:
            continue
        answers.add((zone.name, continent.name))
    if len(answers) != 1:
        return None
    zone_name, continent = answers.pop()
    return Location(zone_name, continent, WHERE_UI_MAP)


def has_entrance(map_facts: MapFacts) -> bool:
    """Whether the Map row states an entrance position on an open world continent."""
    return map_facts.corpse_map in CONTINENT_MAPS and (map_facts.corpse_x, map_facts.corpse_y) != (0.0, 0.0)


def entrance_zones(map_facts: MapFacts, bounds: Mapping[tuple[int, int], era_mod.MapBounds]) -> list[int]:
    """Source b's geometry: the zone UiMaps whose corners on the corpse map hold the entrance
    position (`era_sources.map_bounds`, zone and orphan maps only). The rectangles overlap at
    the edges, so a position near a border sits inside two or three."""
    if not has_entrance(map_facts):
        return []
    x, y = map_facts.corpse_x, map_facts.corpse_y
    return sorted(
        {
            ui_map
            for (ui_map, map_id), box in bounds.items()
            if map_id == map_facts.corpse_map and box.min_x <= x <= box.max_x and box.min_y <= y <= box.max_y
        }
    )


@dataclass(frozen=True)
class EntrancePin:
    """Where a place's entrance is drawn (brief W16): the zone UiMap and the position on it in
    tenths of a percent, x from the left and y from the top."""

    ui_map: int
    x: int
    y: int


def pin_position(box: era_mod.MapBounds, x: float, y: float) -> tuple[int, int]:
    """A world position on one zone map in tenths of a percent (0 to ENTRANCE_SCALE), by the
    same axis rule as the EraSources pins (`era_sources.map_position`): world x drives the
    map's y and world y the map's x, both inverted, then the assignment's UiMin and UiMax."""
    across, down = era_mod.map_position(box, x, y)

    def tenths(percent: float) -> int:
        return max(0, min(ENTRANCE_SCALE, round(percent * ENTRANCE_SCALE / 100.0)))

    return tenths(across), tenths(down)


def entrance_pin(
    facts: BossLootInput,
    map_facts: MapFacts,
    bounds: Mapping[tuple[int, int], era_mod.MapBounds],
    zone: str = "",
) -> EntrancePin | None:
    """The place's entrance as a pin on a zone map: the Map row's corpse position inside a zone
    UiMap (Type 3) assigned to CorpseMapID. Where several hold it, the one named `zone` (the
    place's ez), else the smallest region, then the lowest UiMap id. None where the row states
    no position (CorpseMapID -1, or 0, 0) or no zone map holds it."""
    if map_facts.corpse_map < 0 or (map_facts.corpse_x, map_facts.corpse_y) == (0.0, 0.0):
        return None
    x, y = map_facts.corpse_x, map_facts.corpse_y
    held = [
        box
        for (ui_map, map_id), box in bounds.items()
        if map_id == map_facts.corpse_map
        and ui_map in facts.ui_maps
        and facts.ui_maps[ui_map].type == UI_MAP_ZONE
        and box.min_x <= x <= box.max_x
        and box.min_y <= y <= box.max_y
    ]
    if not held:
        return None
    named = [box for box in held if zone and facts.ui_maps[box.ui_map].name == zone]
    box = min(
        named or held,
        key=lambda b: ((b.max_x - b.min_x) * (b.max_y - b.min_y), b.ui_map),
    )
    across, down = pin_position(box, x, y)
    return EntrancePin(box.ui_map, across, down)


def zoned_points(era_input: era_mod.EraInput) -> list[tuple[int, float, float, int]]:
    """(map, world x, world y, zone UiMap) for every pfQuest spawn whose area this build draws on
    a zone map: pfQuest's percentage turned back into a world position by the zone's own
    corners (the inverse of era_sources.map_position). Read to break a tie, never shipped. A
    spawn pfQuest lists in two zones (a copy in another zone within SHARED_SPAWN_YARDS) is
    left out, both copies."""
    by_map: dict[int, list[era_mod.MapBounds]] = defaultdict(list)
    for box in era_input.map_bounds.values():
        by_map[box.ui_map].append(box)
    out: list[tuple[int, float, float, int]] = []
    for creature in sorted(era_input.unit_points):
        for point in era_input.unit_points[creature]:
            ui_map = era_input.area_maps.get(point.area, 0)
            for box in by_map.get(ui_map, ()):
                wide = box.ui_max_x - box.ui_min_x
                tall = box.ui_max_y - box.ui_min_y
                if not wide or not tall:
                    continue
                west = (point.x / 100.0 - box.ui_min_x) / wide
                north = (point.y / 100.0 - box.ui_min_y) / tall
                out.append(
                    (
                        box.map,
                        box.max_x - north * (box.max_x - box.min_x),
                        box.max_y - west * (box.max_y - box.min_y),
                        ui_map,
                    )
                )
    return _unshared(out)


def _unshared(points: list[tuple[int, float, float, int]]) -> list[tuple[int, float, float, int]]:
    reach = SHARED_SPAWN_YARDS
    grid: dict[tuple[int, int, int], list[tuple[int, float, float, int]]] = defaultdict(list)
    for point in points:
        grid[(point[0], int(point[1] // reach), int(point[2] // reach))].append(point)

    def shared(point: tuple[int, float, float, int]) -> bool:
        map_id, x, y, ui_map = point
        cx, cy = int(x // reach), int(y // reach)
        return any(
            other[3] != ui_map and math.hypot(other[1] - x, other[2] - y) <= reach
            for dx in (-1, 0, 1)
            for dy in (-1, 0, 1)
            for other in grid.get((map_id, cx + dx, cy + dy), ())
        )

    return [point for point in points if not shared(point)]


def nearest_zone(
    map_facts: MapFacts,
    candidates: Collection[int],
    points: Sequence[tuple[int, float, float, int]],
    k: int = NEAREST_SPAWNS,
) -> int:
    """Source b's tie break: of the candidate zones, the one most of the k pfQuest spawns
    nearest the entrance lie in (pfQuest states the zone of every spawn), the nearest spawn
    deciding a tied vote. 0 where no spawn lies in any candidate."""
    x, y = map_facts.corpse_x, map_facts.corpse_y
    near = sorted(
        (math.hypot(px - x, py - y), ui_map)
        for map_id, px, py, ui_map in points
        if map_id == map_facts.corpse_map and ui_map in candidates
    )[:k]
    if not near:
        return 0
    votes: dict[int, int] = defaultdict(int)
    for _distance, ui_map in near:
        votes[ui_map] += 1
    top = max(votes.values())
    return next(ui_map for _distance, ui_map in near if votes[ui_map] == top)


def _top_zone(facts: BossLootInput, area_id: int) -> AreaFacts | None:
    """The outdoor zone an area lies in: its ParentAreaID chain walked to the top, where the top
    is an area of an open world continent. None where the chain leaves the table."""
    area = facts.areas.get(area_id)
    seen: set[int] = set()
    while area is not None and area.parent and area.id not in seen:
        seen.add(area.id)
        area = facts.areas.get(area.parent)
    if area is None or area.parent or area.continent not in CONTINENT_MAPS:
        return None
    return area


def _namesake(place: str, area: str) -> bool:
    shorter = min(len(normalise(place)), len(normalise(area)))
    return shorter >= NAMESAKE_MIN_CHARS and names_match(place, area)


def zone_from_area(facts: BossLootInput, map_facts: MapFacts, area_id: int) -> AreaFacts | None:
    """Source c: the outdoor zone the client's AreaTable puts the place in. First the place's own
    area (`a`, then Map.AreaTableID) where its ParentAreaID leads to a continent's zone; then the
    outdoor area of the place's name ("Blackfathom Deeps" under Ashenvale, "Not Used Deadmines"
    under Westfall), which the client keeps beside the instance's own. Only an area with a
    parent counts, and every one found has to lead to the same zone."""
    for own in (area_id, map_facts.area):
        found = facts.areas.get(own)
        if found is not None and found.parent:
            top = _top_zone(facts, own)
            if top is not None:
                return top
    tops: dict[int, AreaFacts] = {}
    for area in sorted(facts.areas.values(), key=lambda a: a.id):
        if area.continent in CONTINENT_MAPS and area.parent and _namesake(map_facts.name, area.name):
            top = _top_zone(facts, area.id)
            if top is not None:
                tops[top.id] = top
    return next(iter(tops.values())) if len(tops) == 1 else None


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
        # A world boss's zones already say where it is: ez stays absent, ec is the continent
        # they share, from this build's AreaTable (source c).
        continent = stage.world_boss_continent(zones)
        where = Location("", continent, WHERE_AREA if continent else WHERE_NONE)
        raw.append((place, [entry], {"lv": "boss" if lv else "", "hi": "boss" if lv else "", "where": where}))
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
        where = stage.location(m, area)
        pin = entrance_pin(facts, m, era_input.map_bounds, where.zone)
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
        raw.append((place, entries, {"lv": lo_from, "hi": hi_from, "where": where, "pin": pin}))

    raw.sort(
        key=lambda item: (band(item[0]["lv"]), item[0]["lv"] or 0, item[0]["k"], item[0]["name"].lower())
    )

    strings: set[str] = set()
    for place, entries, how in raw:
        strings.add(place["name"])
        if place.get("an"):
            strings.add(place["an"])
        strings.update(name for name in (how["where"].zone, how["where"].continent) if name)
        strings.update(era_input.areas[zone] for zone in place.get("zones", ()))
        strings.update(entry.name for entry in entries)
    table = sorted(strings)
    index = {value: position for position, value in enumerate(table, start=1)}

    places: list[dict] = []
    bosses: list[dict] = []
    notes: list[dict] = []
    for place, entries, how in raw:
        where: Location = how["where"]
        pin: EntrancePin | None = how.get("pin")
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
            "ez": index[where.zone] if where.zone else None,
            "ec": index[where.continent] if where.continent else None,
            "eu": pin.ui_map if pin else None,
            "ex": pin.x if pin else None,
            "ey": pin.y if pin else None,
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
                "zone": where.zone,
                "continent": where.continent,
                "whereFrom": where.source,
                "entrance": (pin.ui_map, pin.x, pin.y) if pin else None,
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
        "withZone": sum(1 for p in places if "ez" in p),
        "withContinent": sum(1 for p in places if "ec" in p),
        "withEntrance": sum(1 for p in places if "eu" in p),
        "cacheFiles": facts.cache_files,
        **stage.named,
    }
    return BossLoot(
        strings=table,
        places=places,
        bosses=bosses,
        counts=counts,
        dropped=stage.dropped,
        notes=notes,
        empty=stage.empty,
        naming=stage.naming,
        naming_notes=stage.naming_notes,
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
        "ez the entrance zone's name (absent for k=3), ec the continent's name, "
        "eu/ex/ey the entrance pin (the zone UiMapID, and x from the left and y from the top in "
        f"tenths of a percent, 0 to {ENTRANCE_SCALE}; all three or none), "
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


def location_lines(table: BossLoot) -> list[str]:
    """The compile's report of where each place is (brief BL13a): one line per place with the
    source its ez and ec came from (and its entrance pin, brief W16), then the count per source,
    then the Era instances that did not resolve both, by name, then the places with no pin."""
    names = {WHERE_UI_MAP: "a", WHERE_ENTRANCE: "b", WHERE_AREA: "c", WHERE_NONE: "none"}
    lines: list[str] = []
    tally: dict[str, int] = defaultdict(int)
    unresolved: list[str] = []
    for note in table.notes:
        source = names[note["whereFrom"]]
        tally[source] += 1
        lines.append(
            f"{source:<4} {note['name']}: {note['zone'] or '-'}, {note['continent'] or '-'}"
            + (", new" if note["new"] else "")
            + (" (entrance {1} {2} on UiMap {0})".format(*note["entrance"]) if note.get("entrance") else "")
        )
        if note["kind"] != KIND_WORLD_BOSS and not note["new"] and not (note["zone"] and note["continent"]):
            unresolved.append(note["name"])
    summary = ", ".join(f"{source} {tally[source]}" for source in ("a", "b", "c", "none"))
    lines.append(f"by source: {summary}")
    lines.append(f"Era instances not fully placed: {', '.join(unresolved) if unresolved else 'none'}")
    pinless = [n["name"] for n in table.notes if n["kind"] != KIND_WORLD_BOSS and not n.get("entrance")]
    lines.append(f"places with no entrance pin: {', '.join(pinless) if pinless else 'none'}")
    return lines


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


def _float(value) -> float:
    try:
        return float(value or 0.0)
    except (TypeError, ValueError):
        return 0.0


def _int(value) -> int:
    try:
        return int(value or 0)
    except (TypeError, ValueError):
        return 0


def _columns(conn: sqlite3.Connection, table: str) -> set[str]:
    """The loaded table's columns; empty where the table is not loaded at all."""
    return {str(row[1]) for row in conn.execute(f"PRAGMA table_info({table})")}


def client_encounter_models(conn: sqlite3.Connection, build: str) -> tuple[str, dict[int, tuple[int, int]]]:
    """(the source that answered, encounter id -> (display id, creature id or 0)) from the
    build's own tables, where it has them: a CreatureDisplayID column on DungeonEncounter (retail
    has one), else an encounter journal (JournalEncounter.DungeonEncounterID joined to
    JournalEncounterCreature, the first creature of each by OrderIndex, with CreatureID where the
    table has that column). ("", {}) where neither holds a row for this build. A lookup of what
    is loaded only; nothing is fetched."""
    found: dict[int, tuple[int, int]] = {}
    if "CreatureDisplayID" in _columns(conn, "DungeonEncounter"):
        for row in conn.execute(
            "SELECT ID, CreatureDisplayID FROM DungeonEncounter WHERE build_id = ?", (build,)
        ):
            if _int(row[1]) > 0:
                found[_int(row[0])] = (_int(row[1]), 0)
        if found:
            return "DungeonEncounter.CreatureDisplayID", found
    journal, creatures = _columns(conn, "JournalEncounter"), _columns(conn, "JournalEncounterCreature")
    if {"ID", "DungeonEncounterID"} <= journal and {
        "JournalEncounterID",
        "CreatureDisplayInfoID",
    } <= creatures:
        creature = "c.CreatureID" if "CreatureID" in creatures else "0"
        order = "c.OrderIndex, c.ID" if "OrderIndex" in creatures else "c.ID"
        rows = conn.execute(
            f"SELECT j.DungeonEncounterID, c.CreatureDisplayInfoID, {creature} "
            "FROM JournalEncounterCreature c JOIN JournalEncounter j "
            "ON j.ID = c.JournalEncounterID AND j.build_id = c.build_id "
            f"WHERE c.build_id = ? ORDER BY j.DungeonEncounterID, {order}",
            (build,),
        )
        for row in rows:
            encounter = _int(row[0])
            if encounter > 0 and encounter not in found and (_int(row[1]) > 0 or _int(row[2]) > 0):
                found[encounter] = (_int(row[1]), _int(row[2]))
        if found:
            return "JournalEncounterCreature", found
    return "", {}


NEW_BOSSES_PROVENANCE = "community"
# Which input named a new encounter, as BossLoot.naming records it.
PROVENANCE_CLIENT = "client tables"
PROVENANCE_CRITERIA = "client criteria"
PROVENANCE_CACHE = "creature cache"
PROVENANCE_CURATED = "curated"
# Criteria.Type for "kill a creature", whose Asset is the creature id.
CRITERIA_KILL_CREATURE = 0


def client_kill_criteria(conn: sqlite3.Connection, build: str) -> list[KillCriterion]:
    """Every kill criterion of the build (Criteria Type 0, Asset > 0) that a CriteriaTree row
    holds, with that row's text and its parent's. Empty where the tables are not loaded. A
    lookup of what is loaded only; nothing is fetched."""
    if not (
        {"ID", "Type", "Asset"} <= _columns(conn, "Criteria")
        and {"ID", "Description_lang", "Parent", "CriteriaID"} <= _columns(conn, "CriteriaTree")
    ):
        return []
    rows = conn.execute(
        "SELECT c.ID, c.Asset, t.Description_lang, p.Description_lang FROM Criteria c "
        "JOIN CriteriaTree t ON t.CriteriaID = c.ID AND t.build_id = c.build_id "
        "LEFT JOIN CriteriaTree p ON p.ID = t.Parent AND p.build_id = t.build_id "
        "WHERE c.build_id = ? AND c.Type = ? AND c.Asset > 0 ORDER BY c.ID, t.ID",
        (build, CRITERIA_KILL_CREATURE),
    )
    found: dict[int, tuple[int, list[str], list[str]]] = {}
    for row in rows:
        creature, texts, parents = found.setdefault(_int(row[0]), (_int(row[1]), [], []))
        for text, into in ((row[2], texts), (row[3], parents)):
            if text and str(text) not in into:
                into.append(str(text))
    return [
        KillCriterion(id=cid, creature=creature, texts=tuple(texts), parents=tuple(parents))
        for cid, (creature, texts, parents) in found.items()
    ]


_DATE = re.compile(r"^\d{4}-\d{2}-\d{2}$")


def load_new_bosses(path: Path) -> dict:
    """curated/new_bosses.json as read. A file that cannot be read at all fails."""
    try:
        raw = json.loads(path.read_text(encoding="utf-8"))
    except (OSError, ValueError) as exc:
        raise BossLootError(f"cannot read {path}: {exc}") from exc
    if not isinstance(raw, dict):
        raise BossLootError(f"{path} is not a JSON object")
    return raw


def _positive(value) -> bool:
    return isinstance(value, int) and not isinstance(value, bool) and value > 0


def validate_new_bosses(
    raw: dict, encounters: Sequence[EncounterFacts], baseline_encounters: Collection[int]
) -> tuple[dict[int, NewBossRow], list[str]]:
    """The rows that pass, by encounter id, and a note for each row refused. A row names an
    encounter of this build that the baseline does not have, by its own name, a creature id,
    an optional display id, provenance "community" and at least one {url, date} source."""
    by_id = {e.id: e for e in encounters}
    rows: dict[int, NewBossRow] = {}
    refused: list[str] = []
    for row in raw.get("encounters") or []:
        if not isinstance(row, dict):
            refused.append("new bosses: a row is not an object")
            continue
        encounter_id = row.get("encounterId")
        what = f"new bosses: encounter {encounter_id!r}"
        encounter = by_id.get(encounter_id) if _positive(encounter_id) else None
        if encounter is None:
            refused.append(f"{what}: not a DungeonEncounter row of this build")
            continue
        if encounter.id in baseline_encounters:
            refused.append(f"{what}: the baseline has it, so it is not new")
            continue
        if encounter.id in rows:
            refused.append(f"{what}: repeated")
            continue
        if row.get("name") != encounter.name:
            refused.append(f"{what}: the build names it {encounter.name!r}, the file {row.get('name')!r}")
            continue
        if not _positive(row.get("creatureId")):
            refused.append(f"{what}: no creatureId")
            continue
        display = row.get("displayId", 0)
        if display != 0 and not _positive(display):
            refused.append(f"{what}: displayId is not a positive id")
            continue
        if row.get("provenance") != NEW_BOSSES_PROVENANCE:
            refused.append(f"{what}: provenance must be {NEW_BOSSES_PROVENANCE!r}")
            continue
        sources = row.get("sources")
        good = (
            isinstance(sources, list)
            and bool(sources)
            and all(
                isinstance(source, dict)
                and isinstance(source.get("url"), str)
                and source["url"].startswith("https://")
                and isinstance(source.get("date"), str)
                and _DATE.match(source["date"])
                for source in sources
            )
        )
        if not good:
            refused.append(f"{what}: every source needs an https url and a YYYY-MM-DD date")
            continue
        rows[encounter.id] = NewBossRow(
            encounter=encounter.id,
            name=encounter.name,
            creature=row["creatureId"],
            display=display,
            sources=tuple((source["url"], source["date"]) for source in sources),
        )
    return rows, refused


def gather_input(
    conn: sqlite3.Connection,
    build: str,
    baseline: str,
    *,
    cmangos_path: Path,
    creature_caches: Sequence[Path] = (),
    new_bosses_path: Path | None = None,
) -> BossLootInput:
    """Read the client tables of both builds and the credits. Everything here is I/O.
    `creature_caches` are the creaturecache.wdb files to read (the client's own first), and
    `new_bosses_path` is curated/new_bosses.json where it is there."""
    maps = {
        _int(row["ID"]): MapFacts(
            id=_int(row["ID"]),
            name=str(row["MapName_lang"] or ""),
            instance_type=_int(row["InstanceType"]),
            max_players=_int(row["MaxPlayers"]),
            area=_int(row["AreaTableID"]),
            corpse_map=_int(row["CorpseMapID"]),
            corpse_x=_float(row["Corpse_0"]),
            corpse_y=_float(row["Corpse_1"]),
            cosmetic_parent=_int(row["CosmeticParentMapID"]),
        )
        for row in _rows(
            conn,
            build,
            "Map",
            "ID, MapName_lang, InstanceType, MaxPlayers, AreaTableID, CorpseMapID, Corpse_0, Corpse_1, "
            "CosmeticParentMapID",
        )
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
    ui_maps = {
        _int(row["ID"]): UiMapFacts(
            id=_int(row["ID"]),
            name=str(row["Name_lang"] or ""),
            parent=_int(row["ParentUiMapID"]),
            type=_int(row["Type"]),
        )
        for row in _rows(conn, build, "UiMap", "ID, Name_lang, ParentUiMapID, Type")
    }
    ui_map_assignments = tuple(
        sorted(
            {
                (_int(row["UiMapID"]), _int(row["MapID"]))
                for row in _rows(conn, build, "UiMapAssignment", "UiMapID, MapID")
            }
        )
    )
    for name, found in (("Map", maps), ("DungeonEncounter", encounters)):
        if not found:
            raise BossLootError(
                f"build {build} has no {name} rows; run `itemtree-data fetch {build} -t {name}` "
                f"then `itemtree-data load {build} -t {name}`"
            )
    notes: list[str] = []
    client_source, client_models = client_encounter_models(conn, build)
    notes.append(
        f"client encounter models from {client_source} ({len(client_models)} encounters)"
        if client_source
        else "no client encounter models on this build"
    )
    kill_criteria = client_kill_criteria(conn, build)
    notes.append(
        f"client achievement criteria: {len(kill_criteria)} kill criteria"
        if kill_criteria
        else "no achievement kill criteria on this build"
    )
    merged = cache_mod.read_many(list(creature_caches), build=build)
    notes.extend(merged.notes)
    curated: dict[int, NewBossRow] = {}
    if new_bosses_path is not None and new_bosses_path.is_file():
        curated, refused = validate_new_bosses(
            load_new_bosses(new_bosses_path), encounters, baseline_encounters
        )
        notes.extend(refused)
    return BossLootInput(
        maps=maps,
        baseline_maps=baseline_maps,
        encounters=encounters,
        baseline_encounters=baseline_encounters,
        dungeons=dungeons,
        tuning=tuning,
        areas=areas,
        credits=read_credits(cmangos_path),
        ui_maps=ui_maps,
        ui_map_assignments=ui_map_assignments,
        client_models=client_models,
        client_source=client_source,
        kill_criteria=kill_criteria,
        cached_creatures=merged.creatures,
        cache_files=len(merged.files_read),
        curated_bosses=curated,
        notes=notes,
    )
