# SPDX-License-Identifier: GPL-3.0-only
# Copyright (c) 2026 Rockjaw Bonesnapper Co
# Public home, the Corresponding Source of EraSources.lua: https://github.com/Rockjaw-Bonesnapper-Co/itemtree-era-sources
"""Historical Classic Era source facts, derived from two pinned community databases.

No client build says where an item comes from: drops, vendors, gathering nodes, containers
and quest turn ins are all server side. This stage fills that gap from the **CMaNGOS Classic
content database**, the 1.12 world database the MaNGOS community maintains, and compiles the
result into a single module, `EraSources.lua`. The addon draws it under the Predicted badge
with a "Classic Era" provenance, never as a fact about the client the player is running.

It is the only source this module reads, and it is read whole: one source of truth, one
credit, and nothing blended in from anywhere else. What it gives over the version 1 table it
replaced on 2026-09-20 is every source an item has rather than one, thirteen categories
rather than five, and gathering at all, so Deviate Scale, Medium Hide, Black Lotus and Iron
Ore have a source and Refreshing Spring Water keeps all 184 of its vendors alongside its
quests. The measurement that settled it is the last section of docs/source-data-options.md.

What is taken, and nothing else: the source category, the creature, object, vendor and quest
NAME, the creature and object **id**, the creature's display id, the Blizzard area id, the
quest id and the faction its race mask implies, the drop chance, the level band of a
summarised group, a limited stock vendor's stock count, the container item's own id, and since
2026-09-20 a handful of **map pins** per creature name per area, and since 2026-09-27 per herb,
vein, fishing pool and chest name per area too, and since brief N3 which creature starts and which
ends each quest, by the creature's name. No prose of any kind: not the
loot rows' `comments`, not quest text, not gossip, not scripts.

Since 2026-09-27 (brief T1, on the owner's ruling of 2026-09-27) two more columns of
`creature_template` are read, for the vendors and the quest givers and enders the table already
names and no other creature: `SubName`, the short title under a name such as "Cooking Supplies",
which is a title and not prose, shipped in `st` so a vendor row can say where to look; and
`Faction`, a FactionTemplate id, reduced through THIS build's own `FactionTemplate` and `Faction`
tables to one number (1 Alliance, 2 Horde, 3 both) and shipped in `cf`, so a recipe whose only
vendor is Alliance can say so. Every recipe vendor is a vendor the table names, so the recipe
sources are covered by the same rule. Nothing else about a faction is shipped.

Since 2026-09-29 (brief W12, on the owner's ruling of 2026-09-29) `quest_template.ReqItemId1..4`,
read before only so a quest only drop could name its quest, ships as well, with the two new
columns beside it, `ReqItemCount1..4`: per kept quest, the items it asks the player to bring and
how many of each, in `qr`, so a quest item's "Used by" can name the quest. Ids and counts only,
never the quest's text; an item this build does not ship is refused as a row for it would be.
A `qr` quest nothing else titles gets its title in `qt`: an index into `s` where `s` holds the
string, and otherwise the title itself as a plain string, so `s` never grows for `qr`.

Since 2026-09-29 (brief W15, owner QA of 2026-09-29: "Quest: Deviate Hides (1486)" showed no
giver) every creature `creature_questrelation` or `creature_involvedrelation` names for a titled
quest ships as a name of its own, even where it drops, sells and trains nothing: its name in
`s`, its kind in `ck`, its display id in `cd`, its pins in `mp`, its `SubName` in `st`, its side
in `cf` and its quest lists in `qg`, read by exactly the rules those columns already follow.
Brief N3 had shipped a giver only where another row already named it. Nothing new is read, and a
creature with no quest link is untouched. Gameobject givers are not read (the objects this
module reads are loot sources only). So that a list record's two digit name field still fits
once `s` passes 8,280 strings, such an `s` is two sorted runs: the names the lists carry, then
the rest. A table that fits stays one sorted run.

Since brief P6a three more tables are read, for the trainers: `npc_trainer` (a creature id and a
spell id per row), `npc_trainer_template` (a template id and a spell id per row, joined to a
creature through `creature_template.TrainerTemplateId`) and, from `spell_template`, the id, the
three `Effect` columns and the three `EffectTriggerSpell` columns and nothing else, to turn a
trainer's "learn" spell into the spell it teaches. Ids only: no spell name, no description, no
cost, no required level or skill. A taught spell is kept only where THIS build's own
`SkillLineAbility` files it under a profession or secondary skill line (the coordinator's decision
on brief P6a: ItemTree's trainer rows are about recipes, a class trainer teaches no item, and the
class trainers' 27,038 pairs would have taken the file past the then 1.6 MB), and the list ships
per trainer NAME in `tr`, so a trainer's page can say what it teaches and a spell's sources can
name its trainers. A trainer is a creature the table lists, so it gets its portrait, pins, title
and side through the same paths a vendor does.

The pins are the one reversal of an old rule, and they are narrow. Until 2026-09-20 this module
stored no coordinate at all. It now reduces each creature's spawns, per zone, to at most six
points on a grid of five percent of that zone's map, quantised to a tenth of a percent, so that
the creature page can draw a map: about eleven thousand numbers standing for seventy thousand
spawns. No respawn timer, no height, no orientation, no guid and no per spawn anything reaches
the file. The positions come from the cmangos dump, which is the GPL-3.0 source this one
generated file already carries the licence of. Since 2026-09-27 the same reduction is made of
each herb's, vein's, fishing pool's and chest's `gameobject` spawns and shipped in `op`, so a
node's page can draw a map the way a creature's does.

Two inputs are pinned, fetched into the gitignored cache, verified by size and sha256 every
run, and never committed:

  * the cmangos dump, for every fact above but the zones, the spawn positions among them;
  * two files of pfQuest's vanilla database, read for the **area id** a creature or an object
    spawns in (the objects file, like the units file, per spawn since 2026-09-27). The cmangos
    spawn tables carry a map and a coordinate and no area at all, and
    turning a coordinate into an area needs terrain data this pipeline does not extract. Its
    own coordinates, which are already a zone percentage, are read for two things and no more:
    to tell which spawn of a creature a cmangos row is, so that spawn's area id can be taken,
    and to CHECK the pipeline's own arithmetic. No pfQuest coordinate is shipped.

The pin arithmetic itself is this build's own: `UiMapAssignment` says where a zone map's
corners sit in the world, and `UiMap`, `UiMapXMapArt` and `WorldMapOverlay` say which zone map
an area id belongs to. Both are read from the client the player is running. `Map` is read the
same way and for one question: which area a whole instance map IS, so that a creature living
inside one has a place at all. Neither database states an area for such a creature, and the
answer is the build's own rather than a guess at an entrance.

What is refused: every row for an id this build does not ship, and for an id it hides unless the
caller names it as withheld (below); a quest only drop,
which the source marks with a negative chance; a chance that is zero, negative, above 100 or
rounds below 0.1; a reference loot loop; a creature or object whose name is scaffolding
rather than content; a container whose own item id this build will not name; and a quest row
our own curated quest table already states first hand.

Withheld ids, since 2026-09-26. `derive` takes an optional `withheld` set: ids this build hides
(an `Item` row and no `ItemSparse` row) that an earlier build named, which the caller ships
beside this table with their earlier details. Their rows are emitted exactly as a named item's
are. The addon hides them until the player's own client can name the item or a setting says to
show them. A hidden id NOT in the set, one no build has ever named, is still refused.

See docs/era-sources.md, which is the record shape's contract and is what the addon half is
briefed from. The whole feature is this module, its `compile` stage, the switch that turns it
off, and the one generated file.
"""

from __future__ import annotations

import gzip
import hashlib
import re
import shutil
import sqlite3
from collections import Counter, defaultdict
from collections.abc import Callable, Collection, Iterator, Mapping, Sequence
from dataclasses import dataclass, field
from pathlib import Path

import httpx

from .build_facts import BuildFacts

# ----- the pinned inputs ------------------------------------------------------------------

CACHE_SUBDIR = "era"
# Every fetch sends these generic browser headers and nothing else: no tool name, version,
# repository url, owner or contact detail, and no Referer (owner rule, 2026-09-30). They match the
# pipeline's shared header set; the constants live here so this file stands alone.
GENERIC_USER_AGENT = (
    "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) "
    "Chrome/140.0.0.0 Safari/537.36"
)
REQUEST_HEADERS = {
    "User-Agent": GENERIC_USER_AGENT,
    "Accept": "*/*",
    "Accept-Language": "en-US,en;q=0.9",
}

CMANGOS_COMMIT = "22b51464f1625f6ef6275771de1f5466c6f5d19e"
PFQUEST_COMMIT = "104f35678ca39ab1fb78b655f815cc7016f5e0c8"


@dataclass(frozen=True)
class Pin:
    """One file this stage reads, pinned to exact bytes.

    The point of pinning is that the stage compiles one known file or nothing: a mismatch
    fails rather than quietly compiling something else.
    """

    name: str
    version: str
    url: str
    sha256: str
    bytes: int
    filename: str

    def path(self, cache_dir: Path) -> Path:
        return cache_dir / CACHE_SUBDIR / self.filename


CMANGOS = Pin(
    name="cmangos-classic-db",
    version=CMANGOS_COMMIT[:12],
    url=(
        f"https://raw.githubusercontent.com/cmangos/classic-db/{CMANGOS_COMMIT}"
        "/Full_DB/ClassicDB_1_12_1_z2815.sql.gz"
    ),
    sha256="4f92db520868ab4e566726f68b5b2e380ae781209beaf22237b4f7f04600d0c0",
    bytes=12959882,
    filename=f"classic-db-{CMANGOS_COMMIT[:12]}.sql.gz",
)

PFQUEST_UNITS = Pin(
    name="pfquest-units",
    version=PFQUEST_COMMIT[:12],
    url=f"https://raw.githubusercontent.com/shagu/pfQuest/{PFQUEST_COMMIT}/db/units.lua",
    sha256="b8de09aa33fd4b16edb2287b8c4224c86e6ee420e717a4d428e2935c22c4a922",
    bytes=3497202,
    filename=f"pfquest-units-{PFQUEST_COMMIT[:12]}.lua",
)

PFQUEST_OBJECTS = Pin(
    name="pfquest-objects",
    version=PFQUEST_COMMIT[:12],
    url=f"https://raw.githubusercontent.com/shagu/pfQuest/{PFQUEST_COMMIT}/db/objects.lua",
    sha256="be4846e2f2049cafba7da5ed18d6422bde35ed0e6f6ac34cb1215c1bbafd306e",
    bytes=2464841,
    filename=f"pfquest-objects-{PFQUEST_COMMIT[:12]}.lua",
)

PINS: tuple[Pin, ...] = (CMANGOS, PFQUEST_UNITS, PFQUEST_OBJECTS)

# Inputs this stage used to read and no longer does. A build compiled before the change has
# them in its manifest, and a manifest that names a file the pipeline has stopped reading is
# not merely stale, it is wrong, so the stage drops them when it records its own. Empty today:
# no manifest under builds/ names an input this stage has stopped reading. Put a name back in
# here the next time a pin is dropped, and old manifests will forget it on their next compile.
RETIRED_INPUTS: tuple[str, ...] = ()

# ----- the credit, and the two licence readings -------------------------------------------

# The one sentence that goes wherever this data is shown: the generated module's header, the
# paragraph in docs/era-sources.md and the addon's README credit line all read it from here.
CREDIT = (
    "Historical Classic Era source data, derived from the CMaNGOS Classic content database "
    "(github.com/cmangos/classic-db), which the MaNGOS community compiled for World of "
    "Warcraft patch 1.12. Creature, object and quest names, vendor, trainer and quest giver "
    "titles and their factions (reduced to Alliance, Horde or both through the client's own "
    "faction tables) and which spells a trainer teaches are that database's own. Drop chances "
    "are that database's own loot table figures. Map pins are reduced from that database's own "
    "spawn positions. Creature and object zones come "
    "from pfQuest's vanilla database (github.com/shagu/pfQuest), which contributes the area "
    "id and nothing else. WoW Forever may differ; the addon shows these as predicted."
)

# There are two honest answers to the licence question and either is one constant away.
# "gpl" is shipped today, which is the owner's decision of 2026-09-20. Neither line claims the
# data is Blizzard's, and neither claims ItemTree's own licence covers the upstream database.
LICENCE_NOTE_FACTS = (
    "This module is a facts only derivation: ids, numbers, the names of creatures, objects "
    "and places, vendor, trainer and quest giver titles and factions, the spell ids a "
    "trainer teaches, and a handful of reduced map points, re-expressed by the pipeline. No prose, "
    "no descriptions, no quest text and no comments are taken from the source database, and "
    "none of its own text is reproduced here."
)

# Where the Corresponding Source of the generated file lives, in the GPL-3.0 section 6(d) sense:
# this compiler, `build_facts.py`, the pins above and the upstream notices, in a public repository.
CORRESPONDING_SOURCE_URL = "https://github.com/Rockjaw-Bonesnapper-Co/itemtree-era-sources"

LICENCE_NOTE_GPL = (
    "This one generated file is distributed under the GNU General Public License version 3, "
    "the licence of the CMaNGOS Classic content database it derives from "
    "(github.com/cmangos/classic-db). The rest of ItemTree is all rights reserved. "
    f"Corresponding Source, as GPL-3.0 section 6(d) asks: {CORRESPONDING_SOURCE_URL} "
    "(the compiler, the pinned inputs and these notices)."
)

# The upstream notices, which travel with the file whichever reading ships. The CMaNGOS line is
# the notice its COPYRIGHT.md carries at the pinned commit, word for word: CMaNGOS states no
# copyright holder or year of its own, it states Blizzard's.
UPSTREAM_CMANGOS = (
    f"CMaNGOS Classic content database: github.com/cmangos/classic-db at commit {CMANGOS_COMMIT}, GPL-3.0."
)
CMANGOS_COPYRIGHT = (
    "CMaNGOS notice (COPYRIGHT.md): World of Warcraft content and materials are trademarks and "
    "copyrights of Blizzard or its licensors. All rights reserved. CMaNGOS project is not "
    "affiliated with Blizzard or its licensors."
)
UPSTREAM_PFQUEST = (
    f"pfQuest vanilla database: github.com/shagu/pfQuest at commit {PFQUEST_COMMIT}, MIT "
    "licensed, read for area ids only."
)

# GPL-3.0 section 5(a): a prominent notice that the work was modified, with a relevant date.
# The date is the Generated stamp on the header's second line, so it is never restated here.
MODIFICATION_NOTICE = (
    "Modified: this file is a modified, reduced derivation of that database, made by the "
    "ItemTree pipeline on the Generated date above; the changes are the reduction this header "
    "describes."
)

LICENCE_FILES = (
    "The licence text ships as LICENSES/GPL-3.0.txt and the CMaNGOS notice as "
    "LICENSES/cmangos-COPYRIGHT.md, beside this file in the ItemTree addon."
)

# "gpl" ships LICENCE_NOTE_GPL, "facts" ships LICENCE_NOTE_FACTS. Changing this one word
# changes the generated header, and docs/era-sources.md sets out both readings either way.
LICENCE_MODE = "gpl"


def licence_note() -> str:
    return LICENCE_NOTE_GPL if LICENCE_MODE == "gpl" else LICENCE_NOTE_FACTS


def licence_lines() -> list[str]:
    """The licence part of the generated header, one comment line each.

    The reading, then the upstream commits and notices. Under "gpl" also the section 5(a)
    modification notice and where the licence files ship.
    """
    upstream = [UPSTREAM_CMANGOS, CMANGOS_COPYRIGHT, UPSTREAM_PFQUEST]
    if LICENCE_MODE == "gpl":
        return [licence_note(), *upstream, MODIFICATION_NOTICE, LICENCE_FILES]
    return [licence_note(), *upstream]


# Kept under its old name because the addon and the manifest both already read it by this
# name: it is the credit sentence, not the licence reading.
PROVENANCE = CREDIT


# ----- the categories ----------------------------------------------------------------------

# Numbers, not strings: 18,000 repeated copies of "Skinned from" would cost more than the
# whole string table does. 1 to 5 are the numbers the first version of this module used, and
# they keep their meanings so a reader written against that version still reads a row it
# understands. 2 is reserved and no longer emitted: a zone drop meant "somewhere in this zone"
# with no creature behind it, and this source always has the creature.
CAT_BOSS_DROP = 1
CAT_ZONE_DROP = 2
CAT_QUEST = 3
CAT_VENDOR = 4
CAT_WORLD_DROP = 5
CAT_CREATURE_DROP = 6
CAT_SKINNED = 7
CAT_HERB = 8
CAT_VEIN = 9
CAT_FISHED = 10
CAT_OBJECT = 11
CAT_PICKPOCKET = 12
CAT_CONTAINER = 13

CATEGORY_NAMES = {
    CAT_BOSS_DROP: "Boss drop",
    CAT_ZONE_DROP: "Zone drop",
    CAT_QUEST: "Quest",
    CAT_VENDOR: "Vendor",
    CAT_WORLD_DROP: "World drop",
    CAT_CREATURE_DROP: "Creature drop",
    CAT_SKINNED: "Skinned from",
    CAT_HERB: "Herb node",
    CAT_VEIN: "Mining vein",
    CAT_FISHED: "Fished",
    CAT_OBJECT: "Object or chest",
    CAT_PICKPOCKET: "Pickpocketed",
    CAT_CONTAINER: "Container item",
}

# Categories that are never emitted by this version. Kept in CATEGORY_NAMES so the legend a
# reader sees is complete and a future version can fill them in without renumbering.
RESERVED_CATEGORIES = frozenset({CAT_ZONE_DROP})

FACTION_ALLIANCE = 1
FACTION_HORDE = 2
FACTION_BOTH = 3

# quest_template.RequiredRaces, as the 1.12 race mask. A quest open to one side only carries
# that side; a quest open to both, or to nobody in particular, carries neither and is shown
# to everyone, which is what an absent `f` means in the module.
RACE_MASK_ALLIANCE = 1 | 4 | 8 | 64  # human, dwarf, night elf, gnome
RACE_MASK_HORDE = 2 | 16 | 32 | 128  # orc, undead, tauren, troll

# gameobject_template.type. Only these two ever carry loot a player can take.
GO_TYPE_CHEST = 3
GO_TYPE_FISHING_HOLE = 25

# LockType names this build's own LockType table gives, which is how a chest is told from a
# herb and a vein without guessing. The ids are the fallback for a build that names none.
LOCK_HERBALISM, LOCK_MINING, LOCK_FISHING = 2, 3, 19
LOCK_NAMES = {LOCK_HERBALISM: "herbalism", LOCK_MINING: "mining", LOCK_FISHING: "fishing"}

# ----- the fan out rules, as named constants -------------------------------------------------

# How many named rows one category may put on one item before the rest become a count.
MAX_NAMED_ROWS = 3

# Above this many distinct creatures, naming three of them is a worse answer than saying the
# item drops out in the world, which is what category 5 already means. Linen Cloth has 737.
WORLD_DROP_CREATURES = 40

# Above this many vendors, three arbitrary names say less than the count does. Refreshing
# Spring Water has 184.
VENDOR_SUMMARY_AT = 20

# A herb or a vein is one node name in many zones. It is listed NODE by node, each node's zone
# rows together (up to this many zones per node, commonest first), and the named row cap counts
# nodes rather than rows: see _node_rows.
MAX_NODE_ZONES = 4

# The two categories whose rows are a node's zones, grouped node by node.
NODE_CATEGORIES = frozenset({CAT_HERB, CAT_VEIN})

# How many further quests a quest row may carry behind the first, in `m`. Unchanged from the
# first version: the case this exists to answer is the same turn in offered to each side.
MAX_FURTHER_QUESTS = 3

# Where a cap would leave exactly this many sources unnamed, the leftovers are named instead
# and no summary row is written. "and 1 more" is a row a player cannot read standing for a
# row we are holding in our hand: Black Lotus grows a fourth zone rather than a count of one.
SUMMARISE_AT_LEAST = 2

# One decimal place. The chances are a 1.12 server's loot tables, so more precision than this
# would be false confidence about a client that is not this one.
CHANCE_PLACES = 1
MIN_CHANCE = 0.1

# How deep a loot reference may be followed before the stage calls it a loop.
MAX_REFERENCE_DEPTH = 4

# Names that mark a row as scaffolding rather than content. Narrow on purpose: a loose rule
# refuses Old Murk-Eye and Old Icebeard, which are real rare creatures with real loot.
SCAFFOLDING_MARKERS = ("(Only GM can see it)", "[UNUSED]", "[PH]", "[DEPRECATED]")


class EraSourcesError(RuntimeError):
    pass


# ----- the two packed encodings -------------------------------------------------------------

# Both of the tables added on 2026-09-20, the creature kinds (`ck`) and the full lists behind
# the summary rows (`x` and `xl`), are packed rather than written as tables of their own.
# Nothing here needs `load`, `loadstring` or a bit library: every value comes back out with
# `math.floor`, `%`, `string.byte` and `string.sub`, which is all Lua 5.1 has.
#
# A record of one of the full lists is a fixed run of base 91 digits, most significant first.
# The alphabet is the printable bytes 35 ("#") to 126 ("~") with 92 (a backslash) left out,
# so no character the Lua writer would escape ever appears and one digit is always one byte.
PACK_BASE = 91
PACK_FIRST = 35
PACK_SKIPPED = 92

# The fields a record carries, in order and in digits. A container record names nothing and
# has no area: it carries the container item's own id where a named record carries its name.
PACK_NAME_DIGITS = 2  # the name's index into s, 0 for a record that names nothing
PACK_AREA_DIGITS = 2  # the area id, 0 for a record with no area
PACK_VALUE_DIGITS = 2  # the chance, the stock and the quest only flag: see pack_value
PACK_CONTAINER_DIGITS = 3  # the container item's own id (c = 13)

# The chance travels in tenths of a percent, so 1000 is 100.0%, and the quest only flag sits
# above it rather than taking a field of its own. A vendor record never carries a chance and
# never carries a condition, so its value is the limited stock count instead.
PACK_TENTHS = 10
PACK_QUEST_ONLY = 2048

# CreatureType, the beast Family and the level band, packed into ONE integer per name.
#
# The field order is not arbitrary. MaxLevel less MinLevel is 0, 1 or 2 for all but twenty of
# the names, and Family is 0 for every name that is not a beast, so the two cheapest fields go
# highest and most values stay at five or six digits. Packing MaxLevel itself would put two
# more digits on every name in the table.
KIND_TYPE_SPAN = 16  # CreatureType, 0 to 15 (this database uses 0 to 11)
KIND_LEVEL_SPAN = 128  # MinLevel, 0 to 127 (this database uses 1 to 63)
KIND_BAND_SPAN = 64  # MaxLevel less MinLevel, 0 to 63
KIND_FAMILY_SPAN = 64  # the beast Family, 0 to 63 (this database uses 0 to 27)

# The categories whose `n` is a creature, which are the ones a kind is shipped for.
CREATURE_CATEGORIES = frozenset({CAT_BOSS_DROP, CAT_CREATURE_DROP, CAT_SKINNED, CAT_PICKPOCKET})

# Brief N3: a VENDOR's name gets a kind too, so its page has a portrait and a map. A plain kind
# (zero or more) is a creature a c = 1, 6, 7 or 12 row names and no vendor row does, exactly as
# before. A vendor's kind is stored NEGATIVE, as -(2 * kind + both + 1), where both is 1 for a
# name that is a vendor AND a creature some creature row names, and 0 for a vendor only. The one
# added for the sign keeps a kind of 0 apart from its vendor twin. One integer per name still, and
# a vendor costs a byte or two over what its kind costs.
KIND_VENDOR_BOTH = 1

# The quest ids a quest giver's two lists hold, in base 91 digits. Three, because Classic quest ids
# run to 9,665 and two digits stop at 8,280.
QG_QUEST_DIGITS = 3

# Brief W12: what a quest asks the player to bring, in `qr`. One record per required item, the
# item id in QR_ITEM_DIGITS base 91 digits and the count in QR_COUNT_DIGITS. Three for the item,
# as a container's own id takes, because Classic item ids run past the 8,280 two digits hold; two
# for the count, because the most any 1.12 quest asks for is 1,200. pack_int fails the
# build rather than wrap if either is ever outgrown.
QR_ITEM_DIGITS = 3
QR_COUNT_DIGITS = 2

