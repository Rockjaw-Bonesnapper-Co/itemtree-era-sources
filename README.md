# itemtree-era-sources

This repository is the Corresponding Source, in the GPL-3.0 sense, for three generated files:

| file | ships in | what it is |
| --- | --- | --- |
| `EraSources.lua` | the ItemTree addon's `ItemTree_Data` folder | historical Classic Era item sources, keyed by item |
| `BossLoot.lua` | the ItemTree addon's `ItemTree_Data` folder | what each Classic Era creature and chest drops, keyed by creature and object id |
| `EraFacts.lua` | the Jettison addon's `Jettison_Data` folder | the Classic Era vendor count per item and the Classic Era quest titles and sides |

Each holds data derived from the pinned CMaNGOS Classic content database alone (and pfQuest's area
ids), so each is distributed under the GNU General Public License version 3, the licence of the
database it is derived from, and so is everything here (see `LICENSE`). The addons themselves are
all rights reserved, and nothing else of either addon is in this repository: each GPL file ships
beside a file of the addon's own (`EraPlaces.lua`, `BossLootIndex.lua`, `Facts.lua`), which the
addon joins to it at run time and which is not derived from these sources.

ItemTree and Jettison are published at CurseForge and at Wago Addons.

## The credit

`EraSources.lua` and `EraFacts.lua` carry this paragraph, word for word, and so does everything
that shows their data:

