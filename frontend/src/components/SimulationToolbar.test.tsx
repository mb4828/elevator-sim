import { fireEvent, render, screen } from '@testing-library/react';
import userEvent from '@testing-library/user-event';
import { beforeEach, describe, expect, it, vi } from 'vitest';
import SimulationToolbar from './SimulationToolbar';
import type { PlaybackRate } from '../hooks/usePlayback';

function makeHandlers() {
  return {
    onFileLoad: vi.fn(),
    onPause: vi.fn(),
    onPlay: vi.fn(),
    onStepBack: vi.fn(),
    onStepEnd: vi.fn(),
    onStepForward: vi.fn(),
    onStepStart: vi.fn(),
  };
}

function renderToolbar(
  handlers: ReturnType<typeof makeHandlers>,
  overrides: Partial<{ lastTick: number; loaded: boolean; loadedFileName: string; playbackRate: PlaybackRate; tick: number }> = {},
) {
  return render(
    <SimulationToolbar
      lastTick={overrides.lastTick ?? 10}
      loaded={overrides.loaded ?? true}
      loadedFileName={overrides.loadedFileName ?? ''}
      playbackRate={overrides.playbackRate ?? null}
      tick={overrides.tick ?? 5}
      {...handlers}
    />,
  );
}

describe('SimulationToolbar', () => {
  let handlers: ReturnType<typeof makeHandlers>;

  beforeEach(() => {
    handlers = makeHandlers();
  });

  it('disables every transport control before a simulation is loaded', () => {
    renderToolbar(handlers, { loaded: false, tick: 0 });

    const buttons = screen.getAllByRole('button');
    const loadButton = screen.getByRole('button', { name: /Load log.json/ });
    for (const button of buttons) {
      if (button !== loadButton) {
        expect(button).toBeDisabled();
      }
    }
  });

  it('shows the loaded file name on the load button', () => {
    renderToolbar(handlers, { loadedFileName: 'run42.json' });

    expect(screen.getByRole('button', { name: /Loaded run42.json/ })).toBeInTheDocument();
  });

  it('invokes playback callbacks from the transport buttons mid-timeline', async () => {
    const user = userEvent.setup();
    renderToolbar(handlers, { tick: 5 });

    await user.click(screen.getByRole('button', { name: 'Play (Space)' }));
    expect(handlers.onPlay).toHaveBeenCalledWith(1);

    await user.click(screen.getByRole('button', { name: 'Play 2x' }));
    expect(handlers.onPlay).toHaveBeenCalledWith(2);

    await user.click(screen.getByRole('button', { name: 'Step back (←)' }));
    expect(handlers.onStepBack).toHaveBeenCalledTimes(1);

    await user.click(screen.getByRole('button', { name: 'Step forward (→)' }));
    expect(handlers.onStepForward).toHaveBeenCalledTimes(1);

    await user.click(screen.getByRole('button', { name: 'Skip to start (Shift + ←)' }));
    expect(handlers.onStepStart).toHaveBeenCalledTimes(1);

    await user.click(screen.getByRole('button', { name: 'Skip to end (Shift + →)' }));
    expect(handlers.onStepEnd).toHaveBeenCalledTimes(1);
  });

  it('enables pause and disables 1x play while playing at 1x', async () => {
    const user = userEvent.setup();
    renderToolbar(handlers, { playbackRate: 1 });

    const pauseButton = screen.getByRole('button', { name: 'Pause (Space)' });
    expect(pauseButton).toBeEnabled();
    await user.click(pauseButton);
    expect(handlers.onPause).toHaveBeenCalledTimes(1);

    expect(screen.getByTestId('PlayArrowIcon').closest('button')).toBeDisabled();
    expect(screen.getByTestId('FastForwardIcon').closest('button')).toBeEnabled();
  });

  it('disables forward controls at the end of the timeline', () => {
    renderToolbar(handlers, { tick: 10, lastTick: 10 });

    expect(screen.getByTestId('PlayArrowIcon').closest('button')).toBeDisabled();
    expect(screen.getByTestId('FastForwardIcon').closest('button')).toBeDisabled();
    expect(screen.getByTestId('ChevronRightIcon').closest('button')).toBeDisabled();
    expect(screen.getByTestId('LastPageIcon').closest('button')).toBeDisabled();
    expect(screen.getByTestId('ChevronLeftIcon').closest('button')).toBeEnabled();
  });

  it('passes a chosen file to onFileLoad and clears the input', () => {
    const { container } = renderToolbar(handlers);
    const input = container.querySelector<HTMLInputElement>('input[type="file"]');
    expect(input).not.toBeNull();
    const file = new File(['{}'], 'log.json', { type: 'application/json' });

    fireEvent.change(input!, { target: { files: [file] } });

    expect(handlers.onFileLoad).toHaveBeenCalledWith(file);
    expect(input!.value).toBe('');
  });
});