# ----- the trainers (brief P6a) ---------------------------------------------------------------
#
# A trainer's list in `tr` is the spell ids it teaches, each as TR_SPELL_DIGITS base 91 digits.
# Three, because the 1.12 spell ids a trainer teaches run to about 30,000 and two digits stop at
# 8,280; pack_int fails the build rather than wrap if one ever outgrows them.
TR_SPELL_DIGITS = 3

# `npc_trainer.spell` is usually the trainer's own "learn" spell rather than the spell the player
# ends up with: its effect is SPELL_EFFECT_LEARN_SPELL and its EffectTriggerSpell is the real one
# (the mage trainer's 1142 teaches 116 Frostbolt). The dump's own spell_template says which.
SPELL_EFFECT_LEARN_SPELL = 36

# SkillLine.CategoryID values: 7 the class trees and pet lines, 9 the secondary skills (Cooking,
# First Aid, Fishing), 11 the professions. All three are READ from THIS build's own
# SkillLineAbility (SKILL_CATEGORIES_READ), so a class spell is known and counted when it is
# refused; only TRAINER_SKILL_CATEGORIES SHIP. The cut, decided on brief P6a: class trainers are
# left out, because ItemTree's trainer rows are about recipes and a class trainer teaches no item,
# and their 27,038 pairs took the file to 1,705,074 bytes, past its then 1.6 MB budget (1.75 MB
# since 2026-09-29, raised for brief W12's qr and qt string titles; 2.0 MB since the same day,
# raised for brief W15's quest givers). Adding 7 back
# here is the whole of undoing it (see docs/era-sources.md).
SKILL_CATEGORY_CLASS = 7
SKILL_CATEGORY_SECONDARY = 9
SKILL_CATEGORY_PROFESSION = 11
SKILL_CATEGORIES_READ = frozenset({SKILL_CATEGORY_CLASS, SKILL_CATEGORY_SECONDARY, SKILL_CATEGORY_PROFESSION})
TRAINER_SKILL_CATEGORIES = frozenset({SKILL_CATEGORY_SECONDARY, SKILL_CATEGORY_PROFESSION})
# 2851 Engraving is a class category line holding the Season of Discovery rune engravings, which
# no trainer in the 1.12 dump teaches and WoW Forever does not have.
ENGRAVING_SKILL_LINE = 2851

# ----- the map pins -----------------------------------------------------------------------
#
# Until 2026-09-20 this module stored no coordinate at all. It now ships a handful of pins per
# creature NAME per AREA, for one purpose: a map on the creature page. What reaches the file is
# not a spawn table. Each creature's spawns are snapped to a grid of PIN_CELL percent of that
# zone's own map, the PIN_CAP fullest cells are kept, and each pin is the mean of its own cell
# quantised to a tenth of a percent, so about eleven thousand numbers stand for seventy thousand
# spawns. No respawn timer, no height, no orientation, no guid and no per spawn anything.
PIN_CAP = 6
PIN_CELL = 5.0
PIN_PLACES = 1

# A pin record is three fixed fields of base 91 digits, most significant first, in the same
# alphabet the `x` lists use: the area id, then x and y in tenths of a percent (0 to 1000). Two
# digits hold 0 to 8,280, which covers every Classic area id and every tenth of a percent.
PIN_AREA_DIGITS = 2
PIN_COORD_DIGITS = 2
PIN_TENTHS = 10

# How close a computed position has to sit to pfQuest's own figure for the two to be called
# agreed. pfQuest is a CHECK and nothing else: no pfQuest coordinate is shipped.
PIN_AGREEMENT = 0.5

# The UiMap types a pin is drawn on, named as the client's Enum.UIMapType names them
# (Blizzard_APIDocumentationGenerated/MapConstantsDocumentation.lua, Forever branch of the
# wow-ui-source mirror). Type 3 is Zone. Type 6 is Orphan, a map with its own art that the
# world map does not reach by drilling down from a continent: 1.60.1.70009 retyped Alterac
# Valley (1459), Arathi Basin (1461), Warsong Gulch (1460) and Darkspear Islands (2524) from
# Zone to Orphan with the same UiMapAssignment bounds, and dropping them lost Alterac Valley's
# 154 pins. Dungeon (4) and Micro (5) stay excluded: the Forever builds ship none so far, and
# a creature inside an instance keeps the instance area answer instead of a pin.
UI_MAP_TYPE_ZONE = 3
UI_MAP_TYPE_ORPHAN = 6
PIN_MAP_TYPES = frozenset({UI_MAP_TYPE_ZONE, UI_MAP_TYPE_ORPHAN})

# ----- the paths (brief W18) ----------------------------------------------------------------
#
# A creature that walks does not stand at its spawn point: Azuregos patrols a stretch of Azshara
# and Lord Kazzak paces the Tainted Scar. CMaNGOS states the walk as waypoints, per spawn in
# `creature_movement` (by guid) or per creature in `creature_movement_template` (by entry and
# path id), and a spawn walks one only when its `MovementType` is 2. The reader keeps every path
# in the dump; what ships (`pt`) is the paths of the creatures whose rank is in PATH_RANKS, the
# CMaNGOS boss rank, because a path is only worth its bytes on a boss's map. A path is placed
# on the zone map of its spawn's own pin area, every point by the same map_position the pins
# use, rounded to a tenth of a percent, a point off that map dropped, a point equal to the one
# before it dropped, and then thinned to PATH_CAP points: evenly spaced by index, the first and
# the last always kept. A path of fewer than PATH_MIN_POINTS points after that is not shipped.
PATH_RANKS = frozenset({3})
PATH_CAP = 32
PATH_MIN_POINTS = 2
# creature.MovementType 2: the spawn walks its waypoints.
MOVEMENT_WAYPOINT = 2

# ----- the instance areas -------------------------------------------------------------------
#
# A creature that lives inside an instance had no place at all until 2026-09-21. pfQuest states
# no area for one (see instance_areas below for the measurement), so `a` was absent on every row
# naming Skum, Onyxia or a Molten Core boss and the addon said "No place is known for this
# creature". The instance's own area is a first hand fact of the build, which is where it now
# comes from. A `Map.InstanceType` of 0 is the open world: the two continents and the handful of
# test maps, none of which ever answers this question.
MAP_INSTANCE_TYPE_WORLD = 0


def pack_digit(value: int) -> str:
    """One base 91 digit as one byte."""
    code = PACK_FIRST + value
    return chr(code if code < PACK_SKIPPED else code + 1)


def pack_int(value: int, digits: int) -> str:
    """One field, most significant digit first.

    A value that will not fit fails the build rather than wrapping: the addon reads these
    widths as fixed, so a table that outgrew one has to change both sides at once.
    """
    if value < 0 or value >= PACK_BASE**digits:
        raise EraSourcesError(f"{value} does not fit in {digits} base {PACK_BASE} digits")
    out: list[str] = []
    for _ in range(digits):
        out.append(pack_digit(value % PACK_BASE))
        value //= PACK_BASE
    return "".join(reversed(out))


def pack_value(row: Mapping, category: int) -> int:
    """The third field of a record: a stock count, or a chance with the quest only flag."""
    if category == CAT_VENDOR:
        return int(row.get("k", 0))
    value = int(round(float(row.get("p", 0.0)) * PACK_TENTHS))
    if "o" in row:
        value += PACK_QUEST_ONLY
    return value


def pack_record(row: Mapping, category: int) -> str:
    """One leftover source, as the fixed run of digits its category's layout asks for."""
    value = pack_int(pack_value(row, category), PACK_VALUE_DIGITS)
    if category == CAT_CONTAINER:
        return pack_int(int(row.get("i", 0)), PACK_CONTAINER_DIGITS) + value
    name = pack_int(int(row.get("n", 0)), PACK_NAME_DIGITS)
    area = pack_int(int(row.get("a", 0)), PACK_AREA_DIGITS)
    return name + area + value


def pack_pin(area: int, x: float, y: float) -> str:
    """One map pin: the area id, then x and y in tenths of a percent."""
    return (
        pack_int(area, PIN_AREA_DIGITS)
        + pack_int(int(round(x * PIN_TENTHS)), PIN_COORD_DIGITS)
        + pack_int(int(round(y * PIN_TENTHS)), PIN_COORD_DIGITS)
    )


def pack_path(area: int, points: Sequence[tuple[float, float]]) -> str:
    """One path (brief W18): the area id once, then each point's x and y in tenths of a percent,
    in walking order. The same digits and widths as a pin, with the area said once."""
    out = [pack_int(area, PIN_AREA_DIGITS)]
    for x, y in points:
        out.append(pack_int(int(round(x * PIN_TENTHS)), PIN_COORD_DIGITS))
        out.append(pack_int(int(round(y * PIN_TENTHS)), PIN_COORD_DIGITS))
    return "".join(out)


def unpack_int(text: str) -> int:
    """The inverse of pack_int, for readers inside the pipeline (boss_loot reads `pt` and `mp`)."""
    value = 0
    for ch in text:
        code = ord(ch)
        value = value * PACK_BASE + (code - 1 if code > PACK_SKIPPED else code) - PACK_FIRST
    return value


def pin_areas(packed: str) -> list[int]:
    """The area of every record of one packed `mp` or `op` string, in record order."""
    width = PIN_AREA_DIGITS + 2 * PIN_COORD_DIGITS
    return [unpack_int(packed[at : at + PIN_AREA_DIGITS]) for at in range(0, len(packed), width)]


def path_area(packed: str) -> int:
    """The area one packed `pt` path is drawn on."""
    return unpack_int(packed[:PIN_AREA_DIGITS])


def thin_path(points: Sequence[tuple[float, float]], cap: int = PATH_CAP) -> list[tuple[float, float]]:
    """At most `cap` points, evenly spaced by index, the first and the last always kept."""
    if len(points) <= cap:
        return list(points)
    if cap < 2:
        raise EraSourcesError(f"a path cap of {cap} cannot keep both ends")
    step = (len(points) - 1) / (cap - 1)
    return [points[int(round(number * step))] for number in range(cap)]


def pack_kind(creature_type: int, family: int, min_level: int, max_level: int) -> int:
    """What kind of creature a name is, as one integer. See the spans above for the order."""
    low = max(0, min(min_level, KIND_LEVEL_SPAN - 1))
    band = max(0, min(max(max_level, low) - low, KIND_BAND_SPAN - 1))
    kind = max(0, min(creature_type, KIND_TYPE_SPAN - 1))
    beast = max(0, min(family, KIND_FAMILY_SPAN - 1))
    return kind + KIND_TYPE_SPAN * (low + KIND_LEVEL_SPAN * (band + KIND_BAND_SPAN * beast))


def vendor_kind(packed: int, creature_too: bool) -> int:
    """A packed kind marked as a vendor's (brief N3): negative, and odd inside where the name is a
    creature some creature row names as well. See KIND_VENDOR_BOTH for the layout."""
    both = KIND_VENDOR_BOTH if creature_too else 0
    return -(2 * packed + both + 1)


def pack_quests(quests: Sequence[int]) -> str:
    """A quest giver's list (brief N3): each quest id as QG_QUEST_DIGITS base 91 digits."""
    return "".join(pack_int(quest, QG_QUEST_DIGITS) for quest in quests)


def pack_requires(requires: Sequence[tuple[int, int]]) -> str:
    """A quest's required items (brief W12): each as the item id then the count, in base 91."""
    return "".join(
        pack_int(item, QR_ITEM_DIGITS) + pack_int(count, QR_COUNT_DIGITS) for item, count in requires
    )


def pack_spells(spells: Sequence[int]) -> str:
    """A trainer's list (brief P6a): each spell id as TR_SPELL_DIGITS base 91 digits."""
    return "".join(pack_int(spell, TR_SPELL_DIGITS) for spell in spells)


# ----- the facts, as plain data so a fixture can hand build them ----------------------------


@dataclass(frozen=True)
class LootEntry:
    """One row of a loot template, holding only the columns this pipeline reads.

    `chance` is `ChanceOrQuestChance` exactly as the source writes it, so a negative value
    still means "only while the player is on the quest" when the rules look at it. `reference`
    is `-mincountOrRef` where the row points at a reference template instead of an item.
    """

    item: int
    chance: float
    group: int = 0
    reference: int = 0


@dataclass(frozen=True)
class CreatureFacts:
    """What `creature_template` states about one creature, stripped to facts.

    Every script column and every piece of text but the name and the `SubName` are never read.
    `subname` is `SubName`, the short title under a name ("Cooking Supplies"), read since
    2026-09-27 on the owner's ruling of that day and shipped in `st` for vendors and quest
    givers and enders only. `faction` is the `Faction` column, a FactionTemplate id, read on the
    same ruling and shipped in `cf` only as the side it resolves to through this build's own
    FactionTemplate and Faction tables (the pinned dump states one `Faction` column, not the
    later `FactionAlliance` and `FactionHorde` pair, and the reader takes whichever it finds).
    `creature_type` is `CreatureType` (1 beast, 2 dragonkin, and so on) and `family` is the
    beast `Family`, both plain ids: what KIND of thing a name is, so the interface can draw a
    spider differently from a murloc.

    `display` is the first `ModelId1..4` the row states, which is a `CreatureDisplayInfo` id and
    the one number the client's own portrait call takes. A creature states up to four models and
    picks one at spawn, so the first one it states is the one a row is drawn with; nothing here
    chooses between them on anything but that order.
    """

    id: int
    name: str = ""
    min_level: int = 0
    max_level: int = 0
    rank: int = 0
    creature_type: int = 0
    family: int = 0
    display: int = 0
    loot: int = 0
    skinning: int = 0
    pickpocket: int = 0
    vendor_template: int = 0
    subname: str = ""
    faction: int = 0
    # Brief P6a: `TrainerTemplateId`, the npc_trainer_template entry this creature teaches from
    # on top of its own npc_trainer rows. 0 for a creature that teaches from no template.
    trainer_template: int = 0


@dataclass(frozen=True)
class ObjectFacts:
    """What `gameobject_template` states about one world object, stripped to facts."""

    id: int
    name: str = ""
    kind: int = 0
    lock: int = 0
    loot: int = 0


@dataclass(frozen=True)
class Spawn:
    """One row of the cmangos `creature` table, stripped to a place on a map.

    `creature` is 0 on the rows that take their creature from `creature_spawn_entry` instead,
    which is how one point in the world spawns one of several creatures. `event` is
    `game_event_creature.event`: positive means the row only exists while that game event is
    running, negative means the row is REMOVED during it and is ordinary the rest of the year.
    `pooled` says the row is one member of a `pool_creature` pool, so one of the pool's points
    holds a creature at a time; every point is still a place the creature is found.

    The z, the orientation, the respawn times, the spawn distance, the movement type and the
    guid itself are read for nothing and reach no shipped table: `guid` is here only so the
    three side tables can be joined to the row.
    """

    guid: int
    creature: int
    map: int
    x: float
    y: float
    event: int = 0
    pooled: bool = False


@dataclass(frozen=True)
class SpawnPoint:
    """One spawn as pfQuest states it: a zone percentage and the area id it sits in.

    pfQuest's own `db/units.lua` has already done the reduction this pipeline cannot, so the
    area id is taken from here exactly as it always has been. The percentage is read only to
    tell one spawn from another and to CHECK the formula: no pfQuest coordinate is shipped.
    """

    x: float
    y: float
    area: int


@dataclass(frozen=True)
class MapBounds:
    """One `UiMapAssignment` row: where a zone map's corners sit in world coordinates.

    `region` is `Region_0`, `Region_1`, `Region_3` and `Region_4`, the min and max of world x
    and world y (`Region_2` and `Region_5` are a z clamp of plus or minus a million on every
    row and are read for nothing). `ui_min` and `ui_max` place the answer inside the sub
    rectangle the assignment covers, and are 0, 0, 1, 1 on 59 of this build's 61 rows.
    """

    ui_map: int
    map: int
    min_x: float
    min_y: float
    max_x: float
    max_y: float
    ui_min_x: float = 0.0
    ui_min_y: float = 0.0
    ui_max_x: float = 1.0
    ui_max_y: float = 1.0

    def key(self) -> tuple[int, int]:
        return (self.ui_map, self.map)


@dataclass(frozen=True)
class MapPin:
    """One shipped pin: a place on one zone map, as a percentage of it.

    `weight` is how many spawns fell in the cell this pin stands for. It is the sort key and
    it is NOT shipped: the player does not need a spawn count and it would be two more digits
    on every record.
    """

    area: int
    x: float
    y: float
    weight: int

    def order(self) -> tuple:
        return (self.area, -self.weight, self.x, self.y)


@dataclass(frozen=True)
class VendorOffer:
    """One line of `npc_vendor` or `npc_vendor_template`. `stock` 0 is unlimited."""

    vendor: int
    item: int
    stock: int = 0


@dataclass(frozen=True)
class QuestFacts:
    """One quest's title, race mask and the items it hands over.

    Quest text of every kind (`Details`, `Objectives`, `OfferRewardText`, `RequestItemsText`)
    is never read: the title is a name, and a name is a fact.
    """

    id: int
    title: str
    races: int = 0
    # The items the quest hands over.
    items: tuple[int, ...] = ()
    # The items the quest asks the player to bring, in the template's slot order. Read so that a
    # quest only drop can name the quest that makes it drop and, since brief W12, so that a quest
    # item can name the quest it is used by (`qr`). Never to describe the quest itself.
    requires: tuple[int, ...] = ()
    # Brief W12: how many of each `requires` asks for, slot by slot (`ReqItemCount1..4`). Empty,
    # or a count of 0, reads as one.
    require_counts: tuple[int, ...] = ()


@dataclass
class EraInput:
    """Everything the derivation reads, so the stage can be driven from a fixture too.

    Everything here but `areas`, `display_ids` and `curated_quests` comes from the two pinned
    files; `areas` is this build's own `AreaTable`, `display_ids` is this build's own
    `CreatureDisplayInfo` and `curated_quests` is the addon's hand maintained table.
    """

    creatures: dict[int, CreatureFacts] = field(default_factory=dict)
    objects: dict[int, ObjectFacts] = field(default_factory=dict)
    creature_loot: dict[int, list[LootEntry]] = field(default_factory=dict)
    skinning_loot: dict[int, list[LootEntry]] = field(default_factory=dict)
    pickpocket_loot: dict[int, list[LootEntry]] = field(default_factory=dict)
    object_loot: dict[int, list[LootEntry]] = field(default_factory=dict)
    fishing_loot: dict[int, list[LootEntry]] = field(default_factory=dict)
    item_loot: dict[int, list[LootEntry]] = field(default_factory=dict)
    reference_loot: dict[int, list[LootEntry]] = field(default_factory=dict)
    vendor_offers: list[VendorOffer] = field(default_factory=list)
    vendor_template_offers: list[VendorOffer] = field(default_factory=list)
    quests: dict[int, QuestFacts] = field(default_factory=dict)
    # Every quest_template entry, whatever it hands over or asks for, title or none. The
    # compile ships these ids beside Era's QuestV2 ids as the quests Classic Era knew, so a
    # quest on screen whose id is in neither reads as new in Forever.
    quest_ids: set[int] = field(default_factory=set)
    # quest id -> (the fixed reward item ids, the reward choice item ids), each in the
    # template's slot order with repeats dropped, for every quest_template entry that hands
    # over at least one item. Ids only: no counts and no text. The compile ships it as the
    # QuestRewards module.
    quest_rewards: dict[int, tuple[tuple[int, ...], tuple[int, ...]]] = field(default_factory=dict)
    areas: dict[int, str] = field(default_factory=dict)
    # Every CreatureDisplayInfo id THIS build carries. Nothing out of that table is shipped:
    # it is read so that a display id the client does not have is refused rather than handed
    # to a portrait call that could only fail.
    display_ids: set[int] = field(default_factory=set)
    unit_zones: dict[int, tuple[int, ...]] = field(default_factory=dict)
    object_zones: dict[int, tuple[int, ...]] = field(default_factory=dict)
    curated_quests: dict[int, set[int]] = field(default_factory=dict)
    # The map pins' three inputs. `spawns` is the cmangos `creature` table, whose positions are
    # the only coordinates this module ships; `spawn_entries` is `creature_spawn_entry`, which
    # names the creature of a row that leaves `id` at 0; `unit_points` is pfQuest per spawn, for
    # the area id and for the cross check. `area_maps` and `map_bounds` are THIS build's own.
    spawns: tuple[Spawn, ...] = ()
    spawn_entries: dict[int, tuple[int, ...]] = field(default_factory=dict)
    # Brief W18, the paths' three inputs: the guids whose `creature.MovementType` is a waypoint
    # walk; `creature_movement`, guid -> its waypoints in walking order as world (x, y); and
    # `creature_movement_template`, creature id -> path id -> the same. CMaNGOS positions only.
    waypoint_guids: set[int] = field(default_factory=set)
    paths: dict[int, tuple[tuple[float, float], ...]] = field(default_factory=dict)
    template_paths: dict[int, dict[int, tuple[tuple[float, float], ...]]] = field(default_factory=dict)
    unit_points: dict[int, tuple[SpawnPoint, ...]] = field(default_factory=dict)
    # areaId -> the zone level UiMap id this build gives it, for every area it can resolve.
    area_maps: dict[int, int] = field(default_factory=dict)
    # (uiMapId, continent mapId) -> that zone map's world bounds.
    map_bounds: dict[tuple[int, int], MapBounds] = field(default_factory=dict)
    # mapId -> the area THIS build gives the whole of that instance map, for every instance map
    # it names one for. A creature whose spawns are all on one such map lives inside that
    # instance and takes this as its area, because no open world area is true of it.
    instance_areas: dict[int, int] = field(default_factory=dict)
    # object id -> every map the cmangos `gameobject` table spawns it on (a guid that leaves `id`
    # at 0 counts for each entry `gameobject_spawn_entry` names). The map alone: the positions
    # are the object pins' input below, not this one's. It exists for one question, whether a herb or a vein
    # pfQuest states no zone for stands inside an instance (see instance_object_zones).
    object_spawn_maps: dict[int, tuple[int, ...]] = field(default_factory=dict)
    # The object map pins' three inputs (brief D7), the twins of `spawns`, `spawn_entries` and
    # `unit_points`. `object_spawns` is the cmangos `gameobject` table, kept only for a chest or a
    # fishing hole with a loot template (see lootable_object_spawns), each a Spawn whose
    # `creature` field holds the object id; `object_spawn_entries` is `gameobject_spawn_entry`
    # for the guids among them that leave `id` at 0; `object_points` is pfQuest per object spawn,
    # for the area id and for the cross check.
    object_spawns: tuple[Spawn, ...] = ()
    object_spawn_entries: dict[int, tuple[int, ...]] = field(default_factory=dict)
    object_points: dict[int, tuple[SpawnPoint, ...]] = field(default_factory=dict)
    # Brief N3: `creature_questrelation` (who starts a quest) and `creature_involvedrelation` (who
    # ends one), each as (creature id, quest id) in the dump's order, and the title of EVERY
    # quest_template entry that has one, which is what names the quests a giver's page lists.
    # Titles only: no quest text of any kind.
    quest_starts: list[tuple[int, int]] = field(default_factory=list)
    quest_ends: list[tuple[int, int]] = field(default_factory=list)
    quest_names: dict[int, str] = field(default_factory=dict)
    # Brief T1: FactionTemplate id -> the side it resolves to (FACTION_ALLIANCE, FACTION_HORDE or
    # FACTION_BOTH), from THIS build's own FactionTemplate and Faction tables by faction_sides.
    # A template this build does not carry has no entry, and a creature on it gets no `cf`.
    faction_sides: dict[int, int] = field(default_factory=dict)
    # Brief P6a, the trainers. `trainer_spells` is `npc_trainer` as (creature id, spell id) and
    # `trainer_template_spells` is `npc_trainer_template` as (template id, spell id), both in the
    # dump's order; `learned_spells` is spell_template's learn spells, spell id -> the spell it
    # teaches. `skill_spells` is THIS build's own SkillLineAbility, spell id -> the SkillLine
    # CategoryID it is filed under, for the TRAINER_SKILL_CATEGORIES lines only (a profession or
    # secondary line wins over a class one where a spell is filed under both).
    trainer_spells: list[tuple[int, int]] = field(default_factory=list)
    trainer_template_spells: list[tuple[int, int]] = field(default_factory=list)
    learned_spells: dict[int, int] = field(default_factory=dict)
    skill_spells: dict[int, int] = field(default_factory=dict)


