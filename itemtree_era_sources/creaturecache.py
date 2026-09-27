# SPDX-License-Identifier: GPL-3.0-only
# Copyright (c) 2026 Rockjaw Bonesnapper Co
# Public home, the Corresponding Source of EraSources.lua and BossLoot.lua: https://github.com/Rockjaw-Bonesnapper-Co/itemtree-era-sources
"""The client's creature cache, `Cache/WDB/<locale>/creaturecache.wdb`, read (brief BL15a).

The client writes every creature a player has seen to this file: the server's answer to the
creature query, as it came. The Boss loot compile reads it the way `--client` reads the hotfix
cache, to name the creature of an encounter new in Forever that no client table and no emulator
dump names (docs/boss-loot.md, "The client's creature cache").

The layout, worked out from the owner's file on 1.60.1.70009 (build stamp 70009) and checked
against that build's CreatureDisplayInfo:

  header, 24 bytes: magic "BOMW" (WMOB reversed), build, locale ("SUne" is enUS reversed),
      record size, record version, cache version; all little endian uint32 but the two tags.
  then records: entry id (int32), body length (uint32), the body. A record of length 0 ends
      the file (its entry id is 0).
  body, the SMSG_QUERY_CREATURE_RESPONSE stats block:
      a big endian bit field, padded to a whole byte: title length (11 bits), alternative
          title length (11), cursor name length (6), leader (1), then for each of four names
          the name length (11) and the alternative name length (11). A length counts the
          closing zero byte; 0 means the string is absent.
      the names, each followed by its alternative, as zero ended strings (absent ones skipped)
      three flag words (uint32 each)
      creature type (uint8), family (int32), classification, the rank (uint8)
      two proxy creature ids (int32 each)
      display count (uint32), total probability (float), then per display:
          display id (uint32), scale (float), probability (float)
      health and power multipliers (float each)
      quest item count (uint32), then nine int32 fields (movement, class, difficulty and so
          on; nothing here reads them)
      title, alternative title and cursor name (zero ended, absent ones skipped)
      the quest item ids (int32 each)

A body that does not end exactly where its length says refuses the whole file, so a layout
change on a later build is an error, never a silent misread.
"""

from __future__ import annotations

import struct
from dataclasses import dataclass
from pathlib import Path

MAGIC = b"BOMW"
HEADER = struct.Struct("<4sI4sIII")
RECORD = struct.Struct("<iI")
NAME_COUNT = 4
TAIL_INTS = 9
# The cache's place under a client folder, per locale.
CACHE_DIR = Path("Cache") / "WDB"
FILE_NAME = "creaturecache.wdb"


class CreatureCacheError(Exception):
    """The file cannot be read, is another build's, or does not fit the layout above."""


@dataclass(frozen=True)
class CachedCreature:
    """One creature as the client cached it. `displays` are the display ids in the order the
    server sent them."""

    id: int
    name: str
    names: tuple[str, ...] = ()
    title: str = ""
    creature_type: int = 0
    family: int = 0
    classification: int = 0
    displays: tuple[int, ...] = ()


@dataclass
class CreatureCache:
    build: int
    locale: str
    creatures: dict[int, CachedCreature]


def cache_path(client: Path, locale: str = "enUS") -> Path:
    """Where the client keeps the file for one locale."""
    return client / CACHE_DIR / locale / FILE_NAME


def build_number(build: str) -> int | None:
    """The number the header states for `build` (1.60.1.70009 is 70009), else None."""
    tail = build.rsplit(".", 1)[-1]
    return int(tail) if tail.isdigit() else None


class _Reader:
    def __init__(self, data: bytes, entry: int) -> None:
        self.data = data
        self.at = 0
        self.entry = entry

    def take(self, fmt: str):
        size = struct.calcsize(fmt)
        if self.at + size > len(self.data):
            raise CreatureCacheError(f"creature {self.entry}: the record ends early")
        values = struct.unpack_from(fmt, self.data, self.at)
        self.at += size
        return values

    def string(self, length: int) -> str:
        """A zero ended string of `length` bytes, the zero included. 0 is an absent string."""
        if length == 0:
            return ""
        end = self.at + length
        if end > len(self.data) or self.data[end - 1] != 0:
            raise CreatureCacheError(f"creature {self.entry}: a string does not end where its length says")
        text = self.data[self.at : end - 1].decode("utf-8", "replace")
        self.at = end
        return text


