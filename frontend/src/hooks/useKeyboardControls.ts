import { useEffect } from "react";

export interface KeyboardControls {
  enabled: boolean;
  onStepStart: () => void;
  onStepBack: () => void;
  onStepForward: () => void;
  onStepEnd: () => void;
  onTogglePlay: () => void;
}

/**
 * Binds transport-style keyboard shortcuts to the playback controls:
 *   ←  / →         step back / forward
 *   Shift + ← / →  skip to start / end
 *   Space          toggle play / pause
 *
 * Ignores key events originating from editable fields so typing elsewhere on
 * the page never scrubs the timeline.
 */
export function useKeyboardControls({
  enabled,
  onStepStart,
  onStepBack,
  onStepForward,
  onStepEnd,
  onTogglePlay,
}: KeyboardControls): void {
  useEffect(() => {
    if (!enabled) return undefined;

    const handleKeyDown = (event: KeyboardEvent) => {
      if (isEditableTarget(event.target)) return;

      if (event.key === "ArrowLeft") {
        event.preventDefault();
        if (event.shiftKey) onStepStart();
        else onStepBack();
        return;
      }

      if (event.key === "ArrowRight") {
        event.preventDefault();
        if (event.shiftKey) onStepEnd();
        else onStepForward();
        return;
      }

      if (event.key === " ") {
        event.preventDefault();
        onTogglePlay();
      }
    };

    window.addEventListener("keydown", handleKeyDown);
    return () => window.removeEventListener("keydown", handleKeyDown);
  }, [enabled, onStepStart, onStepBack, onStepForward, onStepEnd, onTogglePlay]);
}

function isEditableTarget(target: EventTarget | null): boolean {
  if (!(target instanceof HTMLElement)) return false;
  const tagName = target.tagName.toLowerCase();
  return tagName === "input" || tagName === "textarea" || tagName === "select" || target.isContentEditable;
}
