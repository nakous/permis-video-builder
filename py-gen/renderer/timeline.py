"""
Timeline — declarative animation engine.

A Timeline collects named tweens. Each tween animates a value from `start_val`
to `end_val` over a specific time window. Calling `eval()` returns a dict of
the current value of each named property at the current `t`.

Usage (typical scene):

    from renderer.timeline import Timeline
    from renderer.animations import ease_out_back, ease_out

    tl = Timeline(t)
    tl.add("logo_scale", 0.0, 1.0,  start=0.0,  dur=0.55, ease=ease_out_back)
    tl.add("name_alpha", 0.0, 1.0,  start=0.40, dur=0.45)
    tl.add("name_y",     30,  0,    start=0.40, dur=0.45, ease=ease_out)
    s = tl.eval()
    # → s["logo_scale"] in [0..1.05] depending on t

Helpers:
    .add_seq(name, keyframes)   chain of tweens [(val, time), ...]
    .stagger(name_prefix, n, ...) batch of N tweens with stagger_delay
    .pulse(name, period, amp)   continuous sinusoidal (no start/end)
    .breath(name, period, lo, hi)
"""
import math
from renderer.animations import (
    linear, ease_out, ease_in, ease_in_out, ease_out_cubic, ease_out_back,
    ease_out_elastic, ease_out_bounce, ease_spring, pulse as pulse_fn,
    breath as breath_fn,
)


class Tween:
    __slots__ = ("name", "from_val", "to_val", "start", "dur", "ease", "_kind")

    def __init__(self, name, from_val, to_val, start, dur, ease):
        self.name     = name
        self.from_val = from_val
        self.to_val   = to_val
        self.start    = start
        self.dur      = dur
        self.ease     = ease
        self._kind    = "tween"

    def value_at(self, t):
        if self.dur <= 0:
            return self.to_val if t >= self.start else self.from_val
        elapsed = t - self.start
        if elapsed <= 0:
            return self.from_val
        if elapsed >= self.dur:
            return self.to_val
        progress = self.ease(elapsed / self.dur)
        if isinstance(self.from_val, (list, tuple)):
            return tuple(self.from_val[i] + (self.to_val[i] - self.from_val[i]) * progress
                         for i in range(len(self.from_val)))
        return self.from_val + (self.to_val - self.from_val) * progress


class _Pulse:
    __slots__ = ("name", "period", "amp", "base", "start")

    def __init__(self, name, period, amp, base, start):
        self.name   = name
        self.period = period
        self.amp    = amp
        self.base   = base
        self.start  = start

    def value_at(self, t):
        if t < self.start:
            return self.base
        return pulse_fn(t - self.start, period=self.period,
                        amplitude=self.amp, base=self.base)


class _Breath:
    __slots__ = ("name", "period", "lo", "hi", "start")

    def __init__(self, name, period, lo, hi, start):
        self.name   = name
        self.period = period
        self.lo     = lo
        self.hi     = hi
        self.start  = start

    def value_at(self, t):
        if t < self.start:
            return self.lo
        return breath_fn(t - self.start, period=self.period, low=self.lo, high=self.hi)


class Timeline:
    """
    Collects tweens and evaluates them at a given time `t`.
    Multiple tweens with the same name → the LAST one to start (and which has
    actually started by t) wins. This lets you chain tweens cleanly:

        tl.add("scale", 0, 1.2, start=0,   dur=0.3, ease=ease_out_back)
        tl.add("scale", 1.2, 1, start=0.3, dur=0.2, ease=ease_out)
    """

    def __init__(self, t):
        self.t = t
        self._tweens = []

    # ── basic add ───────────────────────────────────────────────────────────
    def add(self, name, from_val, to_val, start=0.0, dur=0.4, ease=ease_out):
        self._tweens.append(Tween(name, from_val, to_val, start, dur, ease))
        return self

    # ── continuous loops ────────────────────────────────────────────────────
    def pulse(self, name, period=1.5, amp=0.05, base=1.0, start=0.0):
        self._tweens.append(_Pulse(name, period, amp, base, start))
        return self

    def breath(self, name, period=2.0, lo=0.92, hi=1.0, start=0.0):
        self._tweens.append(_Breath(name, period, lo, hi, start))
        return self

    # ── chained keyframes ──────────────────────────────────────────────────
    def keyframes(self, name, frames, ease=ease_out):
        """
        frames = [(value, time), ...] sorted by time.
        Builds N-1 tweens that interpolate between consecutive frames.
        """
        for i in range(len(frames) - 1):
            v0, t0 = frames[i]
            v1, t1 = frames[i + 1]
            dur    = max(0.0001, t1 - t0)
            self._tweens.append(Tween(name, v0, v1, t0, dur, ease))
        return self

    # ── stagger : N tweens with same params + delay ─────────────────────────
    def stagger(self, name_prefix, n, from_val, to_val,
                start=0.0, dur=0.4, item_stagger=0.1, ease=ease_out):
        for i in range(n):
            self.add(f"{name_prefix}_{i}", from_val, to_val,
                     start=start + i * item_stagger, dur=dur, ease=ease)
        return self

    # ── evaluate ────────────────────────────────────────────────────────────
    def eval(self):
        """Return dict of current values, with later tweens overriding earlier."""
        state = {}
        # Tweens stored in insertion order. For a given name, prefer the latest
        # one that has at least started (start <= t). This lets keyframes chain.
        latest_started = {}
        latest_pending = {}
        for tw in self._tweens:
            if self.t >= tw.start:
                latest_started[tw.name] = tw
            else:
                # Keep the earliest pending so we read its from_val
                if tw.name not in latest_pending:
                    latest_pending[tw.name] = tw
        for name, tw in latest_pending.items():
            if name not in latest_started:
                state[name] = tw.value_at(self.t)
        for name, tw in latest_started.items():
            state[name] = tw.value_at(self.t)
        return state

    def get(self, name, default=None):
        """Evaluate just one tween. Convenience for one-off lookups."""
        result = default
        for tw in self._tweens:
            if tw.name != name:
                continue
            if self.t >= tw.start:
                result = tw.value_at(self.t)
            elif result is default:
                result = tw.value_at(self.t)   # returns from_val
        return result
