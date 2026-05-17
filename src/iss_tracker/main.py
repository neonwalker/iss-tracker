"""Entry point. Runs the async poller and the Rich Live render loop."""

from __future__ import annotations

import asyncio
import time

from rich.console import Console
from rich.live import Live

from .cli import Args, DemoSource, parse_args
from .iss_api import IssApi
from .theme import get_theme
from .tracker import ViewTracker
from .trail import Trail
from .ui import AppState, build_layout, stats_panel


VIEW_DAMPING = 0.15
TRAIL_MINUTES = 30
DAMPED_STEPS_PER_FRAME = 1


async def _poller(source, state: AppState, trail: Trail, tracker: ViewTracker,
                  poll_seconds: float, stop: asyncio.Event) -> None:
    while not stop.is_set():
        try:
            sample = await source.fetch()
        except Exception as exc:
            state.last_error = type(exc).__name__
        else:
            state.last_sample = sample
            state.last_sample_at = time.time()
            state.last_error = None
            trail.append(sample.lat, sample.lon, float(sample.timestamp))
            tracker.set_target(sample.lat, sample.lon)
        try:
            await asyncio.wait_for(stop.wait(), timeout=poll_seconds)
        except asyncio.TimeoutError:
            pass


async def _render_loop(args: Args, source, console: Console) -> None:
    theme = get_theme(args.theme)
    trail_capacity = int(TRAIL_MINUTES * 60 / args.poll)
    trail = Trail(capacity=trail_capacity)
    tracker = ViewTracker(damping=VIEW_DAMPING)
    state = AppState()

    stop = asyncio.Event()
    poll_task = asyncio.create_task(
        _poller(source, state, trail, tracker, args.poll, stop)
    )

    frame_interval = 1.0 / args.fps
    layout = build_layout(tracker=tracker, trail=trail, theme=theme, state=state)
    try:
        with Live(layout, console=console, screen=True,
                  refresh_per_second=args.fps) as live:
            while True:
                for _ in range(DAMPED_STEPS_PER_FRAME):
                    tracker.step()
                layout["stats"].update(stats_panel(state, theme))
                live.refresh()
                await asyncio.sleep(frame_interval)
    except (KeyboardInterrupt, asyncio.CancelledError):
        pass
    finally:
        stop.set()
        await poll_task


def main() -> None:
    args = parse_args()
    console = Console()
    source = DemoSource() if args.demo else IssApi()
    try:
        asyncio.run(_render_loop(args, source, console))
    except KeyboardInterrupt:
        pass


if __name__ == "__main__":
    main()