@dataclass
class EraSources:
    """The derived table, ready to serialise, plus what was kept and what was refused."""

    strings: list[str] = field(default_factory=list)
    areas: dict[int, int] = field(default_factory=dict)
    rows: dict[int, list[dict]] = field(default_factory=dict)
    # questId -> its title's index into `s`, for the quests that make a quest only drop drop
    # and that no `c = 3` row names anywhere in the table.
    # Since brief W12 a value is either that index or, for a quest only `qr` carries whose title
    # `s` does not hold, the title itself as a plain string.
    quest_titles: dict[int, int | str] = field(default_factory=dict)
    # A creature name's index into `s` -> what kind of creature it is, packed by pack_kind.
    kinds: dict[int, int] = field(default_factory=dict)
    # A creature name's index into `s` -> the CreatureDisplayInfo id the client draws that
    # creature's portrait from. Every id here is one this build's own table carries.
    displays: dict[int, int] = field(default_factory=dict)
    # itemId -> category -> the number of the list in `lists` that holds the rest of it.
    list_index: dict[int, dict[int, int]] = field(default_factory=dict)
    # The lists themselves, each a packed string, each stored once however many items open it.
    lists: list[str] = field(default_factory=list)
    # A creature name's index into `s` -> its map pins, packed by pack_pin.
    pins: dict[int, str] = field(default_factory=dict)
    # An OBJECT name's index into `s` -> its map pins, packed by pack_pin (brief D7). Its own
    # table rather than `mp`, because one string can name a creature and an object both.
    object_pins: dict[int, str] = field(default_factory=dict)
    # Brief W18: a creature name's index into `s` -> the paths it walks, each a string packed by
    # pack_path, for a boss (PATH_RANKS) only. See docs/era-sources.md, "Paths".
    paths: dict[int, list[str]] = field(default_factory=dict)
    # Brief W19: a creature name's index into `s` -> how many records at the END of its `mp`
    # string are hand kept world boss spawn spots rather than CMaNGOS spawns. Written only by
    # boss_loot.apply_spots, from curated/world_boss_spots.json; empty without that file, and
    # then `mc` is not shipped at all. See docs/boss-loot.md, "World boss spots".
    curated_pins: dict[int, int] = field(default_factory=dict)
    # An object name's index into `s` -> the category its rows are filed under (8 herb, 9 vein,
    # 10 fishing pool, 11 chest), for every name `op` carries.
    object_kinds: dict[int, int] = field(default_factory=dict)
    # areaId -> the zone level UiMap id THIS build draws that area on, for every area `z` names
    # that resolves to one. An area with no entry has no map on this build.
    area_maps: dict[int, int] = field(default_factory=dict)
    # Brief N3: a creature or vendor name's index into `s` -> (the quests it starts, the quests it
    # ends), each a string packed by pack_quests, "" where it has none of that side.
    quest_givers: dict[int, tuple[str, str]] = field(default_factory=dict)
    # Brief T1: a vendor or quest giver NAME's index into `s` -> its SubName's index into `s`.
    subnames: dict[int, int] = field(default_factory=dict)
    # Brief T1: a vendor or quest giver NAME's index into `s` -> 1 Alliance, 2 Horde, 3 both.
    factions: dict[int, int] = field(default_factory=dict)
    # Brief P6a: a trainer NAME's index into `s` -> the spell ids it teaches, packed by pack_spells.
    trainers: dict[int, str] = field(default_factory=dict)
    # Brief W12: questId -> the items it asks the player to bring with their counts, packed by
    # pack_requires, for every kept quest that asks for an item this build ships.
    quest_requires: dict[int, str] = field(default_factory=dict)
    counts: dict[str, int] = field(default_factory=dict)
    dropped: dict[str, int] = field(default_factory=dict)

    def module_value(self, generated: str | None = None) -> dict:
        """The module table. `generated` is the compile's stamp, the same one the header prints.

        It ships as `g` (brief E85) so the addon can read at run time which compile a table came
        from: a guess module's creature references index `s` and hold only against the table
        they were compiled with. Left out when no stamp is given, as the unit tests do.
        """
        value = {
            "s": list(self.strings),
            "z": dict(self.areas),
            "r": dict(self.rows),
            "qt": dict(self.quest_titles),
            "ck": dict(self.kinds),
            "cd": dict(self.displays),
            "mp": dict(self.pins),
            "op": dict(self.object_pins),
            "pt": {index: list(walks) for index, walks in self.paths.items()},
            "ok": dict(self.object_kinds),
            "qg": {index: list(pair) for index, pair in self.quest_givers.items()},
            "zm": dict(self.area_maps),
            "st": dict(self.subnames),
            "cf": dict(self.factions),
            "tr": dict(self.trainers),
            "qr": dict(self.quest_requires),
            "x": dict(self.list_index),
            "xl": list(self.lists),
        }
        if self.curated_pins:
            value["mc"] = dict(self.curated_pins)
        if generated:
            value["g"] = generated
        return value


# ----- fetching and verifying the pinned files -----------------------------------------------


def sha256_bytes(data: bytes) -> str:
    return hashlib.sha256(data).hexdigest()


def verify_pin(pin: Pin, path: Path) -> int:
    """Check a file against its pinned size and sha256.

    A mismatch is a failure, not a reason to fetch again.
    """
    size = path.stat().st_size
    if size != pin.bytes:
        raise EraSourcesError(f"{path} is {size} bytes, expected {pin.bytes} for {pin.name} {pin.version}")
    digest = hashlib.sha256()
    with path.open("rb") as handle:
        for chunk in iter(lambda: handle.read(1 << 20), b""):
            digest.update(chunk)
    actual = digest.hexdigest()
    if actual != pin.sha256:
        raise EraSourcesError(
            f"{path} has sha256 {actual}, expected {pin.sha256} for {pin.name} {pin.version}; "
            "delete it and fetch again"
        )
    return size


def fetch_pin(
    pin: Pin,
    cache_dir: Path,
    *,
    force: bool = False,
    transport: httpx.BaseTransport | None = None,
    timeout: float = 300.0,
) -> Path:
    """Put one pinned file in the cache and return its path.

    One request, one file, only when the cache has not already got it. The cache directory is
    gitignored and nothing here is ever committed. CI never runs this: the suite reads hand
    written fixtures.
    """
    dest = pin.path(cache_dir)
    if dest.exists() and not force:
        verify_pin(pin, dest)
        return dest
    dest.parent.mkdir(parents=True, exist_ok=True)
    with httpx.Client(
        timeout=timeout,
        follow_redirects=True,
        headers=dict(REQUEST_HEADERS),
        transport=transport,
    ) as client:
        try:
            response = client.get(pin.url)
        except httpx.HTTPError as exc:
            raise EraSourcesError(f"{pin.url}: {exc}") from exc
    if response.status_code != 200:
        raise EraSourcesError(f"{pin.url} returned HTTP {response.status_code}")
    part = dest.with_name(dest.name + ".part")
    part.write_bytes(response.content)
    try:
        verify_pin(pin, part)
    except EraSourcesError:
        part.unlink(missing_ok=True)
        raise
    shutil.move(str(part), str(dest))
    return dest


def external_inputs() -> list[dict]:
    """What the build manifest records about the files this stage read."""
    return [
        {
            "name": pin.name,
            "version": pin.version,
            "url": pin.url,
            "sha256": pin.sha256,
            "bytes": pin.bytes,
            "note": CREDIT,
        }
        for pin in PINS
    ]


# ----- reading the cmangos dump ----------------------------------------------------------------

_CREATE = re.compile(r"^CREATE TABLE `([a-z_]+)` \(")
_COLUMN = re.compile(r"^\s*`([A-Za-z_0-9]+)`")
_INSERT = re.compile(r"^INSERT INTO `([a-z_]+)` VALUES ")

# Every table this stage reads, and nothing else. Every other table in the dump, which is most
# of it, is skipped without being parsed at all.
WANTED_TABLES = (
    "creature",
    "creature_spawn_entry",
    "pool_creature",
    # Brief W18: a pool that names a creature ENTRY rather than a spawn, so every spawn of that
    # creature is one member of the pool; and the waypoints a spawn or a creature walks. Of the
    # waypoint tables only the ids, the point number and the two world coordinates are read.
    "pool_creature_template",
    "creature_movement",
    "creature_movement_template",
    "game_event_creature",
    "creature_template",
    "gameobject_template",
    "gameobject",
    "gameobject_spawn_entry",
    "creature_loot_template",
    "skinning_loot_template",
    "pickpocketing_loot_template",
    "gameobject_loot_template",
    "fishing_loot_template",
    "item_loot_template",
    "reference_loot_template",
    "npc_vendor",
    "npc_vendor_template",
    "quest_template",
    # Brief N3: which creature starts a quest and which one ends it. Two columns each, a creature
    # id and a quest id, and nothing else in either table.
    "creature_questrelation",
    "creature_involvedrelation",
    # Brief P6a: which creature teaches which spell, directly or through a trainer template, and
    # spell_template's learn effects to turn a trainer's learn spell into the spell it teaches.
    "npc_trainer",
    "npc_trainer_template",
    "spell_template",
)

LOOT_TABLES = {
    "creature_loot_template": "creature_loot",
    "skinning_loot_template": "skinning_loot",
    "pickpocketing_loot_template": "pickpocket_loot",
    "gameobject_loot_template": "object_loot",
    "fishing_loot_template": "fishing_loot",
    "item_loot_template": "item_loot",
    "reference_loot_template": "reference_loot",
}


def split_values(line: str, start: int) -> Iterator[list[str]]:
    """Yield each `(...)` tuple of an extended INSERT as a list of raw field strings.

    A hand rolled scanner rather than a regex, because the dump's text columns hold brackets,
    commas and escaped quotes. Nothing it yields is kept: the callers take the numeric columns
    and the names and throw the rest away without ever looking at it.
    """
    i = start
    depth = 0
    field_chars: list[str] = []
    row: list[str] = []
    in_string = False
    escaped = False
    length = len(line)
    while i < length:
        ch = line[i]
        i += 1
        if in_string:
            if escaped:
                field_chars.append(ch)
                escaped = False
            elif ch == "\\":
                escaped = True
            elif ch == "'":
                in_string = False
            else:
                field_chars.append(ch)
            continue
        if ch == "'":
            in_string = True
            continue
        if ch == "(":
            depth += 1
            field_chars = []
            row = []
            continue
        if ch == ")" and depth:
            depth -= 1
            row.append("".join(field_chars).strip())
            yield row
            field_chars = []
            continue
        if ch == "," and depth == 1:
            row.append("".join(field_chars).strip())
            field_chars = []
            continue
        if depth:
            field_chars.append(ch)
    return


def _num(value: str | float | None, default: float = 0.0) -> float:
    if value is None or value == "NULL" or value == "":
        return default
    try:
        return float(value)
    except ValueError:
        return default


def _int(value: str | float | None, default: int = 0) -> int:
    return int(_num(value, default))


@dataclass
class _Reading:
    """What the dump reader accumulates before it can put it on an EraInput.

    The three spawn side tables are keyed by guid and the dump states `creature` before any of
    them, so the rows are gathered here and joined once the file has been read.
    """

    loot: dict[str, dict[int, list[LootEntry]]] = field(
        default_factory=lambda: {name: defaultdict(list) for name in LOOT_TABLES}
    )
    vendor_rows: list[VendorOffer] = field(default_factory=list)
    vendor_template_rows: list[VendorOffer] = field(default_factory=list)
    # guid -> (creature id, map, x, y), the `creature` table with everything else dropped.
    spawn_rows: list[tuple[int, int, int, float, float]] = field(default_factory=list)
    spawn_entries: dict[int, list[int]] = field(default_factory=lambda: defaultdict(list))
    events: dict[int, int] = field(default_factory=dict)
    pools: set[int] = field(default_factory=set)
    # Brief W18: the creature ids `pool_creature_template` pools, the guids whose MovementType is
    # a waypoint walk, and the waypoints themselves as (point number, x, y), per guid and per
    # (creature id, path id).
    pool_entries: set[int] = field(default_factory=set)
    waypoint_guids: set[int] = field(default_factory=set)
    paths: dict[int, list[tuple[int, float, float]]] = field(default_factory=lambda: defaultdict(list))
    template_paths: dict[tuple[int, int], list[tuple[int, float, float]]] = field(
        default_factory=lambda: defaultdict(list)
    )
    # guid -> (object id, map, x, y), the `gameobject` table with everything else dropped, and
    # the entries `gameobject_spawn_entry` names for a guid that leaves its id at 0.
    object_rows: list[tuple[int, int, int, float, float]] = field(default_factory=list)
    object_entries: dict[int, list[int]] = field(default_factory=lambda: defaultdict(list))


def read_cmangos(path: Path) -> EraInput:
    """Read the pinned dump into the facts this stage keeps, and nothing else.

    The dump is one gzipped mysqldump of 6,457 lines, each INSERT a single very long line, so
    it is read line by line and every table but WANTED_TABLES is skipped on the first regex.
    """
    era = EraInput()
    columns: dict[str, list[str]] = {}
    pending: str | None = None
    reading = _Reading()

    try:
        handle = gzip.open(path, "rt", encoding="utf-8", errors="replace")
    except OSError as exc:
        raise EraSourcesError(f"cannot read {path}: {exc}") from exc
    with handle:
        for line in handle:
            if pending is not None:
                if line.startswith(")"):
                    pending = None
                    continue
                found = _COLUMN.match(line)
                if found:
                    columns[pending].append(found.group(1))
                continue
            create = _CREATE.match(line)
            if create:
                # A table this stage does not read has its definition skipped without a single
                # column name being collected, and its INSERT lines are never parsed at all.
                pending = create.group(1) if create.group(1) in WANTED_TABLES else None
                if pending is not None:
                    columns[pending] = []
                continue
            insert = _INSERT.match(line)
            if not insert:
                continue
            table = insert.group(1)
            if table not in WANTED_TABLES or table not in columns:
                continue
            cols = columns[table]
            index = {name: position for position, name in enumerate(cols)}
            width = len(cols)
            for row in split_values(line, insert.end()):
                if len(row) != width:
                    continue
                _absorb(era, reading, table, row, index)

    for table, attribute in LOOT_TABLES.items():
        setattr(era, attribute, {entry: rows for entry, rows in sorted(reading.loot[table].items())})
    era.vendor_offers = reading.vendor_rows
    era.vendor_template_offers = reading.vendor_template_rows
    era.spawns = tuple(
        Spawn(
            guid=guid,
            creature=creature,
            map=map_id,
            x=x,
            y=y,
            event=reading.events.get(guid, 0),
            pooled=guid in reading.pools or (creature != 0 and creature in reading.pool_entries),
        )
        for guid, creature, map_id, x, y in sorted(reading.spawn_rows)
    )
    era.waypoint_guids = set(reading.waypoint_guids)
    era.paths = {guid: _walk(points) for guid, points in sorted(reading.paths.items())}
    template_paths: dict[int, dict[int, tuple[tuple[float, float], ...]]] = defaultdict(dict)
    for (entry, path_id), points in sorted(reading.template_paths.items()):
        template_paths[entry][path_id] = _walk(points)
    era.template_paths = dict(template_paths)
    era.spawn_entries = {
        guid: tuple(sorted(set(entries))) for guid, entries in sorted(reading.spawn_entries.items())
    }
    era.object_spawn_maps = object_maps(reading.object_rows, reading.object_entries)
    era.object_spawns, era.object_spawn_entries = lootable_object_spawns(
        reading.object_rows, reading.object_entries, era.objects
    )
    return era


def _walk(points: Sequence[tuple[int, float, float]]) -> tuple[tuple[float, float], ...]:
    """One path's waypoints in walking order (by point number), as world (x, y)."""
    return tuple((x, y) for _point, x, y in sorted(points))


def object_maps(rows: Sequence[tuple], entries: Mapping[int, Sequence[int]]) -> dict[int, tuple[int, ...]]:
    """object id -> the maps it spawns on, ascending. A guid with no id of its own stands for
    every entry `gameobject_spawn_entry` names for it. Each row is (guid, id, map, ...): the
    position the reader keeps behind the map is not read here."""
    maps: dict[int, set[int]] = defaultdict(set)
    for guid, oid, map_id, *_rest in rows:
        for member in (oid,) if oid else entries.get(guid, ()):
            if member:
                maps[member].add(map_id)
    return {oid: tuple(sorted(found)) for oid, found in sorted(maps.items())}


def _lootable(obj: ObjectFacts | None) -> bool:
    """A chest or a fishing hole with a loot template: the only objects a source row can name."""
    return obj is not None and obj.kind in (GO_TYPE_CHEST, GO_TYPE_FISHING_HOLE) and bool(obj.loot)


def lootable_object_spawns(
    rows: Sequence[tuple[int, int, int, float, float]],
    entries: Mapping[int, Sequence[int]],
    objects: Mapping[int, ObjectFacts],
) -> tuple[tuple[Spawn, ...], dict[int, tuple[int, ...]]]:
    """The `gameobject` rows an object pin could ever be made from, as spawns, and the spawn
    entries of the guids among them that leave their id at 0.

    Only a chest or a fishing hole with a loot template can be the object a source row names, so
    every other object's spawn (a door, a chair, a mailbox, a quest object) is dropped here, at
    the end of the streaming pass, and never reaches an EraInput. A Spawn's `creature` field
    holds the OBJECT id: the shape is the creature table's, and so is every rule read over it.
    """
    kept_entries: dict[int, tuple[int, ...]] = {}
    spawns: list[Spawn] = []
    for guid, oid, map_id, x, y in sorted(rows):
        if oid:
            if not _lootable(objects.get(oid)):
                continue
        else:
            members = tuple(sorted({e for e in entries.get(guid, ()) if _lootable(objects.get(e))}))
            if not members:
                continue
            kept_entries[guid] = members
        spawns.append(Spawn(guid=guid, creature=oid, map=map_id, x=x, y=y))
    return tuple(spawns), kept_entries


def _absorb(
    era: EraInput,
    reading: _Reading,
    table: str,
    row: list[str],
    index: Mapping[str, int],
) -> None:
    """Take one parsed row into the facts, by table. Every other column is dropped here."""

    def col(name: str) -> str | None:
        position = index.get(name)
        return row[position] if position is not None else None

    if table in LOOT_TABLES:
        entry = _int(col("entry"))
        item = _int(col("item"))
        mincount = _int(col("mincountOrRef"))
        reading.loot[table][entry].append(
            LootEntry(
                item=item,
                chance=_num(col("ChanceOrQuestChance")),
                group=_int(col("groupid")),
                reference=-mincount if mincount < 0 else 0,
            )
        )
        return
    if table == "creature_template":
        cid = _int(col("Entry"))
        display = 0
        # ModelId1 is the model a creature is nearly always drawn with; 2 to 4 are the other
        # models the server may pick at spawn. The first one stated is the answer, so a row that
        # leaves ModelId1 at 0 falls back through the three behind it rather than losing its id.
        for slot in ("ModelId1", "ModelId2", "ModelId3", "ModelId4"):
            display = _int(col(slot))
            if display > 0:
                break
        era.creatures[cid] = CreatureFacts(
            id=cid,
            name=(col("Name") or "").strip(),
            min_level=_int(col("MinLevel")),
            max_level=_int(col("MaxLevel")),
            rank=_int(col("Rank")),
            creature_type=_int(col("CreatureType")),
            family=_int(col("Family")),
            display=max(0, display),
            loot=_int(col("LootId")),
            skinning=_int(col("SkinningLootId")),
            pickpocket=_int(col("PickpocketLootId")),
            vendor_template=_int(col("VendorTemplateId")),
            # Brief T1, the owner's ruling of 2026-09-27: the title under the name and the
            # faction template id. The pinned dump states one `Faction` column; a later dump's
            # `FactionAlliance` is the same template for the side that matters first.
            # An unquoted NULL is how the dump leaves a SubName out, on nearly every creature.
            subname="" if col("SubName") in (None, "NULL") else (col("SubName") or "").strip(),
            faction=_int(col("Faction") if col("Faction") is not None else col("FactionAlliance")),
            trainer_template=_int(col("TrainerTemplateId")),
        )
        return
    if table in ("npc_trainer", "npc_trainer_template"):
        # Brief P6a: the entry and the spell, and nothing else: not the cost, not the required
        # skill, level or abilities, not the condition.
        pair = (_int(col("entry")), _int(col("spell")))
        (era.trainer_spells if table == "npc_trainer" else era.trainer_template_spells).append(pair)
        return
    if table == "spell_template":
        # Brief P6a: the id and the three effects with their trigger spells, and only for a spell
        # one of whose effects is a learn effect. No name, no text, nothing else of the spell.
        for slot in (1, 2, 3):
            if _int(col(f"Effect{slot}")) == SPELL_EFFECT_LEARN_SPELL:
                taught = _int(col(f"EffectTriggerSpell{slot}"))
                if taught > 0:
                    era.learned_spells[_int(col("Id"))] = taught
                    break
        return
    if table == "gameobject_template":
        oid = _int(col("entry"))
        era.objects[oid] = ObjectFacts(
            id=oid,
            name=(col("name") or "").strip(),
            kind=_int(col("type")),
            lock=_int(col("data0")),
            loot=_int(col("data1")),
        )
        return
    if table in ("npc_vendor", "npc_vendor_template"):
        offer = VendorOffer(vendor=_int(col("entry")), item=_int(col("item")), stock=_int(col("maxcount")))
        (reading.vendor_rows if table == "npc_vendor" else reading.vendor_template_rows).append(offer)
        return
    if table == "creature":
        # The position and the map, and nothing else: not the z, not the orientation, not the
        # respawn times and not the spawn distance. Since brief W18 the movement type is read for
        # one bit, whether the spawn walks its waypoints (MOVEMENT_WAYPOINT), kept apart from
        # Spawn in EraInput.waypoint_guids.
        if _int(col("MovementType")) == MOVEMENT_WAYPOINT:
            reading.waypoint_guids.add(_int(col("guid")))
        reading.spawn_rows.append(
            (
                _int(col("guid")),
                _int(col("id")),
                _int(col("map")),
                _num(col("position_x")),
                _num(col("position_y")),
            )
        )
        return
    if table == "creature_spawn_entry":
        reading.spawn_entries[_int(col("guid"))].append(_int(col("entry")))
        return
    if table == "gameobject":
        # The map and the position, and nothing else: not the z, not the orientation, not the
        # rotation, not the spawn mask and not the respawn times. Since 2026-09-27 (brief D7) the
        # position is read for the object map pins, the way the `creature` table's always was.
        reading.object_rows.append(
            (
                _int(col("guid")),
                _int(col("id")),
                _int(col("map")),
                _num(col("position_x")),
                _num(col("position_y")),
            )
        )
        return
    if table == "gameobject_spawn_entry":
        reading.object_entries[_int(col("guid"))].append(_int(col("entry")))
        return
    if table == "game_event_creature":
        reading.events[_int(col("guid"))] = _int(col("event"))
        return
    if table == "pool_creature":
        # The pool's own chance and description are read for nothing: what matters is that the
        # row is one member of a pool, so the point is a place the creature is found.
        reading.pools.add(_int(col("guid")))
        return
    if table == "pool_creature_template":
        # Brief W18: the same, for a pool that names the creature rather than one spawn of it.
        reading.pool_entries.add(_int(col("id")))
        return
    if table == "creature_movement":
        # Brief W18: the point number and the two world coordinates. Not the z, the orientation,
        # the wait time, the script or the comment.
        point = (_int(col("Point")), _num(col("PositionX")), _num(col("PositionY")))
        reading.paths[_int(col("Id"))].append(point)
        return
    if table == "creature_movement_template":
        point = (_int(col("Point")), _num(col("PositionX")), _num(col("PositionY")))
        reading.template_paths[(_int(col("Entry")), _int(col("PathId")))].append(point)
        return
    if table in ("creature_questrelation", "creature_involvedrelation"):
        pair = (_int(col("id")), _int(col("quest")))
        (era.quest_starts if table == "creature_questrelation" else era.quest_ends).append(pair)
        return
    if table == "quest_template":
        qid = _int(col("entry"))
        title = (col("Title") or "").strip()
        if qid > 0:
            era.quest_ids.add(qid)
            if title:
                era.quest_names[qid] = title
        fixed: list[int] = []
        for key in ("RewItemId1", "RewItemId2", "RewItemId3", "RewItemId4"):
            value = _int(col(key))
            if value > 0:
                fixed.append(value)
        choices: list[int] = []
        for number in range(1, 7):
            value = _int(col(f"RewChoiceItemId{number}"))
            if value > 0:
                choices.append(value)
        items: list[int] = fixed + choices
        if qid > 0 and items:
            era.quest_rewards[qid] = (tuple(dict.fromkeys(fixed)), tuple(dict.fromkeys(choices)))
        requires: list[int] = []
        require_counts: list[int] = []
        for number in range(1, 5):
            value = _int(col(f"ReqItemId{number}"))
            if value > 0:
                requires.append(value)
                # Brief W12, the owner's ruling of 2026-09-29: the count beside the id, a number.
                require_counts.append(_int(col(f"ReqItemCount{number}")))
        # A quest that only asks for something is kept too: it hands nothing over, so it makes
        # no c=3 row, but it is what lets a quest only drop name the quest behind it.
        if title and (items or requires):
            era.quests[qid] = QuestFacts(
                id=qid,
                title=title,
                races=_int(col("RequiredRaces")),
                items=tuple(items),
                requires=tuple(requires),
                require_counts=tuple(require_counts),
            )
        return


