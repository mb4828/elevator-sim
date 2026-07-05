import { render, screen } from '@testing-library/react';
import { describe, expect, it } from 'vitest';
import StatsPanel from './StatsPanel';
import type { Stats } from '../types';

const stats: Stats = {
  tick: 7,
  transported: 3,
  riding: 2,
  waiting: 4,
  peakQueue: 6,
  waitSummary: '1.00/2.00/3.00',
  totalSummary: '4.00/5.00/6.00',
};

describe('StatsPanel', () => {
  it('renders every stat row with its value', () => {
    render(<StatsPanel lastTick={20} stats={stats} />);

    expect(screen.getByText('Tick')).toBeInTheDocument();
    expect(screen.getByText('7 / 20')).toBeInTheDocument();
    expect(screen.getByText('Waiting')).toBeInTheDocument();
    expect(screen.getByText('4')).toBeInTheDocument();
    expect(screen.getByText('Riding')).toBeInTheDocument();
    expect(screen.getByText('2')).toBeInTheDocument();
    expect(screen.getByText('Complete')).toBeInTheDocument();
    expect(screen.getByText('3')).toBeInTheDocument();
    expect(screen.getByText('Peak queue')).toBeInTheDocument();
    expect(screen.getByText('6')).toBeInTheDocument();
    expect(screen.getByText('Wait min/avg/max')).toBeInTheDocument();
    expect(screen.getByText('1.00/2.00/3.00')).toBeInTheDocument();
    expect(screen.getByText('Total min/avg/max')).toBeInTheDocument();
    expect(screen.getByText('4.00/5.00/6.00')).toBeInTheDocument();
  });
});
