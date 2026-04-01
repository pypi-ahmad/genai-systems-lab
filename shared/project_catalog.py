"""Shared project catalog loaded from the portfolio JSON manifest."""

from __future__ import annotations

import json
from functools import lru_cache
from pathlib import Path
from typing import Any, Literal

from pydantic import BaseModel, ConfigDict, Field

REPO_ROOT = Path(__file__).resolve().parent.parent
CATALOG_PATH = REPO_ROOT / "portfolio" / "src" / "data" / "project-catalog.json"

Category = Literal["GenAI", "LangGraph", "CrewAI"]


class GraphNode(BaseModel):
    model_config = ConfigDict(frozen=True)

    id: str
    label: str


class GraphEdge(BaseModel):
    model_config = ConfigDict(frozen=True, populate_by_name=True)

    from_id: str = Field(alias="from")
    to: str
    label: str | None = None


class ProjectGraph(BaseModel):
    model_config = ConfigDict(frozen=True)

    nodes: list[GraphNode]
    edges: list[GraphEdge]


class ProjectDemoConfig(BaseModel):
    model_config = ConfigDict(frozen=True)

    enabled: bool | None = None
    title: str | None = None
    description: str | None = None
    ctaLabel: str | None = None


class ProjectCatalogEntry(BaseModel):
    model_config = ConfigDict(frozen=True)

    name: str
    slug: str
    category: Category
    description: str
    tags: list[str]
    highlights: list[str]
    architecture: str
    features: list[str]
    exampleInput: str
    exampleOutput: str
    apiEndpoint: str
    demo: ProjectDemoConfig | None = None
    graph: ProjectGraph


def _normalized_project_key(value: str) -> str:
    return value.removeprefix("genai-").removeprefix("lg-").removeprefix("crew-")


def project_api_name(api_endpoint: str) -> str:
    return api_endpoint.removeprefix("/").removesuffix("/run")


@lru_cache(maxsize=1)
def load_project_catalog() -> tuple[ProjectCatalogEntry, ...]:
    payload = json.loads(CATALOG_PATH.read_text(encoding="utf-8"))
    return tuple(ProjectCatalogEntry.model_validate(item) for item in payload)


def list_project_manifest_entries(*, runnable_projects: set[str] | None = None) -> list[dict[str, Any]]:
    entries: list[dict[str, Any]] = []

    for entry in load_project_catalog():
        if runnable_projects is not None and entry.slug not in runnable_projects:
            continue
        entries.append(entry.model_dump(by_alias=True))

    return entries


def build_pipeline_nodes_index() -> dict[str, list[str]]:
    index: dict[str, list[str]] = {}

    for entry in load_project_catalog():
        node_ids = [node.id for node in entry.graph.nodes]
        api_name = project_api_name(entry.apiEndpoint)
        for key in {
            entry.slug,
            api_name,
            _normalized_project_key(entry.slug),
            _normalized_project_key(api_name),
        }:
            if key:
                index[key] = node_ids

    return index