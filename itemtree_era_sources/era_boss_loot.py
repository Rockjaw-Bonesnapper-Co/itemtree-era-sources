# SPDX-License-Identifier: GPL-3.0-only
# Copyright (c) 2026 Rockjaw Bonesnapper Co
# Public home, the Corresponding Source of EraSources.lua and BossLoot.lua: https://github.com/Rockjaw-Bonesnapper-Co/itemtree-era-sources
"""`BossLoot.lua`, the Classic Era half of the Boss loot tab: what the CMaNGOS Classic content
database says each creature and chest drops, and nothing else (brief GA1).

Owner ruling of 2026-10-09: only data derived from the pinned CMaNGOS dump may be in a GPL file.
Until brief GA1 one GPL file, BossLoot.lua, held the whole Boss loot index, places and encounters
out of this build's own client tables and the curated, owner verified and harvested facts among
them. The index is now two files, and the addon joins them the first time it reads one:

  BossLoot.lua       this module's: per CMaNGOS creature and per chest object, the items it drops
                     and how often. GPL-3.0, like EraSources.lua, and built from a CmangosOnly
                     (era_sources.cmangos_only) and nothing else.
  BossLootIndex.lua  itemtree_data/boss_loot.py's: the places, their bosses, rares and chests, and
                     each loot item's type and item level. Ours, all rights reserved, never mirrored.

Which creatures and chests this file holds is a CMaNGOS rule of its own, never the index's choice,
so the file is the same whatever the client build, the curated files or the creature caches say:

  * a creature with loot whose every always there spawn is on ONE map, and that map is not one of
    the two continents (every dungeon and raid boss, rare and elite lives on its instance map);
  * a creature `instance_encounters` credits for an encounter kill (a boss summoned mid fight has
    no spawn at all);
  * a creature of rank 3 (a boss), wherever it stands (the world bosses);
  * a chest (gameobject type 3) with loot whose every spawn is on one map that is not a continent.

A creature or a chest whose name is scaffolding (era_sources.is_scaffolding) is left out, and so is
one whose list is empty once the world drops are taken out.

The shape (ItemTree-Data docs/boss-loot.md, "The two files"):

    { v = 2, c = { [creatureId] = "records" }, o = { [objectId] = "records" } }

Each list is fixed 5 byte records in the EraSources xl alphabet (base 91, the bytes 35 to 126
without 92, most significant digit first): the item id (3 digits) and the value (2: the chance in
tenths of a percent by the EraSources rule, plus 2048 where the drop is quest only, 0 where no
usable chance is stated), in item id order. A world drop (an item more than
era_sources.WORLD_DROP_CREATURES creatures drop) is left out of every list.
"""

from __future__ import annotations

import gzip
import re
from collections import defaultdict
from collections.abc import Collection, Iterable, Mapping
from dataclasses import dataclass, field
from pathlib import Path

# Relative, as era_sources.py's own are, so the public mirror's package reads them as they are.
from . import era_sources as era_mod
from .luaout import lua_module, lua_value

MODULE_NAME = "BossLoot"
# The contract version of this half. Version 1 was the whole index in one GPL file, before brief GA1.
CONTRACT_VERSION = 2
# The keys the module may hold at the top, and nothing else (checked before any text is made).
TOP_FIELDS = frozenset({"v", "c", "o"})

RECORD_ITEM_DIGITS = 3
RECORD_VALUE_DIGITS = 2
RECORD_BYTES = RECORD_ITEM_DIGITS + RECORD_VALUE_DIGITS

# The open world continents (CMaNGOS map ids): a creature or chest standing only on one of them is
# out in the world, never inside an instance.
CONTINENT_MAPS = frozenset({0, 1})
# CMaNGOS creature_template.Rank 3: a boss.
CMANGOS_BOSS = 3
# instance_encounters.creditType 0: the credit is a creature kill.
CREDIT_KILL = 0
# The shipped file may not grow past this. It is about 70 KB.
MAX_FILE_BYTES = 200 * 1024

INSTANCE_ENCOUNTERS = "INSERT INTO `instance_encounters` VALUES "

# A stamp (build, baseline, generated, pipeline version) is a short identifier, never data.
_STAMP = re.compile(r"^[A-Za-z0-9_.:+\-]{1,64}$")


