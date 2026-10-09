# SPDX-License-Identifier: GPL-3.0-only
# Copyright (c) 2026 Rockjaw Bonesnapper Co
# Public home, the Corresponding Source of EraSources.lua and Jettison_Data/EraFacts.lua: https://github.com/Rockjaw-Bonesnapper-Co/itemtree-era-sources
"""Jettison's Classic Era facts: `Jettison_Data/EraFacts.lua` (brief JS1, which split brief IT3's file).

Jettison (the addon once called Droplist) reads a handful of facts per item live through
ItemTreeAPI when ItemTree is installed. Without ItemTree it reads the same facts baked into its
own load on demand folder, Jettison_Data, as TWO files, and combines them at run time:

  EraFacts.lua  this module's: ONLY what derives from the Classic Era tables (the CMaNGOS Classic
                content database, through the EraSources table the compile derives from it, and
                its quest_template titles and race masks). GPL-3.0, like EraSources.lua.
  Facts.lua     itemtree_data/jettison_facts.py's: everything else, ours (the Forever client's
                tables, our curated and community mined data, the item effects). All rights
                reserved, never mirrored, and never written by this module.

The shape, to the letter (ItemTree-Data docs/data-format.md, "Jettison facts"):

    Jettison_EraFacts = {
      v = 1, build = "...", generated = "...",
      items = { [itemId] = { vc } },
      quests = { [questId] = { t, f } },
    }

  vc  how many Classic Era vendors sell the item, as Keep.EraVendorCount counts them: each named
      vendor row of EraSources and each record of an opened vendor list once (one per name and
      area), a limited stock vendor (k, or a record's stock field) left out. Absent for 0.
  t   the quest's Classic Era title: the EraSources table's own (`qt`, and the quest of every
      c = 3 row and its further quests), then quest_template's title for any other quest. A title
      era_sources calls scaffolding is left out.
  f   the side its quest_template race mask states (0 both, 1 Alliance, 2 Horde).

`quests` holds EVERY quest the Era tables title or side, not only the quests Facts.lua's rows
reference: which quests those are is our data, and this file is built without it. Jettison looks a
quest up here first and in Facts.lua's own titles second, and takes the larger of the two vendor
counts, so the combined answer is the one the single file of brief IT3 gave.

Why this module can hold nothing of ours. `build_era_facts` takes the EraSources table and the
CMaNGOS half of the EraInput the era sources stage read (era_sources.cmangos_only, a CmangosOnly:
since brief GA1 this build's tables and the addon's curated quests have nowhere to ride on it; type
checked: nothing else is accepted in their place), the compile's two stamps (short identifiers,
checked) and one omission list, and nothing else. It reads only the attributes ERA_SOURCES_READ and
ERA_INPUT_READ name; every key it writes is in the allow lists below, checked again when the text is
made. Its GPL lines come from the one helper that writes them (era_sources.gpl_licence_lines). The
omission list, `leave_out_titles`, is the quests whose Era title holds, as whole words, the Era name
of an item the build withholds (Jettison's file holds no item name). It is a set of quest ids and
can only take an Era title OUT: it never puts a value in. The caller works it out
(jettison_facts.write_files); this module imports only what the public mirror holds (era_sources.py
and luaout.py) and is mirrored byte for byte by scripts/sync-era-sources.sh.
"""

from __future__ import annotations

import re
from collections.abc import Collection, Mapping, Sequence
from dataclasses import dataclass, field
from pathlib import Path
from typing import Any

# Relative, as era_sources.py's own are, so the public mirror's package reads them as they are.
from . import era_sources as era_mod
from .luaout import lua_value

# The contract's version: Jettison's reader refuses any other.
CONTRACT_VERSION = 1
GLOBAL = "Jettison_EraFacts"
FILE_NAME = "EraFacts.lua"
# Jettison's load on demand folder: under about 600 KB a file is comfortable. A guard, not a budget.
MAX_BYTES = 600 * 1024

