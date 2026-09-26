# SPDX-License-Identifier: GPL-3.0-only
# Copyright (c) 2026 Rockjaw Bonesnapper Co
# Public home, the Corresponding Source of EraSources.lua: https://github.com/Rockjaw-Bonesnapper-Co/itemtree-era-sources
"""The four facts about one client build that the era sources compiler needs, and no more.

`era_sources.derive` takes an `EraInput` (the pinned upstream databases, read) and one object
that satisfies `BuildFacts`. The ItemTree pipeline passes its whole build graph, which has many
more fields; this protocol names the only four the compiler reads, so that anyone holding those
four facts for a build can run the compiler without the rest of the pipeline.

All four come from the game client's own database tables for the build being compiled:

  * `items`: every item id this build NAMES, that is every id with both an `Item` row and an
    `ItemSparse` row. Only membership is read: a source row for an id not in here is dropped.
  * `undiscovered`: the ids this build LISTS but hides, an `Item` row with no `ItemSparse` row
    (the WoW Forever beta ships about 12,500 of them). Only membership is read, to count why
    a row was dropped. No row is emitted for one unless the caller passes it to `derive` in
    `withheld`, the ids an earlier build named, whose rows then ship as a named item's do.
  * `locks`: the `Lock` table by id. Each value needs a `types` attribute: the
    `(LockType id, required skill)` pairs of the lock's slots whose Type is 2 (a LockType
    rather than a key item). Used to tell a herb node, a mining vein and a fishing pool from any
    other locked object.
  * `lock_types`: the `LockType` table, id to its `Name_lang` ("Herbalism", "Mining",
    "Fishing" and so on). A build that does not load it falls back to the well known ids.

The pipeline's `BuildGraph` declares these as `dict[int, Item]`, `dict[int, UndiscoveredItem]`,
`dict[int, LockInfo]` and `dict[int, str]`. The protocol states them as read only mappings with
the values' contents left open (apart from a lock's `types`), so it needs none of those classes
and any dataclass or plain object with four such attributes satisfies it.
"""

from __future__ import annotations

from collections.abc import Mapping
from typing import Protocol


class LockFacts(Protocol):
    """One `Lock` row, as far as the compiler reads it."""

    @property
    def types(self) -> tuple[tuple[int, int], ...]: ...


class BuildFacts(Protocol):
    """What the era sources compiler reads about the client build it compiles for."""

    @property
    def items(self) -> Mapping[int, object]:
        """Item ids this build names (an `Item` row and an `ItemSparse` row)."""
        ...

    @property
    def undiscovered(self) -> Mapping[int, object]:
        """Item ids this build lists but hides (an `Item` row and no `ItemSparse` row)."""
        ...

    @property
    def locks(self) -> Mapping[int, LockFacts]:
        """The `Lock` table by id; each value carries its `(LockType id, skill)` pairs."""
        ...

    @property
    def lock_types(self) -> Mapping[int, str]:
        """The `LockType` table: id to `Name_lang`."""
        ...