class EraBossLootError(ValueError):
    """The Classic Era half cannot be read, built or written as asked: say why, write nothing."""


# ----- reading the credits out of the pinned dump ------------------------------------------------


def read_credits(path: Path) -> dict[int, tuple[int, ...]]:
    """CMaNGOS instance_encounters: DungeonEncounter id -> the creatures credited for its kill.

    The same rows guesses/pipeline.py reads, read afresh here (entry, creditType, creditEntry):
    only creditType 0, a creature kill, is kept.
    """
    found: dict[int, set[int]] = defaultdict(set)
    try:
        handle = gzip.open(path, "rt", encoding="utf-8", errors="replace")
    except OSError as exc:
        raise EraBossLootError(f"cannot read {path}: {exc}") from exc
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


# ----- the CMaNGOS rules the index shares ---------------------------------------------------------


def spawn_maps(facts) -> dict[int, frozenset[int]]:
    """creature id -> every map its always there spawns are on (the era_sources pin rules: an
    event only spawn is not a place it is found, a spawn with no id takes creature_spawn_entry's).
    `facts` is a CmangosOnly or an EraInput: only `spawns` and `spawn_entries` are read."""
    maps: dict[int, set[int]] = defaultdict(set)
    for spawn in facts.spawns:
        if spawn.event > 0:
            continue
        ids = (spawn.creature,) if spawn.creature else tuple(facts.spawn_entries.get(spawn.guid, ()))
        for creature in ids:
            if creature:
                maps[creature].add(spawn.map)
    return {creature: frozenset(found) for creature, found in maps.items()}


def world_drop_items(facts, loot: Mapping[int, Mapping[int, era_mod.Drop]]) -> set[int]:
    """Every item more than WORLD_DROP_CREATURES distinct creatures drop, over the whole table.
    `facts` is a CmangosOnly or an EraInput: only `creatures` is read."""
    droppers: dict[int, int] = defaultdict(int)
    for creature in facts.creatures.values():
        if not creature.loot or era_mod.is_scaffolding(creature.name):
            continue
        for item in loot.get(creature.loot, {}):
            droppers[item] += 1
    return {item for item, count in droppers.items() if count > era_mod.WORLD_DROP_CREATURES}


def loot_value(drop: era_mod.Drop) -> int:
    """The chance in tenths of a percent by the EraSources rule, plus the quest only flag."""
    percent = era_mod.chance_percent(drop.chance)
    value = int(round(percent * era_mod.PACK_TENTHS)) if percent is not None else 0
    if drop.quest_only:
        value += era_mod.PACK_QUEST_ONLY
    return value


def kept_creatures(cmangos: era_mod.CmangosOnly, maps: Mapping[int, frozenset[int]]) -> list[int]:
    """The creatures this file holds a list for, by the CMaNGOS rule in the module docstring, in id
    order. Scaffolding and an empty list are left out by `build`."""
    credited = {cid for found in cmangos.credits.values() for cid in found}
    kept: list[int] = []
    for cid in sorted(cmangos.creatures):
        facts = cmangos.creatures[cid]
        if not facts.loot:
            continue
        where = maps.get(cid, frozenset())
        alone = len(where) == 1 and not where <= CONTINENT_MAPS
        if alone or cid in credited or facts.rank == CMANGOS_BOSS:
            kept.append(cid)
    return kept


def kept_objects(cmangos: era_mod.CmangosOnly) -> list[int]:
    """The chests this file holds a list for: gameobject type 3 with loot, every spawn on one map
    that is not a continent, in id order."""
    kept: list[int] = []
    for oid in sorted(cmangos.objects):
        obj = cmangos.objects[oid]
        if obj.kind != era_mod.GO_TYPE_CHEST or not obj.loot:
            continue
        where = tuple(cmangos.object_spawn_maps.get(oid, ()))
        if len(where) == 1 and where[0] not in CONTINENT_MAPS:
            kept.append(oid)
    return kept


# ----- the records --------------------------------------------------------------------------------


def pack_record(item: int, value: int) -> str:
    """One 5 byte record: the item id, then the value."""
    return era_mod.pack_int(item, RECORD_ITEM_DIGITS) + era_mod.pack_int(value, RECORD_VALUE_DIGITS)