# ----- reading pfQuest's zone map ---------------------------------------------------------------

_PF_ID = re.compile(r"^  \[(\d+)\] = \{")
# { x, y, zone, respawn }. The third number is the area id, which is what this file has always
# been read for. The two coordinates in front of it are already a percentage of the zone map, and
# since 2026-09-20 they are read as well, for two things and no more: to tell one spawn of a
# creature from another so that each one's own area id can be taken, and to CHECK the formula the
# pipeline computes its own pins with. No pfQuest coordinate is ever shipped. The respawn timer
# is matched so the line can be recognised and is discarded.
_PF_COORD = re.compile(r"^\s*\[\d+\] = \{ (-?[\d.]+), (-?[\d.]+), (\d+), -?[\d.]+ \},?\s*$")


def read_spawn_points(path: Path) -> dict[int, tuple[SpawnPoint, ...]]:
    """id -> each spawn pfQuest states for it, as a zone percentage and an area id.

    Read with a line reader rather than a Lua interpreter so that nothing else in the file can
    reach the pipeline: a line that is not one spawn in the one shape above is not read at all.
    """
    points: dict[int, list[SpawnPoint]] = {}
    try:
        text = path.read_text(encoding="utf-8", errors="replace")
    except OSError as exc:
        raise EraSourcesError(f"cannot read {path}: {exc}") from exc
    current: int | None = None
    for line in text.splitlines():
        found = _PF_ID.match(line)
        if found:
            current = int(found.group(1))
            continue
        if current is None:
            continue
        coord = _PF_COORD.match(line)
        if coord:
            area = int(coord.group(3))
            if area > 0:
                points.setdefault(current, []).append(
                    SpawnPoint(x=float(coord.group(1)), y=float(coord.group(2)), area=area)
                )
    return {key: tuple(value) for key, value in sorted(points.items())}


def zones_from_points(points: Mapping[int, Sequence[SpawnPoint]]) -> dict[int, tuple[int, ...]]:
    """id -> the area ids that id spawns in, commonest first.

    Commonest first, ties by the lower area id, so the one area a row carries never depends on
    the order the file happened to state its spawns in.
    """
    zones: dict[int, tuple[int, ...]] = {}
    for key in sorted(points):
        seen: dict[int, int] = {}
        for point in points[key]:
            seen[point.area] = seen.get(point.area, 0) + 1
        if seen:
            order = sorted(seen.items(), key=lambda pair: (-pair[1], pair[0]))
            zones[key] = tuple(area for area, _count in order)
    return zones


def read_zone_map(path: Path) -> dict[int, tuple[int, ...]]:
    """id -> the area ids that id spawns in, commonest first, and nothing else. The stage itself
    reads the objects file through read_spawn_points since brief D7, because the object map pins
    match each spawn to its area the way the creature pins do; this is the zones alone."""
    return zones_from_points(read_spawn_points(path))


# ----- the three things that come from our own data --------------------------------------------


def area_names(conn: sqlite3.Connection, build: str) -> dict[int, str]:
    """areaId -> the name THIS build gives that area.

    The source states an area id and no name. A name a player reads has to be one the client
    itself uses, so it comes from the build's own AreaTable and never from either database.
    """
    try:
        cursor = conn.execute("SELECT ID, AreaName_lang FROM AreaTable WHERE build_id = ?", (build,))
    except sqlite3.OperationalError as exc:
        raise EraSourcesError(
            f"build {build} has no AreaTable loaded ({exc}); run "
            f"`itemtree-data fetch {build} -t AreaTable` then `itemtree-data load {build} -t AreaTable`"
        ) from exc
    names = {int(row["ID"]): str(row["AreaName_lang"] or "") for row in cursor}
    names = {area: name for area, name in names.items() if name}
    if not names:
        raise EraSourcesError(
            f"build {build} has no named AreaTable rows; run "
            f"`itemtree-data fetch {build} -t AreaTable` then `itemtree-data load {build} -t AreaTable`"
        )
    return names


def build_display_ids(conn: sqlite3.Connection, build: str) -> set[int]:
    """Every CreatureDisplayInfo id THIS build carries.

    The third party database states a creature's model id, and the client's own portrait call
    takes a display id: the two are the same id space, but only the client can say which of
    them it still has. So the shipped id is checked against this table and nothing else, and an
    id this build does not carry is refused rather than drawn.

    Read for the ID column alone. Nothing out of this table is shipped, the same way nothing
    but a name is taken out of AreaTable.
    """
    try:
        cursor = conn.execute("SELECT ID FROM CreatureDisplayInfo WHERE build_id = ?", (build,))
    except sqlite3.OperationalError as exc:
        raise EraSourcesError(
            f"build {build} has no CreatureDisplayInfo loaded ({exc}); run "
            f"`itemtree-data fetch {build} -t CreatureDisplayInfo` then "
            f"`itemtree-data load {build} -t CreatureDisplayInfo`"
        ) from exc
    ids = {int(row["ID"]) for row in cursor}
    if not ids:
        raise EraSourcesError(
            f"build {build} has no CreatureDisplayInfo rows; run "
            f"`itemtree-data fetch {build} -t CreatureDisplayInfo` then "
            f"`itemtree-data load {build} -t CreatureDisplayInfo`"
        )
    return ids


def _map_table(conn: sqlite3.Connection, build: str, table: str, columns: str) -> list[sqlite3.Row]:
    """One of the four map tables for this build, or a failure that says what to run."""
    try:
        cursor = conn.execute(f"SELECT {columns} FROM {table} WHERE build_id = ?", (build,))
    except sqlite3.OperationalError as exc:
        raise EraSourcesError(
            f"build {build} has no {table} loaded ({exc}); run "
            f"`itemtree-data fetch {build} -t {table}` then `itemtree-data load {build} -t {table}`"
        ) from exc
    rows = cursor.fetchall()
    if not rows:
        raise EraSourcesError(
            f"build {build} has no {table} rows; run "
            f"`itemtree-data fetch {build} -t {table}` then `itemtree-data load {build} -t {table}`"
        )
    return rows


def map_bounds(conn: sqlite3.Connection, build: str) -> dict[tuple[int, int], MapBounds]:
    """(zone UiMap id, continent map id) -> where that zone map's corners sit in the world.

    Only a Zone (`UiMap.Type` 3) or Orphan (Type 6) map is kept, see PIN_MAP_TYPES. The Forever
    builds ship no Dungeon map, so a spawn on an instance's own map id finds no bounds here and
    gets no pin, which is the honest answer: there is no map to draw it on.
    """
    zone_maps = {
        int(row["ID"])
        for row in _map_table(conn, build, "UiMap", "ID, Type")
        if int(row["Type"] or 0) in PIN_MAP_TYPES
    }
    out: dict[tuple[int, int], MapBounds] = {}
    columns = "UiMapID, MapID, Region_0, Region_1, Region_3, Region_4, UiMin_0, UiMin_1, UiMax_0, UiMax_1"
    for row in _map_table(conn, build, "UiMapAssignment", columns):
        ui_map = int(row["UiMapID"] or 0)
        if ui_map not in zone_maps:
            continue
        bounds = MapBounds(
            ui_map=ui_map,
            map=int(row["MapID"] or 0),
            min_x=_num(row["Region_0"]),
            min_y=_num(row["Region_1"]),
            max_x=_num(row["Region_3"]),
            max_y=_num(row["Region_4"]),
            ui_min_x=_num(row["UiMin_0"]),
            ui_min_y=_num(row["UiMin_1"]),
            ui_max_x=_num(row["UiMax_0"], 1.0),
            ui_max_y=_num(row["UiMax_1"], 1.0),
        )
        if bounds.max_x == bounds.min_x or bounds.max_y == bounds.min_y:
            continue
        out.setdefault(bounds.key(), bounds)
    if not out:
        raise EraSourcesError(f"build {build} has no zone level UiMapAssignment rows to place a pin in")
    return out


def area_maps(conn: sqlite3.Connection, build: str, areas: Mapping[int, str]) -> dict[int, int]:
    """areaId -> the Zone or Orphan UiMap id THIS build draws that area on (see PIN_MAP_TYPES).

    Three lookups, in this order, which is the order that works on this build: the area is the
    root area of a zone map's own `UiMapAssignment` row; or a `WorldMapOverlay` names it among
    the subzones one piece of map art covers, joined through `UiMapXMapArt`; or its
    `AreaTable.ParentAreaID` resolves one of the two.

    An area with no answer gets no entry and ships no pin. On 1.60.1.69913 that is the eight
    instance root areas whose parent is 0, because this build has no dungeon map to draw.
    """
    zone_maps = {
        int(row["ID"])
        for row in _map_table(conn, build, "UiMap", "ID, Type")
        if int(row["Type"] or 0) in PIN_MAP_TYPES
    }
    direct: dict[int, int] = {}
    for row in _map_table(conn, build, "UiMapAssignment", "UiMapID, AreaID"):
        area = int(row["AreaID"] or 0)
        ui_map = int(row["UiMapID"] or 0)
        if area and ui_map in zone_maps:
            direct.setdefault(area, ui_map)
    art = {
        int(row["UiMapArtID"] or 0): int(row["UiMapID"] or 0)
        for row in _map_table(conn, build, "UiMapXMapArt", "UiMapArtID, UiMapID")
    }
    overlaid: dict[int, int] = {}
    for row in _map_table(
        conn, build, "WorldMapOverlay", "UiMapArtID, AreaID_0, AreaID_1, AreaID_2, AreaID_3"
    ):
        ui_map = art.get(int(row["UiMapArtID"] or 0), 0)
        if ui_map not in zone_maps:
            continue
        for column in ("AreaID_0", "AreaID_1", "AreaID_2", "AreaID_3"):
            area = int(row[column] or 0)
            if area:
                overlaid.setdefault(area, ui_map)
    parents = {
        int(row["ID"]): int(row["ParentAreaID"] or 0)
        for row in conn.execute("SELECT ID, ParentAreaID FROM AreaTable WHERE build_id = ?", (build,))
    }

    def resolve(area: int) -> int:
        seen: set[int] = set()
        while area and area not in seen:
            seen.add(area)
            found = direct.get(area) or overlaid.get(area)
            if found:
                return found
            area = parents.get(area, 0)
        return 0

    out: dict[int, int] = {}
    for area in sorted(areas):
        found = resolve(area)
        if found:
            out[area] = found
    return out


def instance_areas(conn: sqlite3.Connection, build: str, areas: Mapping[int, str]) -> dict[int, int]:
    """mapId -> the area THIS build gives the whole of that instance map.

    A creature inside an instance has no open world area, and neither database states one for
    it: on the pinned files not one of the 934 creatures whose spawns are all on a single
    instance map carries a pfQuest area at all. The cmangos spawn row does carry the MAP id
    though, and a map's own area is a first hand fact of the build, so that is where it comes
    from. Only an instance map is ever an answer: `InstanceType` 0 is the open world.

    Two lookups, in this order, which is the order that is first hand:

      1. `Map.AreaTableID`, the map's own root area. 23 of this build's instance maps state one,
         Wailing Caverns, Molten Core and Onyxia's Lair among them.
      2. otherwise the one `AreaTable` row whose `ContinentID` is that map and whose
         `ParentAreaID` is 0, where there is EXACTLY one. That adds Scholomance, Stratholme,
         Scarlet Monastery, Shadowfang Keep, Zul'Farrak and the two Razorfens.

    Where the first states an area the second is not consulted, because the map's own column is
    the better fact: on Blackrock Spire, Blackrock Depths and Sunken Temple the build carries a
    second area of the same place and the map names the one the zone is properly called.

    Where neither answers, no area is shipped and the row keeps the empty place it has today.
    That is two maps on 1.60.1.69913: Deadmines states no `AreaTableID` and its map carries five
    parentless areas (Westfall, The Great Sea, Unused Ironcladcove, ***On Map Dungeon*** and The
    Deadmines), and Alterac Valley carries two. There is no single right answer there, so the
    stage takes none rather than guessing one.
    """
    direct: dict[int, int] = {}
    instance_maps: set[int] = set()
    for row in _map_table(conn, build, "Map", "ID, AreaTableID, InstanceType"):
        map_id = int(row["ID"] or 0)
        if int(row["InstanceType"] or 0) == MAP_INSTANCE_TYPE_WORLD:
            continue
        instance_maps.add(map_id)
        area = int(row["AreaTableID"] or 0)
        if area in areas:
            direct[map_id] = area
    roots: dict[int, list[int]] = defaultdict(list)
    for row in conn.execute(
        "SELECT ID, ParentAreaID, ContinentID FROM AreaTable WHERE build_id = ?", (build,)
    ):
        if int(row["ParentAreaID"] or 0):
            continue
        area = int(row["ID"] or 0)
        if area in areas:
            roots[int(row["ContinentID"] or 0)].append(area)
    out = dict(direct)
    for map_id in sorted(instance_maps - set(direct)):
        found = roots.get(map_id, ())
        if len(found) == 1:
            out[map_id] = found[0]
    return dict(sorted(out.items()))


# ----- the side a creature is on (brief T1) ----------------------------------------------------
#
# The owner's ruling of 2026-09-27: a creature's `Faction` (a FactionTemplate id) may be read, and
# what ships is one number per name, the side the template resolves to through THIS build's own
# FactionTemplate and Faction tables. The template's own group bits say it first: a template that
# is a member of or friendly to exactly one of the two player groups is that side's, and one
# friendly to every player (the player group bit in FriendGroup) or to both is both. A template
# friendly to neither is read by what it is hostile to: hostile to exactly one side makes it the
# other side's, hostile to both makes it both. Only then does the Faction tree decide, by the root
# its faction hangs from (469 Alliance, 67 Horde). Anything else, which is every neutral vendor
# (Booty Bay, Gadgetzan, the Argent Dawn), is both.

FACTION_GROUP_PLAYER = 0x1
FACTION_GROUP_ALLIANCE = 0x2
FACTION_GROUP_HORDE = 0x4
FACTION_ROOT_ALLIANCE = 469
FACTION_ROOT_HORDE = 67
# A Faction parent chain longer than this is a loop in the data, and is read as no root at all.
FACTION_DEPTH = 16
FACTION_TEMPLATE_SLOTS = 8


@dataclass(frozen=True)
class FactionTemplateFacts:
    """One `FactionTemplate` row: the faction it belongs to, its three group masks and the
    factions it lists as friends and as enemies by id."""

    id: int
    faction: int = 0
    group: int = 0
    friend_group: int = 0
    enemy_group: int = 0
    friends: tuple[int, ...] = ()
    enemies: tuple[int, ...] = ()


def faction_root(faction: int, parents: Mapping[int, int]) -> int:
    """The top of a faction's `ParentFactionID` chain, or 0 for a loop."""
    current = faction
    for _step in range(FACTION_DEPTH):
        parent = parents.get(current, 0)
        if not parent:
            return current
        current = parent
    return 0


def template_side(template: FactionTemplateFacts, parents: Mapping[int, int]) -> int:
    """The side one faction template is on: FACTION_ALLIANCE, FACTION_HORDE or FACTION_BOTH."""
    if template.friend_group & FACTION_GROUP_PLAYER:
        return FACTION_BOTH
    roots_friend = {faction_root(f, parents) for f in template.friends if f}
    roots_enemy = {faction_root(f, parents) for f in template.enemies if f}
    member = template.group | template.friend_group
    alliance = bool(member & FACTION_GROUP_ALLIANCE) or FACTION_ROOT_ALLIANCE in roots_friend
    horde = bool(member & FACTION_GROUP_HORDE) or FACTION_ROOT_HORDE in roots_friend
    if alliance != horde:
        return FACTION_ALLIANCE if alliance else FACTION_HORDE
    if alliance:
        return FACTION_BOTH
    enemy = template.enemy_group
    hostile_alliance = bool(enemy & FACTION_GROUP_ALLIANCE) or FACTION_ROOT_ALLIANCE in roots_enemy
    hostile_horde = bool(enemy & FACTION_GROUP_HORDE) or FACTION_ROOT_HORDE in roots_enemy
    if hostile_alliance != hostile_horde:
        return FACTION_HORDE if hostile_alliance else FACTION_ALLIANCE
    if hostile_alliance:
        return FACTION_BOTH
    root = faction_root(template.faction, parents)
    if root == FACTION_ROOT_ALLIANCE:
        return FACTION_ALLIANCE
    if root == FACTION_ROOT_HORDE:
        return FACTION_HORDE
    return FACTION_BOTH


def faction_sides(templates: Sequence[FactionTemplateFacts], parents: Mapping[int, int]) -> dict[int, int]:
    """FactionTemplate id -> its side, for every template given."""
    ordered = sorted(templates, key=lambda template: template.id)
    return {template.id: template_side(template, parents) for template in ordered}


def read_faction_sides(conn: sqlite3.Connection, build: str) -> dict[int, int]:
    """FactionTemplate id -> its side, from THIS build's own FactionTemplate and Faction tables.

    Read for the ids, the group masks, the friend and enemy lists and the parent ids. No faction
    name, no reputation figure and nothing else out of either table is read or shipped.
    """

    def number(row: sqlite3.Row, column: str) -> int:
        return int(row[column] or 0) if column in row.keys() else 0

    templates = [
        FactionTemplateFacts(
            id=number(row, "ID"),
            faction=number(row, "Faction"),
            group=number(row, "FactionGroup"),
            friend_group=number(row, "FriendGroup"),
            enemy_group=number(row, "EnemyGroup"),
            friends=tuple(number(row, f"Friend_{slot}") for slot in range(FACTION_TEMPLATE_SLOTS)),
            enemies=tuple(number(row, f"Enemies_{slot}") for slot in range(FACTION_TEMPLATE_SLOTS)),
        )
        for row in _map_table(conn, build, "FactionTemplate", "*")
    ]
    parents = {
        number(row, "ID"): number(row, "ParentFactionID") for row in _map_table(conn, build, "Faction", "*")
    }
    return faction_sides(templates, parents)


def skill_spell_categories(
    abilities: Sequence[tuple[int, int]], categories: Mapping[int, int]
) -> dict[int, int]:
    """spell id -> the SkillLine CategoryID a trainer's spell is filed under (brief P6a).

    `abilities` is SkillLineAbility as (spell, skill line) and `categories` is SkillLine's id to
    CategoryID. Only SKILL_CATEGORIES_READ lines count, and never the Engraving line. A spell
    filed under a profession or secondary line and a class line both reads as the profession.
    """
    out: dict[int, int] = {}
    for spell, line in abilities:
        category = categories.get(line)
        if spell <= 0 or line == ENGRAVING_SKILL_LINE or category not in SKILL_CATEGORIES_READ:
            continue
        current = out.get(spell)
        if current is None or current == SKILL_CATEGORY_CLASS:
            out[spell] = category
    return dict(sorted(out.items()))


def read_skill_spells(conn: sqlite3.Connection, build: str) -> dict[int, int]:
    """THIS build's own SkillLineAbility and SkillLine, reduced by skill_spell_categories.

    Read for the spell ids, the skill line ids and the category ids. No name, no rank, no class
    mask and nothing else out of either table is read or shipped.
    """
    abilities = [
        (int(row["Spell"] or 0), int(row["SkillLine"] or 0))
        for row in _map_table(conn, build, "SkillLineAbility", '"Spell", "SkillLine"')
    ]
    categories = {
        int(row["ID"] or 0): int(row["CategoryID"] or 0)
        for row in _map_table(conn, build, "SkillLine", '"ID", "CategoryID"')
    }
    return skill_spell_categories(abilities, categories)


_QUEST_BLOCK = re.compile(r"^  \[(\d+)\] = \{", re.MULTILINE)
_COMMENT = re.compile(r"--[^\n]*")


def parse_curated_quests(text: str) -> dict[int, set[int]]:
    """questId -> the item ids our own curated quest table already hands back.

    Data/curated/Quests.lua is hand maintained in the addon and is a first hand fact about the
    game, so a source row saying the same thing is noise. The file is a plain Lua table
    literal written in one shape, so it is read with a reader rather than a Lua interpreter.
    """
    rewards: dict[int, set[int]] = {}
    marks = list(_QUEST_BLOCK.finditer(text))
    for position, mark in enumerate(marks):
        quest = int(mark.group(1))
        end = marks[position + 1].start() if position + 1 < len(marks) else len(text)
        body = _COMMENT.sub("", text[mark.end() : end])
        items: set[int] = set()
        for key in ("rewards", "choice"):
            found = re.search(key + r"\s*=\s*\{([^}]*)\}", body)
            if found:
                items.update(int(value) for value in re.findall(r"\d+", found.group(1)))
        rewards[quest] = items
    return rewards


def read_curated_quests(path: Path) -> dict[int, set[int]]:
    try:
        text = path.read_text(encoding="utf-8")
    except OSError as exc:
        raise EraSourcesError(f"cannot read the curated quests at {path}: {exc}") from exc
    return parse_curated_quests(text)


# ----- the rules ----------------------------------------------------------------------------


def chance_percent(value: float | None) -> float | None:
    """A loot table chance as a percentage, or None when the number is not worth shipping.

    The source states a percentage directly. Zero, anything above 100 and anything that rounds
    below 0.1 are refused, and the row is kept without a chance, which reads as "we do not
    know" instead of as a wrong number. A quest only drop reaches this as its absolute value,
    under exactly the same rules as any other chance.
    """
    if value is None:
        return None
    percent = round(float(value), CHANCE_PLACES)
    if percent < MIN_CHANCE or percent > 100.0:
        return None
    return percent


def is_quest_only(entry: LootEntry) -> bool:
    """A negative ChanceOrQuestChance: the item drops only while the player is on the quest.

    The row is kept and marked. "Which creature drops it" is the answer a player wants for a
    quest item, and the addon can say the condition in words even though it cannot check it.
    The number itself is the absolute value, which is the chance the source states.
    """
    return entry.chance < 0


def is_scaffolding(name: str) -> bool:
    """Whether a creature or object name marks a row as build scaffolding, not content.

    Deliberately narrow. A loose rule ("starts with Old", "contains TEST") refuses Old
    Murk-Eye, Old Icebeard and Old Serra'kis, which are real rare creatures with real loot.
    """
    if not name:
        return True
    return any(marker in name for marker in SCAFFOLDING_MARKERS)


def faction_of(races: int) -> int | None:
    """The side a quest's race mask implies, or None for a quest open to everyone."""
    if races <= 0:
        return None
    alliance = bool(races & RACE_MASK_ALLIANCE)
    horde = bool(races & RACE_MASK_HORDE)
    if alliance and not horde:
        return FACTION_ALLIANCE
    if horde and not alliance:
        return FACTION_HORDE
    return None


@dataclass(frozen=True)
class Drop:
    """What one loot template gives one item: how often, and on what condition.

    `quest_only` is the source's negative chance, meaning the item drops only while the player
    is on a quest that asks for it. It is a fact about the drop, not a reason to hide it.
    """

    chance: float
    quest_only: bool = False


@dataclass(frozen=True)
class _Normalised:
    """One loot row after the group rule, with its chance made positive and its flag kept."""

    item: int
    chance: float
    reference: int
    quest_only: bool


