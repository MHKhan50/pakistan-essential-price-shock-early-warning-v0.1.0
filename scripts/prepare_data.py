"""Validate and normalize the downloaded PBS-derived weekly city/item CSV."""
import argparse
from pathlib import Path

from pakprice.data import normalize_raw_csv


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--input", type=Path, required=True)
    parser.add_argument("--out", type=Path, required=True)
    args = parser.parse_args()
    count = normalize_raw_csv(args.input, args.out)
    print("Wrote {} clean city-item-week average-price observations to {}".format(count, args.out))


if __name__ == "__main__":
    main()
