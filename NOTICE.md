# Notice

This repository is the corresponding source for derived data that ships in the ItemTree World
of Warcraft addon as `Data/generated/EraSources.lua`.

## Upstream data

- **CMaNGOS Classic content database**, [cmangos/classic-db](https://github.com/cmangos/classic-db),
  at commit `22b51464f1625f6ef6275771de1f5466c6f5d19e`. Licensed under the GNU General Public
  License version 3. Its licence and its copyright notice are vendored verbatim at
  `third_party/cmangos-classic-db/LICENSE.md` and `third_party/cmangos-classic-db/COPYRIGHT.md`.
  Every source fact in the derived file but the zones comes from it: the sources, the
  creature, object, vendor and quest names and ids, drop chances, vendor stock and the spawn
  positions the map pins are reduced from.
- **pfQuest**, [shagu/pfQuest](https://github.com/shagu/pfQuest), at commit
  `104f35678ca39ab1fb78b655f815cc7016f5e0c8`, files `db/units.lua` and `db/objects.lua`.
  Licensed under the MIT licence, vendored verbatim at `third_party/pfQuest/LICENSE`. It gives
  the area id a creature or object spawns in, and nothing else is shipped from it.

World of Warcraft content and materials are trademarks and copyrights of Blizzard or its
licensors (see CMaNGOS's `COPYRIGHT.md`). This repository is not affiliated with Blizzard
Entertainment, CMaNGOS or pfQuest.

## Corresponding source

Per GPL v3, the **corresponding source** for that derived data is this repository. The build
script is exactly these files:

- `itemtree_era_sources/era_sources.py`, the compiler
- `itemtree_era_sources/build_facts.py`, the build facts it reads
- `itemtree_era_sources/luaout.py`, the writer that produces the .lua bytes
- `itemtree_era_sources/paths.py`, for `pipeline_version`

with the pinned inputs listed in `README.md`. The derived file is a modified, reduced
derivation of the CMaNGOS database: the reduction is described in its own header and in the
compiler's docstrings. The upstream notices are vendored under `third_party/`, and this
repository is licensed under GPL-3.0 (`LICENSE`).
