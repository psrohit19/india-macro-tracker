"""
Daily refresh entry point.

  python3 pipeline/refresh.py            # run live fetchers, rebuild everything
  python3 pipeline/refresh.py --sample   # skip fetchers (offline rebuild)

Each fetcher writes data/live/{id}.json; generate_data.build() overlays live
observations onto the catalog (tiles flip SAMPLE -> LIVE automatically at
>= 14 observations). A failing fetcher never blocks the build — the series
keeps its last stored live data, or stays sample.
"""
import sys
import traceback
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent))
import generate_data


def run_fetchers():
    import fetchers.esankhyiki as esankhyiki      # CPI / CFPI / WPI / IIP (live)
    import fetchers.nsdl_fii as nsdl_fii          # FII daily (live, accumulating)
    import fetchers.fred as fred                  # global block (works outside sandbox)
    import fetchers.nse_dii as nse_dii            # DII daily (stub - anti-bot)
    import news
    for mod in (esankhyiki, nsdl_fii, fred, nse_dii, news):
        try:
            mod.fetch()
        except NotImplementedError:
            print(f"  [skip] {mod.__name__}: not wired yet")
        except Exception as e:
            print(f"  [fail] {mod.__name__}: {e!r} — keeping last good data")
            traceback.print_exc()


def main():
    if "--sample" not in sys.argv:
        run_fetchers()
    generate_data.build()
    import build_dashboard  # noqa: F401  (writes dashboard.html)
    import make_edition     # noqa: F401  (writes edition.html)
    import alerts
    alerts.deliver(alerts.evaluate())


if __name__ == "__main__":
    main()