# The allow lists: the only keys the file may carry, at the top, in an item row and in a quest.
TOP_FIELDS = frozenset({"v", "build", "generated", "items", "quests"})
ITEM_FIELDS = frozenset({"vc"})
QUEST_FIELDS = frozenset({"t", "f"})

# What build_era_facts reads of its two Era inputs, and nothing more (tests/test_jettison.py holds
# it to these). The second is a CmangosOnly (brief GA1), which carries no table of this build's and
# no curated quest id at all.
ERA_SOURCES_READ = frozenset({"rows", "list_index", "lists", "strings", "quest_titles"})
ERA_INPUT_READ = frozenset({"quest_names", "quests"})

# A stamp (build, baseline, generated, pipeline version) is a short identifier, never data.
_STAMP = re.compile(r"^[A-Za-z0-9_.:+\-]{1,64}$")

CONTRACT_LINE = (
    "Contract: Jettison brief JS1 (Jettison_Data/EraFacts.lua, v = 1, read with Facts.lua beside it) "
    "and ItemTree-Data docs/data-format.md, Jettison facts."
)


class EraFactsError(ValueError):
    """The Era facts cannot be built or written as asked: say why, write nothing."""


# ----- the Era facts, pure ------------------------------------------------------------------------

_VENDOR_RECORD = era_mod.PACK_NAME_DIGITS + era_mod.PACK_AREA_DIGITS + era_mod.PACK_VALUE_DIGITS


def era_vendor_counts(era: era_mod.EraSources | None) -> dict[int, int]:
    """itemId -> how many Classic Era vendors sell it, as Keep.EraVendorCount counts them: each
    named vendor row and each record of an opened vendor list once (one per name and area), a
    limited stock vendor (k, or a record's stock field) left out. A summary row with no list adds
    what it stands for past the named rows."""
    if era is None:
        return {}
    lists = list(era.lists or [])
    index = era.list_index or {}
    out: dict[int, int] = {}
    for item, rows in (era.rows or {}).items():
        count = 0
        named = 0
        summary = None
        for row in rows:
            if row.get("c") != era_mod.CAT_VENDOR:
                continue
            if "t" in row:
                summary = row
                continue
            named += 1
            if not row.get("k"):
                count += 1
        if summary is not None:
            number = (index.get(item) or {}).get(era_mod.CAT_VENDOR)
            if number and 1 <= number <= len(lists):
                packed = lists[number - 1]
                for at in range(0, len(packed), _VENDOR_RECORD):
                    record = packed[at : at + _VENDOR_RECORD]
                    stock = era_mod.unpack_int(record[-era_mod.PACK_VALUE_DIGITS :])
                    if not stock:
                        count += 1
            else:
                count += max(0, int(summary.get("t", 0)) - named)
        if count:
            out[int(item)] = count
    return out


def era_titles(era: era_mod.EraSources | None, era_input: era_mod.CmangosOnly | None) -> dict[int, str]:
    """questId -> the Classic Era title: the EraSources table's own (`qt`, and the quest of every
    c = 3 row and its further quests), then quest_template's title for any other quest. A title
    era_sources calls scaffolding is left out."""
    out: dict[int, str] = {}
    strings = list(era.strings or []) if era is not None else []

    def at(value: Any) -> str | None:
        if isinstance(value, str):
            return value or None
        if isinstance(value, int) and 1 <= value <= len(strings):
            return strings[value - 1]
        return None

    if era is not None:
        for quest, value in (era.quest_titles or {}).items():
            if title := at(value):
                out.setdefault(int(quest), title)
        for rows in (era.rows or {}).values():
            for row in rows:
                if row.get("c") != era_mod.CAT_QUEST:
                    continue
                for one in (row, *(row.get("m", ()) or ())):
                    title = at(one.get("n"))
                    if isinstance(one.get("q"), int) and title:
                        out.setdefault(one["q"], title)
    if era_input is not None:
        for quest, title in (era_input.quest_names or {}).items():
            if title and not era_mod.is_scaffolding(title):
                out.setdefault(int(quest), title)
    return out


