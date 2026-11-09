"""Download the pinned OpenDoc Pakistan weekly PBS SPI city-item CSV."""
import argparse
import hashlib
import os
import tempfile
import urllib.request
from pathlib import Path

URL = "https://huggingface.co/datasets/opendoc-pakistan/pakistan_inflation_and_prices/resolve/54c5231/data/processed/weekly_spi_city_item_prices.csv"
EXPECTED_SHA256 = "010b8bf43458bc5751c933a4516cc3c9888457df4560ec5db2e635c842089f4b"


def fetch(output: Path) -> str:
    output.parent.mkdir(parents=True, exist_ok=True)
    request = urllib.request.Request(URL, headers={"User-Agent": "PakPriceSentinel/0.1.0 research-data-fetcher"})
    digest = hashlib.sha256()
    fd, temp_name = tempfile.mkstemp(prefix="pakprices-", suffix=".csv", dir=str(output.parent))
    os.close(fd)
    temp_path = Path(temp_name)
    try:
        with urllib.request.urlopen(request, timeout=90) as response, temp_path.open("wb") as target:
            while True:
                block = response.read(1024 * 1024)
                if not block:
                    break
                target.write(block)
                digest.update(block)
        actual = digest.hexdigest()
        if actual != EXPECTED_SHA256:
            raise ValueError("SHA-256 mismatch: expected {}, received {}. Do not use unverified data.".format(EXPECTED_SHA256, actual))
        temp_path.replace(output)
        return actual
    finally:
        if temp_path.exists():
            temp_path.unlink()


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--out", type=Path, default=Path("data/raw/weekly_spi_city_item_prices.csv"))
    args = parser.parse_args()
    checksum = fetch(args.out)
    print("Verified source file: {}".format(args.out))
    print("SHA-256: {}".format(checksum))


if __name__ == "__main__":
    main()
