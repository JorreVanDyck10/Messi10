"""Fetch only explicitly selected Commons role-development images and attribution.

Existing source bytes are immutable. Unknown licenses/missing files are recorded
as rejected candidates rather than silently imported as training examples.
"""

from __future__ import annotations

import html
import re
import time
from datetime import UTC, datetime
from pathlib import Path
from urllib.parse import urlsplit

import cv2
import requests

from football_pipeline.contracts import read_json, sha256_file, write_json
from football_pipeline.video import ROOT


def plain(value):
    return html.unescape(re.sub(r"<[^>]+>", "", value or "")).strip()


def main():
    config_path = ROOT / "configs/role-sources-v3.json"
    output = ROOT / "datasets/roles-teams-v3"
    (output / "sources").mkdir(parents=True, exist_ok=True)
    target = output / "source-provenance.json"
    previous = read_json(target) if target.is_file() else {"sources": [], "rejected": []}
    saved = {r["id"]: r for r in previous["sources"]}
    records, rejected = [], []
    session = requests.Session()
    session.headers["User-Agent"] = "FootballCVResearch/1.0 educational role classification"
    for source in read_json(config_path)["sources"]:
        if source["id"] in saved:
            record = saved[source["id"]]
            if sha256_file(output / record["image"]) != record["sha256"]:
                raise ValueError("Existing source changed; restore its original bytes")
            records.append(record)
            continue
        response = session.get(
            "https://commons.wikimedia.org/w/api.php",
            params={
                "action": "query",
                "format": "json",
                "prop": "imageinfo",
                "iiprop": "url|extmetadata|size",
                "iiurlwidth": 1600,
                "titles": source["title"],
            },
            timeout=30,
        )
        if response.status_code == 429:
            rejected.append({**source, "reason": "Commons rate limit; source deferred, not used in dataset"})
            break
        response.raise_for_status()
        page = next(iter(response.json()["query"]["pages"].values()))
        if "imageinfo" not in page:
            rejected.append({**source, "reason": "Commons file unavailable"})
            continue
        info = page["imageinfo"][0]
        metadata = info.get("extmetadata", {})
        license_name = metadata.get("LicenseShortName", {}).get("value", "")
        license_url = metadata.get("LicenseUrl", {}).get("value", "")
        if not (license_name.startswith(("CC BY", "CC0", "Public domain"))):
            rejected.append(
                {**source, "reason": "No supported explicit free-image license", "metadata": info}
            )
            continue
        url = info.get("thumburl", info["url"]).split("?")[0]
        suffix = Path(urlsplit(info["url"]).path).suffix.lower()
        if suffix not in {".jpg", ".jpeg", ".png", ".webp"}:
            raise ValueError("Unexpected image extension in the Commons source URL")
        path = output / "sources" / (source["id"] + suffix)
        if path.exists():
            raise ValueError("Unregistered source file exists; inspect rather than overwrite it")
        download = session.get(url, timeout=45)
        download.raise_for_status()
        path.write_bytes(download.content)
        pixels = cv2.imread(str(path))
        if pixels is None:
            raise ValueError("Downloaded source is not a readable image")
        record = {
            **source,
            "image": path.relative_to(output).as_posix(),
            "sha256": sha256_file(path),
            "variant_url": url,
            "description_url": info["descriptionurl"],
            "license": plain(license_name),
            "license_url": plain(license_url),
            "author": plain(metadata.get("Artist", {}).get("value", "")),
            "retrieved_at": datetime.now(UTC).isoformat(),
            "metadata": info,
            "delivered_image_size": [pixels.shape[1], pixels.shape[0]],
            "modifications": "Commons thumbnail requested at width 1600 (actual delivered dimensions recorded), selected role crops and research overlays; no endorsement.",
        }
        records.append(record)
        write_json(
            target, {"config_sha256": sha256_file(config_path), "sources": records, "rejected": rejected}
        )
        print(source["id"], len(download.content), license_name, flush=True)
        time.sleep(1)
    write_json(target, {"config_sha256": sha256_file(config_path), "sources": records, "rejected": rejected})
    attribution = [
        "# Source attribution",
        "",
        "Role development data; images and derivatives retain the licenses below.",
        "",
    ]
    for record in records:
        attribution.extend(
            [
                f"- **{record['id']}**: [{record['title']}]({record['description_url']}), {record['author']}; "
                f"[{record['license']}]({record['license_url']}). {record['modifications']}",
            ]
        )
    video_source = output / "extracted-video-source.json"
    if video_source.is_file():
        video = read_json(video_source)
        attribution.append(
            f"- **nz-canada-frame0**: [Commons source]({video['source']}), {video['author']}; "
            f"[{video['license']}]({video['license_url']}). {video['changes']}"
        )
    (output / "ATTRIBUTION.md").write_text("\n".join(attribution) + "\n", encoding="utf-8")


if __name__ == "__main__":
    main()
