"""
Seed the Pinecone index with all events from data/*.json.

Pipeline:
  1. Load 241 events from the three domain JSON files
  2. Build a text representation for each event
  3. Embed via Pinecone's hosted `multilingual-e5-large` (1024 dims)
  4. Upsert into Pinecone namespace "events" with metadata for filtering

The index must already exist (name: "srishti", dim: 1024, metric: cosine).
"""

import json
import os
import time
from pathlib import Path

from dotenv import load_dotenv
from pinecone import Pinecone

load_dotenv(Path(__file__).resolve().parents[1] / ".env")

DATA_DIR = Path(__file__).resolve().parents[1] / "data"
INDEX_NAME = os.environ.get("PINECONE_INDEX_NAME", "srishti")
EMBED_MODEL = "multilingual-e5-large"
NAMESPACE = "events"
BATCH_SIZE = 90  # Pinecone embed API caps at 96 texts per call
UPSERT_BATCH = 100


def load_events() -> list[dict]:
    """Load all events from the three domain files, tagging each with its id."""
    events: list[dict] = []
    for name in (
        "conferences_2025_2026.json",
        "music_festivals_2025_2026.json",
        "sporting_events_2025_2026.json",
    ):
        with open(DATA_DIR / name) as f:
            batch = json.load(f)
        for i, e in enumerate(batch):
            # Stable ID: domain + ASCII slug of name (Pinecone requires ASCII IDs)
            raw = (e.get("name") or f"unknown_{i}").lower()
            ascii_name = raw.encode("ascii", "ignore").decode("ascii")
            slug = "".join(c if c.isalnum() else "_" for c in ascii_name)[:80]
            if not slug.strip("_"):
                slug = f"event_{i}"
            e["_id"] = f"{e.get('domain', 'event')}__{slug}"
        events.extend(batch)
    return events


def build_embedding_text(e: dict) -> str:
    """Compose the text that will be embedded for a single event."""
    parts = [
        e.get("name") or "",
        f"Domain: {e.get('domain')}",
        f"Category: {e.get('category')}",
        f"Location: {e.get('city')}, {e.get('country')}",
        f"Venue: {e.get('venue_name') or 'unknown'}",
        f"Date: {e.get('start_date')} to {e.get('end_date') or e.get('start_date')}",
    ]
    if e.get("description"):
        parts.append(f"Description: {e['description'][:500]}")
    if e.get("sponsors"):
        parts.append(f"Sponsors: {', '.join(e['sponsors'][:10])}")
    if e.get("speakers"):
        parts.append(f"Speakers/Artists: {', '.join(e['speakers'][:10])}")
    return " | ".join(p for p in parts if p)


def build_metadata(e: dict) -> dict:
    """Metadata used for Pinecone filters. Must be string/number/bool/list."""
    return {
        "name": e.get("name") or "",
        "domain": e.get("domain") or "event",
        "category": e.get("category") or "",
        "city": e.get("city") or "",
        "country": e.get("country") or "",
        "year": int(e.get("year") or 0),
        "start_date": e.get("start_date") or "",
        "estimated_attendance": int(e.get("estimated_attendance") or 0),
        "ticket_price_max": float(e.get("ticket_price_max") or 0),
        "data_source": e.get("data_source") or "",
        "sponsors_count": len(e.get("sponsors") or []),
        "speakers_count": len(e.get("speakers") or []),
    }


def chunk(lst: list, n: int):
    for i in range(0, len(lst), n):
        yield lst[i : i + n]


def main() -> None:
    pc = Pinecone(api_key=os.environ["PINECONE_API_KEY"])
    index = pc.Index(INDEX_NAME)

    # Quick stats check before
    stats_before = index.describe_index_stats()
    print(f"Index before: {stats_before.get('total_vector_count', 0)} vectors")

    events = load_events()
    print(f"Loaded {len(events)} events total")

    texts_to_embed = [build_embedding_text(e) for e in events]

    # Embed in batches of 90
    all_vectors: list[list[float]] = []
    for batch_idx, text_batch in enumerate(chunk(texts_to_embed, BATCH_SIZE)):
        print(f"  Embedding batch {batch_idx + 1} ({len(text_batch)} texts)...")
        result = pc.inference.embed(
            model=EMBED_MODEL,
            inputs=text_batch,
            parameters={"input_type": "passage", "truncate": "END"},
        )
        for item in result:
            all_vectors.append(item["values"])
        time.sleep(0.5)  # be gentle on the free tier

    assert len(all_vectors) == len(events), (
        f"embedding count mismatch: {len(all_vectors)} vs {len(events)}"
    )

    # Build Pinecone records
    records = [
        {
            "id": e["_id"],
            "values": vec,
            "metadata": build_metadata(e),
        }
        for e, vec in zip(events, all_vectors)
    ]

    # Upsert in batches
    for batch_idx, rec_batch in enumerate(chunk(records, UPSERT_BATCH)):
        print(f"  Upserting batch {batch_idx + 1} ({len(rec_batch)} records)...")
        index.upsert(vectors=rec_batch, namespace=NAMESPACE)

    # Final stats
    time.sleep(2)  # Pinecone propagation delay
    stats_after = index.describe_index_stats()
    print(f"\nIndex after: {stats_after.get('total_vector_count', 0)} total vectors")
    ns = stats_after.get("namespaces", {}).get(NAMESPACE, {})
    print(f"Namespace '{NAMESPACE}': {ns.get('vector_count', 0)} vectors")


if __name__ == "__main__":
    main()
