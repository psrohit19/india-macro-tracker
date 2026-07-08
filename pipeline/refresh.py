"""
Refresh entry point — runs every 4 hours via GitHub Actions.

  python3 pipeline/refresh.py            # run ALL fetchers, rebuild everything
  python3 pipeline/refresh.py --sample   # skip fetchers (offline rebuild)

Every module in pipeline/fetchers/ that exposes fetch() is discovered and run,
newest data merging into data/live/*.json. A failing or stubbed fetcher never
blocks the build — its series keeps the last stored data (staleness stays
visible in the tile's period label and the freshness table).
"""
import importlib
import pkgutil
import sys
import time
import traceback
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent))
import generate_data


def run_fetchers():
    import fetchers
    import news
    mods = []
    for m in pkgutil.iter_modules(fetchers.__path__):
        try:
            mods.append(importlib.import_module(f"fetchers.{m.name}"))
        except Exception as e:
            print(f"  [import-fail] {m.name}: {e!r}")
    mods.append(news)
    for mod in mods:
        fn = getattr(mod, "fetch", None)
        if not callable(fn):
            continue
        t0 = time.time()
        try:
            fn()
            print(f"  [ok]   {mod.__name__} ({time.time() - t0:.0f}s)")
        except NotImplementedError:
            print(f"  [stub] {mod.__name__}")
        except Exception as e:
            print(f"  [fail] {mod.__name__}: {e!r} — keeping last good data")
            traceback.print_exc()


def main():
    if "--sample" not in sys.argv:
        run_fetchers()
    generate_data.build()
    import build_dashboard  # noqa: F401  (writes dashboard.html + index.html)
    import make_edition     # noqa: F401  (writes edition.html)
    import alerts
    alerts.deliver(alerts.evaluate())


if __name__ == "__main__":
    main()
