import { Box, Paper, Stack, Typography, useTheme } from '@mui/material';
import { BarChart } from '@mui/x-charts/BarChart';
import type { LoadedSimulation } from '../logic';

interface Props {
  sim: LoadedSimulation;
  tick: number;
}

interface HistogramBin {
  label: string;
  count: number;
}

const MAX_BINS = 12;
const BIN_WIDTH_STEPS = [1, 2, 5, 10, 20, 50, 100, 200, 500];

/** Groups wait times into equal-width bins, choosing a width that keeps the bin count readable. */
export function buildHistogramBins(waitTimes: number[]): HistogramBin[] {
  if (waitTimes.length === 0) return [];

  const maxWait = Math.max(...waitTimes);
  // Fall back to one bin covering everything when even the widest step overflows MAX_BINS.
  const width = BIN_WIDTH_STEPS.find((candidate) => Math.ceil((maxWait + 1) / candidate) <= MAX_BINS) ?? maxWait + 1;
  const bins = Array.from({ length: Math.ceil((maxWait + 1) / width) }, (_, index) => ({
    label: width === 1 ? `${index}` : `${index * width}–${index * width + width - 1}`,
    count: 0,
  }));
  for (const waitTime of waitTimes) {
    const bin = bins[Math.floor(waitTime / width)];
    if (bin) bin.count += 1;
  }
  return bins;
}

export default function WaitTimeHistogram({ sim, tick }: Props) {
  const theme = useTheme();
  const waitTimes = Object.values(sim.journeys)
    .filter((journey) => journey.boardTime !== null && journey.boardTime <= tick && journey.waitTime !== null)
    .map((journey) => journey.waitTime as number);
  const bins = buildHistogramBins(waitTimes);

  return (
    <Paper variant="outlined" sx={{ minWidth: 0, p: { xs: 2, md: 3 } }}>
      <Stack spacing={2}>
        <Box>
          <Typography variant="h6" component="h2">
            Wait Time Distribution
          </Typography>
          <Typography variant="body2" color="text.secondary">
            Wait times of passengers boarded by the current tick
          </Typography>
        </Box>
        <Box sx={{ display: 'grid', height: 500, minWidth: 0, overflow: 'hidden', placeItems: 'center' }}>
          {bins.length > 0 ? (
            <BarChart
              height={500}
              margin={{ bottom: 48, left: 56, right: 24, top: 16 }}
              series={[{ color: theme.palette.warning.main, data: bins.map((bin) => bin.count), label: 'Passengers' }]}
              slotProps={{
                legend: { hidden: true },
              }}
              xAxis={[{ data: bins.map((bin) => bin.label), label: 'Wait time (ticks)', scaleType: 'band' }]}
              yAxis={[{ label: 'Passengers' }]}
            />
          ) : (
            <Typography color="text.secondary" variant="body2">
              No passengers have boarded yet.
            </Typography>
          )}
        </Box>
      </Stack>
    </Paper>
  );
}