def era_sides(era_input: era_mod.CmangosOnly | None) -> dict[int, int]:
    """questId -> 0 both, 1 Alliance, 2 Horde, for the quests whose race mask the Era input read."""
    out: dict[int, int] = {}
    if era_input is None:
        return out
    for quest, facts in (era_input.quests or {}).items():
        out[int(quest)] = era_mod.faction_of(int(getattr(facts, "races", 0) or 0)) or 0
    return out


@dataclass
class EraFacts:
    """The built table and what the report says about it."""

    value: dict
    counts: dict[str, int] = field(default_factory=dict)
    # Set once written: the file and its size.
    path: Path | None = None
    bytes: int = 0
    # The quests whose Era title was left out (leave_out_titles), in id order.
    titles_left_out: list[int] = field(default_factory=list)


def _check_inputs(era: Any, cmangos: Any) -> None:
    if era is not None and not isinstance(era, era_mod.EraSources):
        raise TypeError(f"era must be the EraSources table or None, not {type(era).__name__}")
    if cmangos is not None and not isinstance(cmangos, era_mod.CmangosOnly):
        raise TypeError(
            "cmangos must be the CMaNGOS half of the era input (era_sources.cmangos_only) or None, "
            f"not {type(cmangos).__name__}"
        )


def check_stamp(name: str, value: Any) -> str:
    """A stamp is a short identifier (a build id, an ISO time, a version), never data."""
    if not isinstance(value, str) or not _STAMP.match(value):
        raise EraFactsError(f"{name} must be a short identifier, not {value!r}")
    return value


def _quest_ids(value: Any) -> frozenset[int]:
    if not isinstance(value, Collection) or isinstance(value, (str, bytes, Mapping)):
        raise TypeError("leave_out_titles must be a set of quest ids")
    if not all(isinstance(q, int) and not isinstance(q, bool) and q > 0 for q in value):
        raise TypeError("leave_out_titles holds quest ids only")
    return frozenset(value)


def build_era_facts(
    era: era_mod.EraSources | None,
    cmangos: era_mod.CmangosOnly | None,
    *,
    build: str,
    generated: str,
    leave_out_titles: Collection[int] = frozenset(),
) -> EraFacts:
    """Jettison_EraFacts' table, from the Era inputs alone. `era` is the EraSources table the
    compile derived (None when the era sources stage is off), `cmangos` the CMaNGOS half of the
    EraInput it read (era_sources.cmangos_only); `build` and `generated` the compile's stamps;
    `leave_out_titles` the quests whose Era title is left out (it holds a withheld item's Era
    name). With neither input the table is empty."""
    _check_inputs(era, cmangos)
    check_stamp("build", build)
    check_stamp("generated", generated)
    leave_out = _quest_ids(leave_out_titles)
    counts = era_vendor_counts(era)
    titles = era_titles(era, cmangos)
    sides = era_sides(cmangos)
    items = {item: {"vc": count} for item, count in sorted(counts.items())}
    quests: dict[int, dict[str, Any]] = {}
    left_out: list[int] = []
    for quest in sorted(set(titles) | set(sides)):
        entry: dict[str, Any] = {}
        if quest in titles:
            if quest in leave_out:
                left_out.append(quest)
            else:
                entry["t"] = titles[quest]
        if quest in sides:
            entry["f"] = sides[quest]
        if entry:
            quests[quest] = entry
    value = {"v": CONTRACT_VERSION, "build": build, "generated": generated, "items": items, "quests": quests}
    check_value(value)
    report = {
        "items": len(items),
        "vc": len(items),
        "quests": len(quests),
        "questsNamed": sum(1 for entry in quests.values() if "t" in entry),
        "sides": sum(1 for entry in quests.values() if "f" in entry),
        "titlesLeftOut": len(left_out),
    }
    return EraFacts(value=value, counts=report, titles_left_out=left_out)


