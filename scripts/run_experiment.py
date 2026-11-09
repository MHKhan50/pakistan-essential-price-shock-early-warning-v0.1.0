"""Run the chronological price-shock forecasting experiment."""
import argparse
import json
from pathlib import Path

from pakprice.experiment import run_experiment


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--input", type=Path, required=True, help="Canonical CSV created by scripts.prepare_data")
    parser.add_argument("--out", type=Path, default=Path("results/official_spi"))
    parser.add_argument("--shock-threshold", type=float, default=0.05, help="One-week price rise threshold, e.g. 0.05 for 5%%")
    parser.add_argument("--alpha", type=float, default=0.10, help="Conformal miscoverage level")
    parser.add_argument("--ridge-alpha", type=float, default=5.0)
    args = parser.parse_args()
    summary = run_experiment(args.input, args.out, args.shock_threshold, args.alpha, args.ridge_alpha)
    print(json.dumps(summary, indent=2, sort_keys=True))
    print("\nResults written to {}".format(args.out))


if __name__ == "__main__":
    main()
