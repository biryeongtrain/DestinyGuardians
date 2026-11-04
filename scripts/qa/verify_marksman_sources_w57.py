#!/usr/bin/env python3
"""Offline W57 provenance verification. Reads evidence; creates only a new --out file.

Uses the Python standard library, makes no network requests, and never refreshes
or repairs evidence. Private full sources and the W51-pinned inventory cache are
required. A passing result establishes captured-source integrity, not gameplay.
"""

import argparse
from datetime import datetime, timezone
import hashlib
from html.parser import HTMLParser
import json
from pathlib import Path
import sys


REFERENCE = "art/weapons/w57/references/"
AUDIT = "docs/qa/2026-10-24/w57/source-evidence/provenance-pins.json"
EXPECTED_ARTICLES = {
    "bungie_9_1_5": {
        "slug": "destiny_update_9_1_5",
        "title": "Destiny 2 Update 9.1.5",
        "heading": "Marksman's Dodge",
        "quotes": [
            "Now picks up nearby ammo bricks on activation.",
            "Now reloads all weapons on activation.",
        ],
    },
    "bungie_9_5_0": {
        "slug": "destiny_update_9_5_0",
        "title": "Destiny 2 Update 9.5.0",
        "heading": "Marksman’s Dodge",
        "quotes": ["Increased ammo pickup radius from 10 meters to 15 meters."],
    },
}
DEFINITION_QUOTE = (
    "Dodging automatically collects nearby ammo boxes and reloads all weapons."
)


def digest(path):
    h = hashlib.sha256()
    with path.open("rb") as stream:
        for chunk in iter(lambda: stream.read(1024 * 1024), b""):
            h.update(chunk)
    return h.hexdigest()


def canonical_digest(value):
    body = json.dumps(value, ensure_ascii=False, sort_keys=True,
                      separators=(",", ":"), allow_nan=False).encode("utf-8")
    return hashlib.sha256(body).hexdigest()


class BodyText(HTMLParser):
    def __init__(self):
        super().__init__(convert_charrefs=True)
        self.chunks = []

    def handle_data(self, data):
        self.chunks.append(data)


def normalize_html(body):
    parser = BodyText()
    parser.feed(body)
    parser.close()
    return " ".join(" ".join(parser.chunks).split())


class VerificationError(Exception):
    pass


def require(condition, message):
    if not condition:
        raise VerificationError(message)


