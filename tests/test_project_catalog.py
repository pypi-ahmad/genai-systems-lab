"""Tests for the shared project catalog that feeds both backend and frontend."""

from __future__ import annotations

import json

from shared.project_catalog import (
    CATALOG_PATH,
    build_pipeline_nodes_index,
    list_project_manifest_entries,
    load_project_catalog,
    project_api_name,
)


def test_catalog_json_is_valid_and_non_empty():
    raw = json.loads(CATALOG_PATH.read_text(encoding="utf-8"))
    assert isinstance(raw, list)
    assert len(raw) == 20, f"Expected 20 projects, got {len(raw)}"


def test_load_project_catalog_returns_typed_entries():
    catalog = load_project_catalog()
    assert len(catalog) == 20
    slugs = [entry.slug for entry in catalog]
    assert "genai-research-system" in slugs
    assert "genai-nl2sql-agent" in slugs


def test_every_entry_has_required_graph_nodes():
    for entry in load_project_catalog():
        assert len(entry.graph.nodes) >= 2, f"{entry.slug} needs at least 2 graph nodes"
        assert len(entry.graph.edges) >= 1, f"{entry.slug} needs at least 1 graph edge"


def test_pipeline_nodes_index_covers_all_projects():
    index = build_pipeline_nodes_index()
    catalog = load_project_catalog()
    for entry in catalog:
        assert entry.slug in index, f"{entry.slug} missing from pipeline index"
        assert len(index[entry.slug]) >= 2


def test_project_api_name_strips_properly():
    assert project_api_name("/research-system/run") == "research-system"
    assert project_api_name("/nl2sql-agent/run") == "nl2sql-agent"
    assert project_api_name("browser-agent/run") == "browser-agent"


def test_list_project_manifest_entries_with_filter():
    all_entries = list_project_manifest_entries()
    assert len(all_entries) == 20

    filtered = list_project_manifest_entries(
        runnable_projects={"genai-research-system", "genai-nl2sql-agent"}
    )
    assert len(filtered) == 2
    slugs = {e["slug"] for e in filtered}
    assert slugs == {"genai-research-system", "genai-nl2sql-agent"}


def test_catalog_entries_have_consistent_api_endpoints():
    for entry in load_project_catalog():
        api = project_api_name(entry.apiEndpoint)
        assert api, f"{entry.slug} has empty apiEndpoint"
        assert "/" not in api, f"{entry.slug} apiEndpoint not fully stripped: {api}"
