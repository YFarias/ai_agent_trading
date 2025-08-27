# enum.py
from enum import Enum


class Timeframe(Enum):
    """Canonical timeframes for the project."""
    H4  = "4h"
    H8  = "8h"
    H12 = "12h"
    D1  = "1d"   # daily
    W1  = "1w"   # weekly
    M1  = "1M"   # monthly


class Pattern(Enum):
    # Pennants / Flags / High Tight
    PENNANT            = "pennant"             # 1 (neutral; mastro + short triangle)
    BULLISH_PENNANT    = "bullish_pennant"     # 2 (bullish)
    BEARISH_PENNANT    = "bearish_pennant"     # 3 (bearish)
    BULL_FLAG          = "bull_flag"           # 4 (bullish) 
    BEAR_FLAG          = "bear_flag"           # 5 (bearish) 
    HIGH_TIGHT_FLAG    = "high_tight_flag"     # 6 (neutral) 
    FLAGPOLE           = "flagpole"            # 7 (component/measurement) (bullish)

    # Triangles
    TRIANGLE           = "triangle"            # 8 (generic/neutral)
    ASC_TRIANGLE       = "ascending_triangle"  # 9 (tends to bullish)
    DESC_TRIANGLE      = "descending_triangle" # 10 (tends to bearish)
    SYM_TRIANGLE       = "sym_triangle"        # 11 (neutral)

    # Wedges
    WEDGE              = "wedge"               # 12 (generic/neutral)
    RISING_WEDGE       = "rising_wedge"        # 13 (tends to bearish)
    FALLING_WEDGE      = "falling_wedge"       # 14 (tends to bullish)

    # Diamonds
    DIAMOND            = "diamond"             # 15 (neutral)
    DIAMOND_TOP        = "diamond_top"         # 16 (bearish)
    DIAMOND_BOTTOM     = "diamond_bottom"      # 17 (bullish)

    # Broadening / Megaphone
    MEGAPHONE          = "megaphone"           # 18 (broadening formation)

    # Ranges / Retângulos
    RECTANGLE          = "rectangle"           # 19

    # Rounding
    ROUNDING_BOTTOM    = "rounding_bottom"     # 20 (saucer, bullish)
    ROUNDING_TOP       = "rounding_top"        # 21 (bearish)

    # Island Reversal / Dead Cat
    ISLAND_REVERSAL    = "island_reversal"     # 22
    DEAD_CAT_BOUNCE    = "dead_cat_bounce"     # 23

    # Measured Move / Bump & Run / Parabolic
    MEASURED_MOVE_UP   = "measured_move_up"    # 24 (continuation bullish)
    BUMP_AND_RUN       = "bump_and_run"        # 25 (reversal bearish)
    PARABOLIC_CURVE    = "parabolic_curve"     # 26

    # Canais
    RISING_CHANNEL     = "rising_channel"      # 27 (bullish)
    FALLING_CHANNEL    = "falling_channel"     # 28 (bearish)

    # Basic Reversals 
    DOUBLE_TOP_BOTTOM  = "double_top_bottom"     # 29 (reversal)
    HEAD_SHOULDERS     = "head_shoulders"        # 30 (reversal)
    TRIPLE_BOTTOM      = "triple_bottom"         # 31 (reversal)
    CUP_HANDLE         = "cup_handle"            # 32 (reversal)
    INVERTED_CUP_HANDLE= "inverted_cup_handle"   # 33 (reversal)


class SignalKind(Enum):
    """Nature of the signal that the pattern tends to generate."""
    CONTINUATION = "continuation"
    REVERSAL     = "reversal"
    BILATERAL    = "bilateral"  # depends on the breakout side


class TriggerType(Enum):
    """Trigger types (how the entry is confirmed)."""
    BREAK_ABOVE_BOUNDARY = "break_above_boundary"
    BREAK_BELOW_BOUNDARY = "break_below_boundary"
    GAP_CONFIRMATION     = "gap_confirmation"      # Island Reversal
    TRENDLINE_BREAK      = "trendline_break"       # Bump&Run, Parabolic
    LEG2_CONFIRMATION    = "leg2_confirmation"     # Measured Move Up


class StopMethod(Enum):
    """Technical stop methods."""
    OPPOSITE_BOUNDARY  = "opposite_boundary"       # opposite side of the pattern
    RECENT_EXTREME     = "recent_extreme"          # recent swing high/low
    BEYOND_GAP_EXTREME = "beyond_gap_extreme"      # Island Reversal
    BEYOND_TRENDLINE   = "beyond_trendline"        # after trendline break


class TargetMethod(Enum):
    """Target projection methods."""
    FLAGPOLE       = "flagpole"                    # flagpole projection
    PATTERN_HEIGHT = "pattern_height"              # pattern height (triangle/rectangle/diamond)
    WEDGE_HEIGHT   = "wedge_height"
    CHANNEL_WIDTH  = "channel_width"
    MEASURED_MOVE  = "measured_move"               # leg 2 ≈ leg 1
    PARABOLIC_BREAK= "parabolic_break"             # conservative target after parabolic break
    NONE           = "none"                        # when the element does not generate a direct target