def _group_chances(entries: Sequence[LootEntry]) -> list[_Normalised]:
    """Apply the loot group rule: a zero chance inside a group shares what the group has left.

    A groupid of 0 means the row rolls on its own. Inside a group exactly one row is chosen,
    the explicit chances are taken first and the rows that state none divide the remainder.
    A quest chance is negative in the source, so the group arithmetic is done on absolute
    values and the flag travels beside the number.
    """
    by_group: dict[int, list[LootEntry]] = defaultdict(list)
    for entry in entries:
        by_group[entry.group].append(entry)
    out: list[_Normalised] = []
    for group, rows in sorted(by_group.items()):
        stated = [_Normalised(row.item, abs(row.chance), row.reference, is_quest_only(row)) for row in rows]
        if group == 0:
            out.extend(stated)
            continue
        explicit = sum(row.chance for row in stated if row.chance > 0)
        zeros = [row for row in stated if row.chance <= 0]
        share = max(0.0, 100.0 - explicit) / len(zeros) if zeros else 0.0
        for row in stated:
            out.append(row if row.chance > 0 else _Normalised(row.item, share, row.reference, row.quest_only))
    return out


def expand_loot(
    table: Mapping[int, Sequence[LootEntry]],
    reference_loot: Mapping[int, Sequence[LootEntry]],
    dropped: dict[str, int],
) -> dict[int, dict[int, Drop]]:
    """template entry -> {itemId: the best Drop that template gives it}.

    A row whose `reference` is set points at a reference template rather than an item, and the
    item's effective chance is the two multiplied. References are followed to
    MAX_REFERENCE_DEPTH and a template that reappears on its own path is a loop: it is counted
    and abandoned rather than followed. A reference reached through a quest chance is quest
    only all the way down.

    Where one template gives the same item both ways, the unconditional drop wins: it is the
    better answer and the condition would be false of it.
    """

    def walk(
        entries: Sequence[LootEntry],
        weight: float,
        path: tuple[int, ...],
        quest_only: bool,
        into: dict[int, Drop],
    ) -> None:
        for entry in _group_chances(entries):
            conditional = quest_only or entry.quest_only
            if entry.reference:
                if entry.reference in path or len(path) >= MAX_REFERENCE_DEPTH:
                    dropped["refLoop"] += 1
                    continue
                walk(
                    reference_loot.get(entry.reference, ()),
                    weight * entry.chance / 100.0,
                    (*path, entry.reference),
                    conditional,
                    into,
                )
                continue
            if entry.item <= 0:
                continue
            # weight is 1.0 at the top and the product of the referencing rows' chances below
            # it, so a 20% row pointing at a template that gives the item 50% reads 10%.
            #
            # A chance of zero still makes a row: the source states plenty of them, and the
            # honest answer is "this creature drops it and we cannot say how often", not
            # silence. The chance rule drops the number later and keeps the row.
            found = into.get(entry.item)
            effective = weight * entry.chance
            better = (not conditional, effective)
            if found is None or better > (not found.quest_only, found.chance):
                into[entry.item] = Drop(chance=effective, quest_only=conditional)

    out: dict[int, dict[int, Drop]] = {}
    for entry_id in sorted(table):
        acc: dict[int, Drop] = {}
        walk(table[entry_id], 1.0, (), False, acc)
        out[entry_id] = acc
    return out


class _Strings:
    """A string table that hands back 1 based indexes and keeps each string once."""

    def __init__(self) -> None:
        self._index: dict[str, int] = {}
        self._values: list[str] = []

    def add(self, value: str) -> int:
        found = self._index.get(value)
        if found is None:
            found = len(self._index) + 1
            self._index[value] = found
            self._values.append(value)
        return found

    def find(self, value: str) -> int:
        """The insertion index a string already has, or 0 where the table does not hold it."""
        return self._index.get(value, 0)

    def value(self, index: int) -> str:
        """The string at one insertion index, or "" for an index this table never handed out."""
        return self._values[index - 1] if 0 < index <= len(self._values) else ""

    def sorted_table(self, first: Collection[int] = ()) -> tuple[list[str], dict[int, int]]:
        """The strings in sorted order, and a remap from the insertion index to the new one.

        Sorting keeps the file stable: the same inputs always compile to the same bytes.

        `first` is insertion indexes that must take the lowest numbers once the table is too long
        for them (brief W15, 2026-09-29): the names a packed list record carries, whose field is
        PACK_NAME_DIGITS base 91 digits and stops at 8,280. A table longer than that is two sorted
        runs, those strings and then every other one, so every list record still fits; a table
        that fits is the one sorted run it always was, so a small table's indexes do not move.
        """
        fits = len(self._values) < PACK_BASE**PACK_NAME_DIGITS
        front = set() if fits else {self._values[i - 1] for i in first if 0 < i <= len(self._values)}
        order = sorted(front) + sorted(value for value in self._index if value not in front)
        remap = {self._index[value]: position + 1 for position, value in enumerate(order)}
        return order, remap


# ----- one candidate source, before the caps ---------------------------------------------------


@dataclass(frozen=True)
class _Source:
    """One thing that gives an item, before the caps decide whether it gets named."""

    category: int
    name: str = ""
    area: int = 0
    chance: float = 0.0
    stock: int = 0
    container: int = 0
    min_level: int = 0
    max_level: int = 0
    # The source says this one only drops while the player is on a quest that asks for it.
    quest_only: bool = False
    # The quest that asks for it, where the source names one without guesswork.
    quest: int = 0
    # A herb or a vein only: where this zone stands in the node's own zones, commonest first.
    # It orders a node's zone rows (see _node_rows) and nothing else.
    spot: int = 0

    def order(self) -> tuple:
        """Best first, and never by anything that varies between runs.

        A drop anyone can get sorts before a quest only one, so the cap of three named rows
        spends its slots on the answer that is true for every player first.
        """
        return (self.quest_only, -self.chance, self.name, self.area, self.container)


def _lock_kind(graph: BuildFacts, lock_id: int) -> str:
    """What this build's own Lock and LockType say a locked object asks of the player.

    The name is preferred over the id, because the name is what the client itself calls the
    skill; the well known ids are the fallback for a build whose LockType is not loaded.
    """
    info = graph.locks.get(lock_id)
    if info is None:
        return ""
    for lock_type, _skill in info.types:
        named = (graph.lock_types.get(lock_type) or "").strip().lower()
        if named in ("herbalism", "mining", "fishing"):
            return named
        if not named and lock_type in LOCK_NAMES:
            return LOCK_NAMES[lock_type]
    return ""


def _object_category(graph: BuildFacts, obj: ObjectFacts) -> int:
    if obj.kind == GO_TYPE_FISHING_HOLE:
        return CAT_FISHED
    kind = _lock_kind(graph, obj.lock)
    if kind == "herbalism":
        return CAT_HERB
    if kind == "mining":
        return CAT_VEIN
    if kind == "fishing":
        return CAT_FISHED
    return CAT_OBJECT


def _zone_of(zones: Mapping[int, tuple[int, ...]], key: int, areas: Mapping[int, str]) -> int:
    """The area id a creature or object is most often found in, where this build names it."""
    for area in zones.get(key, ()):  # commonest first
        if area in areas:
            return area
    return 0


def instance_zones(era_input: EraInput) -> dict[int, int]:
    """creature id -> the area of the instance it lives inside, where that is its whole place.

    Only where EVERY spawn the dump keeps for that creature is on ONE map and that map is an
    instance this build names an area for. A creature with spawns on two instance maps, or on an
    instance map and the open world both, gets nothing here: the answer would be half true, and
    the open world area it already has is the better one.

    The spawns are read through the same `_spawns_by_creature` rules the pins use, so a game
    event only spawn is not a place the creature is found here either.
    """
    if not era_input.instance_areas:
        return {}
    by_creature, _event_only, _nameless = _spawns_by_creature(era_input.spawns, era_input.spawn_entries)
    out: dict[int, int] = {}
    for creature in sorted(by_creature):
        places = {spawn.map for spawn in by_creature[creature]}
        if len(places) != 1:
            continue
        area = era_input.instance_areas.get(next(iter(places)), 0)
        if area:
            out[creature] = area
    return out


def instance_object_zones(era_input: EraInput) -> dict[int, int]:
    """object id -> the area of the instance it stands inside, where that is its whole place.

    The object twin of instance_zones, by the same rule: only where EVERY spawn the dump keeps
    for that object is on ONE map and that map is an instance this build names an area for.
    pfQuest states no zone for an object inside an instance, so without this a herb in Zul'Gurub
    is a row with no place at all.
    """
    if not era_input.instance_areas:
        return {}
    out: dict[int, int] = {}
    for oid, maps in sorted(era_input.object_spawn_maps.items()):
        if len(maps) != 1:
            continue
        area = era_input.instance_areas.get(maps[0], 0)
        if area:
            out[oid] = area
    return out


def collect(era_input: EraInput, graph: BuildFacts, dropped: dict[str, int]) -> dict[int, list[_Source]]:
    """Every candidate source for every item, before any cap is applied."""
    areas = era_input.areas
    creatures = era_input.creatures
    objects = era_input.objects
    candidates: dict[int, list[_Source]] = defaultdict(list)

    # itemId -> the one quest whose own required item fields ask for it. The source states
    # this directly, so it costs nothing and guesses nothing: where two or more quests ask
    # for the same item there is no single right answer and the row simply carries no q.
    asks: dict[int, list[int]] = defaultdict(list)
    for quest_id in sorted(era_input.quests):
        for required in era_input.quests[quest_id].requires:
            asks[required].append(quest_id)

    def asked_by(item: int) -> int:
        found = asks.get(item, ())
        return found[0] if len(found) == 1 else 0

    # Where a creature lives inside an instance, that instance IS its place. Read once, and only
    # ever consulted for a creature neither database names an open world area for.
    inside = instance_zones(era_input)

    def place_of(cid: int) -> int:
        """The area a creature's row carries: the open world one first, the instance second."""
        return _zone_of(era_input.unit_zones, cid, areas) or inside.get(cid, 0)

    expanded = {
        "creature": expand_loot(era_input.creature_loot, era_input.reference_loot, dropped),
        "skinning": expand_loot(era_input.skinning_loot, era_input.reference_loot, dropped),
        "pickpocket": expand_loot(era_input.pickpocket_loot, era_input.reference_loot, dropped),
        "object": expand_loot(era_input.object_loot, era_input.reference_loot, dropped),
        "fishing": expand_loot(era_input.fishing_loot, era_input.reference_loot, dropped),
        "item": expand_loot(era_input.item_loot, era_input.reference_loot, dropped),
    }

    # Creatures: one loot template can serve many creatures, so the map runs the other way.
    for attribute, key, category in (
        ("creature", "loot", CAT_CREATURE_DROP),
        ("skinning", "skinning", CAT_SKINNED),
        ("pickpocket", "pickpocket", CAT_PICKPOCKET),
    ):
        by_template: dict[int, list[int]] = defaultdict(list)
        for cid in sorted(creatures):
            template = getattr(creatures[cid], key)
            if template:
                by_template[template].append(cid)
        for template, items in expanded[attribute].items():
            for cid in by_template.get(template, ()):
                facts = creatures[cid]
                if is_scaffolding(facts.name):
                    dropped["scaffolding"] += 1
                    continue
                # A boss keeps the category the first version of this module used, because a
                # boss drop is a different answer from "a hundred trash mobs drop it".
                kind = CAT_BOSS_DROP if (category == CAT_CREATURE_DROP and facts.rank == 3) else category
                for item, drop in sorted(items.items()):
                    candidates[item].append(
                        _Source(
                            category=kind,
                            name=facts.name,
                            area=place_of(cid),
                            chance=drop.chance,
                            min_level=facts.min_level,
                            max_level=facts.max_level,
                            quest_only=drop.quest_only,
                            quest=asked_by(item) if drop.quest_only else 0,
                        )
                    )

    # World objects. Only a chest and a fishing hole ever carry loot a player can take.
    inside_objects = instance_object_zones(era_input)
    by_object_template: dict[int, list[int]] = defaultdict(list)
    for oid in sorted(objects):
        obj = objects[oid]
        if obj.kind in (GO_TYPE_CHEST, GO_TYPE_FISHING_HOLE) and obj.loot:
            by_object_template[obj.loot].append(oid)
    for template, items in expanded["object"].items():
        for oid in by_object_template.get(template, ()):
            obj = objects[oid]
            if is_scaffolding(obj.name):
                dropped["scaffolding"] += 1
                continue
            category = _object_category(graph, obj)
            spawn_zones = [area for area in era_input.object_zones.get(oid, ()) if area in areas]
            # A herb or a vein is one name in many places, so it is listed by zone, commonest
            # first; one pfQuest places nowhere takes the instance it stands inside, where the
            # dump's own spawns say so. Everything else is listed once, in the zone it is
            # commonest in.
            if category in NODE_CATEGORIES and spawn_zones:
                places = spawn_zones[:MAX_NODE_ZONES]
            elif category in NODE_CATEGORIES and inside_objects.get(oid):
                places = [inside_objects[oid]]
            else:
                places = [spawn_zones[0]] if spawn_zones else [0]
            for item, drop in sorted(items.items()):
                for spot, area in enumerate(places):
                    candidates[item].append(
                        _Source(
                            category=category,
                            name=obj.name,
                            area=area,
                            chance=drop.chance,
                            quest_only=drop.quest_only,
                            quest=asked_by(item) if drop.quest_only else 0,
                            spot=spot,
                        )
                    )

    # Fishing by zone: the template entry IS an area id, stated first hand by the source.
    for area, items in expanded["fishing"].items():
        if area not in areas:
            dropped["noArea"] += 1
            continue
        for item, drop in sorted(items.items()):
            candidates[item].append(
                _Source(
                    category=CAT_FISHED,
                    area=area,
                    chance=drop.chance,
                    quest_only=drop.quest_only,
                    quest=asked_by(item) if drop.quest_only else 0,
                )
            )

    # Container items: the container is an item this build names itself, so the row carries its
    # id and no string, and the addon can make it a real edge instead of a dead end.
    for container, items in expanded["item"].items():
        if container not in graph.items:
            dropped["containerNotShipped"] += 1
            continue
        for item, drop in sorted(items.items()):
            candidates[item].append(
                _Source(
                    category=CAT_CONTAINER,
                    container=container,
                    chance=drop.chance,
                    quest_only=drop.quest_only,
                    quest=asked_by(item) if drop.quest_only else 0,
                )
            )

    # Vendors: a creature sells its own lines and its template's.
    by_template_offers: dict[int, list[VendorOffer]] = defaultdict(list)
    for offer in era_input.vendor_template_offers:
        by_template_offers[offer.vendor].append(offer)
    direct: dict[int, list[VendorOffer]] = defaultdict(list)
    for offer in era_input.vendor_offers:
        direct[offer.vendor].append(offer)
    for cid in sorted(set(direct) | {c for c in creatures if creatures[c].vendor_template}):
        facts = creatures.get(cid)
        if facts is None:
            # An npc_vendor line for a creature the dump has no template row for. Nothing to
            # name, so nothing to show.
            dropped["scaffolding"] += 1
            continue
        if is_scaffolding(facts.name):
            dropped["scaffolding"] += 1
            continue
        offers = list(direct.get(cid, ()))
        if facts.vendor_template:
            offers.extend(by_template_offers.get(facts.vendor_template, ()))
        # A vendor inside an instance gets the instance too. It falls out of the same call and
        # says the same true thing: five vendors on this build stand inside one.
        area = place_of(cid)
        for offer in offers:
            if offer.item <= 0:
                continue
            candidates[offer.item].append(
                _Source(category=CAT_VENDOR, name=facts.name, area=area, stock=offer.stock)
            )

    return candidates


# ----- the caps ---------------------------------------------------------------------------------


def _summary(category: int, group: Sequence[_Source], total: int | None = None) -> dict:
    """The row that stands for a whole category: how many sources it has, and their level band.

    `t` is always the total for that category on that item, never the leftover. The addon
    subtracts the named rows it has already drawn, which is one rule for both the capped case
    (three named, t of 242, so "and 239 more") and the summarise in place case (no named rows
    at all, so "184 vendors"). One meaning, decidable from the list itself. For a herb or a vein
    the sources are NODES, so `total` is the node count and the addon counts the nodes it drew.
    """
    row: dict = {"c": category, "t": len(group) if total is None else total}
    levels = [source for source in group if source.min_level]
    if levels:
        row["lo"] = min(source.min_level for source in levels)
        row["hi"] = max(source.max_level or source.min_level for source in levels)
    # o only where the condition is true of EVERY source the row stands for. A group holding
    # one drop anyone can get is not a quest only group.
    if group and all(source.quest_only for source in group):
        row["o"] = 1
    return row


def _named_row(source: _Source, strings: _Strings, used_areas: dict[int, int], areas: Mapping[int, str]):
    row: dict = {"c": source.category}
    if source.container:
        row["i"] = source.container
    elif source.name:
        row["n"] = strings.add(source.name)
    if source.area:
        row["a"] = source.area
        used_areas[source.area] = strings.add(areas[source.area])
    percent = chance_percent(source.chance)
    if percent is not None:
        row["p"] = percent
    if source.stock:
        row["k"] = source.stock
    if source.quest_only:
        row["o"] = 1
        if source.quest:
            row["q"] = source.quest
    return row


def by_node(ranked: Sequence[_Source]) -> list[list[_Source]]:
    """A herb's or a vein's sources, grouped into nodes, in the order to draw them.

    A node is one name. The nodes go best first (a node anyone can gather before a quest only
    one, then the node's best chance, then its name), and inside one node its zone rows go the
    way the node's own zones do: anyone first, best chance first, then commonest first as the
    spawn table states them, then area id. Nothing here varies between runs.

    A row with no area inside a node that has zones says nothing its zone rows do not (one of
    the node's objects pfQuest places nowhere, Copper Vein's on Copper Ore), so it is dropped.
    """
    nodes: dict[str, list[_Source]] = {}
    for source in ranked:
        nodes.setdefault(source.name, []).append(source)
    for name, group in nodes.items():
        placed = [source for source in group if source.area]
        if placed:
            nodes[name] = placed
    groups = [
        sorted(group, key=lambda source: (source.quest_only, -source.chance, source.spot, source.area))
        for group in nodes.values()
    ]
    groups.sort(
        key=lambda group: (
            all(source.quest_only for source in group),
            -max(source.chance for source in group),
            group[0].name,
        )
    )
    return groups


def _node_rows(
    category: int,
    ranked: Sequence[_Source],
    listed: Callable[[Sequence[_Source]], list[dict]],
    strings: _Strings,
    used_areas: dict[int, int],
    areas: Mapping[int, str],
    counts: dict[str, int],
) -> tuple[list[dict], list[dict]]:
    """Rule 1 for a herb or a vein, counted in NODES rather than rows.

    The first MAX_NAMED_ROWS nodes are named, each with all its zone rows together; the summary
    row's `t` is the node count; and the list behind it holds the remaining nodes' zone rows in
    the same node major order. The leftover of one exception is the same, by node: four nodes
    are four named nodes and no summary.
    """
    nodes = by_node(ranked)
    named = MAX_NAMED_ROWS
    if len(nodes) == MAX_NAMED_ROWS + 1:
        named = len(nodes)
        counts["summaryOfOne"] += 1
    rows = [_named_row(source, strings, used_areas, areas) for node in nodes[:named] for source in node]
    if len(nodes) > named:
        counts["summaryRows"] += 1
        rows.append(_summary(category, ranked, total=len(nodes)))
        return rows, listed([source for node in nodes[named:] for source in node])
    return rows, []


def _rows_for_category(
    category: int,
    sources: list[_Source],
    strings: _Strings,
    used_areas: dict[int, int],
    areas: Mapping[int, str],
    counts: dict[str, int],
    creature_names: set[str],
) -> tuple[list[dict], list[dict]]:
    """The rows one category puts on one item, and the rest of the list behind them.

    The second half of the answer is the sources a summary row stands for, in the same order
    and in the same row shape, so they can be packed into `xl` and opened by a player. A
    category that got no summary row has nothing left over, and `c = 5` never ships a list.
    """
    # The same creature, object or vendor can reach an item twice, through a template and
    # through a reference. One name in one place is one row.
    unique: dict[tuple, _Source] = {}
    for source in sources:
        key = (source.name, source.area, source.container)
        best = unique.get(key)
        if best is None or source.chance > best.chance:
            unique[key] = source
    ranked = sorted(unique.values(), key=lambda source: source.order())

    if category == CAT_CREATURE_DROP and len(ranked) > WORLD_DROP_CREATURES:
        # Rule 2: naming three of seven hundred says less than "it drops out in the world".
        counts["worldDropRule"] += 1
        # No chance on it. The best of seven hundred creatures is 100% for Refreshing Spring
        # Water, and "World drop, 100%" is a sentence that is true of one creature and false
        # of the row. A summary row never carries a chance, whichever rule made it.
        #
        # No list either, and this is the one place a list is refused rather than shipped:
        # the 1,098 world drop rows stand for 357,692 creatures between them, which is about
        # 2.1 MB packed. See docs/era-sources.md.
        return [_summary(CAT_WORLD_DROP, ranked)], []

    def listed(rest: Sequence[_Source]) -> list[dict]:
        # A name in a list is a name the player can now read, so it gets a kind like any
        # other: the list rows are the ones a search has to match.
        if category in CREATURE_CATEGORIES:
            creature_names.update(source.name for source in rest if source.name)
        return [_named_row(source, strings, used_areas, areas) for source in rest]

    if category in NODE_CATEGORIES:
        return _node_rows(category, ranked, listed, strings, used_areas, areas, counts)

    if category == CAT_VENDOR and len(ranked) > VENDOR_SUMMARY_AT:
        # Rule 3: three arbitrary vendors out of 184 say less than the count does. The count
        # names none of them, so the whole list is what sits behind it.
        counts["vendorSummaryRule"] += 1
        return [_summary(CAT_VENDOR, ranked)], listed(ranked)

    # Rule 1, and the exception the owner asked for on 2026-09-20: a summary standing for
    # exactly one source says less than that source does, and the player cannot open it, so
    # where the cap would leave one over it is named instead and no summary row is written.
    named = MAX_NAMED_ROWS
    if len(ranked) == MAX_NAMED_ROWS + 1:
        named = len(ranked)
        counts["summaryOfOne"] += 1
    rows = [_named_row(source, strings, used_areas, areas) for source in ranked[:named]]
    if category in CREATURE_CATEGORIES:
        creature_names.update(source.name for source in ranked[:named] if source.name)
    if len(ranked) > named:
        # Everything past the cap is kept as a truthful count, never silently dropped, and the
        # rest of the list is shipped behind it so the count can be opened and searched.
        counts["summaryRows"] += 1
        rows.append(_summary(category, ranked))
        return rows, listed(ranked[named:])
    return rows, []


def _quest_rows(
    offered: Sequence[QuestFacts],
    strings: _Strings,
    counts: dict[str, int],
) -> list[dict]:
    """The one quest row for an item, with the other turn ins behind it in `m`.

    The shape is unchanged from the first version of this module: the first quest in `q`, `n`
    and `f`, and up to MAX_FURTHER_QUESTS others in `m`, each with the same three keys. The
    commonest reason an item has several is that each side has its own turn in.
    """
    if not offered:
        return []
    if len(offered) > 1:
        counts["multiQuest"] += 1
    first, *further = offered
    row: dict = {"c": CAT_QUEST, "q": first.id, "n": strings.add(first.title)}
    side = faction_of(first.races)
    if side:
        row["f"] = side
    if len(further) > MAX_FURTHER_QUESTS:
        counts["furtherQuestsDropped"] += len(further) - MAX_FURTHER_QUESTS
        further = further[:MAX_FURTHER_QUESTS]
    if further:
        entries = []
        for quest in further:
            entry: dict = {"q": quest.id, "n": strings.add(quest.title)}
            side = faction_of(quest.races)
            if side:
                entry["f"] = side
            entries.append(entry)
        row["m"] = entries
        counts["furtherQuests"] += len(entries)
    return [row]


def _quest_titles(
    era_input: EraInput,
    entries: Mapping[int, Sequence[dict]],
    strings: _Strings,
) -> dict[int, int]:
    """questId -> its title's index into `s`, for the quests an `o` row names and nothing else.

    A quest only row carries `q`, the quest that makes the item drop, but the addon can only
    title a quest the table itself names, and it names a quest by handing an item over on it
    (`c = 3`). 1,526 rows carry `q` and only 592 of those quests appear on a `c = 3` row
    anywhere in the table, so the other 934 rows said "only while on a quest" although the
    source database has the title in front of it.

    The titles the addon cannot already reach are shipped here, in one small table rather than
    as a key on each row: 478 quests against 934 rows, and it measured 1.8 KB smaller. Titles
    only. No `Details`, no `Objectives`, no `RequestItemsText`, ever.
    """
    handed_over: set[int] = set()
    for rows in entries.values():
        for row in rows:
            if row["c"] == CAT_QUEST:
                handed_over.add(row["q"])
                for further in row.get("m", ()):
                    handed_over.add(further["q"])
    titles: dict[int, int] = {}
    for rows in entries.values():
        for row in rows:
            if "o" not in row:
                continue
            quest = row.get("q")
            if not quest or quest in handed_over or quest in titles:
                continue
            facts = era_input.quests.get(quest)
            if facts is not None and facts.title:
                titles[quest] = strings.add(facts.title)
    return titles