> Historical Classic Era source data, derived from the CMaNGOS Classic content database
> (github.com/cmangos/classic-db), which the MaNGOS community compiled for World of Warcraft
> patch 1.12. Creature, object and quest names, vendor, trainer and quest giver titles and their
> factions (reduced to Alliance, Horde or both through the client's own faction tables) and which
> spells a trainer teaches are that database's own. Drop chances are that database's own loot
> table figures. Map pins are reduced from that database's own spawn positions. Creature and
> object zones come from pfQuest's vanilla database (github.com/shagu/pfQuest), which contributes
> the area id and nothing else. WoW Forever may differ; the addon shows these as predicted.

`BossLoot.lua` carries its own:

> Historical Classic Era boss loot, derived from the CMaNGOS Classic content database
> (github.com/cmangos/classic-db), which the MaNGOS community compiled for World of Warcraft
> patch 1.12. Which items a creature or a chest drops, and how often, are that database's own
> loot table figures. WoW Forever may differ; the addon shows these as predicted.

## What is here

| file | what it is |
| --- | --- |
| `itemtree_era_sources/era_sources.py` | the compiler of `EraSources.lua`: fetches and verifies the pinned inputs, reads them, applies every rule, and builds the module's value and header |
| `itemtree_era_sources/era_boss_loot.py` | the compiler of `BossLoot.lua`: per CMaNGOS creature and chest, the items it drops and how often, from the CMaNGOS input alone |
| `itemtree_era_sources/jettison.py` | the compiler of Jettison's `EraFacts.lua`: the Classic Era vendor counts, quest titles and sides |
| `itemtree_era_sources/build_facts.py` | `BuildFacts`, the plain selections about a client build `era_sources.derive` takes (ids and whole numbers, made by the caller) |
| `itemtree_era_sources/luaout.py` | the writer: serialises a module's value and header into the .lua bytes (`lua_value`, `lua_module`) |
| `itemtree_era_sources/test_rows.py` | the markers that keep test and placeholder rows out of every file |
| `NOTICE.md` | the upstream databases, their licences and commits |
| `third_party/` | the upstream licence and copyright notices, verbatim |

The six Python files are byte for byte copies of the ones in the ItemTree data pipeline, which a
sync script checks every time they are published. The one helper that writes a GPL licence line
into a generated file, `era_sources.gpl_declaration`, is here, and the pipeline's own tests fail if
any file outside these six writes one.

Comments refer to `docs/era-sources.md`, `docs/boss-loot.md` and `docs/data-format.md`. Those live
in the private pipeline and are not published here; the record shape they describe is restated,
field by field, in the header of each generated file itself.

## The pinned inputs

Each input is fetched once into a local `cache/era/` folder and checked against its size and
sha256 on every run: the compiler compiles those exact bytes or fails. They are never
committed. These are the `Pin` records in `era_sources.py`.

| name | repository | commit | path | sha256 | bytes |
| --- | --- | --- | --- | --- | --- |
| `cmangos-classic-db` | cmangos/classic-db (GPL-3.0) | `22b51464f1625f6ef6275771de1f5466c6f5d19e` | `Full_DB/ClassicDB_1_12_1_z2815.sql.gz` | `4f92db520868ab4e566726f68b5b2e380ae781209beaf22237b4f7f04600d0c0` | 12,959,882 |
| `pfquest-units` | shagu/pfQuest (MIT) | `104f35678ca39ab1fb78b655f815cc7016f5e0c8` | `db/units.lua` | `b8de09aa33fd4b16edb2287b8c4224c86e6ee420e717a4d428e2935c22c4a922` | 3,497,202 |
| `pfquest-objects` | shagu/pfQuest (MIT) | `104f35678ca39ab1fb78b655f815cc7016f5e0c8` | `db/objects.lua` | `be4846e2f2049cafba7da5ed18d6422bde35ed0e6f6ac34cb1215c1bbafd306e` | 2,464,841 |

## How each file is built

1. `era_sources.read_inputs(cache_dir=...)` fetches the three pins with `fetch_pin` (one request
   each, only when the cache lacks them), reads the dump with `read_cmangos` and pfQuest's files
   with `read_spawn_points`, and returns an `EraInput` holding the CMaNGOS and pfQuest facts.
2. `BossLoot.lua`: `era_sources.cmangos_only(era_input, credits=era_boss_loot.read_credits(dump))`
   is the CMaNGOS half of that input (a `CmangosOnly`, the one type the writer takes), and
   `era_boss_loot.build` then `era_boss_loot.module_text` make the file. Which creatures and chests
   it holds is a CMaNGOS rule of its own (see the module docstring), so it needs nothing about a
   client build.
3. `EraSources.lua`: `era_sources.derive(era_sources.cmangos_only(era_input), build_facts)`, where
   `build_facts` is a `BuildFacts` the caller made (next section), applies every rule and returns an
   `EraSources`; `era_sources.module_text(table, build=..., baseline=..., generated=...,
   version=...)` writes the file: the GPL keys alone (`GPL_FIELDS`), each place in `s` that only a
   zone name would hold left empty.
4. `EraFacts.lua`: `jettison.build_era_facts(era_sources_table, cmangos_only, ...)` then
   `jettison.file_text(...)`.

## What `EraSources.lua`'s compiler still needs from a game client

Neither database knows which items a given WoW client build names, so `derive` is also told about
the build it compiles for, and those answers still choose and order the CMaNGOS rows it keeps. The
compiler reads no client table and no file of the addon's itself, and its code names none: the
caller (the ItemTree pipeline) reads the build's own tables and the addon's own quest table, works
out each answer, and hands it over as a `BuildFacts` (`build_facts.py`), plain selections of ids
and whole numbers with no string of any kind:

| selection | what it decides | what the caller makes it from |
| --- | --- | --- |
| `items`, `withheld`, `undiscovered` | which items get a row (named by the build, or withheld: hidden by it and named by an earlier build), and how a refused one is counted | `Item`, `ItemSparse` |
| `row_areas` | which pfQuest area ids a row keeps | `AreaTable` |
| `area_ranks`, `area_ties` | where the place of an area's name sorts in `s`: how many of the dump's own strings (`era_sources.dump_strings`) sort before the name, and its order among the names of that rank. The name itself never reaches the compiler | `AreaTable` |
| `creature_instances`, `object_instances` | the area of a creature or an object that lives inside an instance | `Map`, with the dump's own spawns |
| `node_categories` | which loot chests are a herb, a vein or a pool | `Lock`, `LockType` |
| `known_displays` | which creature display ids `cd` keeps | `CreatureDisplayInfo` |
| `profession_spells`, `class_spells` | which taught spells `tr` keeps, and how a refused one is counted | `SkillLineAbility`, `SkillLine` |
| `quest_items_left_out` | quest rewards the addon already states, which are not repeated | the addon's own quest table |

None of their values is written into the file but the item, area and category ids those rules
choose: each place in `s` that only an area name would hold is shipped empty, and the zone names,
maps, pins, paths and sides, and which creature pages are one page with Forever's, are the addon's
own `EraPlaces.lua`, made beside it by ItemTree's own pipeline code, which is not here. `EraSources.lua`'s `ci` (per creature name `ck` carries, the lowest
`creature_template` entry of exactly that name: the id the addon keys a Classic Era creature's
page by) and `oi` (per object name a row or list names, a herb, a vein, a fishing pool or a chest,
the lowest `gameobject_template` entry of exactly that name: the id the addon keys an object's
page by) come from the dump alone and need nothing of a client build.
