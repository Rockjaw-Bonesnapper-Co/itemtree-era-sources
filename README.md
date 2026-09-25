# itemtree-era-sources

This repository is the Corresponding Source, in the GPL-3.0 sense, for one file:
`Data/generated/EraSources.lua`, the module of historical Classic Era item sources that ships
inside the ItemTree World of Warcraft addon. That one generated file is distributed under the
GNU General Public License version 3, the licence of the database it is derived from, and so is
everything here (see `LICENSE`). The ItemTree addon itself is all rights reserved, and nothing
else of ItemTree is in this repository.

ItemTree is published at CurseForge and at Wago Addons.

## The credit

The generated file carries this paragraph, word for word, and so does everything that shows
its data:

> Historical Classic Era source data, derived from the CMaNGOS Classic content database
> (github.com/cmangos/classic-db), which the MaNGOS community compiled for World of Warcraft
> patch 1.12. Drop chances are that database's own loot table figures. Map pins are reduced
> from that database's own spawn positions. Creature and object zones come from pfQuest's
> vanilla database (github.com/shagu/pfQuest), which contributes the area id and nothing else.
> WoW Forever may differ; the addon shows these as predicted.

## What is here

| file | what it is |
| --- | --- |
| `itemtree_era_sources/era_sources.py` | the compiler: fetches and verifies the pinned inputs, reads them, applies every rule, and builds the module's value and header |
| `itemtree_era_sources/build_facts.py` | `BuildFacts`, the four facts about a client build the compiler needs |
| `itemtree_era_sources/luaout.py` | the writer: serialises the module's value and header into the .lua bytes (`lua_value`, `lua_module`) |
| `itemtree_era_sources/paths.py` | `pipeline_version`, which the compiler's user agent names (and the pipeline's path layout, unused here) |
| `NOTICE.md` | the upstream databases, their licences and commits |
| `third_party/` | the upstream licence and copyright notices, verbatim |

The four Python files are byte for byte copies of the ones in the ItemTree data pipeline,
which a sync script checks every time they are published.

Comments in `era_sources.py` refer to `docs/era-sources.md` and `docs/source-data-options.md`.
Those live in the private pipeline and are not published here; the record shape they describe
is restated, field by field, in the header of the generated `EraSources.lua` itself.

## The pinned inputs

Each input is fetched once into a local `cache/era/` folder and checked against its size and
sha256 on every run: the compiler compiles those exact bytes or fails. They are never
committed. These are the `Pin` records in `era_sources.py`.

| name | repository | commit | path | sha256 | bytes |
| --- | --- | --- | --- | --- | --- |
| `cmangos-classic-db` | cmangos/classic-db (GPL-3.0) | `22b51464f1625f6ef6275771de1f5466c6f5d19e` | `Full_DB/ClassicDB_1_12_1_z2815.sql.gz` | `4f92db520868ab4e566726f68b5b2e380ae781209beaf22237b4f7f04600d0c0` | 12,959,882 |
| `pfquest-units` | shagu/pfQuest (MIT) | `104f35678ca39ab1fb78b655f815cc7016f5e0c8` | `db/units.lua` | `b8de09aa33fd4b16edb2287b8c4224c86e6ee420e717a4d428e2935c22c4a922` | 3,497,202 |
| `pfquest-objects` | shagu/pfQuest (MIT) | `104f35678ca39ab1fb78b655f815cc7016f5e0c8` | `db/objects.lua` | `be4846e2f2049cafba7da5ed18d6422bde35ed0e6f6ac34cb1215c1bbafd306e` | 2,464,841 |

## What the compiler needs from the game client

Neither database knows which items a given WoW client build names, so the compiler also takes
facts about the build it compiles for. The private ItemTree pipeline reads them out of the game
client's own database tables. Anyone who has them for a build can run the compiler.

`BuildFacts` (in `build_facts.py`) is the object `derive` takes. Four attributes, each a
mapping by id:

| attribute | what it is | client tables |
| --- | --- | --- |
| `items` | every item id the build names; only membership is read | `Item` and `ItemSparse` (an id with a row in both) |
| `undiscovered` | the item ids the build lists but hides; only membership is read, and no row is ever emitted for one | `Item` (an id with no `ItemSparse` row) |
| `locks` | lock id to its `types`, the `(LockType id, skill)` pairs of its slots | `Lock` |
| `lock_types` | LockType id to its name, which tells a herb node, a vein and a pool apart | `LockType` (`Name_lang`) |

The rest of the build's facts travel in the `EraInput`. `gather_input` reads them from a SQLite
database holding the client tables with a `build_id` column: area names (`AreaTable`), the
creature display ids the build has (`CreatureDisplayInfo`), which zone map each area is drawn
on and where its corners sit (`UiMap`, `UiMapAssignment`, `UiMapXMapArt`, `WorldMapOverlay`,
`AreaTable`), and the area of each instance map (`Map`, `AreaTable`). It also reads the addon's
own hand maintained quest table (`curated_quests`: quest id to the items it rewards), so that no
row repeats a quest reward the addon already states first hand; an empty file is a valid answer.

## How the module is built

1. `gather_input(conn, build, cache_dir=..., curated_quests_path=...)` fetches the three pins
   with `fetch_pin` (one request each, only when the cache lacks them), reads the dump with
   `read_cmangos` and pfQuest's files with `read_spawn_points` and `read_zone_map`, and adds
   the client facts above. It returns an `EraInput`.
2. `derive(era_input, build_facts)` applies every rule and returns an `EraSources`.
3. The writer: `EraSources.module_value()` is the Lua table's value, and
   `header_lines(table)` is the header comment, the field legend, the credit and the licence
   lines (`licence_lines()`). `luaout.lua_value(value, indent=1)` turns the value into a
   deterministic Lua table literal, and `luaout.lua_module("EraSources", header, body)` writes
   the .lua bytes: each header line as one `--` comment line, after two stamp lines ("ItemTree
   generated data. Do not edit." and the build and Generated date), then the table inside a
   self registering module function.

The licence of the generated file and its header text are chosen by one constant,
`LICENCE_MODE`, which is `"gpl"`.