def _creature_kinds(
    era_input: EraInput,
    names: set[str],
    strings: _Strings,
    counts: dict[str, int],
) -> dict[int, int]:
    """A creature name's index into `s` -> what kind of creature it is, packed by pack_kind.

    Keyed by the NAME and not by a creature id, because the table has never carried creature
    ids and the row the player reads is a name: every row naming "Deviate Creeper" wants the
    same icon. Where two creatures share a name and disagree, the commoner CreatureType wins
    (ties by the lower id, so the answer never depends on dictionary order), the commoner
    Family among the creatures of that type wins with it, and the level band is the widest of
    all of them: a name that covers levels 11 to 14 and 36 to 40 covers 11 to 40.

    Ids and numbers only. `SubName` is not read here. Since 2026-09-27, on the owner's ruling of
    that day, it is read for vendors and quest givers alone and ships in `st`: see
    _titles_and_sides.
    """
    by_name: dict[str, list[CreatureFacts]] = defaultdict(list)
    for creature_id in sorted(era_input.creatures):
        facts = era_input.creatures[creature_id]
        if facts.name in names:
            by_name[facts.name].append(facts)
    kinds: dict[int, int] = {}
    conflicts = 0
    for name in sorted(by_name):
        creatures = by_name[name]
        types = Counter(facts.creature_type for facts in creatures)
        kind = min(types.items(), key=lambda pair: (-pair[1], pair[0]))[0]
        families = Counter(facts.family for facts in creatures if facts.creature_type == kind)
        family = min(families.items(), key=lambda pair: (-pair[1], pair[0]))[0] if families else 0
        low = min(facts.min_level for facts in creatures)
        high = max(max(facts.max_level, facts.min_level) for facts in creatures)
        if len({(f.creature_type, f.family, f.min_level, f.max_level) for f in creatures}) > 1:
            conflicts += 1
        kinds[strings.add(name)] = pack_kind(kind, family, low, high)
    counts["kindConflicts"] = conflicts
    return kinds


def _creature_displays(
    era_input: EraInput,
    names: set[str],
    strings: _Strings,
    counts: dict[str, int],
    dropped: dict[str, int],
) -> dict[int, int]:
    """A creature name's index into `s` -> the display id the client draws its portrait from.

    Keyed by the NAME, for the same reason `ck` is: the table has never carried creature ids
    and every row naming "Deviate Creeper" wants the same portrait. Where two creatures share a
    name and state different models the commonest wins, ties by the lower display id so the
    answer never depends on dictionary order.

    Every id is checked against THIS build's own `CreatureDisplayInfo` and an id the build does
    not carry is dropped: the addon may only ever hand the client an id the client has. A name
    whose creatures state no model at all simply gets no entry, which reads in the addon exactly
    as a name with no kind does, and the row keeps its stock kind icon.

    One plain integer per name. No portrait file, no model path and no art of any kind is
    shipped: the id names the client's own model and the client draws it.
    """
    by_name: dict[str, list[CreatureFacts]] = defaultdict(list)
    for creature_id in sorted(era_input.creatures):
        facts = era_input.creatures[creature_id]
        if facts.name in names:
            by_name[facts.name].append(facts)
    displays: dict[int, int] = {}
    conflicts = 0
    without = 0
    for name in sorted(by_name):
        stated = [facts for facts in by_name[name] if facts.display > 0]
        if not stated:
            without += 1
            continue
        counted = Counter(facts.display for facts in stated)
        if len(counted) > 1:
            conflicts += 1
        display = min(counted.items(), key=lambda pair: (-pair[1], pair[0]))[0]
        if display not in era_input.display_ids:
            dropped["displayNotInBuild"] += 1
            continue
        displays[strings.add(name)] = display
    counts["displayConflicts"] = conflicts
    counts["namesWithoutDisplay"] = without
    return displays


# ----- the map pins ---------------------------------------------------------------------------


def map_position(bounds: MapBounds, x: float, y: float) -> tuple[float, float]:
    """A world position as a percentage of one zone map, by this build's own assignment row.

    Both axes cross over and both invert, which is what makes this worth spelling out. World x
    runs north (high) to south (low) and drives the map's y, which runs north 0 to south 100.
    World y runs west (high) to east (low) and drives the map's x, which runs west 0 to east
    100. `ui_min` and `ui_max` then place the answer inside the sub rectangle the assignment
    covers, which does nothing on all but this build's two Azeroth rows.

    Verified against published pins: Hogger computes to 26.4, 93.7 in Elwynn Forest against
    classicdb.ch's 26.4, 93.7, and Goldshire to 42.5, 65.9, which is the 42, 65 everyone quotes.
    """
    north = (bounds.max_x - x) / (bounds.max_x - bounds.min_x)
    west = (bounds.max_y - y) / (bounds.max_y - bounds.min_y)
    across = bounds.ui_min_x + west * (bounds.ui_max_x - bounds.ui_min_x)
    down = bounds.ui_min_y + north * (bounds.ui_max_y - bounds.ui_min_y)
    return across * 100.0, down * 100.0


