"""Optional: dump the fake dataset to Parquet files for inspection.

Not required at runtime (the dev engine builds the data in-memory), but handy if
you want to eyeball the demo data or load it elsewhere.

    python -m dev_data.generate
    # -> writes dev_data/data/*.parquet
"""

from __future__ import annotations

from pathlib import Path

from dev_data.fake_data import build_frames

OUT_DIR = Path(__file__).resolve().parent / "data"


def main() -> None:
    OUT_DIR.mkdir(parents=True, exist_ok=True)
    frames = build_frames()
    for name, df in frames.items():
        path = OUT_DIR / f"{name}.parquet"
        df.to_parquet(path, index=False)
        print(f"  {name:<28} {len(df):>7,} rows -> {path.relative_to(OUT_DIR.parent.parent)}")
    print(f"\nDone. {len(frames)} tables written to {OUT_DIR}")


if __name__ == "__main__":
    main()
