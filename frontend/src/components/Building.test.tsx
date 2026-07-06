import { act, render, screen } from '@testing-library/react';
import { afterEach, beforeEach, describe, expect, it, vi } from 'vitest';
import Building from './Building';
import type { FrameElevator, LoadedFrame, LoadedSimulation } from '../logic';

function sampleSim(): LoadedSimulation {
  return {
    floors: 8,
    elevators: [{ id: 1, capacity: 4 }],
    passengers: [{ id: 1, full_id: 'passenger1', request_time: 0, start_floor: 2, destination_floor: 5 }],
    frames: [],
    journeys: {},
    peakQueueByTick: [],
  };
}

const idleElevator: FrameElevator = {
  id: 1,
  floor: 0,
  direction: 'idle',
  phase: 'moving',
  passenger_count: 0,
  target_floor: null,
};

function frameWithWaitingPassenger(): LoadedFrame {
  return {
    time: 5,
    complete: false,
    elevators: [idleElevator],
    passengers: [{ id: 1, status: 'waiting', elevator_id: null }],
  };
}

function emptyFrame(): LoadedFrame {
  return { time: 0, complete: false, elevators: [idleElevator], passengers: [] };
}

describe('Building', () => {
  it('renders one row per floor', () => {
    render(<Building frame={emptyFrame()} sim={sampleSim()} />);

    for (let floor = 0; floor < 8; floor += 1) {
      expect(screen.getByText(`F${floor}`)).toBeInTheDocument();
    }
  });

  it("shows a waiting passenger's full ID in its accessible label", () => {
    render(<Building frame={frameWithWaitingPassenger()} sim={sampleSim()} />);

    expect(screen.getByLabelText('passenger1 [-]')).toBeInTheDocument();
  });

  it('renders riding passengers inside their elevator and skips unknown IDs', () => {
    const frame: LoadedFrame = {
      time: 1,
      complete: false,
      elevators: [{ ...idleElevator, passenger_count: 1 }],
      passengers: [
        { id: 1, status: 'riding', elevator_id: 1 },
        { id: 99, status: 'riding', elevator_id: 1 },
      ],
    };

    render(<Building frame={frame} sim={sampleSim()} />);

    expect(screen.getByLabelText('passenger1 [1]')).toBeInTheDocument();
    expect(screen.queryByLabelText(/^#99/)).not.toBeInTheDocument();
  });

  describe('jumping back to the start of the timeline', () => {
    beforeEach(() => {
      vi.useFakeTimers();
    });

    afterEach(() => {
      vi.useRealTimers();
    });

    it("keeps the full ID label while a waiting passenger's icon exits, instead of dropping it", () => {
      const sim = sampleSim();
      const { rerender } = render(<Building frame={frameWithWaitingPassenger()} sim={sim} />);
      expect(screen.getByLabelText('passenger1 [-]')).toBeInTheDocument();

      // Simulate the "back to start" control jumping straight to a frame where
      // nobody is waiting yet, rather than stepping through incrementally.
      act(() => {
        rerender(<Building frame={emptyFrame()} sim={sim} />);
      });

      // Mid exit-animation, the icon must still resolve full passenger data
      // instead of falling back to a bare "#1" label.
      expect(screen.getByLabelText('passenger1 [-]')).toBeInTheDocument();

      act(() => {
        vi.advanceTimersByTime(200);
      });

      expect(screen.queryByLabelText(/^#1/)).not.toBeInTheDocument();
    });
  });
});
