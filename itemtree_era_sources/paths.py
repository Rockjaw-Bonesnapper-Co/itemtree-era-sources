# SPDX-License-Identifier: GPL-3.0-only
# Copyright (c) 2026 Rockjaw Bonesnapper Co
# Public home, the Corresponding Source of EraSources.lua: https://github.com/Rockjaw-Bonesnapper-Co/itemtree-era-sources
"""Repository layout. Every path the pipeline touches is derived from one root."""

from __future__ import annotations

import os
from dataclasses import dataclass
from importlib import metadata
from pathlib import Path


def pipeline_version() -> str:
    try:
        return metadata.version("itemtree-data")
    except metadata.PackageNotFoundError:
        return "0.0.0+local"


@dataclass(frozen=True)
class Paths:
    """All filesystem locations, derived from the repository root.

    Override the root with ITEMTREE_DATA_ROOT and the sibling addon checkout with
    ITEMTREE_ADDON_ROOT. Tests construct Paths(tmp_path) directly.
    """

    root: Path

    @classmethod
    def default(cls) -> Paths:
        env = os.environ.get("ITEMTREE_DATA_ROOT")
        root = Path(env).expanduser().resolve() if env else Path(__file__).resolve().parent.parent
        return cls(root)

    @property
    def builds(self) -> Path:
        return self.root / "builds"

    @property
    def cache(self) -> Path:
        return self.root / "cache"

    @property
    def db(self) -> Path:
        return self.root / "db" / "itemtree.sqlite"

    @property
    def out(self) -> Path:
        return self.root / "out"

    @property
    def assets(self) -> Path:
        return self.root / "assets" / "blizzard"

    @property
    def baseline_file(self) -> Path:
        return self.builds / "BASELINE"

    @property
    def addon_root(self) -> Path:
        env = os.environ.get("ITEMTREE_ADDON_ROOT")
        return Path(env).expanduser().resolve() if env else self.root.parent / "ItemTree"

    @property
    def addon_generated(self) -> Path:
        return self.addon_root / "Data" / "generated"

    def build_dir(self, build: str) -> Path:
        return self.builds / build

    def manifest_path(self, build: str) -> Path:
        return self.build_dir(build) / "manifest.json"

    def out_data_dir(self, build: str) -> Path:
        return self.out / build / "Data"

    def diff_dir(self, baseline: str, target: str) -> Path:
        return self.out / "diff" / f"{baseline}__{target}"

    def read_baseline(self) -> str | None:
        try:
            value = self.baseline_file.read_text(encoding="utf-8").strip()
        except FileNotFoundError:
            return None
        return value or None

    def write_baseline(self, build: str) -> None:
        self.builds.mkdir(parents=True, exist_ok=True)
        self.baseline_file.write_text(build + "\n", encoding="utf-8")


def validate_build_id(build: str) -> str:
    """Build ids look like 1.15.9.69722. Fixture builds may use a 'fx-' prefix."""
    parts = build.split(".")
    if build.startswith("fx-"):
        return build
    if len(parts) != 4 or not all(p.isdigit() for p in parts):
        raise ValueError(f"'{build}' is not a build id of the form major.minor.patch.build")
    return build
