"""Sector and industry from SEC SIC codes (the desk has no GICS file; Silicon read one from another machine).

EDGAR's submissions document carries each registrant's SIC code and its description. The 11 sector funds (XLK ... XLU)
are the board's sector benchmarks, so a SIC code is mapped to the sector whose fund it belongs to by SIC range. This is
the desk's own approximation, declared on the board: SIC is an industrial classification of the 1930s-1980s and several
ranges split between sectors; a code the table does not place gives no sector (never a guess). The industry (the peer
group for the peer-rank and industry-strength leaves) is the 4-digit SIC itself, as SEC describes it."""

# (low, high, sector): the first range that holds the code wins, so the narrow ranges come first
RANGES = (
    (1311, 1389, "Energy"), (1200, 1299, "Energy"), (2911, 2999, "Energy"), (5171, 5172, "Energy"),
    (4610, 4619, "Energy"),
    (1000, 1199, "Materials"), (1400, 1499, "Materials"), (2800, 2819, "Materials"), (2820, 2832, "Materials"),
    (2860, 2899, "Materials"), (2400, 2499, "Materials"), (2600, 2699, "Materials"), (3200, 3299, "Materials"),
    (3300, 3399, "Materials"), (3080, 3099, "Materials"), (3081, 3089, "Materials"), (3411, 3411, "Materials"),
    (2833, 2836, "Health Care"), (3841, 3851, "Health Care"), (3826, 3826, "Health Care"), (3829, 3829, "Health Care"),
    (5047, 5047, "Health Care"), (5122, 5122, "Health Care"), (5912, 5912, "Consumer Staples"),
    (8000, 8099, "Health Care"), (8731, 8734, "Health Care"), (2830, 2831, "Health Care"),
    (2840, 2844, "Consumer Staples"), (100, 999, "Consumer Staples"), (2000, 2199, "Consumer Staples"),
    (5140, 5159, "Consumer Staples"), (5400, 5499, "Consumer Staples"),
    (3570, 3579, "Information Technology"), (3660, 3669, "Information Technology"),
    (3670, 3679, "Information Technology"), (3680, 3699, "Information Technology"),
    (3810, 3825, "Information Technology"), (7370, 7379, "Information Technology"),
    (3559, 3559, "Information Technology"), (3600, 3659, "Industrials"),
    (4800, 4899, "Communication Services"), (2700, 2799, "Communication Services"),
    (7810, 7829, "Communication Services"), (7840, 7841, "Communication Services"), (4830, 4841, "Communication Services"),
    (4900, 4991, "Utilities"),
    (6500, 6553, "Real Estate"), (6798, 6798, "Real Estate"), (6790, 6799, "Real Estate"),
    (6000, 6499, "Financials"), (6700, 6789, "Financials"), (6800, 6899, "Financials"),
    (1500, 1531, "Consumer Discretionary"), (2200, 2399, "Consumer Discretionary"), (2500, 2599, "Consumer Discretionary"),
    (3010, 3079, "Consumer Discretionary"), (3100, 3199, "Consumer Discretionary"), (3711, 3716, "Consumer Discretionary"),
    (3900, 3999, "Consumer Discretionary"), (5200, 5399, "Consumer Discretionary"),
    (5500, 5999, "Consumer Discretionary"), (7000, 7369, "Consumer Discretionary"), (7500, 7699, "Consumer Discretionary"),
    (7900, 7999, "Consumer Discretionary"), (8200, 8299, "Consumer Discretionary"), (3140, 3149, "Consumer Discretionary"),
    (1532, 1799, "Industrials"), (2900, 2910, "Energy"), (3400, 3599, "Industrials"), (3700, 3799, "Industrials"),
    (3800, 3809, "Industrials"), (3830, 3899, "Industrials"), (4000, 4799, "Industrials"), (5000, 5199, "Industrials"),
    (7380, 7499, "Industrials"), (8700, 8799, "Industrials"), (3600, 3699, "Industrials"),
)


def sector_of_sic(sic):
    """the sector (GICS name) of a SIC code, or None when no range places it"""
    try:
        code = int(sic)
    except (TypeError, ValueError):
        return None
    for lo, hi, name in RANGES:
        if lo <= code <= hi:
            return name
    return None


def classify(sic, sic_description=None):
    """-> {"sector","sub_industry"} for the board, or None without a sector. sub_industry is the SIC itself."""
    sec = sector_of_sic(sic)
    if not sec:
        return None
    return {"sector": sec, "sub_industry": f"SIC {int(sic)}" + (f" {sic_description}" if sic_description else "")}