def reduce_pins(area: int, points: Sequence[tuple[float, float]]) -> list[MapPin]:
    """One creature's spawns in one area, reduced to at most PIN_CAP points.

    Snap each spawn to a grid of PIN_CELL percent of the zone map (about 25 pixels on a map
    drawn 500 pixels wide, where a pin is 12 to 16 pixels, so two kept pins cannot sit on top
    of one another), rank the cells by how many spawns fell in them, keep the fullest PIN_CAP,
    and make each pin the mean of its own cell to PIN_PLACES decimal places.

    Ties are broken by the cell's own position, so the answer never depends on the order the
    spawns were read in. One pass over the group, and no clustering library.
    """
    cells: dict[tuple[int, int], list[tuple[float, float]]] = defaultdict(list)
    for x, y in points:
        cells[(int(x // PIN_CELL), int(y // PIN_CELL))].append((x, y))
    ranked = sorted(cells.items(), key=lambda pair: (-len(pair[1]), pair[0]))
    pins: list[MapPin] = []
    for _cell, members in ranked[:PIN_CAP]:
        pins.append(
            MapPin(
                area=area,
                x=round(sum(point[0] for point in members) / len(members), PIN_PLACES),
                y=round(sum(point[1] for point in members) / len(members), PIN_PLACES),
                weight=len(members),
            )
        )
    return pins


def _spawns_by_creature(
    spawns: Sequence[Spawn], entries: Mapping[int, Sequence[int]]
) -> tuple[dict[int, list[Spawn]], int, int]:
    """creature id -> the spawns that are always there, plus what was left out and why.

    Two of the dump's own rules are applied here and nowhere else:

      * a row whose `id` is 0 takes its creature from `creature_spawn_entry`, and a row with no
        entry there names no creature and is left out (568 of the 2,802 on this dump);
      * a row `game_event_creature` gives a POSITIVE event id only exists while that event is
        running, so it is left out: a Hallow's End spawn is not where the creature is found. A
        negative event id means the row is removed during the event and is ordinary the rest of
        the year, so it is kept.

    A pooled row is kept. One member of a pool holds a creature at a time, but every point in
    the pool is a place the creature is found, which is exactly what a pin says.
    """
    by_creature: dict[int, list[Spawn]] = defaultdict(list)
    event_only = 0
    nameless = 0
    for spawn in spawns:
        if spawn.event > 0:
            event_only += 1
            continue
        ids = (spawn.creature,) if spawn.creature else tuple(entries.get(spawn.guid, ()))
        if not ids:
            nameless += 1
            continue
        for creature in ids:
            by_creature[creature].append(spawn)
    return by_creature, event_only, nameless


def _pin_area(
    spawn: Spawn,
    candidates: Sequence[int],
    maps: Mapping[int, int],
    bounds: Mapping[tuple[int, int], MapBounds],
    points: Mapping[int, list[SpawnPoint]],
) -> tuple[int, float, float] | None:
    """Which of a creature's own areas one spawn sits in, and where on that area's map.

    The area comes from the spawn's own area id and never from testing the zone boxes, which
    overlap badly: 35,476 of the dump's 66,310 positions fall inside two or more of this
    build's zone assignments. A creature known in one area has every spawn in it. A creature
    known in several (468 names have two zones, the worst has sixteen) has each spawn matched to
    the pfQuest spawn it IS, by position on each candidate's own map, and takes that spawn's
    area id, which is the same number this file has always been read for.

    None where the spawn is on a map the zone has no assignment for, which is every spawn
    inside an instance, or where the computed position falls outside every candidate's map.
    Where pfQuest states no position at all for a candidate the commonest area wins, which is
    what the rest of this stage has always done with the same list.
    """
    best: tuple[int, float, float] | None = None
    best_gap = float("inf")
    for area in candidates:  # commonest first
        found = bounds.get((maps[area], spawn.map))
        if found is None:
            continue
        x, y = map_position(found, spawn.x, spawn.y)
        if not (0.0 <= x <= 100.0 and 0.0 <= y <= 100.0):
            continue
        if len(candidates) == 1:
            return (area, x, y)
        gap = min(
            (max(abs(point.x - x), abs(point.y - y)) for point in points.get(area, ())),
            default=float("inf"),
        )
        if best is None or gap < best_gap:
            best, best_gap = (area, x, y), gap
    return best


@dataclass
class _Placed:
    """What placing one set of spawns on their zone maps found, before any reduction."""

    # (name, area) -> every placed position, as a zone map percentage.
    groups: dict[tuple[str, int], list[tuple[float, float]]] = field(
        default_factory=lambda: defaultdict(list)
    )
    checked: int = 0
    agreed: int = 0
    instance: int = 0
    outside: int = 0
    no_area: int = 0


def _place_spawns(
    era_input: EraInput,
    by_name: Mapping[str, Sequence[int]],
    by_id: Mapping[int, Sequence[Spawn]],
    zones: Mapping[int, tuple[int, ...]],
    stated: Mapping[int, Sequence[SpawnPoint]],
) -> _Placed:
    """Every spawn of every id each name stands for, placed on the zone map of its own area.

    The one placing pass, shared by the creature pins and the object pins: `zones` and `stated`
    are pfQuest's areas and points for the same ids (units for a creature, objects for an
    object), and the rules are the same for both. A spawn whose id pfQuest knows no area for is
    counted in `no_area` and dropped, one on a map no candidate zone has an assignment for (every
    instance) in `instance`, and one whose position falls outside every candidate's map in
    `outside`.
    """
    placed = _Placed()
    for name in sorted(by_name):
        for key in by_name[name]:
            spawns = by_id.get(key, ())
            if not spawns:
                continue
            points: dict[int, list[SpawnPoint]] = defaultdict(list)
            for point in stated.get(key, ()):
                points[point.area].append(point)
            candidates = [
                area for area in zones.get(key, ()) if area in era_input.areas and area in era_input.area_maps
            ]
            if not candidates:
                placed.no_area += len(spawns)
                continue
            maps = {area: era_input.area_maps[area] for area in candidates}
            for spawn in spawns:
                found = _pin_area(spawn, candidates, maps, era_input.map_bounds, points)
                if found is None:
                    if any(era_input.map_bounds.get((maps[area], spawn.map)) for area in candidates):
                        placed.outside += 1
                    else:
                        placed.instance += 1
                    continue
                area, x, y = found
                placed.groups[(name, area)].append((x, y))
                # The cross check, on the real run: how close the formula's own answer sits to
                # the nearest pfQuest spawn of the same id in the same area. pfQuest is a
                # reduction of a different world database, so the two do not have the same spawn
                # set and a disagreement is news about a build, not a failure.
                here = points.get(area)
                if here:
                    placed.checked += 1
                    gap = min(max(abs(point.x - x), abs(point.y - y)) for point in here)
                    if gap <= PIN_AGREEMENT:
                        placed.agreed += 1
    return placed


def _reduce_placed(
    placed: _Placed,
    era_input: EraInput,
    strings: _Strings,
    used_areas: dict[int, int],
) -> tuple[dict[int, tuple[MapPin, ...]], int, list[float]]:
    """Each (name, area) group reduced to its pins, keyed by the name's index into `s`, with the
    number of spawns the kept groups stand for and each group's coverage share."""
    pins: dict[int, list[MapPin]] = defaultdict(list)
    total = 0
    shares: list[float] = []
    for (name, area), points_in_area in sorted(placed.groups.items()):
        made = reduce_pins(area, points_in_area)
        if not made:
            continue
        # How much of the group the kept cells account for. Per group, the way the measurement
        # that chose the cap and the cell size was made: a handful of huge groups would
        # otherwise drown out the three thousand ordinary ones.
        shares.append(sum(pin.weight for pin in made) / len(points_in_area))
        total += len(points_in_area)
        pins[strings.add(name)].extend(made)
        used_areas[area] = strings.add(era_input.areas[area])
    ordered = {
        index: tuple(sorted(made, key=lambda pin: pin.order())) for index, made in sorted(pins.items())
    }
    return ordered, total, shares


def _creature_pins(
    era_input: EraInput,
    names: set[str],
    strings: _Strings,
    used_areas: dict[int, int],
    counts: dict[str, int],
    dropped: dict[str, int],
) -> dict[int, tuple[MapPin, ...]]:
    """A creature name's index into `s` -> its map pins, in the order the addon draws them.

    Keyed by the NAME, for the same reason `ck` and `cd` are: the table has never carried
    creature ids, and every row naming "Defias Bandit" wants the same map. Pinned per name per
    AREA and never per map, because map 0 is the whole of Eastern Kingdoms and Defias Bandit is
    one creature id spanning Elwynn Forest and Westfall.

    A name with no spawn row anywhere gets no pins and that is not an error: 374 of the names
    this module ships are summons, instance script spawns and event bosses.
    """
    by_creature, event_only, nameless = _spawns_by_creature(era_input.spawns, era_input.spawn_entries)
    counts["pinSpawnsEventOnly"] = event_only
    counts["pinSpawnsWithoutCreature"] = nameless
    counts["pinSpawnsPooled"] = sum(1 for spawn in era_input.spawns if spawn.pooled)

    by_name: dict[str, list[int]] = defaultdict(list)
    for creature in sorted(era_input.creatures):
        facts = era_input.creatures[creature]
        if facts.name in names:
            by_name[facts.name].append(creature)

    placed = _place_spawns(era_input, by_name, by_creature, era_input.unit_zones, era_input.unit_points)
    pins, total, shares = _reduce_placed(placed, era_input, strings, used_areas)

    dropped["pinInsideInstance"] = placed.instance
    dropped["pinOutsideMap"] = placed.outside
    dropped["pinNoAreaKnown"] = placed.no_area
    counts["pins"] = sum(len(made) for made in pins.values())
    counts["pinNames"] = len(pins)
    counts["pinGroups"] = len(placed.groups)
    counts["pinSpawnsPlaced"] = total
    counts["pinCoverageMeanPercent"] = int(round(100.0 * sum(shares) / len(shares))) if shares else 0
    counts["pinCoverageWorstPercent"] = int(round(100.0 * min(shares))) if shares else 0
    counts["pinSpawnsChecked"] = placed.checked
    counts["pinSpawnsAgreed"] = placed.agreed
    counts["pinAgreementPercent"] = (
        int(round(100.0 * placed.agreed / placed.checked)) if placed.checked else 0
    )
    return pins


def template_walk(era_input: EraInput, creature: int) -> tuple[tuple[float, float], ...] | None:
    """The creature's own `creature_movement_template` path, the lowest path id where it states
    several (a script picks between them; path 0 is the one a spawn walks by default)."""
    by_path = era_input.template_paths.get(creature)
    if not by_path:
        return None
    return by_path[min(by_path)] or None


def spawn_walk(era_input: EraInput, spawn: Spawn, creature: int) -> tuple[tuple[float, float], ...] | None:
    """The path one spawn walks: none unless its MovementType is a waypoint walk, then its own
    `creature_movement` rows, else its creature's template path."""
    if spawn.guid not in era_input.waypoint_guids:
        return None
    return era_input.paths.get(spawn.guid) or template_walk(era_input, creature)


def place_path(box: MapBounds, walk: Sequence[tuple[float, float]]) -> tuple[list[tuple[float, float]], int]:
    """A path on one zone map: (its points as map percentages rounded to a tenth, in walking
    order, a point off the map or equal to the one before it dropped; how many were off the map)."""
    out: list[tuple[float, float]] = []
    off = 0
    for world_x, world_y in walk:
        x, y = map_position(box, world_x, world_y)
        if not (0.0 <= x <= 100.0 and 0.0 <= y <= 100.0):
            off += 1
            continue
        point = (round(x, PIN_PLACES), round(y, PIN_PLACES))
        if out and out[-1] == point:
            continue
        out.append(point)
    return out, off


def _zone_candidates(era_input: EraInput, creature: int) -> list[int]:
    """The creature's pfQuest areas this build names and draws, commonest first (the pin rule)."""
    return [
        area
        for area in era_input.unit_zones.get(creature, ())
        if area in era_input.areas and area in era_input.area_maps
    ]


def listed_creatures(era_input: EraInput) -> set[int]:
    """Every creature id any `creature` row names, an event only row included."""
    out: set[int] = set()
    for spawn in era_input.spawns:
        out.update((spawn.creature,) if spawn.creature else era_input.spawn_entries.get(spawn.guid, ()))
    out.discard(0)
    return out


def _unspawned_walkers(
    era_input: EraInput, listed: Collection[int]
) -> dict[tuple[tuple[float, float], ...], list[int]]:
    """A template path -> the creatures with no `creature` row at all (script spawns) that walk
    exactly it. The four dragons of the Emerald Dream share one, which is how the dump says any of
    them walks it. A creature whose only rows are event only is not one: it is not found at all."""
    walkers: dict[tuple[tuple[float, float], ...], list[int]] = defaultdict(list)
    for creature in sorted(era_input.template_paths):
        if creature in listed:
            continue
        walk = template_walk(era_input, creature)
        if walk:
            walkers[walk].append(creature)
    return walkers


def shared_places(era_input: EraInput) -> set[int]:
    """Brief W18: the creature ids whose places are shared, so at a time the creature stands at
    one of them, or another creature does: a pooled spawn (`pool_creature`, or a creature
    `pool_creature_template` pools), a spawn `creature_spawn_entry` gives several creatures, or,
    for a creature with no `creature` row at all, a template path another such creature walks too."""
    out: set[int] = set()
    for spawn in era_input.spawns:
        if spawn.event > 0:
            continue
        ids = (spawn.creature,) if spawn.creature else tuple(era_input.spawn_entries.get(spawn.guid, ()))
        if spawn.pooled or len(ids) > 1:
            out.update(creature for creature in ids if creature)
    for creatures in _unspawned_walkers(era_input, listed_creatures(era_input)).values():
        if len(creatures) > 1:
            out.update(creatures)
    return out


def _creature_paths(
    era_input: EraInput,
    names: set[str],
    strings: _Strings,
    used_areas: dict[int, int],
    counts: dict[str, int],
    dropped: dict[str, int],
) -> dict[int, list[str]]:
    """Brief W18: a boss name's index into `s` -> the paths it walks, packed by pack_path.

    Only a creature whose rank is in PATH_RANKS and whose name the table ships. A spawn that
    walks (spawn_walk) has its path drawn on the zone map of the spawn's own pin area, found by
    the very rule the pins use (_pin_area), so the path and the pin are on one map. A creature
    with no `creature` row at all (a script spawn: Maws, the four dragons) walks its template
    path; the dump states no map for one, so it is drawn on the first of the creature's own
    pfQuest areas whose zone map holds every point of it, then the first of the areas of every
    other spawnless creature that walks exactly the same path (the dragons share one). A path
    none of those holds, or with fewer than PATH_MIN_POINTS points on its map, is not shipped.
    """
    by_creature, _event_only, _nameless = _spawns_by_creature(era_input.spawns, era_input.spawn_entries)
    listed = listed_creatures(era_input)
    walkers = _unspawned_walkers(era_input, listed)
    boxes: dict[int, list[MapBounds]] = defaultdict(list)
    for (ui_map, _map_id), box in sorted(era_input.map_bounds.items()):
        boxes[ui_map].append(box)

    def holds(box: MapBounds, walk: Sequence[tuple[float, float]]) -> bool:
        for world_x, world_y in walk:
            x, y = map_position(box, world_x, world_y)
            if not (0.0 <= x <= 100.0 and 0.0 <= y <= 100.0):
                return False
        return True

    out: dict[int, set[str]] = defaultdict(set)
    points_shipped = thinned = off_map = not_placed = 0
    for creature in sorted(era_input.creatures):
        facts = era_input.creatures[creature]
        if facts.rank not in PATH_RANKS or facts.name not in names:
            continue
        candidates = _zone_candidates(era_input, creature)
        found: list[tuple[int, MapBounds, tuple[tuple[float, float], ...]]] = []
        spawns = by_creature.get(creature, ())
        if spawns:
            stated: dict[int, list[SpawnPoint]] = defaultdict(list)
            for point in era_input.unit_points.get(creature, ()):
                stated[point.area].append(point)
            maps = {area: era_input.area_maps[area] for area in candidates}
            for spawn in spawns:
                walk = spawn_walk(era_input, spawn, creature)
                if not walk:
                    continue
                where = None
                if candidates:
                    where = _pin_area(spawn, candidates, maps, era_input.map_bounds, stated)
                if where is None:
                    not_placed += 1
                    continue
                found.append((where[0], era_input.map_bounds[(maps[where[0]], spawn.map)], walk))
        elif creature in listed:
            # Every row it has is event only, so it is not found at all, as its pins say.
            continue
        else:
            walk = template_walk(era_input, creature)
            if not walk:
                continue
            shared = list(candidates)
            for other in walkers.get(walk, ()):
                if other != creature:
                    shared.extend(area for area in _zone_candidates(era_input, other) if area not in shared)
            chosen = next(
                (
                    (area, box)
                    for area in shared
                    for box in boxes.get(era_input.area_maps[area], ())
                    if holds(box, walk)
                ),
                None,
            )
            if chosen is None:
                not_placed += 1
                continue
            found.append((chosen[0], chosen[1], walk))
        for area, box, walk in found:
            on_map, missed = place_path(box, walk)
            off_map += missed
            if len(on_map) < PATH_MIN_POINTS:
                not_placed += 1
                continue
            kept = thin_path(on_map)
            thinned += len(on_map) - len(kept)
            packed = pack_path(area, kept)
            index = strings.add(facts.name)
            if packed not in out[index]:
                out[index].add(packed)
                points_shipped += len(kept)
            used_areas[area] = strings.add(era_input.areas[area])
    counts["pathNames"] = len(out)
    counts["paths"] = sum(len(walks) for walks in out.values())
    counts["pathPoints"] = points_shipped
    counts["pathPointsThinned"] = thinned
    counts["pathPointsOffMap"] = off_map
    dropped["pathNotPlaced"] = not_placed
    return {index: sorted(walks) for index, walks in sorted(out.items())}


# The categories whose `n` is an OBJECT, which are the ones an object pin is made for, and the
# word each is counted under.
OBJECT_CATEGORIES = {CAT_HERB: "Herb", CAT_VEIN: "Vein", CAT_FISHED: "Pool", CAT_OBJECT: "Chest"}


def _object_pins(
    era_input: EraInput,
    names: Mapping[str, int],
    strings: _Strings,
    used_areas: dict[int, int],
    counts: dict[str, int],
    dropped: dict[str, int],
) -> dict[int, tuple[MapPin, ...]]:
    """An OBJECT name's index into `s` -> its map pins (brief D7), by exactly the creature rule.

    `names` is every object name a shipped row or list names, with the category it is filed
    under. Each name stands for every chest or fishing hole of that name with a loot template,
    which is what `object_spawns` holds; the area of each spawn is pfQuest's objects file, read
    the way its units file is for a creature, and a spawn of an object pfQuest places nowhere is
    dropped and counted under `objectPinNoAreaKnown`. Keyed by the name, like `mp`, and shipped
    in `op` beside it: see derive for why the two are not one table.
    """
    by_object, _event_only, nameless = _spawns_by_creature(
        era_input.object_spawns, era_input.object_spawn_entries
    )
    counts["objectPinSpawnsWithoutObject"] = nameless

    by_name: dict[str, list[int]] = defaultdict(list)
    for oid in sorted(era_input.objects):
        obj = era_input.objects[oid]
        if obj.name in names and _lootable(obj) and not is_scaffolding(obj.name):
            by_name[obj.name].append(oid)

    placed = _place_spawns(era_input, by_name, by_object, era_input.object_zones, era_input.object_points)
    pins, total, _shares = _reduce_placed(placed, era_input, strings, used_areas)

    dropped["objectPinInsideInstance"] = placed.instance
    dropped["objectPinOutsideMap"] = placed.outside
    dropped["objectPinNoAreaKnown"] = placed.no_area
    counts["objectPins"] = sum(len(made) for made in pins.values())
    counts["objectPinNames"] = len(pins)
    counts["objectPinGroups"] = len(placed.groups)
    counts["objectPinSpawnsPlaced"] = total
    counts["objectPinSpawnsChecked"] = placed.checked
    counts["objectPinSpawnsAgreed"] = placed.agreed
    for category, word in OBJECT_CATEGORIES.items():
        kept = [index for index in pins if names.get(strings.value(index), 0) == category]
        counts[f"objectPinNames{word}"] = len(kept)
        counts[f"objectPins{word}"] = sum(len(pins[index]) for index in kept)
    return pins


def _object_names(
    entries: Mapping[int, Sequence[dict]],
    leftovers: Mapping[int, Mapping[int, Sequence[dict]]],
    strings: _Strings,
) -> dict[str, int]:
    """Every object name a shipped row or a packed list names -> the category it is filed under.

    The rows still carry insertion indexes here, before the string table is sorted. A name filed
    under two object categories (a node that is also a chest somewhere) takes the lower number,
    so the answer never depends on the order the items were read in.
    """
    found: dict[str, int] = {}

    def note(row: Mapping) -> None:
        category = row.get("c")
        if category in OBJECT_CATEGORIES and "n" in row and "t" not in row:
            name = strings.value(row["n"])
            if name:
                found[name] = min(found.get(name, category), category)

    for rows in entries.values():
        for row in rows:
            note(row)
    for by_kind_rows in leftovers.values():
        for rest in by_kind_rows.values():
            for row in rest:
                note(row)
    return dict(sorted(found.items()))


def _vendor_names(
    entries: Mapping[int, Sequence[dict]],
    leftovers: Mapping[int, Mapping[int, Sequence[dict]]],
    strings: _Strings,
) -> set[str]:
    """Every vendor name a shipped row or a packed list names (brief N3).

    These are the names a vendor's page can be opened on, so they are the ones that get a kind,
    a portrait and pins beside the creatures'. Read off the rows while they still carry insertion
    indexes, the way _object_names reads the object names.
    """
    found: set[str] = set()

    def note(row: Mapping) -> None:
        if row.get("c") == CAT_VENDOR and "n" in row and "t" not in row:
            name = strings.value(row["n"])
            if name:
                found.add(name)

    for rows in entries.values():
        for row in rows:
            note(row)
    for by_kind_rows in leftovers.values():
        for row in by_kind_rows.get(CAT_VENDOR, ()):
            note(row)
    return found


def _handed_over(entries: Mapping[int, Sequence[dict]]) -> set[int]:
    """Every quest a c = 3 row names, first or further: the quests the addon can already title."""
    found: set[int] = set()
    for rows in entries.values():
        for row in rows:
            if row["c"] == CAT_QUEST:
                found.add(row["q"])
                for further in row.get("m", ()):
                    found.add(further["q"])
    return found


def _giver_names(era_input: EraInput) -> set[str]:
    """Every creature NAME that starts or ends a quest the table can title (brief W15).

    Owner QA, 2026-09-29: "Quest: Deviate Hides (1486)" showed no giver, because Nalpak gives
    and takes it and Nalpak drops, sells and trains nothing, so brief N3's rule (a giver ships
    only where some other row already names it) left him out. Since 2026-09-29 every such name
    ships: it joins the creature, vendor and trainer names in `ck`, `cd`, `mp`, `st`, `cf` and
    `qg`. The same tests _quest_givers applies decide it: a creature with no template, no name
    or a scaffolding name gives nothing, and a quest with no title or a scaffolding one is no
    reason to ship a name. A creature with no quest link is not read here at all.
    """
    found: set[str] = set()
    for relation in (era_input.quest_starts, era_input.quest_ends):
        for creature_id, quest in relation:
            facts = era_input.creatures.get(creature_id)
            if facts is None or is_scaffolding(facts.name):
                continue
            title = era_input.quest_names.get(quest, "")
            if title and not is_scaffolding(title):
                found.add(facts.name)
    return found


def _quest_givers(
    era_input: EraInput,
    names: set[str],
    strings: _Strings,
    counts: dict[str, int],
    dropped: dict[str, int],
) -> dict[int, tuple[tuple[int, ...], tuple[int, ...]]]:
    """A creature or vendor NAME's index into `s` -> (the quests it starts, the quests it ends).

    Brief N3. Keyed by the name, the way `ck`, `cd` and `mp` are: every creature of one name is
    the same giver to a player, so "Innkeeper Farley" starts what any creature called that
    starts. `names` is every name the table ships a page for, which since brief W15 (2026-09-29)
    includes every giver _giver_names finds, so a giver that drops, sells and trains nothing,
    such as Nalpak, gets its entry too. What `questGiverNotShipped` counts now is a relation row
    whose creature has no template, no name or a scaffolding name.

    A quest is kept only where quest_template gives it a title, and a title that is scaffolding
    is refused like a scaffolding name, because a quest the addon cannot title is a row that says
    nothing. Each list is quest id ascending with repeats dropped; a quest a name both starts and
    ends is in both.
    """
    by_id = era_input.creatures
    lists: dict[str, tuple[set[int], set[int]]] = {}
    for side, relation in ((0, era_input.quest_starts), (1, era_input.quest_ends)):
        for creature_id, quest in relation:
            facts = by_id.get(creature_id)
            if facts is None:
                dropped["questGiverNotShipped"] += 1
                continue
            title = era_input.quest_names.get(quest, "")
            if not title:
                dropped["questGiverUntitled"] += 1
                continue
            if is_scaffolding(title):
                dropped["questGiverScaffolding"] += 1
                continue
            if facts.name not in names:
                dropped["questGiverNotShipped"] += 1
                continue
            lists.setdefault(facts.name, (set(), set()))[side].add(quest)
    out: dict[int, tuple[tuple[int, ...], tuple[int, ...]]] = {}
    for name in sorted(lists):
        starts, ends = lists[name]
        out[strings.add(name)] = (tuple(sorted(starts)), tuple(sorted(ends)))
    counts["questGiverNames"] = len(out)
    counts["questGiverStarts"] = sum(len(pair[0]) for pair in out.values())
    counts["questGiverEnds"] = sum(len(pair[1]) for pair in out.values())
    counts["questGiverBoth"] = sum(len(set(pair[0]) & set(pair[1])) for pair in out.values())
    # Brief W15: how many distinct quests have a giver or an ender the table names.
    counts["questGiverQuests"] = len({quest for pair in out.values() for side in pair for quest in side})
    return out


def _quest_requires(
    era_input: EraInput,
    shipped: Callable[[int], bool],
    counts: dict[str, int],
    dropped: dict[str, int],
) -> dict[int, tuple[tuple[int, int], ...]]:
    """questId -> (item id, count) for each item the quest asks the player to bring (brief W12).

    Owner, 2026-09-29 (queue item 136): Deviate Hide showed "Used by (0)" although its creature's
    loot row says "only on the quest", because a quest's required items never reached the file
    and the addon had no edge from the item to the quest. This is that edge, ids and counts only.

    Every kept quest (a title, and items or requires) that asks for something is a candidate. A
    required item this build does not ship, and does not ship as withheld, is refused the way a
    row for it would be, and a quest left asking for nothing has no entry. A quest whose title is
    scaffolding is refused like a scaffolding name. The items are in the template's slot order;
    an item named in two slots is one entry with the two counts added. A count of 0 reads as one.
    """
    out: dict[int, tuple[tuple[int, int], ...]] = {}
    for quest_id in sorted(era_input.quests):
        quest = era_input.quests[quest_id]
        if not quest.requires:
            continue
        if is_scaffolding(quest.title):
            dropped["questRequiresScaffolding"] += 1
            continue
        wanted: dict[int, int] = {}
        for slot, item in enumerate(quest.requires):
            if not shipped(item):
                dropped["questRequiresNotShipped"] += 1
                continue
            count = quest.require_counts[slot] if slot < len(quest.require_counts) else 0
            wanted[item] = wanted.get(item, 0) + max(count, 1)
        if wanted:
            out[quest_id] = tuple(wanted.items())
    counts["questRequiresQuests"] = len(out)
    counts["questRequiresPairs"] = sum(len(pairs) for pairs in out.values())
    counts["questRequiresItems"] = len({item for pairs in out.values() for item, _count in pairs})
    counts["questRequiresCountAboveOne"] = sum(
        1 for pairs in out.values() for _item, count in pairs if count > 1
    )
    return out


def _vendor_creatures(era_input: EraInput) -> set[int]:
    """Every creature id that sells anything, by `npc_vendor` or by a vendor template."""
    found = {offer.vendor for offer in era_input.vendor_offers}
    found.update(cid for cid, facts in era_input.creatures.items() if facts.vendor_template)
    return found


def _titles_and_sides(
    era_input: EraInput,
    names: set[str],
    strings: _Strings,
    counts: dict[str, int],
    trainers: Collection[int] = (),
) -> tuple[dict[int, int], dict[int, int]]:
    """Brief T1: a vendor or quest giver NAME's index into `s` -> (its SubName's index into `s`,
    its side), for the names given and no other.

    Keyed by the name, the way `ck` and `qg` are. Where creatures share a name, the ones that sell
    something speak for it if any of them does (so "Innkeeper Farley" the vendor is not titled by
    a quest giver of the same name), and among those the commonest non empty SubName wins, ties by
    the lowest creature id. The side is the one every such creature's template agrees on, and 3
    (both) where they disagree; a creature on a template this build does not carry says nothing,
    and a name none of whose creatures can be read has no `cf` entry at all.

    Brief P6a: the names now include the trainers, and `trainers` is the creature ids that teach.
    Where no creature of a name sells anything, the ones that teach speak for it next, so a
    trainer's title is its "Journeyman Enchanter" rather than some quest giver's of its name.
    """
    sellers = _vendor_creatures(era_input)
    teachers = set(trainers)
    by_name: dict[str, list[CreatureFacts]] = defaultdict(list)
    for creature_id in sorted(era_input.creatures):
        facts = era_input.creatures[creature_id]
        if facts.name in names:
            by_name[facts.name].append(facts)
    subnames: dict[int, int] = {}
    sides: dict[int, int] = {}
    conflicts = 0
    for name in sorted(by_name):
        creatures = by_name[name]
        speaking = (
            [facts for facts in creatures if facts.id in sellers]
            or [facts for facts in creatures if facts.id in teachers]
            or creatures
        )
        titles = Counter(facts.subname for facts in speaking if facts.subname)
        if titles:
            first = {}
            for facts in speaking:
                first.setdefault(facts.subname, facts.id)
            title = min(titles, key=lambda value: (-titles[value], first[value]))
            if len(titles) > 1:
                conflicts += 1
            subnames[strings.add(name)] = strings.add(title)
        found = {
            era_input.faction_sides[facts.faction]
            for facts in speaking
            if facts.faction in era_input.faction_sides
        }
        if found:
            sides[strings.add(name)] = found.pop() if len(found) == 1 else FACTION_BOTH
    counts["subnames"] = len(subnames)
    counts["subnameConflicts"] = conflicts
    counts["factions"] = len(sides)
    for side, label in ((FACTION_ALLIANCE, "Alliance"), (FACTION_HORDE, "Horde"), (FACTION_BOTH, "Both")):
        counts[f"factions{label}"] = sum(1 for value in sides.values() if value == side)
    return subnames, sides


def trainer_creature_spells(era_input: EraInput) -> dict[int, set[int]]:
    """creature id -> every spell id it teaches, before any reduction (brief P6a).

    A creature teaches its own `npc_trainer` rows and every row of the `npc_trainer_template`
    entry its TrainerTemplateId names. A learn spell (see SPELL_EFFECT_LEARN_SPELL) stands for the
    spell it teaches, which is the one a player, the build and the addon know it by.
    """
    templates: dict[int, set[int]] = defaultdict(set)
    for template, spell in era_input.trainer_template_spells:
        templates[template].add(spell)
    taught: dict[int, set[int]] = defaultdict(set)
    for creature, spell in era_input.trainer_spells:
        taught[creature].add(spell)
    for creature_id, facts in era_input.creatures.items():
        if facts.trainer_template and templates.get(facts.trainer_template):
            taught[creature_id] |= templates[facts.trainer_template]
    learned = era_input.learned_spells
    return {
        creature: {learned.get(spell, spell) for spell in spells if spell > 0}
        for creature, spells in sorted(taught.items())
        if creature > 0
    }


def _trainer_lists(
    era_input: EraInput,
    counts: dict[str, int],
    dropped: dict[str, int],
) -> tuple[dict[str, tuple[int, ...]], set[int]]:
    """A trainer NAME -> the spell ids its creatures teach, ascending (brief P6a), and the ids
    of the creatures that stand behind those names.

    Keyed by the name, the way `ck`, `qg` and `st` are: every creature called "Kitta Firewind"
    is the same trainer to a player. Reduced to spells THIS build's own SkillLineAbility files
    under a profession or secondary line (TRAINER_SKILL_CATEGORIES), so no spell id the client
    cannot name ships; a class spell the build knows is refused by the cut and counted under
    `trainerSpellClass`, so a class trainer ships nothing. A creature with no name, or a
    scaffolding one, teaches nothing that ships: there is no page to open it on.
    """
    known = era_input.skill_spells
    lists: dict[str, set[int]] = defaultdict(set)
    teachers: set[int] = set()
    for creature, spells in trainer_creature_spells(era_input).items():
        facts = era_input.creatures.get(creature)
        if facts is None or not facts.name or is_scaffolding(facts.name):
            dropped["trainerUnnamed"] += 1
            continue
        kept = {spell for spell in spells if known.get(spell) in TRAINER_SKILL_CATEGORIES}
        classed = sum(1 for spell in spells if spell in known and spell not in kept)
        dropped["trainerSpellClass"] += classed
        dropped["trainerSpellUnknown"] += len(spells) - len(kept) - classed
        if not kept:
            dropped["trainerNothingKnown"] += 1
            continue
        lists[facts.name] |= kept
        teachers.add(creature)
    out = {name: tuple(sorted(lists[name])) for name in sorted(lists)}
    pairs = [(name, spell) for name, spells in out.items() for spell in spells]
    counts["trainerNames"] = len(out)
    counts["trainerCreatures"] = len(teachers)
    counts["trainerPairs"] = len(pairs)
    counts["trainerSpells"] = len({spell for _name, spell in pairs})
    return out, teachers


def derive(era_input: EraInput, graph: BuildFacts, *, withheld: Collection[int] = ()) -> EraSources:
    """Turn the two pinned databases into the table the addon ships, counting every refusal.

    `withheld` names the hidden ids whose rows ship anyway: ids this build lists and will not
    name, which an earlier build did name. Their rows are emitted exactly as a named item's
    are, and `counts["withheldItems"]` and `counts["withheldRows"]` say how many. Every other
    hidden id is refused and counted under `dropped["hidden"]`, as before.
    """
    withheld_ids = frozenset(withheld)
    dropped: dict[str, int] = {
        "hidden": 0,
        "notShipped": 0,
        "refLoop": 0,
        "scaffolding": 0,
        "noArea": 0,
        "containerNotShipped": 0,
        "curatedQuest": 0,
        "displayNotInBuild": 0,
        "pinInsideInstance": 0,
        "pinOutsideMap": 0,
        "pinNoAreaKnown": 0,
        "pathNotPlaced": 0,
        "objectPinInsideInstance": 0,
        "objectPinOutsideMap": 0,
        "objectPinNoAreaKnown": 0,
        "questGiverNotShipped": 0,
        "questGiverUntitled": 0,
        "questGiverScaffolding": 0,
        "trainerUnnamed": 0,
        "trainerSpellUnknown": 0,
        "trainerSpellClass": 0,
        "trainerNothingKnown": 0,
        "questRequiresNotShipped": 0,
        "questRequiresScaffolding": 0,
    }
    counts: dict[str, int] = {
        "multiQuest": 0,
        "furtherQuests": 0,
        "furtherQuestsDropped": 0,
        "worldDropRule": 0,
        "vendorSummaryRule": 0,
        "summaryRows": 0,
        "summaryOfOne": 0,
    }
    strings = _Strings()
    used_areas: dict[int, int] = {}
    areas = era_input.areas
    # Every creature name any shipped row or any full list names, for the kinds table.
    creature_names: set[str] = set()

    candidates = collect(era_input, graph, dropped)

    # itemId -> the quests that hand it over, in quest id order, built once.
    quests_for: dict[int, list[QuestFacts]] = defaultdict(list)
    for quest_id in sorted(era_input.quests):
        quest = era_input.quests[quest_id]
        for item in quest.items:
            quests_for[item].append(quest)

    # Every item either database says anything about, counted once per item.
    for item in sorted(set(candidates) | set(quests_for)):
        if item not in graph.items and item not in withheld_ids:
            dropped["hidden" if item in graph.undiscovered else "notShipped"] += 1
            candidates.pop(item, None)
            quests_for.pop(item, None)

    # The curated duplicate rule, applied quest by quest so that an item offered by an
    # Alliance quest we state first hand and a Horde quest we do not keeps the half we
    # cannot state. A row left with nothing is the duplicate and is counted as one.
    for item in sorted(quests_for):
        kept = [q for q in quests_for[item] if item not in era_input.curated_quests.get(q.id, set())]
        if not kept:
            dropped["curatedQuest"] += 1
        quests_for[item] = kept

    entries: dict[int, list[dict]] = {}
    leftovers: dict[int, dict[int, list[dict]]] = defaultdict(dict)
    by_category: dict[int, int] = dict.fromkeys(CATEGORY_NAMES, 0)

    for item in sorted(set(candidates) | set(quests_for)):
        by_kind: dict[int, list[_Source]] = defaultdict(list)
        for source in candidates.get(item, ()):
            by_kind[source.category].append(source)
        rows: list[dict] = []
        # Rows are emitted in category order, and within a category best chance first with the
        # summary row last, so the addon draws them in file order and never sorts.
        for category in sorted(by_kind):
            made, rest = _rows_for_category(
                category, by_kind[category], strings, used_areas, areas, counts, creature_names
            )
            rows.extend(made)
            if rest:
                leftovers[item][category] = rest
        rows.extend(_quest_rows(quests_for.get(item, ()), strings, counts))
        if not rows:
            continue
        rows.sort(key=lambda row: (row["c"], 1 if "t" in row else 0))
        entries[item] = rows
        for row in rows:
            by_category[row["c"]] = by_category.get(row["c"], 0) + 1

    quest_titles = _quest_titles(era_input, entries, strings)
    # Brief N3: a vendor's name joins ck, cd and mp beside the creatures', so a vendor's page has a
    # portrait and a map. One entry per name: a name that is a creature and a vendor both is one
    # kind, one display and one set of pins, and its kind says it is both.
    vendor_names = _vendor_names(entries, leftovers, strings)
    # Brief P6a: a trainer's name joins them too, so a trainer's page has a portrait, a map, a
    # title and a side. A trainer's kind stays a plain kind: `tr` is what says it teaches.
    trainer_lists, teachers = _trainer_lists(era_input, counts, dropped)
    trainer_names = set(trainer_lists)
    # Brief W15 (2026-09-29): every creature that starts or ends a titled quest ships as a name
    # of its own, with its kind, portrait, pins, title, side and quest lists, even where it drops,
    # sells and trains nothing. Its kind stays a plain kind: `qg` is what says it gives quests.
    giver_names = _giver_names(era_input)
    npc_names = creature_names | vendor_names | trainer_names | giver_names
    kinds = _creature_kinds(era_input, npc_names, strings, counts)
    for index in kinds:
        name = strings.value(index)
        if name in vendor_names:
            kinds[index] = vendor_kind(kinds[index], name in creature_names)
    displays = _creature_displays(era_input, npc_names, strings, counts, dropped)
    # Who starts and ends which quest, for the same names (brief N3). A quest a giver lists that no
    # c = 3 row titles gets its title in qt, which is the table the addon names a quest from first.
    givers = _quest_givers(era_input, npc_names, strings, counts, dropped)
    handed_over = _handed_over(entries)
    added = 0
    for starts, ends in givers.values():
        for quest in (*starts, *ends):
            if quest not in handed_over and quest not in quest_titles:
                quest_titles[quest] = strings.add(era_input.quest_names[quest])
                added += 1
    counts["questGiverTitlesAdded"] = added
    # Brief W12: what each kept quest asks the player to bring, so a quest item's Used by can name
    # the quest. Titled at the end, once every other string is in.
    requires = _quest_requires(
        era_input, lambda item: item in graph.items or item in withheld_ids, counts, dropped
    )
    # Brief T1, the owner's ruling of 2026-09-27: the title under the name and the side, for the
    # vendors and the quest givers and enders the table names, and no other creature. Every
    # recipe's vendor is one of those vendors, so "Alliance only" on a recipe needs nothing more.
    titled_names = vendor_names | trainer_names | {strings.value(index) for index in givers}
    subnames, sides = _titles_and_sides(era_input, titled_names, strings, counts, teachers)
    trainers = {strings.add(name): spells for name, spells in trainer_lists.items()}
    # The pins go last, because a pin's own area is an area the player can now read and so has to
    # reach `z` and `s` before the string table is sorted.
    pins = _creature_pins(era_input, npc_names, strings, used_areas, counts, dropped)
    # Brief W18: a boss's paths, after the pins for the same reason: a path's area reaches `z`.
    paths = _creature_paths(era_input, npc_names, strings, used_areas, counts, dropped)
    counts["vendorNames"] = len(vendor_names)
    counts["vendorNamesSharedWithCreature"] = len(vendor_names & creature_names)
    counts["vendorKinds"] = sum(1 for packed in kinds.values() if packed < 0)
    counts["vendorDisplays"] = sum(1 for index in displays if strings.value(index) in vendor_names)
    counts["vendorPinNames"] = sum(1 for index in pins if strings.value(index) in vendor_names)
    counts["vendorPins"] = sum(
        len(made) for index, made in pins.items() if strings.value(index) in vendor_names
    )
    counts["trainerNamesSharedWithOthers"] = len(trainer_names & (creature_names | vendor_names))
    giver_only = giver_names - creature_names - vendor_names - trainer_names
    counts["giverOnlyNames"] = len(giver_only)
    counts["giverOnlyPinNames"] = sum(1 for index in pins if strings.value(index) in giver_only)
    counts["giverOnlyTitles"] = sum(1 for index in subnames if strings.value(index) in giver_only)
    counts["trainerDisplays"] = sum(1 for index in displays if index in trainers)
    counts["trainerPinNames"] = sum(1 for index in pins if index in trainers)
    counts["trainerTitles"] = sum(1 for index in subnames if index in trainers)
    counts["trainerSides"] = sum(1 for index in sides if index in trainers)
    # The object pins (brief D7), for every object name a shipped row or list names. Shipped in
    # `op` rather than in `mp`: `s` is one string table, and a name can be a creature's and an
    # object's both, so one table keyed by name could not say whose pins it holds.
    object_names = _object_names(entries, leftovers, strings)
    object_pins = _object_pins(era_input, object_names, strings, used_areas, counts, dropped)
    counts["objectPinNamesSharedWithCreature"] = sum(
        1 for index in object_pins if strings.value(index) in creature_names
    )

    # Brief W12: a qr quest no c = 3 row and no qt entry titles gets its title in qt. Where `s`
    # already holds that very string the entry is its index, as every qt entry was before; where it
    # does not, the entry is the title itself, a plain string (the coordinator's ruling of
    # 2026-09-29). `s` never grows for qr: a list record's name field is PACK_NAME_DIGITS (two)
    # digits, which stop at 8,280, and before brief W15 `s` held 7,852 on 1.60.1.70009, so the
    # 646 new titles qr would add would have taken it past what a list can index. Brief W15 took
    # `s` past 8,280 anyway and put the list names first instead (see _Strings.sorted_table).
    by_index = 0
    by_string = 0
    for quest in requires:
        if quest in handed_over or quest in quest_titles:
            continue
        title = era_input.quests[quest].title
        index = strings.find(title)
        if index:
            quest_titles[quest] = index
            by_index += 1
        else:
            quest_titles[quest] = title
            by_string += 1
    counts["questRequiresTitlesByIndex"] = by_index
    counts["questRequiresTitlesByString"] = by_string

    # Brief W15: the names a list record packs go first, so their two digit field always fits.
    listed_names = {
        row["n"]
        for by_kind_rows in leftovers.values()
        for rest in by_kind_rows.values()
        for row in rest
        if row.get("n")
    }
    table, remap = strings.sorted_table(listed_names)
    counts["stringsListed"] = len(listed_names)
    counts["stringsListedFirst"] = int(len(table) >= PACK_BASE**PACK_NAME_DIGITS)
    for rows in entries.values():
        for row in rows:
            if "n" in row:
                row["n"] = remap[row["n"]]
            for further in row.get("m", ()):
                further["n"] = remap[further["n"]]
    for by_kind_rows in leftovers.values():
        for rest in by_kind_rows.values():
            for row in rest:
                if "n" in row:
                    row["n"] = remap[row["n"]]
    areas_out = {area: remap[index] for area, index in sorted(used_areas.items())}
    # A qt value is an index into `s` (remapped with it) or, for a qr quest only, the title itself.
    quest_titles = {
        quest: title if isinstance(title, str) else remap[title]
        for quest, title in sorted(quest_titles.items())
    }
    kinds = {remap[index]: packed for index, packed in kinds.items()}
    subnames = {remap[index]: remap[title] for index, title in subnames.items()}
    sides = {remap[index]: side for index, side in sides.items()}
    trainers_out = {remap[index]: pack_spells(spells) for index, spells in trainers.items()}
    displays = {remap[index]: display for index, display in displays.items()}
    givers_out = {
        remap[index]: (pack_quests(starts), pack_quests(ends)) for index, (starts, ends) in givers.items()
    }
    pins_out = {
        remap[index]: "".join(pack_pin(pin.area, pin.x, pin.y) for pin in made)
        for index, made in pins.items()
    }
    paths_out = {remap[index]: walks for index, walks in paths.items()}
    object_pins_out = {
        remap[index]: "".join(pack_pin(pin.area, pin.x, pin.y) for pin in made)
        for index, made in object_pins.items()
    }
    object_kinds_out = {remap[index]: object_names[strings.value(index)] for index in object_pins}
    # The map to draw, for every area a pin or a row uses. An area this build resolves to no
    # zone map gets no entry and no pin: the eight instance root areas are the whole of that on
    # 1.60.1.69913, and the addon says the creature is inside the instance instead.
    area_maps_out = {
        area: era_input.area_maps[area] for area in sorted(areas_out) if area in era_input.area_maps
    }

    # The lists, packed and then shared: the 184 vendors of one drink are the vendors of every
    # drink, so an identical list is written once and every item that opens it points at the
    # same number.
    pool: dict[str, int] = {}
    list_index: dict[int, dict[int, int]] = {}
    list_entries = 0
    for item in sorted(leftovers):
        for category in sorted(leftovers[item]):
            rest = leftovers[item][category]
            packed = "".join(pack_record(row, category) for row in rest)
            number = pool.get(packed)
            if number is None:
                number = len(pool) + 1
                pool[packed] = number
            list_index.setdefault(item, {})[category] = number
            list_entries += len(rest)
    lists = [packed for packed, _number in sorted(pool.items(), key=lambda pair: pair[1])]

    all_rows = [row for rows in entries.values() for row in rows]
    # The areas that are an instance rather than a place out in the world, so the two halves of
    # "rows with an area" can be told apart in the counts and in the doc.
    instance_ids = set(era_input.instance_areas.values())
    counts["items"] = len(entries)
    counts["rows"] = len(all_rows)
    counts["rowsWithChance"] = sum(1 for row in all_rows if "p" in row)
    counts["rowsWithArea"] = sum(1 for row in all_rows if "a" in row)
    counts["rowsInsideInstance"] = sum(1 for row in all_rows if row.get("a") in instance_ids)
    counts["listEntriesInsideInstance"] = sum(
        1
        for by_kind_rows in leftovers.values()
        for rest in by_kind_rows.values()
        for row in rest
        if row.get("a") in instance_ids
    )
    counts["instanceAreas"] = len(instance_ids & set(areas_out))
    counts["rowsNamed"] = sum(1 for row in all_rows if "n" in row)
    # The hidden ids the caller named as withheld, whose rows ship all the same. See derive.
    counts["withheldItems"] = sum(1 for item in entries if item in withheld_ids)
    counts["withheldRows"] = sum(len(rows) for item, rows in entries.items() if item in withheld_ids)
    counts["rowsWithFurtherQuests"] = sum(1 for row in all_rows if "m" in row)
    counts["rowsQuestOnly"] = sum(1 for row in all_rows if "o" in row)
    counts["questOnlyWithQuest"] = sum(1 for row in all_rows if "o" in row and "q" in row)
    counts["strings"] = len(table)
    counts["areas"] = len(areas_out)
    counts["questTitles"] = len(quest_titles)
    counts["questTitlesAsString"] = sum(1 for title in quest_titles.values() if isinstance(title, str))
    counts["kinds"] = len(kinds)
    counts["displays"] = len(displays)
    counts["questRelationStartRows"] = len(era_input.quest_starts)
    counts["questRelationEndRows"] = len(era_input.quest_ends)
    counts["areaMaps"] = len(area_maps_out)
    counts["areasWithNoMap"] = len(areas_out) - len(area_maps_out)
    counts["listsShipped"] = sum(len(by_kind_rows) for by_kind_rows in list_index.values())
    counts["listsStored"] = len(lists)
    counts["listEntries"] = list_entries
    for category, name in CATEGORY_NAMES.items():
        counts[name] = by_category.get(category, 0)
    return EraSources(
        strings=table,
        areas=areas_out,
        rows=dict(sorted(entries.items())),
        quest_titles=quest_titles,
        kinds=dict(sorted(kinds.items())),
        displays=dict(sorted(displays.items())),
        pins=dict(sorted(pins_out.items())),
        paths=dict(sorted(paths_out.items())),
        object_pins=dict(sorted(object_pins_out.items())),
        object_kinds=dict(sorted(object_kinds_out.items())),
        area_maps=area_maps_out,
        quest_givers=dict(sorted(givers_out.items())),
        subnames=dict(sorted(subnames.items())),
        factions=dict(sorted(sides.items())),
        trainers=dict(sorted(trainers_out.items())),
        quest_requires={quest: pack_requires(pairs) for quest, pairs in sorted(requires.items())},
        list_index={
            item: dict(sorted(by_kind_rows.items())) for item, by_kind_rows in sorted(list_index.items())
        },
        lists=lists,
        counts=counts,
        dropped=dropped,
    )


# ----- the header the module carries -------------------------------------------------------------


def header_lines(table: EraSources) -> list[str]:
    """The field legend, the credit and the licence note, in the module's header comment."""
    counts = table.counts
    emitted = [
        f"{counts.get(name, 0)} {name.lower()}"
        for category, name in CATEGORY_NAMES.items()
        if counts.get(name, 0)
    ]
    return [
        "Historical Classic Era sources. Facts only, linked by item id.",
        "{ s = {strings}, z = { [areaId] = string index }, r = { [itemId] = { row, row, ... } }, "
        "qt = { [questId] = string index or title }, ck = { [string index] = packed creature kind }, "
        "cd = { [string index] = creature display id }, "
        "mp = { [string index] = packed map pins }, op = { [string index] = packed map pins }, "
        "pt = { [string index] = { packed path, ... } }, "
        "ok = { [string index] = object category }, qg = { [string index] = { starts, ends } }, "
        "zm = { [areaId] = uiMapId }, st = { [string index] = string index }, "
        "cf = { [string index] = side }, tr = { [string index] = packed spell ids }, "
        "qr = { [questId] = packed required items }, "
        "x = { [itemId] = { [c] = list number } }, xl = { packed list, ... }, "
        + ("mc = { [string index] = count }, " if table.curated_pins else "")
        + "g = the Generated stamp above }",
        "r[itemId] is a LIST of rows, in the order to draw them: category ascending, best "
        "chance first inside a category, the summary row last. Never sort it. A herb or a vein "
        "(c=8, 9) is listed NODE by node: one row per zone the node stands in, a node's zone "
        "rows together (commonest zone first), the nodes best chance first then by name. Its "
        f"cap counts nodes, not rows: {MAX_NAMED_ROWS} named nodes, t is the NODE count, and "
        "its x list holds the remaining nodes' rows in the same order.",
        "row = { c category, n name (index into s), a areaId, p chance, q questId, f faction, "
        "m {further quests}, i container item id, k vendor stock, o quest only, t how many "
        "in all, lo/hi level band }",
        "Every key but c is optional. Read what your category promises and nothing else. "
        "s: every string once, sorted; once it holds more than 8,280 strings (it does since "
        "2026-09-29) in two sorted runs: first the names an xl list record carries, whose field is "
        "two base 91 digits and stops at 8,280, then every other string. The order means nothing "
        "else; look a string up by its index.",
        "c: 1 boss drop, 2 zone drop (reserved, never emitted), 3 quest, 4 vendor, 5 world "
        "drop, 6 creature drop, 7 skinned from, 8 herb node, 9 mining vein, 10 fished, "
        "11 world object or chest, 12 pickpocketed, 13 found inside a container item.",
        "t: a summary row. t is how many sources this category has on this item IN TOTAL, so "
        "the addon subtracts the named rows it has already drawn to say 'and n more'. It "
        f"names nothing and carries no chance of its own. lo and hi are that group's level "
        f"band. The cap is {MAX_NAMED_ROWS} named rows per category per item, and a category "
        f"with exactly {SUMMARISE_AT_LEAST - 1} more than that names them all and writes no "
        "summary row at all.",
        "n: the creature (c=1, 6, 7, 12), the object (c=8, 9, 10, 11), the vendor (c=4) or "
        "the quest (c=3). A c=5 row and a c=13 row name nothing.",
        "i: the container item's own id (c=13). This build names that item itself, so the row "
        "carries no string and the addon can draw it as a real edge.",
        "a: the area, as an id THIS build's AreaTable names; z[a] is its index into s. For "
        "c=10 with no n the area IS the fishing zone, stated first hand by the source. Where a "
        "creature's (or a herb's or a vein's) every spawn is on one instance map, a is that "
        "INSTANCE's own area, taken "
        "from this build's Map table: such an area has no entry in zm and no pins in mp, and "
        "the addon says the creature is inside it rather than drawing a map.",
        "p: the chance as a percentage to one decimal place. Absent where the source states "
        f"none, or one below {MIN_CHANCE}, at or below 0, or above 100.",
        "k: a limited stock vendor's stock count (c=4). Absent means unlimited.",
        "o: 1 means this source only gives the item while the player is on a quest that asks "
        "for it. Say so in words; there is nothing to check. On a summary row it means every "
        "source it stands for is that way. Ordinary rows come before o rows in a category.",
        "q: on a c=3 row, the quest that hands the item over. On an o row, the quest that "
        "makes it drop, where the source names exactly one; absent means unknown, never none.",
        "f: 1 Alliance, 2 Horde, 3 both (c=3); absent means the quest is open to everyone.",
        f"m: the other quests that hand the same item over (c=3), at most {MAX_FURTHER_QUESTS}: "
        "{ { q questId, n name, f faction }, ... }. Present only where there is more than one, "
        "so an Alliance player is never shown only the Horde quest.",
        "qt: the title of a quest an o row names in q, a qg list names or qr carries, for the "
        "quests no c=3 row names anywhere in the table. A value is a NUMBER, an index into s, or "
        "(only for a qr quest whose title s does not hold) a STRING, the title itself: test the "
        "type. Titles only, and the addon reads its own quest index first.",
        "ck: what kind of creature a NAME is, one integer per name: CreatureType + "
        f"{KIND_TYPE_SPAN} * (MinLevel + {KIND_LEVEL_SPAN} * (MaxLevel less MinLevel + "
        f"{KIND_BAND_SPAN} * beast Family)). Present for the names c=1, 6, 7 and 12 rows and "
        "their x lists use, for the vendor names c=4 rows and lists use, and for the trainer "
        "names tr carries (a trainer's is a plain kind), and since 2026-09-29 for every quest "
        "giver and ender qg carries, including one that drops, sells and trains nothing (a "
        "plain kind: qg is what says it gives quests). A vendor's is "
        "NEGATIVE, -(2 * kind + both + 1), both 1 where the name is a creature row's too. Where "
        "two creatures share a name, the commoner type and the widest level band.",
        "cd: the CreatureDisplayInfo id the client draws that NAME's portrait from, keyed the "
        "way ck is. creature_template.ModelId1 (falling back to ModelId2..4 where it is 0), "
        "the commonest where creatures of one name disagree, and every id checked against THIS "
        "build's own CreatureDisplayInfo: an id this build has not is not shipped. A plain "
        "integer, no art of any kind. A name with no entry keeps its stock kind icon.",
        "mp: where a creature NAME is found, as map pins, keyed the way ck is. One packed "
        f"string per name, a run of fixed {PIN_AREA_DIGITS + 2 * PIN_COORD_DIGITS} byte records "
        "in the same base 91 alphabet the x lists use, most significant digit first: areaId "
        f"({PIN_AREA_DIGITS} digits), then x and y in TENTHS of a percent of that area's zone "
        f"map ({PIN_COORD_DIGITS} each, 0 to 1000). In order: area ascending, then the fullest "
        f"cell first. At most {PIN_CAP} pins per name per area, each the mean of a "
        f"{PIN_CELL:.0f} percent cell of that map, so the pins are a picture of where the "
        "creature is found and not a copy of a spawn table. No spawn count, no respawn timer, "
        "no height. A name with no entry has no pins, which is not an error.",
        *(
            [
                "mc: the names whose mp string ends in hand kept world boss spawn spots, keyed the "
                "way mp is: the last count records of that name's mp string are a spot a world "
                "boss the database spawns by script can appear at, kept by hand beside this file, "
                "and not a CMaNGOS spawn. The same record shape as every other pin. "
                f"{sum(table.curated_pins.values())} such pins over {len(table.curated_pins)} names.",
            ]
            if table.curated_pins
            else []
        ),
        "op: where an OBJECT name is found (c=8, 9, 10, 11: a herb, a vein, a fishing pool, a "
        "chest), as map pins in exactly mp's packing and by exactly mp's rule, over the cmangos "
        "gameobject spawns of every chest or fishing hole of that name with loot, each spawn's "
        "area taken from pfQuest's objects file. Its own table and not mp, because s is one "
        "string table and one name can be a creature's and an object's both. "
        "pt: the paths a boss NAME walks (cmangos creature rank 3 only), keyed the way ck is: a "
        "list of packed strings, one per path, each the areaId once "
        f"({PIN_AREA_DIGITS} digits) then every point's x and y in TENTHS of a percent of that "
        f"area's zone map ({PIN_COORD_DIGITS} digits each), in walking order, from the cmangos "
        "creature_movement and creature_movement_template waypoints, drawn on the zone map of "
        f"the spawn's own pin area. At most {PATH_CAP} points, thinned evenly with the first and "
        "the last kept. A name with no entry walks no known path.",
        "ok: the category an op name's rows are filed under (8 herb, 9 vein, 10 fishing pool, "
        "11 chest; the lower where a name is filed under two), for every name op carries and "
        "no other, so the addon can say what a node is and whether it has a map without "
        "decoding a pin.",
        "qg: the quests a creature NAME starts and ends (creature_questrelation, "
        "creature_involvedrelation), keyed the way ck is: two packed strings, each quest id as "
        f'{QG_QUEST_DIGITS} base 91 digits, ascending, "" for none. A quest in both lists is '
        "both started and ended there. Every quest here is titled by a c=3 row or by qt. Since "
        "2026-09-29 every creature that starts or ends a titled quest has an entry, not only "
        "one that drops, sells or trains something: such a giver ships its name, ck, cd, mp, st "
        "and cf the way a vendor does. Object givers are not read.",
        "zm: the zone level UiMap id THIS build draws an area on, for every area z names that "
        "resolves to one. Absent means this build has no map for that area, which is every "
        "instance root area: this build ships no dungeon map at all, so a creature inside one "
        "has no pin and no map and the addon says so rather than guessing an entrance. "
        "st: the title under a vendor's, a trainer's or a quest giver's NAME "
        "(creature_template.SubName, such as Cooking Supplies), as an index into s, keyed the way "
        "ck is. Present only for the vendor names c=4 rows and lists use, the names tr and qg "
        "carry, and only where the source states one. Where creatures share a name, a vendor's "
        "title wins, then a trainer's, then the commonest. "
        "cf: the side a vendor's, a trainer's or a quest giver's NAME is on, keyed the way st "
        "is: 1 Alliance, 2 Horde, 3 both, from creature_template.Faction through THIS build's "
        "own FactionTemplate and Faction tables. Neutral (Booty Bay, Gadgetzan) is 3. Where "
        "creatures of one name disagree, 3. Absent means the build could not say. "
        "tr: the spells a trainer NAME teaches (npc_trainer, and npc_trainer_template through "
        "creature_template.TrainerTemplateId, a learn spell read as the spell it teaches by "
        "spell_template's learn effect), keyed the way ck is: one packed string, each spell id as "
        f"{TR_SPELL_DIGITS} base 91 digits, ascending. Only spells THIS build's SkillLineAbility "
        "files under a profession or secondary skill line: no class trainer. A spell's trainers "
        "are the "
        "names whose list holds it. "
        "qr: what a quest asks the player to bring (quest_template.ReqItemId1..4 and "
        "ReqItemCount1..4), keyed by quest id: one packed string, a run of fixed "
        f"{QR_ITEM_DIGITS + QR_COUNT_DIGITS} byte records in the x lists' base 91 alphabet, most "
        f"significant digit first: the item id ({QR_ITEM_DIGITS} digits) then how many "
        f"({QR_COUNT_DIGITS} digits), in the quest's own slot order. Only items this build ships "
        "(or withholds); a quest asking for none of them has no entry. An item's Used by quests "
        "are the quests whose record holds it. Every quest here is titled by a c=3 row or by qt "
        "(as an index or as a plain string; s gains no string for qr).",
        "x, xl: the rest of the list a summary row stands for, so it can be opened and "
        "searched. x[itemId][c] is a 1 based number into xl, and xl holds each distinct list "
        "once. A list is a run of fixed width records of base 91 digits (the bytes 35 to 126 "
        "with 92 left out), most significant first: c=13 is i (3 digits) then value (2), "
        "every other category is n (2), a (2), value (2). 0 means the field is absent. The "
        f"value is the stock for c=4, and otherwise the chance in tenths of a percent plus "
        f"{PACK_QUEST_ONLY} where the source is quest only. A list entry never carries q: the "
        "row says 'only while on a quest' and names none. c=5 ships no list.",
        CREDIT,
        *licence_lines(),
        "No item names, tooltips, flavour text, icons, comments or quest text are taken from "
        "either source. No row is emitted for an item this build hides, except the "
        f"{counts.get('withheldItems', 0)} withheld items an earlier build named, whose "
        f"{counts.get('withheldRows', 0)} rows ship so they can show once the client names the "
        "item. The pins in mp and op are the one coordinate this module takes, and they are "
        "reduced: no spawn table, no respawn timer, no height, and no pfQuest coordinate at all"
        + (" (the hand kept spots mc marks aside)." if table.curated_pins else "."),
        f"{counts.get('items', 0)} items, {counts.get('rows', 0)} rows ({', '.join(emitted)}), "
        f"{counts.get('rowsWithChance', 0)} with a chance, {counts.get('rowsWithArea', 0)} with "
        f"an area, over {counts.get('strings', 0)} strings and {counts.get('areas', 0)} areas.",
        f"{counts.get('questTitles', 0)} quest titles in qt, {counts.get('kinds', 0)} creature "
        f"kinds in ck ({counts.get('vendorKinds', 0)} of them vendors), "
        f"{counts.get('displays', 0)} creature display ids in cd, "
        f"{counts.get('questGiverNames', 0)} quest givers in qg ({counts.get('giverOnlyNames', 0)} "
        f"of them givers only; starts {counts.get('questGiverStarts', 0)}, ends "
        f"{counts.get('questGiverEnds', 0)}, {counts.get('questGiverQuests', 0)} quests in all), and "
        f"{counts.get('listEntries', 0)} further sources in "
        f"{counts.get('listsShipped', 0)} lists, stored as {counts.get('listsStored', 0)} "
        f"distinct packed strings; {counts.get('subnames', 0)} titles in st and "
        f"{counts.get('factions', 0)} sides in cf (Alliance {counts.get('factionsAlliance', 0)}, "
        f"Horde {counts.get('factionsHorde', 0)}, both {counts.get('factionsBoth', 0)}); "
        f"{counts.get('trainerNames', 0)} trainers in tr ({counts.get('trainerCreatures', 0)} "
        f"creatures) teaching {counts.get('trainerPairs', 0)} name and spell pairs over "
        f"{counts.get('trainerSpells', 0)} spells, profession and secondary only; "
        f"{counts.get('questRequiresQuests', 0)} quests in qr asking for "
        f"{counts.get('questRequiresItems', 0)} items ({counts.get('questRequiresPairs', 0)} quest "
        f"and item pairs; {counts.get('questRequiresTitlesByIndex', 0)} titled in qt by index, "
        f"{counts.get('questRequiresTitlesByString', 0)} by string).",
        f"{counts.get('pins', 0)} map pins in mp over {counts.get('pinNames', 0)} names and "
        f"{counts.get('pinGroups', 0)} name and area groups, standing for "
        f"{counts.get('pinSpawnsPlaced', 0)} spawns; {counts.get('objectPins', 0)} object map pins "
        f"in op over {counts.get('objectPinNames', 0)} names (herbs "
        f"{counts.get('objectPinsHerb', 0)}, veins {counts.get('objectPinsVein', 0)}, fishing "
        f"pools {counts.get('objectPinsPool', 0)}, chests {counts.get('objectPinsChest', 0)}), "
        f"standing for {counts.get('objectPinSpawnsPlaced', 0)} spawns; and "
        f"{counts.get('areaMaps', 0)} area to "
        f"UiMap answers in zm ({counts.get('areasWithNoMap', 0)} areas this build has no map "
        "for).",
        f"{counts.get('rowsInsideInstance', 0)} rows and "
        f"{counts.get('listEntriesInsideInstance', 0)} list entries carry one of the "
        f"{counts.get('instanceAreas', 0)} instance areas, which are places with no map.",
    ]


# ----- assembling the stage -----------------------------------------------------------------------


def gather_input(
    conn: sqlite3.Connection,
    build: str,
    *,
    cache_dir: Path,
    curated_quests_path: Path,
    force: bool = False,
) -> EraInput:
    """Fetch the pinned files and collect the two things that come from our own data.

    Everything here is I/O. The rules live in `derive`, which takes only this and a graph.
    """
    cmangos = fetch_pin(CMANGOS, cache_dir, force=force)
    units = fetch_pin(PFQUEST_UNITS, cache_dir, force=force)
    objects = fetch_pin(PFQUEST_OBJECTS, cache_dir, force=force)
    era_input = read_cmangos(cmangos)
    era_input.unit_points = read_spawn_points(units)
    era_input.unit_zones = zones_from_points(era_input.unit_points)
    era_input.object_points = read_spawn_points(objects)
    era_input.object_zones = zones_from_points(era_input.object_points)
    era_input.areas = area_names(conn, build)
    era_input.display_ids = build_display_ids(conn, build)
    era_input.area_maps = area_maps(conn, build, era_input.areas)
    era_input.map_bounds = map_bounds(conn, build)
    era_input.instance_areas = instance_areas(conn, build, era_input.areas)
    era_input.faction_sides = read_faction_sides(conn, build)
    era_input.skill_spells = read_skill_spells(conn, build)
    era_input.curated_quests = read_curated_quests(curated_quests_path)
    return era_input