def verify(root, cache_override, report):
    def path(value):
        p = Path(value)
        return p if p.is_absolute() else root / p

    def read(value):
        return json.loads(path(value).read_text(encoding="utf-8"))

    audit = read(AUDIT)
    require(audit["task"] == "W57" and audit["schemaVersion"] == 1,
            "Unexpected audit schema/task")
    pins = audit["inputPins"] + audit["outputPins"]
    require(len({p["path"] for p in pins}) == len(pins), "Duplicate audit pins")
    expected_pins = {p["path"]: p["sha256"] for p in pins}
    for pin in pins:
        actual = digest(path(pin["path"]))
        require(actual == pin["sha256"], "SHA-256 mismatch: " + pin["path"])
        report["checkedHashes"][pin["path"]] = actual
    report["checks"].append("All pinned reference, script, private source and W51 input hashes match")

    def pinned(pin):
        require(expected_pins.get(pin["path"]) == pin["sha256"],
                "Nested pin missing/different in audit: " + pin["path"])

    def retrieval(record_pin, body_pin, url):
        pinned(record_pin)
        pinned(body_pin)
        rec = read(record_pin["path"])
        require(rec["status"] == 200, "Retrieval was not HTTP 200")
        require(rec["requestUrl"] == url and rec["responseUrl"] == url,
                "Unexpected request/response URL")
        require(rec["bodyPath"] == body_pin["path"] and
                rec["sha256"] == body_pin["sha256"] and
                rec["bytes"] == path(body_pin["path"]).stat().st_size,
                "Retrieval record does not describe the pinned response")
        return rec

    sources = read(REFERENCE + "sources.json")
    require({s["id"] for s in sources["sources"]} == set(EXPECTED_ARTICLES)
            and len(sources["sources"]) == 2, "Expected exactly two articles")
    pinned(sources["retrieval"]["cmsPatternSource"])
    settings_rec = retrieval(sources["retrieval"]["settingsRetrievalRecord"],
                             sources["retrieval"]["settings"],
                             "https://www.bungie.net/Platform/Settings/")
    settings = read(sources["retrieval"]["settings"]["path"])
    require(settings["ErrorCode"] == 1, "Official Settings response failed")
    parameters = settings["Response"]["systems"]["ContentStack"]["parameters"]
    require(bool(parameters["ApiKey"]) and
            parameters["EnvPlusDeliveryToken"].startswith("{live}{"),
            "Settings does not identify live CMS delivery")
    # Do not include delivery credentials in diagnostics or generated results.
    del parameters, settings, settings_rec

    quote_count = 0
    for source in sources["sources"]:
        expected = EXPECTED_ARTICLES[source["id"]]
        slug = expected["slug"]
        require(source["primary"] is True and source["publisher"] == "Bungie",
                "Expected primary Bungie source")
        require(source["url"] == "https://www.bungie.net/7/en/News/Article/" + slug,
                "Canonical article URL mismatch")
        require(source["title"] == expected["title"] and
                source["sectionHeading"] == expected["heading"] and
                source["evidenceSubstrings"] == expected["quotes"],
                "Article evidence metadata differs from bounded W57 evidence")
        require(source["bodyField"] == "html_content" and
                source["environment"] == "live" and source["locale"] == "en-us",
                "Unexpected article body/delivery selector")
        rec = retrieval(source["retrievalRecord"], source["response"], source["requestUrl"])
        require(source["retrievedAt"] == rec["retrievedAt"], "Retrieval date mismatch")
        require(source["requestUrl"].startswith(
            "https://cdn.contentstack.io/v3/content_types/news_article/entries?"),
            "Unexpected CMS endpoint")
        # Parse the query as data, never evaluate source content.
        from urllib.parse import parse_qs, urlsplit
        query = parse_qs(urlsplit(source["requestUrl"]).query)
        require(query == {
            "environment": ["live"], "locale": ["en-us"],
            "query": [json.dumps({"url.hosted_url": "/" + slug}, separators=(",", ":"))],
            "limit": ["2"], "include_count": ["true"],
        }, "CMS query is not the bounded exact-slug request")
        response = read(source["response"]["path"])
        require(response["count"] == 1 and len(response["entries"]) == 1,
                "Expected exactly one CMS article")
        entry = response["entries"][0]
        pinned(source["article"])
        require(entry == read(source["article"]["path"]), "Full article differs from response entry")
        require(canonical_digest(entry) == source["articleCanonicalSha256"],
                "Article canonical digest mismatch")
        require(entry["uid"] == source["deliveryUid"] and
                entry["title"] == source["title"] and
                entry["date"] == source["publishedAt"] and
                entry["updated_at"] == source["updatedAt"] and
                entry["locale"] == "en-us" and
                entry["url"]["hosted_url"] == source["hostedUrl"] == "/" + slug,
                "Article identity/date/locale mismatch")
        retrieval(source["pageRetrievalRecord"], source["pageShell"], source["url"])
        text = normalize_html(entry["html_content"])
        require(text.count(source["sectionHeading"]) == 1, "Ambiguous ability heading")
        window_size = source["evidenceWindowCharacters"]
        require(window_size == 300, "Evidence window must stay bounded")
        start = text.index(source["sectionHeading"]) + len(source["sectionHeading"])
        window = text[start:start + window_size]
        for quote in source["evidenceSubstrings"]:
            require(quote in window, "Evidence absent near ability heading: " + source["id"])
            quote_count += 1
        words = len(" ".join([source["sectionHeading"]] + source["evidenceSubstrings"]).split())
        require(words == source["quotedWordsIncludingHeading"] and words <= 25,
                "Article quote budget mismatch/exceeded")
        report["articles"].append({
            "id": source["id"], "url": source["url"], "publishedAt": source["publishedAt"],
            "retrievedAt": source["retrievedAt"], "quotedWordsIncludingHeading": words,
        })
    report["checks"].append("Two exact official CMS entries, article equality, dates, headings and three evidence substrings match")

    manifest = read(REFERENCE + "official-manifest.json")
    pinned(manifest["w51Provenance"])
    w51 = read(manifest["w51Provenance"]["path"])
    require(manifest["pinnedManifest"] == w51["manifest"] and
            manifest["officialInventoryUrl"] == w51["source"] and
            manifest["fullCache"]["path"] == w51["fullCachePath"] and
            manifest["fullCache"]["sha256"] == w51["fullCacheSha256"],
            "W51 manifest/cache provenance mismatch")
    current = manifest["currentMetadata"]
    rec = retrieval(current["retrievalRecord"], current["response"], current["endpoint"])
    require(current["endpoint"] == "https://www.bungie.net/Platform/Destiny2/Manifest/",
            "Unexpected Manifest endpoint")
    raw = read(current["response"]["path"])
    require(raw["ErrorCode"] == 1, "Manifest API response failed")
    live = raw["Response"]
    inventory_path = live["jsonWorldComponentContentPaths"]["en"]["DestinyInventoryItemDefinition"]
    require(live["version"] == current["version"] == w51["manifest"]["version"] and
            inventory_path == current["inventoryPath"] == w51["manifest"]["path"] and
            current["matchesW51Version"] is True and current["matchesW51InventoryPath"] is True and
            current["retrievedAt"] == rec["retrievedAt"],
            "Captured live Manifest does not match W51 version/path/date")
    require(manifest["officialInventoryUrl"] == "https://www.bungie.net" + inventory_path,
            "Official inventory URL/path mismatch")
    cache_path = cache_override or path(manifest["fullCache"]["path"])
    cache_hash = digest(cache_path)
    require(cache_hash == manifest["fullCache"]["sha256"] and
            cache_path.stat().st_size == manifest["fullCache"]["bytes"],
            "Full inventory cache hash/length mismatch")
    report["checkedHashes"][str(cache_path)] = cache_hash
    pinned(manifest["selectedDefinition"])
    selected = read(manifest["selectedDefinition"]["path"])
    require(set(selected) == {"426473316"}, "Expected one complete selected definition")
    with cache_path.open(encoding="utf-8") as stream:
        inventory = json.load(stream)
    definition = selected["426473316"]
    require(definition == inventory["426473316"], "Selected definition differs from full official cache")
    require(manifest["definitionHash"] == definition["hash"] == 426473316 and
            manifest["name"] == definition["displayProperties"]["name"] == "Marksman's Dodge" and
            canonical_digest(definition) == manifest["definitionCanonicalSha256"],
            "Selected definition identity/canonical digest mismatch")
    require(manifest["descriptionEvidenceSubstrings"] == [DEFINITION_QUOTE] and
            DEFINITION_QUOTE in definition["displayProperties"]["description"],
            "Official definition evidence substring mismatch")
    require(len(DEFINITION_QUOTE.split()) == manifest["descriptionQuoteWords"] <= 25,
            "Definition quote budget mismatch/exceeded")
    report["checks"].append("W51 full-cache hash, complete definition equality and definition evidence match")
    report["checks"].append("Captured current Manifest version and English inventory path equal W51 pins; no inventory redownload")
    report["exactEvidenceSubstrings"] = quote_count + 1
    report["manifestVersion"] = current["version"]
    report["manifestMetadataRetrievedAt"] = current["retrievedAt"]
    report["definitionHash"] = 426473316
    report["unprovenGameplay"] = [x["id"] for x in sources["unprovenGameplay"]]


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--root", type=Path, default=Path(__file__).resolve().parents[2])
    parser.add_argument("--cache", type=Path, help="Relocated identical inventory cache; same pinned SHA required")
    parser.add_argument("--out", type=Path, required=True,
                        help="New JSON result file; parent must exist; existing files are never overwritten")
    args = parser.parse_args()
    out = args.out.absolute()
    if out.exists() or out.is_symlink() or not out.parent.is_dir():
        print("--out must be a new file with an existing parent; no evidence was changed", file=sys.stderr)
        return 2
    report = {
        "schemaVersion": 1, "task": "W57", "status": "failed",
        "verifiedAt": datetime.now(timezone.utc).isoformat(),
        "offline": True, "networkRequests": 0, "inputsModified": False,
        "liveGameplayVerified": False, "runtimeInspected": False,
        "exhaustivePatchAudit": False, "checkedHashes": {}, "checks": [],
        "articles": [], "errors": [],
    }
    try:
        verify(args.root.resolve(), args.cache, report)
        report["status"] = "passed"
    except (VerificationError, OSError, ValueError, KeyError, TypeError) as exc:
        report["errors"].append(str(exc))
    try:
        # Exclusive creation also handles an output path appearing during verification.
        with out.open("x", encoding="utf-8") as stream:
            json.dump(report, stream, indent=2, ensure_ascii=False, allow_nan=False)
            stream.write("\n")
    except OSError as exc:
        print("Could not create new result: " + str(exc), file=sys.stderr)
        return 2
    print(json.dumps({"status": report["status"], "filesHashed": len(report["checkedHashes"]),
                      "errors": report["errors"], "out": str(out)}))
    return 0 if report["status"] == "passed" else 1


if __name__ == "__main__":
    sys.exit(main())
