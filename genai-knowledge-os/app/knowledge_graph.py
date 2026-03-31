import json
import os

from shared.llm.gemini import generate_structured


MODEL = "gemini-3.1-pro-preview"

EXTRACTION_SCHEMA = {
    "type": "object",
    "properties": {
        "entities": {
            "type": "array",
            "items": {
                "type": "object",
                "properties": {
                    "name": {"type": "string"},
                    "type": {"type": "string"},
                },
                "required": ["name", "type"],
            },
        },
        "relationships": {
            "type": "array",
            "items": {
                "type": "object",
                "properties": {
                    "source": {"type": "string"},
                    "target": {"type": "string"},
                    "relation": {"type": "string"},
                },
                "required": ["source", "target", "relation"],
            },
        },
    },
    "required": ["entities", "relationships"],
}

PROMPT_TEMPLATE = """Extract entities and relationships from the following text.

Entities are key concepts, technologies, methods, people, or topics mentioned.
Relationships describe how entities are connected (e.g. "uses", "is a type of", "improves", "depends on").

Return only entities and relationships that are clearly stated or strongly implied in the text. Do not invent connections.

Text:
{text}"""


class KnowledgeGraph:
    def __init__(self, path: str | None = None):
        self._entities: dict[str, dict] = {}
        self._relationships: list[dict] = []
        self._path = path
        if path and os.path.exists(path):
            self.load()

    def extract_and_add(self, text: str, source: str = "") -> dict:
        text = text.strip()
        if not text:
            return {"entities": [], "relationships": []}

        prompt = PROMPT_TEMPLATE.format(text=text)
        result = generate_structured(prompt, model=MODEL, schema=EXTRACTION_SCHEMA)

        entities = result.get("entities", [])
        relationships = result.get("relationships", [])

        for entity in entities:
            name = entity.get("name", "").strip().lower()
            if not name:
                continue
            if name not in self._entities:
                self._entities[name] = {
                    "name": name,
                    "type": entity.get("type", "concept"),
                    "sources": [],
                }
            if source and source not in self._entities[name]["sources"]:
                self._entities[name]["sources"].append(source)

        for rel in relationships:
            src = rel.get("source", "").strip().lower()
            tgt = rel.get("target", "").strip().lower()
            relation = rel.get("relation", "").strip().lower()
            if not src or not tgt or not relation:
                continue
            if not any(
                r["source"] == src and r["target"] == tgt and r["relation"] == relation
                for r in self._relationships
            ):
                self._relationships.append({
                    "source": src,
                    "target": tgt,
                    "relation": relation,
                    "doc_source": source,
                })

        return {"entities": entities, "relationships": relationships}

    def get_entity(self, name: str) -> dict | None:
        return self._entities.get(name.strip().lower())

    def get_connections(self, name: str) -> list[dict]:
        key = name.strip().lower()
        return [
            r for r in self._relationships
            if r["source"] == key or r["target"] == key
        ]

    def get_entities(self) -> list[dict]:
        return list(self._entities.values())

    def get_relationships(self) -> list[dict]:
        return list(self._relationships)

    def save(self) -> None:
        if not self._path:
            return
        os.makedirs(os.path.dirname(self._path) or ".", exist_ok=True)
        data = {
            "entities": self._entities,
            "relationships": self._relationships,
        }
        with open(self._path, "w", encoding="utf-8") as f:
            json.dump(data, f)

    def load(self) -> None:
        if not self._path or not os.path.exists(self._path):
            return
        with open(self._path, "r", encoding="utf-8") as f:
            data = json.load(f)
        self._entities = data.get("entities", {})
        self._relationships = data.get("relationships", [])

    def __len__(self) -> int:
        return len(self._entities)
