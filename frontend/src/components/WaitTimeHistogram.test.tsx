import { render, screen } from '@testing-library/react';
import { describe, expect, it, vi } from 'vitest';
import WaitTimeHistogram, { buildHistogramBins } from './WaitTimeHistogram';
import { parseSimulation } from '../logic';
import type { OutputFile } from '../logic';

interface BarChartStubProps {
  series?: Array<Record<string, unknown>>;
  xAxis?: Array<Record<string, unknown>>;
}

let lastBarChartProps: BarChartStubProps | undefined;

vi.mock('@mui/x-charts/BarChart', () => ({
  BarChart: (props: BarChartStubProps) => {
    lastBarChartProps = props;
    return <div data-testid="wait-histogram" />;
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
      { time: 4, complete: false, elevators: [], passengers: [{ id: 2, status: 'waiting', elevator_id: null }] },
      { time: 5, complete: false, elevators: [], passengers: [{ id: 2, status: 'riding', elevator_id: 1 }] },
      { time: 6, complete: true, elevators: [], passengers: [] },
    ],
  };
}

describe('WaitTimeHistogram', () => {
  it('shows an empty message before any passenger has boarded', () => {
    const sim = parseSimulation({ ...sampleOutputFile(), passengers: [], frames: [] });

    render(<WaitTimeHistogram sim={sim} tick={0} />);

    expect(screen.getByText('No passengers have boarded yet.')).toBeInTheDocument();
    expect(screen.queryByTestId('wait-histogram')).not.toBeInTheDocument();
  });

  it('bins the wait times of passengers boarded by the current tick', () => {
    const sim = parseSimulation(sampleOutputFile());

    render(<WaitTimeHistogram sim={sim} tick={6} />);

    expect(screen.getByTestId('wait-histogram')).toBeInTheDocument();
    expect(lastBarChartProps?.xAxis?.[0]?.data).toEqual(['0', '1']);
    expect(lastBarChartProps?.series?.[0]?.data).toEqual([1, 1]);
  });

  it('excludes passengers who have not boarded yet at the current tick', () => {
    const sim = parseSimulation(sampleOutputFile());

    render(<WaitTimeHistogram sim={sim} tick={2} />);

    expect(lastBarChartProps?.xAxis?.[0]?.data).toEqual(['0']);
    expect(lastBarChartProps?.series?.[0]?.data).toEqual([1]);
  });
});

describe('buildHistogramBins', () => {
  it('returns no bins for an empty list', () => {
    expect(buildHistogramBins([])).toEqual([]);
  });

  it('uses single-tick bins for small ranges', () => {
    expect(buildHistogramBins([0, 2, 2])).toEqual([
      { label: '0', count: 1 },
      { label: '1', count: 0 },
      { label: '2', count: 2 },
    ]);
  });

  it('widens bins to keep the bin count readable', () => {
    const bins = buildHistogramBins([0, 3, 17]);

    expect(bins).toHaveLength(9);
    expect(bins[0]).toEqual({ label: '0–1', count: 1 });
    expect(bins[1]).toEqual({ label: '2–3', count: 1 });
    expect(bins[8]).toEqual({ label: '16–17', count: 1 });
  });
});