def parse_record(entry: int, body: bytes) -> CachedCreature:
    """One record's body. Raises CreatureCacheError where it does not fit the layout."""
    bits_len = (29 + NAME_COUNT * 22 + 7) // 8
    if len(body) < bits_len:
        raise CreatureCacheError(f"creature {entry}: the record ends early")
    bits = int.from_bytes(body[:bits_len], "big")
    total = bits_len * 8

    def field_at(start: int, width: int) -> int:
        return (bits >> (total - start - width)) & ((1 << width) - 1)

    title_len, title_alt_len, cursor_len = field_at(0, 11), field_at(11, 11), field_at(22, 6)
    name_lens = [(field_at(29 + 22 * i, 11), field_at(40 + 22 * i, 11)) for i in range(NAME_COUNT)]
    reader = _Reader(body, entry)
    reader.at = bits_len
    names: list[str] = []
    for name_len, alt_len in name_lens:
        names.append(reader.string(name_len))
        reader.string(alt_len)
    reader.take("<3I")
    (creature_type,) = reader.take("<B")
    (family,) = reader.take("<i")
    (classification,) = reader.take("<B")
    reader.take("<2i")
    (count,) = reader.take("<I")
    reader.take("<f")
    displays = tuple(reader.take("<Iff")[0] for _ in range(count))
    reader.take("<2f")
    (quest_items,) = reader.take("<I")
    reader.take(f"<{TAIL_INTS}i")
    title = reader.string(title_len)
    reader.string(title_alt_len)
    reader.string(cursor_len)
    reader.take(f"<{quest_items}i")
    if reader.at != len(body):
        raise CreatureCacheError(
            f"creature {entry}: {len(body) - reader.at} bytes left over; the layout has changed"
        )
    return CachedCreature(
        id=entry,
        name=names[0],
        names=tuple(name for name in names if name),
        title=title,
        creature_type=creature_type,
        family=family,
        classification=classification,
        displays=displays,
    )


def parse(data: bytes, *, build: int | None = None) -> CreatureCache:
    """The whole file. `build`, where given, is the only build stamp accepted."""
    if len(data) < HEADER.size:
        raise CreatureCacheError("too short for a WDB header")
    magic, stamp, locale, _size, _version, _cache_version = HEADER.unpack_from(data, 0)
    if magic != MAGIC:
        raise CreatureCacheError(f"not a creature cache (magic {magic!r})")
    if build is not None and stamp != build:
        raise CreatureCacheError(f"the cache is build {stamp}'s, not {build}'s")
    creatures: dict[int, CachedCreature] = {}
    offset = HEADER.size
    while offset + RECORD.size <= len(data):
        entry, length = RECORD.unpack_from(data, offset)
        offset += RECORD.size
        if length == 0:
            break
        if offset + length > len(data):
            raise CreatureCacheError(f"creature {entry}: the record runs past the end of the file")
        creatures[entry] = parse_record(entry, data[offset : offset + length])
        offset += length
    return CreatureCache(build=stamp, locale=locale[::-1].decode("ascii", "replace"), creatures=creatures)


def read(path: Path, *, build: str | None = None) -> CreatureCache:
    """Read the file. `build` is the compile's build id; a cache of any other build is refused."""
    try:
        data = path.read_bytes()
    except OSError as exc:
        raise CreatureCacheError(f"cannot read {path}: {exc}") from exc
    number = build_number(build) if build else None
    if build and number is None:
        raise CreatureCacheError(f"build {build} states no client build number to check the cache against")
    return parse(data, build=number)


# The drop folder under the data root's cache/ for the files testers send (gitignored, as the
# rest of cache/ is). Every *.wdb in it is read beside the client's own.
DROP_DIR = Path("creaturecache")


@dataclass
class MergedCache:
    """Every file read, merged by creature entry id. `notes` names each file refused and each
    creature two files disagree on."""

    creatures: dict[int, CachedCreature]
    files_read: list[Path]
    notes: list[str]


def drop_files(cache_dir: Path) -> list[Path]:
    """The testers' files: every *.wdb under `cache_dir`/creaturecache, in name order."""
    folder = cache_dir / DROP_DIR
    return sorted(path for path in folder.rglob("*.wdb") if path.is_file()) if folder.is_dir() else []


def read_many(paths: list[Path], *, build: str) -> MergedCache:
    """Read and merge `paths` in order. A file that cannot be read, is another build's or does
    not fit the layout is left out with a note naming it. A creature two files name keeps the
    first file's record; where the later one states other display ids, that is noted."""
    merged = MergedCache(creatures={}, files_read=[], notes=[])
    first_file: dict[int, Path] = {}
    for path in paths:
        try:
            cache = read(path, build=build)
        except CreatureCacheError as exc:
            merged.notes.append(f"{path.name} left out: {exc}")
            continue
        merged.files_read.append(path)
        for entry, creature in cache.creatures.items():
            kept = merged.creatures.get(entry)
            if kept is None:
                merged.creatures[entry] = creature
                first_file[entry] = path
            elif kept.displays != creature.displays:
                merged.notes.append(
                    f"creature {entry} ({kept.name}): {path.name} states displays "
                    f"{list(creature.displays)}, {first_file[entry].name} {list(kept.displays)}; "
                    "kept the first"
                )
    return merged
