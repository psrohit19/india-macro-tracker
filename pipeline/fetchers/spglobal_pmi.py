"""S&P Global PMI fetcher (stub) — pmi_mfg, pmi_svc, global_pmi.

STATUS: not automated. The three PMI series in data/live/ are hand-seeded
from public S&P Global press releases and credible press coverage:

  * pmi_mfg    — HSBC India Manufacturing PMI, headline index (final print)
  * pmi_svc    — HSBC India Services PMI, Business Activity Index (final print)
  * global_pmi — J.P.Morgan Global Composite PMI, Output Index headline

Why there is no working fetch() here:

  * Free access is HEADLINE-ONLY. S&P Global publishes each month's headline
    number in a public press release (pmi.spglobal.com/Public/Release/
    PressReleases); the underlying time series and all sub-indices (new
    orders, employment, prices, etc.) are licensed products.
  * S&P Global PMI data is IP-RESTRICTED. Sub-index data requires a paid
    subscription, and redistribution is prohibited — any seeded values must
    remain internal to this dashboard and must not be republished.
  * Flash vs final: India and the global aggregates publish flash estimates
    that are later revised; only FINAL prints are seeded. The global
    composite is also occasionally restated by ~0.1pt in the following
    month's release — the seed uses each month's own press-release headline.

Future automation would scrape ONLY the press-release headline number
(one float per month per series) from the public press-release pages,
never the licensed dataset. Until then, update data/live/{pmi_mfg,pmi_svc,
global_pmi}.json by hand each month from the press releases.
"""


def fetch():
    """Not implemented — data is hand-seeded from press releases (see module docstring)."""
    raise NotImplementedError(
        "spglobal_pmi is hand-seeded; scrape press-release headlines only if automating."
    )
