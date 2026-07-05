import { act, renderHook } from "@testing-library/react";
import { afterEach, beforeEach, describe, expect, it, vi } from "vitest";
import { usePlayback } from "./usePlayback";

describe("usePlayback", () => {
  beforeEach(() => {
    vi.useFakeTimers();
  });

  afterEach(() => {
    vi.useRealTimers();
  });

  it("starts paused at tick zero", () => {
    const { result } = renderHook(() => usePlayback(3, true));

    expect(result.current.tick).toBe(0);
    expect(result.current.playbackRate).toBeNull();
  });

  it("advances one tick per second at 1x and pauses at the end of the timeline", () => {
    const { result } = renderHook(() => usePlayback(2, true));

    act(() => result.current.play(1));
    act(() => vi.advanceTimersByTime(1000));
    expect(result.current.tick).toBe(1);
    expect(result.current.playbackRate).toBe(1);

    act(() => vi.advanceTimersByTime(1000));
    expect(result.current.tick).toBe(2);
    expect(result.current.playbackRate).toBeNull();

    act(() => vi.advanceTimersByTime(5000));
    expect(result.current.tick).toBe(2);
  });

  it("advances twice as fast at 2x", () => {
    const { result } = renderHook(() => usePlayback(10, true));

    act(() => result.current.play(2));
    act(() => vi.advanceTimersByTime(1000));

    expect(result.current.tick).toBe(2);
  });

  it("does not advance while disabled", () => {
    const { result } = renderHook(() => usePlayback(3, false));

    act(() => result.current.play(1));
    act(() => vi.advanceTimersByTime(3000));

    expect(result.current.tick).toBe(0);
  });

  it("clamps manual steps to the timeline and pauses playback", () => {
    const { result } = renderHook(() => usePlayback(2, true));

    act(() => result.current.stepBack());
    expect(result.current.tick).toBe(0);

    act(() => result.current.play(1));
    act(() => result.current.stepForward());
    expect(result.current.tick).toBe(1);
    expect(result.current.playbackRate).toBeNull();

    act(() => result.current.stepForward());
    act(() => result.current.stepForward());
    expect(result.current.tick).toBe(2);

    act(() => result.current.stepBack());
    expect(result.current.tick).toBe(1);
  });

  it("jumps to the start and end of the timeline", () => {
    const { result } = renderHook(() => usePlayback(5, true));

    act(() => result.current.stepEnd());
    expect(result.current.tick).toBe(5);

    act(() => result.current.stepStart());
    expect(result.current.tick).toBe(0);
  });

  it("toggles between playing at 1x and paused", () => {
    const { result } = renderHook(() => usePlayback(3, true));

    act(() => result.current.togglePlay());
    expect(result.current.playbackRate).toBe(1);

    act(() => result.current.togglePlay());
    expect(result.current.playbackRate).toBeNull();
  });

  it("does not start playing from the end of the timeline", () => {
    const { result } = renderHook(() => usePlayback(2, true));

    act(() => result.current.stepEnd());
    act(() => result.current.togglePlay());

    expect(result.current.playbackRate).toBeNull();
  });

  it("resets to a paused tick zero", () => {
    const { result } = renderHook(() => usePlayback(4, true));

    act(() => result.current.play(1));
    act(() => vi.advanceTimersByTime(2000));
    act(() => result.current.reset());

    expect(result.current.tick).toBe(0);
    expect(result.current.playbackRate).toBeNull();
  });
});