def unpack_records(packed: str) -> list[tuple[int, int]]:
    """(item, value) per record, in the string's order. Refuses a length that is not whole records."""
    if len(packed) % RECORD_BYTES:
        raise EraBossLootError(f"a loot list of {len(packed)} bytes is not whole {RECORD_BYTES} byte records")
    out: list[tuple[int, int]] = []
    for start in range(0, len(packed), RECORD_BYTES):
        item = era_mod.unpack_int(packed[start : start + RECORD_ITEM_DIGITS])
        value = era_mod.unpack_int(packed[start + RECORD_ITEM_DIGITS : start + RECORD_BYTES])
        out.append((item, value))
    return out


def _records(drops: Mapping[int, era_mod.Drop], world: Collection[int]) -> str:
    return "".join(pack_record(item, loot_value(drops[item])) for item in sorted(drops) if item not in world)


# ----- the table ----------------------------------------------------------------------------------


@dataclass
class EraBossLoot:
    """The built table and what the header and the compile report say about it."""

    value: dict
    counts: dict[str, int] = field(default_factory=dict)
    # The world drop items, for the index (boss_loot counts them per entry as w); never shipped here.
    world: frozenset[int] = frozenset()


def build(cmangos: era_mod.CmangosOnly) -> EraBossLoot:
    """The Classic Era half, from the CMaNGOS dump's facts alone (a CmangosOnly, type checked)."""
    if not isinstance(cmangos, era_mod.CmangosOnly):
        raise TypeError(f"the Classic Era half is built from a CmangosOnly, not {type(cmangos).__name__}")
    dropped: dict[str, int] = defaultdict(int)
    creature_loot = era_mod.expand_loot(cmangos.creature_loot, cmangos.reference_loot, dropped)
    object_loot = era_mod.expand_loot(cmangos.object_loot, cmangos.reference_loot, dropped)
    world = world_drop_items(cmangos, creature_loot)
    maps = spawn_maps(cmangos)
    creatures: dict[int, str] = {}
    scaffolding = 0
    for cid in kept_creatures(cmangos, maps):
        facts = cmangos.creatures[cid]
        if era_mod.is_scaffolding(facts.name):
            scaffolding += 1
            continue
        packed = _records(creature_loot.get(facts.loot, {}), world)
        if packed:
            creatures[cid] = packed
    objects: dict[int, str] = {}
    for oid in kept_objects(cmangos):
        obj = cmangos.objects[oid]
        if era_mod.is_scaffolding(obj.name):
            scaffolding += 1
            continue
        packed = _records(object_loot.get(obj.loot, {}), world)
        if packed:
            objects[oid] = packed
    value = {"v": CONTRACT_VERSION, "c": creatures, "o": objects}
    check_value(value)
    counts = {
        "creatures": len(creatures),
        "objects": len(objects),
        "records": sum(len(p) for p in (*creatures.values(), *objects.values())) // RECORD_BYTES,
        "worldDropItems": len(world),
        "scaffolding": scaffolding,
        "refLoop": dropped.get("refLoop", 0),
    }
    return EraBossLoot(value=value, counts=counts, world=frozenset(world))


def check_value(value: Mapping) -> None:
    """Every key in the allow list and every list whole records: a CMaNGOS fact, nothing else."""
    extra = set(value) - TOP_FIELDS
    if extra:
        raise EraBossLootError(
            f"{MODULE_NAME}.lua: keys not allowed at the top: {', '.join(sorted(map(str, extra)))}"
        )
    if value.get("v") != CONTRACT_VERSION:
        raise EraBossLootError(f"{MODULE_NAME}.lua: v must be {CONTRACT_VERSION}")
    for key in ("c", "o"):
        held = value.get(key)
        if not isinstance(held, Mapping):
            raise EraBossLootError(f"{MODULE_NAME}.lua: {key} must be a table")
        for ident, packed in held.items():
            if not isinstance(ident, int) or isinstance(ident, bool) or ident <= 0:
                raise EraBossLootError(f"{MODULE_NAME}.lua: {key} is keyed by ids, not {ident!r}")
            if not isinstance(packed, str) or not packed or len(packed) % RECORD_BYTES:
                raise EraBossLootError(f"{MODULE_NAME}.lua: {key}[{ident}] is not whole loot records")


# ----- the file -----------------------------------------------------------------------------------

