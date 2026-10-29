"""Download explicitly selected Commons sources with their attribution metadata."""

import json
import sys
import time
from pathlib import Path

import requests

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "src"))
from football_pipeline.contracts import sha256_file


def main():
    """Download de expliciet gekozen Commons-beelden en bewaar hun bron- en attributiegegevens bij de
    rolvoorbeelden.
    """
    root = Path(__file__).resolve().parents[1]
    target = root / "datasets/roles-teams-v1/sources"
    target.mkdir(parents=True, exist_ok=True)
    config = json.loads((root / "configs/role-photo-sources.json").read_text(encoding="utf-8"))
    provenance = target.parent / "source-provenance.json"
    previous = {
        source["id"]: source
        for source in (
            json.loads(provenance.read_text(encoding="utf-8"))["sources"] if provenance.is_file() else []
        )
    }
    session = requests.Session()
    session.headers["User-Agent"] = "FootballCVResearch/1.0 educational role classification"
    records = []
    for source in config["sources"]:
        if source["id"] in previous:
            saved = previous[source["id"]]
            path = target.parent / saved["image"]
            if not path.is_file():
                response = session.get(saved["variant_url"], timeout=30)
                response.raise_for_status()
                import hashlib

                if hashlib.sha256(response.content).hexdigest() != saved["sha256"]:
                    raise ValueError(
                        "Bronbestand gewijzigd; gebruik git lfs pull of maak een nieuwe datasetversie."
                    )
                path.write_bytes(response.content)
            if sha256_file(path) != saved["sha256"]:
                raise ValueError("Bestaande bronbeelden gewijzigd; ze worden niet overschreven.")
            records.append(saved)
            continue
        response = session.get(
            "https://commons.wikimedia.org/w/api.php",
            params={
                "action": "query",
                "format": "json",
                "prop": "imageinfo",
                "iiprop": "url|extmetadata|size",
                "iiurlwidth": 960,
                "titles": source["title"],
            },
            timeout=30,
        )
        response.raise_for_status()
        page = next(iter(response.json()["query"]["pages"].values()))
        info = page["imageinfo"][0]
        suffix = Path(source["title"]).suffix.lower()
        path = target / (source["id"] + suffix)
        if not path.is_file():
            download_url = info.get("thumburl", info["url"]).split("?")[0]
            image = session.get(download_url, timeout=30)
            for delay in (2, 5, 10):
                if image.status_code != 429:
                    break
                time.sleep(delay)
                image = session.get(download_url, timeout=30)
            image.raise_for_status()
            path.write_bytes(image.content)
        records.append(
            {
                **source,
                "image": path.relative_to(target.parent).as_posix(),
                "sha256": sha256_file(path),
                "metadata": info,
            }
        )
        (target.parent / "source-provenance.json").write_text(
            json.dumps({"sources": records}, indent=2, ensure_ascii=False) + "\n", encoding="utf-8"
        )
        print(source["id"], info["width"], info["height"], flush=True)
        time.sleep(1)
    (target.parent / "source-provenance.json").write_text(
        json.dumps({"sources": records}, indent=2, ensure_ascii=False) + "\n", encoding="utf-8"
    )


if __name__ == "__main__":
    main()
