import { fireEvent, render, screen } from '@testing-library/react';
import { describe, expect, it, vi } from 'vitest';
import App from './App';
import type { OutputFile } from './logic';

vi.mock('@mui/x-charts/BarChart', () => ({
  BarChart: () => <div data-testid="bar-chart" />,
}));

function validOutputFile(): OutputFile {
  return {
    version: 1,
    floors: 2,
    elevators: [{ id: 1, capacity: 2 }],
    passengers: [{ id: 1, full_id: 'passenger1', request_time: 0, start_floor: 0, destination_floor: 1 }],
    frames: [
      {
        time: 0,
        complete: false,
        elevators: [
          { id: 1, floor: 0, direction: 'idle', phase: 'idle', passenger_count: 0, target_floor: null },
        ],
        passengers: [{ id: 1, status: 'waiting', elevator_id: null }],
      },
      {
        time: 1,
        complete: true,
        elevators: [
          { id: 1, floor: 1, direction: 'idle', phase: 'idle', passenger_count: 0, target_floor: null },
        ],
        passengers: [],
      },
    ],
  };
}

function loadFile(contents: string, name = 'log.json') {
  const input = document.querySelector<HTMLInputElement>('input[type="file"]');
  expect(input).not.toBeNull();
  fireEvent.change(input!, { target: { files: [new File([contents], name, { type: 'application/json' })] } });
}

describe('App', () => {
  it('renders the load placeholder before a simulation is loaded', () => {
    render(<App />);

    expect(screen.getByText('Load a simulation output JSON file')).toBeInTheDocument();
  });

  it('renders the simulation views after loading a valid file', async () => {
    render(<App />);

    loadFile(JSON.stringify(validOutputFile()), 'run.json');

    expect(await screen.findByText('Simulation')).toBeInTheDocument();
    expect(screen.getByText('Live Stats')).toBeInTheDocument();
    expect(screen.getByText('Passenger Progress')).toBeInTheDocument();
    expect(screen.getByRole('button', { name: /Loaded run.json/ })).toBeInTheDocument();
  });

  it('shows a parse error without a loaded simulation', async () => {
    render(<App />);

    loadFile('{"floors": 4}');

    expect(
      await screen.findByText('Expected a simulation file with valid passengers and frames arrays.'),
    ).toBeInTheDocument();
  });

  it('keeps showing the current simulation and surfaces the error when a later load fails', async () => {
    render(<App />);
    loadFile(JSON.stringify(validOutputFile()));
    await screen.findByText('Simulation');

    loadFile('not json at all');

    expect(await screen.findByRole('alert')).toBeInTheDocument();
    expect(screen.getByText('Simulation')).toBeInTheDocument();
  });
});
