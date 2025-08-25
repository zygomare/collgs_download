#!/usr/bin/env python3
import os
import sys
import json
import pathlib
import urllib.parse
import requests
from typing import Any, Dict, Iterable, Set

BASE_PREFIX = "https://collgs.lu/"


def load_config(config_path: str) -> Dict[str, Any]:
    """Load configuration from file or exit if not found"""
    if not config_path or not os.path.exists(config_path):
        print(f"Error: Config file '{config_path}' not found.")
        print("Creating a sample config file 'sample_config.json'...")

        # Create a detailed sample config to help the user get started
        sample_config = {
            "base_url": "https://collgs.lu/catalog/oseo/search",
            "parameters": {
                "parentIdentifier": "S2_MSIL2A",
                "box": "-73.3533267672645,45.78947623450331,-73.2349231864892,45.879022657149314",
                "timeStart": "2025-03-01T00:00:00.000Z",
                "timeEnd": "2025-08-26T00:00:00.000Z",
                "cloudCover": "[0,49]",
                "httpAccept": "json",
                "productType": "S2MSI2A",
                "platform": "Sentinel-2",
                "orbitDirection": "ASCENDING",
                "maxRecords": 100
            },
            "output_directory": "downloads",
            "connection": {
                "timeout": 120,
                "retries": 3,
                "user_agent": "eo-downloader/1.0"
            },
            "download_options": {
                "chunk_size": 65536,
                "skip_existing": True
            }
        }

        with open("sample_config.json", "w") as f:
            json.dump(sample_config, f, indent=2)
        print("Please edit this file and run the script again with:")
        print("python collgs_download.py sample_config.json")
        sys.exit(1)

    try:
        with open(config_path, 'r') as f:
            config = json.load(f)

            # Verify essential keys exist with default values if missing
            if "base_url" not in config:
                config["base_url"] = "https://collgs.lu/catalog/oseo/search"
            if "parameters" not in config:
                config["parameters"] = {}
            if "parameters" in config and "httpAccept" not in config["parameters"]:
                config["parameters"]["httpAccept"] = "json"
            if "output_directory" not in config:
                config["output_directory"] = "downloads"

            return config
    except (json.JSONDecodeError, IOError) as e:
        print(f"Error reading config file: {e}")
        sys.exit(1)


def build_url_from_config(config: Dict[str, Any]) -> str:
    """Build a URL from configuration parameters"""
    base_url = config.get("base_url", "https://collgs.lu/catalog/oseo/search")
    params = config.get("parameters", {})

    # Ensure httpAccept is set to json
    if "httpAccept" not in params:
        params["httpAccept"] = "json"

    return f"{base_url}?{urllib.parse.urlencode(params, safe='[],:')}"


def resolve_url(u: str) -> str:
    """Prefix relative URLs with the host."""
    if u.startswith("http://") or u.startswith("https://"):
        return u
    # normalize to avoid double slashes
    return urllib.parse.urljoin(BASE_PREFIX, u.lstrip("/"))


def find_zip_links(obj: Any) -> Set[str]:
    """
    Recursively scan a JSON-like structure for .zip URLs.
    Prioritizes 'data' sections but will also look anywhere to be resilient.
    """
    found: Set[str] = set()

    def _walk(node: Any):
        if isinstance(node, dict):
            # If there's an explicit 'data' key, search it first
            if "data" in node:
                _walk(node["data"])
            # Check common link fields
            for k, v in node.items():
                if isinstance(v, (dict, list)):
                    _walk(v)
                elif isinstance(v, str):
                    if k.lower() in {"url", "href", "downloadlink", "file", "link"} or v.endswith(
                            ".zip") or ".zip" in v:
                        if ".zip" in v.lower():
                            found.add(v)
        elif isinstance(node, list):
            for item in node:
                _walk(item)

    _walk(obj)
    return found


def stream_download(url: str, out_dir: pathlib.Path, chunk_size: int, skip_existing: bool,
                    timeout: int) -> pathlib.Path:
    """Download a file with streaming and basic progress display."""
    out_dir.mkdir(parents=True, exist_ok=True)
    name = pathlib.Path(urllib.parse.urlparse(url).path).name or "download.zip"
    dest = out_dir / name

    if skip_existing and dest.exists():
        print(f"Skipping existing file: {dest}")
        return dest

    with requests.get(url, stream=True, timeout=timeout) as r:
        r.raise_for_status()
        total = int(r.headers.get("Content-Length", "0"))
        downloaded = 0
        with open(dest, "wb") as f:
            for part in r.iter_content(chunk_size=chunk_size):
                if not part:
                    continue
                f.write(part)
                downloaded += len(part)
                if total:
                    pct = downloaded * 100 // total
                    sys.stdout.write(f"\rDownloading {name} [{pct}%]")
                    sys.stdout.flush()
        if total:
            sys.stdout.write("\n")
    return dest


def main():
    if len(sys.argv) < 2 or not sys.argv[1].endswith('.json'):
        print("Usage: python collgs_download.py <config_file> [output_dir]")
        print("Example: python collgs_download.py config.json")

        # Create sample config file if it doesn't exist
        if not os.path.exists("sample_config.json"):
            load_config(None)  # This will create sample config and exit
        else:
            print("Sample config already exists: sample_config.json")

        sys.exit(1)

    config_path = sys.argv[1]
    config = load_config(config_path)

    # Build URL from config
    url = build_url_from_config(config)

    # Get output directory from command line or config
    out_dir = pathlib.Path(sys.argv[2]) if len(sys.argv) > 2 else pathlib.Path(
        config.get("output_directory", "downloads"))

    # Get connection settings
    connection = config.get("connection", {})
    timeout = connection.get("timeout", 120)
    retries = connection.get("retries", 3)
    user_agent = connection.get("user_agent", "eo-downloader/1.0")

    # Get download options
    download_options = config.get("download_options", {})
    chunk_size = download_options.get("chunk_size", 65536)
    skip_existing = download_options.get("skip_existing", True)

    headers = {"Accept": "application/json", "User-Agent": user_agent}
    print(f"Fetching JSON from: {url}")

    # Implement retries
    session = requests.Session()
    adapter = requests.adapters.HTTPAdapter(max_retries=retries)
    session.mount('http://', adapter)
    session.mount('https://', adapter)

    resp = session.get(url, headers=headers, timeout=timeout)
    resp.raise_for_status()

    try:
        payload = resp.json()
    except json.JSONDecodeError:
        print("The response is not valid JSON. Make sure the URL includes httpAccept=json.")
        sys.exit(2)

    candidates = find_zip_links(payload)
    if not candidates:
        print("No .zip links found in the JSON (including the 'data' section).")
        sys.exit(0)

    abs_urls = sorted({resolve_url(u) for u in candidates})
    print(f"Found {len(abs_urls)} ZIP file(s). Starting downloads to: {out_dir.resolve()}")
    for zurl in abs_urls:
        try:
            print(f"-> {zurl}")
            path = stream_download(zurl, out_dir, chunk_size, skip_existing, timeout)
            print(f"Saved: {path}")
        except Exception as e:
            print(f"Failed to download {zurl}: {e}")


if __name__ == "__main__":
    main()