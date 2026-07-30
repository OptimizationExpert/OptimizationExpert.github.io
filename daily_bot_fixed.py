import json
import datetime
from pathlib import Path

import arxiv

KEYWORDS = [
    "constraint programming",
    "mixed integer linear programming",
    "MILP",
    "combinatorial optimization",
    "CP-SAT",
]

MAX_RESULTS = 15
OUTPUT_PATH = Path("data/items.json")


def run() -> None:
    query = " OR ".join(KEYWORDS)
    results = []

    search = arxiv.Search(
        query=query,
        max_results=MAX_RESULTS,
        sort_by=arxiv.SortCriterion.SubmittedDate,
        sort_order=arxiv.SortOrder.Descending,
    )

    client = arxiv.Client(
        page_size=MAX_RESULTS,
        delay_seconds=3.0,
        num_retries=3,
    )

    for paper in client.results(search):
        results.append(
            {
                "title": paper.title,
                "url": paper.entry_id,
                "published": paper.published.strftime("%Y-%m-%d"),
                "summary": " ".join(paper.summary.split())[:300],
                "source": "arXiv",
            }
        )

    output = {
        "generated_at": datetime.datetime.now(datetime.UTC).isoformat(),
        "items": results,
    }

    OUTPUT_PATH.parent.mkdir(parents=True, exist_ok=True)
    with OUTPUT_PATH.open("w", encoding="utf-8") as file:
        json.dump(output, file, ensure_ascii=False, indent=2)

    print(f"Saved {len(results)} papers to {OUTPUT_PATH}")


if __name__ == "__main__":
    run()
