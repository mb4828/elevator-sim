import { render, screen } from '@testing-library/react';
import { describe, expect, it, vi } from 'vitest';
import ProgressChart from './ProgressChart';
import { parseSimulation } from '../simulation';
import type { OutputFile } from '../types';

interface BarChartStubProps {
  dataset?: Array<Record<string, unknown>>;
}

let lastBarChartProps: BarChartStubProps | undefined;

vi.mock('@mui/x-charts/BarChart', () => ({
  BarChart: (props: BarChartStubProps) => {
    lastBarChartProps = props;
    return <div data-testid="bar-chart" />;
  },
}));

function sampleOutputFile(): OutputFile {
  return {
    floors: 4,
    elevators: [{ id: 1, capacity: 4 }],
    passengers: [
      { id: 1, full_id: 'passenger1', request_time: 0, start_floor: 0, destination_floor: 3 },
      { id: 2, full_id: 'passenger2', request_time: 3, start_floor: 1, destination_floor: 0 },
    ],
    frames: [
      { time: 0, complete: false, elevators: [], passengers: [{ id: 1, status: 'waiting', elevator_id: null }] },
      { time: 1, complete: false, elevators: [], passengers: [{ id: 1, status: 'riding', elevator_id: 1 }] },
      { time: 2, complete: false, elevators: [], passengers: [{ id: 1, status: 'riding', elevator_id: 1 }] },
      { time: 3, complete: false, elevators: [], passengers: [{ id: 2, status: 'waiting', elevator_id: null }] },
      { time: 4, complete: true, elevators: [], passengers: [] },
    ],
  };
}

describe('ProgressChart', () => {
  it('shows an empty message before any passenger has requested', () => {
    const sim = parseSimulation({ ...sampleOutputFile(), passengers: [], frames: [] });

    render(<ProgressChart sim={sim} tick={0} />);

    expect(screen.getByText('No passengers have entered yet.')).toBeInTheDocument();
    expect(screen.queryByTestId('bar-chart')).not.toBeInTheDocument();
  });

  it('charts one stacked row per requested passenger with wait and ride segments', () => {
    const sim = parseSimulation(sampleOutputFile());

    render(<ProgressChart sim={sim} tick={2} />);

    expect(screen.getByTestId('bar-chart')).toBeInTheDocument();
    expect(lastBarChartProps?.dataset).toHaveLength(1);
    expect(lastBarChartProps?.dataset?.[0]).toMatchObject({
      label: 'passenger1',
      offset: 0,
      waiting: 0,
      riding: 2,
    });
  });

  it('includes later passengers once the timeline reaches their request', () => {
    const sim = parseSimulation(sampleOutputFile());

    render(<ProgressChart sim={sim} tick={4} />);

    expect(lastBarChartProps?.dataset).toHaveLength(2);
    expect(lastBarChartProps?.dataset?.[1]).toMatchObject({ label: 'passenger2', offset: 3 });
  });
});