CREDIT = (
    "Historical Classic Era boss loot, derived from the CMaNGOS Classic content database "
    "(github.com/cmangos/classic-db), which the MaNGOS community compiled for World of Warcraft "
    "patch 1.12. Which items a creature or a chest drops, and how often, are that database's own "
    "loot table figures. WoW Forever may differ; the addon shows these as predicted."
)


def licence_lines() -> list[str]:
    """The licence part of the header, through the one GPL helper (era_sources.gpl_licence_lines)."""
    return era_mod.gpl_licence_lines(
        what="This generated file",
        rest=(
            "The rest of ItemTree is all rights reserved, BossLootIndex.lua beside it included, "
            "which holds the places and their bosses and which the addon joins this file to."
        ),
        source="the compilers, the pinned inputs and these notices",
        pfquest=False,
    )


def check_stamp(name: str, value: object) -> str:
    """A stamp is a short identifier (a build id, an ISO time, a version), never data."""
    if not isinstance(value, str) or not _STAMP.match(value):
        raise EraBossLootError(f"{name} must be a short identifier, not {value!r}")
    return value


def header_lines(table: EraBossLoot, *, build: str, baseline: str, generated: str, version: str) -> list[str]:
    """The whole header comment: the stamp, the legend, the credit and the licence."""
    for name, stamp in (
        ("build", build),
        ("baseline", baseline),
        ("generated", generated),
        ("version", version),
    ):
        check_stamp(name, stamp)
    counts = table.counts
    return [
        "ItemTree generated data. Do not edit.",
        f"Module: {MODULE_NAME} | Build: {build} | Baseline: {baseline} | Generated: {generated} "
        f"| Pipeline: {version}",
        "The Classic Era half of the Boss loot index: what each CMaNGOS creature and chest drops. "
        "docs/boss-loot.md in the pipeline is the contract. The addon joins it to BossLootIndex.lua, "
        "which names the places and their bosses, rares and chests by these ids.",
        f"{{ v = {CONTRACT_VERSION}, c = {{ [creatureId] = loot }}, o = {{ [objectId] = loot }} }}. "
        "v is the contract version; refuse any other.",
        f"loot: fixed {RECORD_BYTES} byte records in the EraSources xl alphabet (base "
        f"{era_mod.PACK_BASE}, bytes {era_mod.PACK_FIRST} to 126 without {era_mod.PACK_SKIPPED}, most "
        f"significant first): item id ({RECORD_ITEM_DIGITS}), value ({RECORD_VALUE_DIGITS}: the chance "
        f"in tenths of a percent, plus {era_mod.PACK_QUEST_ONLY} where quest only, 0 = no chance "
        "stated), in item id order.",
        "Held: every creature with loot whose always there spawns are all on one map that is not a "
        "continent, every creature instance_encounters credits for a kill, every rank 3 creature, and "
        "every chest whose spawns are all on one map that is not a continent; scaffolding left out. "
        f"An item more than {era_mod.WORLD_DROP_CREATURES} creatures drop is a world drop and is in no "
        "list.",
        CREDIT,
        *licence_lines(),
        f"{counts.get('creatures', 0)} creatures, {counts.get('objects', 0)} chests, "
        f"{counts.get('records', 0)} loot records; {counts.get('worldDropItems', 0)} world drop items "
        "left out.",
    ]


def module_text(
    table: EraBossLoot, *, build: str, baseline: str, generated: str, version: str, pretty: bool = False
) -> str:
    """BossLoot.lua, whole: the header made here (header_lines, from the four stamps, each checked)
    and the self registering module. The value is checked first, so no key outside the allow list
    can be written. The compile's one way to write the file: nothing but the EraBossLoot `build`
    made and the stamps can reach it (brief GA1)."""
    if not isinstance(table, EraBossLoot):
        raise TypeError(
            f"BossLoot.lua is written from the EraBossLoot build made, not {type(table).__name__}"
        )
    check_value(table.value)
    header = header_lines(table, build=build, baseline=baseline, generated=generated, version=version)
    return lua_module(MODULE_NAME, header, lua_value(table.value, pretty=pretty, indent=1))


def records_of(value: Mapping, key: str, ids: Iterable[int]) -> dict[int, list[tuple[int, int]]]:
    """(item, value) records of each id that has a list, for the join's readers and the tests."""
    held = value.get(key) or {}
    return {ident: unpack_records(held[ident]) for ident in ids if ident in held}