def check_value(value: Mapping) -> None:
    """Every key in the allow lists and every value of its one type: an Era fact, nothing else."""
    extra = set(value) - TOP_FIELDS
    if extra:
        raise EraFactsError(f"{FILE_NAME}: keys not allowed at the top: {', '.join(sorted(map(str, extra)))}")
    if value.get("v") != CONTRACT_VERSION:
        raise EraFactsError(f"{FILE_NAME}: v must be {CONTRACT_VERSION}")
    for name in ("build", "generated"):
        check_stamp(name, value.get(name))
    for item, row in (value.get("items") or {}).items():
        if not isinstance(item, int) or not isinstance(row, Mapping) or set(row) - ITEM_FIELDS:
            raise EraFactsError(f"{FILE_NAME}: item {item!r} holds a field that is not an Era fact")
        if not isinstance(row.get("vc"), int) or row["vc"] <= 0:
            raise EraFactsError(f"{FILE_NAME}: item {item}'s vc must be a positive count")
    for quest, entry in (value.get("quests") or {}).items():
        if not isinstance(quest, int) or not isinstance(entry, Mapping) or set(entry) - QUEST_FIELDS:
            raise EraFactsError(f"{FILE_NAME}: quest {quest!r} holds a field that is not an Era fact")
        if "t" in entry and not isinstance(entry["t"], str):
            raise EraFactsError(f"{FILE_NAME}: quest {quest}'s title must be a string")
        if "f" in entry and entry["f"] not in (0, 1, 2):
            raise EraFactsError(f"{FILE_NAME}: quest {quest}'s side must be 0, 1 or 2")


# ----- the file -----------------------------------------------------------------------------------


def licence_lines() -> list[str]:
    """era_sources' credit and GPL lines, through the one GPL helper (era_sources.gpl_licence_lines),
    word for word but for where this file ships: Jettison's folder rather than ItemTree's."""
    files = (
        "The licence text ships as LICENSES/GPL-3.0.txt and the CMaNGOS notice as "
        "LICENSES/cmangos-COPYRIGHT.md, beside this file's folder in the Jettison package."
    )
    return [
        era_mod.CREDIT,
        *era_mod.gpl_licence_lines(
            what="This one generated file",
            rest="The rest of Jettison and of ItemTree is all rights reserved, Facts.lua beside it included.",
            source="the compiler, the pinned inputs and these notices",
            licence_files=files,
        ),
    ]


def header_lines(*, build: str, baseline: str, generated: str, version: str) -> list[str]:
    for name, value in (
        ("build", build),
        ("baseline", baseline),
        ("generated", generated),
        ("version", version),
    ):
        check_stamp(name, value)
    return [
        "ItemTree generated data for Jettison. Do not edit.",
        f"Module: {GLOBAL} | Build: {build} | Baseline: {baseline} | Generated: {generated} "
        f"| Pipeline: {version}",
        CONTRACT_LINE,
        "Only the facts derived from the Classic Era tables, which Jettison combines with Facts.lua's "
        "at run time: items[itemId] = { vc = how many Classic Era vendors sell it (one per name and "
        "area, limited stock left out) }; quests[questId] = { t = the Classic Era title, f = the side "
        "its race mask states (0 both, 1 Alliance, 2 Horde) }, for every quest the Era tables title. "
        "No item names: a title holding the Era name of an item the build withholds is left out.",
        *licence_lines(),
    ]


def module_text(value: Mapping, header: Sequence[str]) -> str:
    """The file: the header comment and one global assignment, nothing else. The value is checked
    against the allow lists first, so no key outside them can be written."""
    check_value(value)
    head = "".join(f"-- {line}\n" for line in header)
    return f"{head}{GLOBAL} = {lua_value(value)}\n"


def file_text(facts: EraFacts, *, build: str, baseline: str, generated: str, version: str) -> str:
    """EraFacts.lua, whole: the header made here from the four stamps (each a short identifier,
    checked) and the checked value. The compile's one way to write the file (brief GA1): nothing
    but the EraFacts this module built and the stamps can reach it."""
    if not isinstance(facts, EraFacts):
        raise TypeError(
            f"EraFacts.lua is written from the EraFacts build_era_facts made, not {type(facts).__name__}"
        )
    return module_text(
        facts.value, header_lines(build=build, baseline=baseline, generated=generated, version=version)
    )
