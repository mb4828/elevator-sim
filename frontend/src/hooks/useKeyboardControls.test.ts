import { fireEvent, renderHook } from "@testing-library/react";
import { beforeEach, describe, expect, it, vi } from "vitest";
import { useKeyboardControls } from "./useKeyboardControls";

function makeHandlers() {
  return {
    onStepStart: vi.fn(),
    onStepBack: vi.fn(),
    onStepForward: vi.fn(),
    onStepEnd: vi.fn(),
    onTogglePlay: vi.fn(),
  };
}

describe("useKeyboardControls", () => {
  let handlers: ReturnType<typeof makeHandlers>;

  beforeEach(() => {
    handlers = makeHandlers();
  });

  it("maps arrow keys to steps and shifted arrows to jumps", () => {
    renderHook(() => useKeyboardControls({ enabled: true, ...handlers }));

    fireEvent.keyDown(window, { key: "ArrowLeft" });
    expect(handlers.onStepBack).toHaveBeenCalledTimes(1);

    fireEvent.keyDown(window, { key: "ArrowRight" });
    expect(handlers.onStepForward).toHaveBeenCalledTimes(1);

    fireEvent.keyDown(window, { key: "ArrowLeft", shiftKey: true });
    expect(handlers.onStepStart).toHaveBeenCalledTimes(1);

    fireEvent.keyDown(window, { key: "ArrowRight", shiftKey: true });
    expect(handlers.onStepEnd).toHaveBeenCalledTimes(1);
  });

  it("maps the space bar to play/pause", () => {
    renderHook(() => useKeyboardControls({ enabled: true, ...handlers }));

    fireEvent.keyDown(window, { key: " " });

    expect(handlers.onTogglePlay).toHaveBeenCalledTimes(1);
  });

  it("ignores unrelated keys", () => {
    renderHook(() => useKeyboardControls({ enabled: true, ...handlers }));

    fireEvent.keyDown(window, { key: "a" });

    expect(handlers.onStepBack).not.toHaveBeenCalled();
    expect(handlers.onStepForward).not.toHaveBeenCalled();
    expect(handlers.onTogglePlay).not.toHaveBeenCalled();
  });

  it("does nothing while disabled", () => {
    renderHook(() => useKeyboardControls({ enabled: false, ...handlers }));

    fireEvent.keyDown(window, { key: "ArrowRight" });
    fireEvent.keyDown(window, { key: " " });

    expect(handlers.onStepForward).not.toHaveBeenCalled();
    expect(handlers.onTogglePlay).not.toHaveBeenCalled();
  });

  it("ignores key events from editable fields", () => {
    renderHook(() => useKeyboardControls({ enabled: true, ...handlers }));
    const input = document.createElement("input");
    document.body.appendChild(input);

    fireEvent.keyDown(input, { key: "ArrowRight" });

    expect(handlers.onStepForward).not.toHaveBeenCalled();
    input.remove();
  });
});
