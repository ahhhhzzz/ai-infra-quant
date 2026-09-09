"""One bounded public access check per route. Never bypass a challenge or use a secret."""

import argparse
from datetime import UTC, datetime
from hashlib import sha256
from pathlib import Path
from urllib.error import HTTPError, URLError
from urllib.request import Request, urlopen

from ..phase_a import write_new

URLS = (
    "https://stooq.com/q/d/?s=nvda.us",
    "https://stooq.com/t/",
    "https://www.alphavantage.co/documentation/",
    "https://www.alphavantage.co/query?function=TIME_SERIES_DAILY&symbol=NVDA&outputsize=full&apikey=demo",
    "https://in.help.yahoo.com/kb/SLN2311.html",
)


def attempt(output: Path, raw_dir: Path) -> None:
    raw_dir.mkdir(parents=True, exist_ok=False)
    rows = []
    for i, url in enumerate(URLS):
        row = {"url": url, "retrieved_at": datetime.now(UTC).isoformat()}
        try:
            request = Request(url, headers={"User-Agent": "PAQS-Q-R02-public-research/1.0"})
            with urlopen(request, timeout=20) as response:
                body = response.read(2_000_001)
                row["http_status"] = str(response.status)
            if len(body) > 2_000_000:
                row["result"] = "BODY_BOUND_EXCEEDED"
            else:
                path = raw_dir / f"public-{i}.txt"
                path.write_bytes(body)
                row.update(
                    {
                        "raw_file": str(path.resolve()),
                        "sha256": sha256(body).hexdigest(),
                        "bytes": str(len(body)),
                        "result": "FETCHED_REQUIRES_CONTENT_REVIEW",
                    }
                )
                if "query?" in url:
                    row["public_demo_response"] = body.decode("utf-8", errors="replace")[:2000]
        except (HTTPError, URLError, TimeoutError, OSError) as exc:
            row.update(
                {"result": "UNAVAILABLE", "error_type": type(exc).__name__, "error": str(exc)}
            )
        rows.append(row)
    write_new(
        output,
        {
            "attempts": rows,
            "open_d_requests": 0,
            "automatic_retries": 0,
            "additional_ceiling": "2026-09-09T14:00:00Z",
            "note": "No observations normalized before source/calendar/terms review.",
        },
    )


if __name__ == "__main__":
    parser = argparse.ArgumentParser()
    parser.add_argument("--output", type=Path, required=True)
    parser.add_argument("--raw-dir", type=Path, required=True)
    args = parser.parse_args()
    attempt(args.output, args.raw_dir)
