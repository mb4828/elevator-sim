import { render, screen } from '@testing-library/react';
import { describe, expect, it, vi } from 'vitest';
import ProgressChart from './ProgressChart';
import { parseSimulation } from '../logic';
import type { OutputFile } from '../logic';

interface ChartContainerStubProps {
  series?: Array<Record<string, unknown>>;
  yAxis?: Array<Record<string, unknown>>;
}

let lastContainerProps: ChartContainerStubProps | undefined;

vi.mock('@mui/x-charts/ResponsiveChartContainer', () => ({
  ResponsiveChartContainer: (props: ChartContainerStubProps) => {
    lastContainerProps = props;
    return <div data-testid="progress-chart" />;
  },
}));
vi.mock('@mui/x-charts/BarChart', () => ({ BarPlot: () => null }));
vi.mock('@mui/x-charts/LineChart', () => ({ LinePlot: () => null }));
vi.mock('@mui/x-charts/ChartsXAxis', () => ({ ChartsXAxis: () => null }));
vi.mock('@mui/x-charts/ChartsYAxis', () => ({ ChartsYAxis: () => null }));
vi.mock('@mui/x-charts/ChartsTooltip', () => ({ ChartsTooltip: () => null }));

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
    expect(screen.queryByTestId('progress-chart')).not.toBeInTheDocument();
  });

  it('charts one stacked row per requested passenger with wait and ride segments', () => {
    const sim = parseSimulation(sampleOutputFile());

    render(<ProgressChart sim={sim} tick={2} />);

    expect(screen.getByTestId('progress-chart')).toBeInTheDocument();
    expect(lastContainerProps?.yAxis?.[0]?.data).toEqual(['passenger1']);
    const seriesByLabel = Object.fromEntries(
      (lastContainerProps?.series ?? []).map((series) => [series.label ?? 'offset', series.data]),
    );
    expect(seriesByLabel.offset).toEqual([0]);
    expect(seriesByLabel.Waiting).toEqual([0]);
    expect(seriesByLabel.Riding).toEqual([2]);
  });

  it('includes later passengers once the timeline reaches their request', () => {
    const sim = parseSimulation(sampleOutputFile());

    render(<ProgressChart sim={sim} tick={4} />);

    expect(lastContainerProps?.yAxis?.[0]?.data).toEqual(['passenger1', 'passenger2']);
    expect(lastContainerProps?.series?.[0]?.data).toEqual([0, 3]);
  });

  it('overlays the waiting queue length as a line revealed up to the current tick', () => {
    const sim = parseSimulation(sampleOutputFile());

    render(<ProgressChart sim={sim} tick={2} />);

    const lineSeries = lastContainerProps?.series?.find((series) => series.type === 'line');
    expect(lineSeries).toMatchObject({ yAxisKey: 'queue' });
    expect(lineSeries?.data).toEqual([1, 0, 0, null, null]);
  });

  it('charts the full queue length history at the final tick', () => {
    const sim = parseSimulation(sampleOutputFile());

    render(<ProgressChart sim={sim} tick={4} />);

    const lineSeries = lastContainerProps?.series?.find((series) => series.type === 'line');
    expect(lineSeries?.data).toEqual([1, 0, 0, 1, 0]);
  });
});
