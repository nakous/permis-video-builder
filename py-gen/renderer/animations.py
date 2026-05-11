import math


def linear(t):
    return max(0.0, min(1.0, t))

def ease_out(t):
    t = max(0.0, min(1.0, t))
    return 1 - (1 - t) ** 2

def ease_in(t):
    t = max(0.0, min(1.0, t))
    return t * t

def ease_in_out(t):
    t = max(0.0, min(1.0, t))
    return t * t * (3 - 2 * t)

def ease_spring(t):
    """Slight overshoot then settle — good for pop-in elements."""
    t = max(0.0, min(1.0, t))
    c4 = (2 * math.pi) / 3
    if t == 0:
        return 0.0
    if t == 1:
        return 1.0
    return 2 ** (-10 * t) * math.sin((t * 10 - 0.75) * c4) + 1

def ease_out_cubic(t):
    t = max(0.0, min(1.0, t))
    return 1 - (1 - t) ** 3


def interpolate(from_val, to_val, elapsed, duration, easing=ease_out):
    """Return the interpolated value at `elapsed` seconds within `duration`."""
    if duration <= 0:
        return to_val
    progress = easing(elapsed / duration)
    if isinstance(from_val, (list, tuple)):
        return tuple(from_val[i] + (to_val[i] - from_val[i]) * progress
                     for i in range(len(from_val)))
    return from_val + (to_val - from_val) * progress


def lerp(a, b, t):
    """Simple linear interpolation."""
    return a + (b - a) * t
