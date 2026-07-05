import { render, screen } from '@testing-library/react';
import { describe, expect, it } from 'vitest';
import ElevatorCar from './ElevatorCar';
import type { FrameElevator, PassengerDefinition } from '../types';

function makeElevator(overrides: Partial<FrameElevator> = {}): FrameElevator {
  return {
    id: 1,
    floor: 2,
    direction: 'idle',
    phase: 'idle',
    passenger_count: 0,
    target_floor: null,
    ...overrides,
  };
}

function makePassenger(id: number, start: number, dest: number): PassengerDefinition {
  return { id, request_time: 0, start_floor: start, destination_floor: dest };
}

function renderCar(elevator: FrameElevator, passengers: PassengerDefinition[] = []) {
  return render(
    <ElevatorCar
      elevator={elevator}
      index={0}
      passengers={passengers}
      assignedElevatorById={new Map()}
      totalElevators={1}
      totalFloors={8}
    />,
  );
}

describe('ElevatorCar', () => {
  it('shows a neutral indicator while idle', () => {
    renderCar(makeElevator());

    expect(screen.getByTestId('RemoveIcon')).toBeInTheDocument();
    expect(screen.getByText('idle')).toBeInTheDocument();
  });

  it('shows an upward arrow with the target floor while moving up', () => {
    renderCar(makeElevator({ direction: 'up', phase: 'moving', target_floor: 6 }));

    expect(screen.getByTestId('PlayArrowIcon')).toBeInTheDocument();
    expect(screen.getByText('6')).toBeInTheDocument();
    expect(screen.getByText('moving')).toBeInTheDocument();
  });

  it('shows a downward arrow without a floor number when no stop is queued', () => {
    renderCar(makeElevator({ direction: 'down', phase: 'moving' }));

    expect(screen.getByTestId('PlayArrowIcon')).toBeInTheDocument();
    expect(screen.queryByText(/^\d+$/)).not.toBeInTheDocument();
  });

  it('labels riding passengers with their destinations', () => {
    renderCar(makeElevator({ phase: 'loading', passenger_count: 2 }), [
      makePassenger(1, 0, 5),
      makePassenger(2, 6, 1),
    ]);

    expect(screen.getByLabelText('#1 to 5 [-]')).toBeInTheDocument();
    expect(screen.getByLabelText('#2 to 1 [-]')).toBeInTheDocument();
    expect(screen.getByText('loading')).toBeInTheDocument();
  });
});
