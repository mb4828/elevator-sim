import { useCallback, useEffect, useState } from "react";

export type PlaybackRate = 1 | 2 | null;

export interface Playback {
  tick: number;
  playbackRate: PlaybackRate;
  play: (rate: 1 | 2) => void;
  pause: () => void;
  togglePlay: () => void;
  stepStart: () => void;
  stepBack: () => void;
  stepForward: () => void;
  stepEnd: () => void;
  reset: () => void;
}

/**
 * Owns the playback cursor (`tick`) and the auto-advance loop for a timeline of
 * `lastTick + 1` frames. Any manual step pauses playback so the two never fight
 * over the cursor. Pass `enabled: false` (e.g. before a simulation loads) to
 * keep the interval from running.
 */
export function usePlayback(lastTick: number, enabled: boolean): Playback {
  const [tick, setTick] = useState(0);
  const [playbackRate, setPlaybackRate] = useState<PlaybackRate>(null);

  const play = useCallback((rate: 1 | 2) => setPlaybackRate(rate), []);
  const pause = useCallback(() => setPlaybackRate(null), []);

  const stepStart = useCallback(() => {
    setPlaybackRate(null);
    setTick(0);
  }, []);

  const stepBack = useCallback(() => {
    setPlaybackRate(null);
    setTick((value) => Math.max(0, value - 1));
  }, []);

  const stepForward = useCallback(() => {
    setPlaybackRate(null);
    setTick((value) => Math.min(lastTick, value + 1));
  }, [lastTick]);

  const stepEnd = useCallback(() => {
    setPlaybackRate(null);
    setTick(lastTick);
  }, [lastTick]);

  const togglePlay = useCallback(() => {
    setPlaybackRate((value) => {
      if (value) return null;
      return tick < lastTick ? 1 : null;
    });
  }, [lastTick, tick]);

  const reset = useCallback(() => {
    setPlaybackRate(null);
    setTick(0);
  }, []);

  useEffect(() => {
    if (!enabled || !playbackRate) return undefined;

    const interval = window.setInterval(() => {
      setTick((value) => {
        const nextTick = Math.min(lastTick, value + 1);
        if (nextTick >= lastTick) {
          setPlaybackRate(null);
        }
        return nextTick;
      });
    }, 1000 / playbackRate);

    return () => window.clearInterval(interval);
  }, [enabled, lastTick, playbackRate]);

  return {
    tick,
    playbackRate,
    play,
    pause,
    togglePlay,
    stepStart,
    stepBack,
    stepForward,
    stepEnd,
    reset,
  };
}
