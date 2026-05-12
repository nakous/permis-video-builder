"""
Animation primitives — easings + interpolation + stagger helpers.

Easings return a value in roughly [0, 1] for an input in [0, 1] (some overshoot
slightly above 1 — that is intentional for spring/back/bounce).
"""
import math


# ─────────────────────────── basic easings ──────────────────────────────────

def linear(t):
    return _clamp01(t)

def ease_in(t):
    t = _clamp01(t)
    return t * t

def ease_out(t):
    t = _clamp01(t)
    return 1 - (1 - t) ** 2

def ease_in_out(t):
    t = _clamp01(t)
    return t * t * (3 - 2 * t)

def ease_out_cubic(t):
    t = _clamp01(t)
    return 1 - (1 - t) ** 3

def ease_in_out_cubic(t):
    t = _clamp01(t)
    if t < 0.5:
        return 4 * t * t * t
    return 1 - ((-2 * t + 2) ** 3) / 2

def ease_out_quint(t):
    t = _clamp01(t)
    return 1 - (1 - t) ** 5


# ─────────────────────────── overshoot / spring ─────────────────────────────

def ease_spring(t):
    """Slight elastic overshoot then settle. Good for pop-in elements."""
    t = _clamp01(t)
    if t in (0.0, 1.0):
        return t
    c4 = (2 * math.pi) / 3
    return 2 ** (-10 * t) * math.sin((t * 10 - 0.75) * c4) + 1


def ease_out_back(t, overshoot=1.70158):
    """Slight overshoot — modern UI feel. overshoot=1.7 is the standard value."""
    t = _clamp01(t)
    c1 = overshoot
    c3 = c1 + 1
    return 1 + c3 * (t - 1) ** 3 + c1 * (t - 1) ** 2


def ease_out_elastic(t):
    """Stronger spring than ease_spring — pronounced bounce-back."""
    t = _clamp01(t)
    if t in (0.0, 1.0):
        return t
    c4 = (2 * math.pi) / 3
    return 2 ** (-10 * t) * math.sin((t * 10 - 0.75) * c4) + 1


def ease_out_bounce(t):
    """Multiple decreasing bounces — playful, like a falling ball."""
    t = _clamp01(t)
    n1, d1 = 7.5625, 2.75
    if t < 1 / d1:
        return n1 * t * t
    if t < 2 / d1:
        t -= 1.5 / d1
        return n1 * t * t + 0.75
    if t < 2.5 / d1:
        t -= 2.25 / d1
        return n1 * t * t + 0.9375
    t -= 2.625 / d1
    return n1 * t * t + 0.984375


# ─────────────────────────── interpolation ──────────────────────────────────

def interpolate(from_val, to_val, elapsed, duration, easing=ease_out):
    """Return interpolated value at `elapsed` seconds within `duration`."""
    if duration <= 0:
        return to_val
    progress = easing(elapsed / duration)
    if isinstance(from_val, (list, tuple)):
        return tuple(from_val[i] + (to_val[i] - from_val[i]) * progress
                     for i in range(len(from_val)))
    return from_val + (to_val - from_val) * progress


def lerp(a, b, t):
    return a + (b - a) * t


def lerp_color(c1, c2, t):
    """Linearly interpolate between two RGB(A) tuples."""
    t = _clamp01(t)
    return tuple(int(c1[i] + (c2[i] - c1[i]) * t) for i in range(len(c1)))


# ─────────────────────────── stagger / sequencing ───────────────────────────

def stagger_progress(t, index, base_delay, item_stagger, duration, easing=ease_out):
    """
    Return the eased progress (0..1) for an item that starts at
    base_delay + index * item_stagger and takes `duration` seconds.
    """
    elapsed = t - base_delay - index * item_stagger
    if elapsed <= 0:
        return 0.0
    return easing(min(1.0, elapsed / duration))


def char_stagger_progress(t, char_index, base_delay, char_stagger, duration, easing=ease_out):
    """Same as stagger_progress but named for kinetic typography (per-char)."""
    return stagger_progress(t, char_index, base_delay, char_stagger, duration, easing)


# ─────────────────────────── continuous loops ───────────────────────────────

def pulse(t, period=1.5, amplitude=0.05, base=1.0):
    """Smooth sine pulse — useful for breathing scale/opacity."""
    return base + amplitude * math.sin(2 * math.pi * t / period)


def shake(t, duration, amplitude=12, frequency=22):
    """
    Decaying screen-shake offset. Returns (dx, dy).
    `duration`: shake lifetime in seconds.
    """
    if t >= duration or duration <= 0:
        return 0, 0
    decay = (1 - t / duration) ** 2
    a = amplitude * decay
    dx = a * math.sin(2 * math.pi * frequency * t)
    dy = a * math.cos(2 * math.pi * frequency * t * 0.85 + 1.3)
    return int(dx), int(dy)


def breath(t, period=2.0, low=0.92, high=1.0):
    """Soft breath cycle for opacity/glow — between low and high."""
    s = (math.sin(2 * math.pi * t / period) + 1) / 2  # 0..1
    return low + (high - low) * s


# ─────────────────────────── helpers ────────────────────────────────────────

def _clamp01(t):
    return max(0.0, min(1.0, t))
