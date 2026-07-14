import { Box, Chip, Paper, Stack, Typography, useTheme } from '@mui/material';
import { BarPlot } from '@mui/x-charts/BarChart';
import { ChartsTooltip } from '@mui/x-charts/ChartsTooltip';
import { ChartsXAxis } from '@mui/x-charts/ChartsXAxis';
import { ChartsYAxis } from '@mui/x-charts/ChartsYAxis';
import { LinePlot } from '@mui/x-charts/LineChart';
import { ResponsiveChartContainer } from '@mui/x-charts/ResponsiveChartContainer';
import type { LoadedSimulation } from '../logic';

interface Props {
  sim: LoadedSimulation;
  tick: number;
}

export default function ProgressChart({ sim, tick }: Props) {
  const theme = useTheme();
  const total = Math.max(1, sim.frames.length);
  const journeys = Object.values(sim.journeys)
    .filter((journey) => journey.requestTime <= tick)
    .sort((left, right) => left.id - right.id);
  const chartRows = journeys.map((journey) => {
    const waitEnd = Math.min(journey.boardTime ?? tick, tick);
    const rideEnd = Math.min(journey.completeTime ?? tick, tick);

    return {
      complete: journey.completeTime !== null && tick >= journey.completeTime ? 2 : 0,
      label: journey.fullId,
      offset: journey.requestTime,
      riding: journey.boardTime !== null && tick >= journey.boardTime ? Math.max(0, rideEnd - journey.boardTime) : 0,
      waiting: tick >= journey.requestTime ? Math.max(0, waitEnd - journey.requestTime) : 0,
    };
  });
  // Revealed only up to the current tick so the line grows with playback.
  const queueByTick = sim.frames.map((frame, index) =>
    index <= tick ? frame.passengers.filter((passenger) => passenger.status === 'waiting').length : null,
  );
  const peakQueue = Math.max(1, ...sim.peakQueueByTick.slice(-1));

  return (
    <Paper variant="outlined" sx={{ minWidth: 0, p: { xs: 2, md: 3 } }}>
      <Stack spacing={2}>
        <Stack
          direction={{ xs: 'column', sm: 'row' }}
          justifyContent="space-between"
          alignItems={{ xs: 'flex-start', sm: 'center' }}
          spacing={1.5}
        >
          <Box>
            <Typography variant="h6" component="h2">
              Passenger Progress
            </Typography>
            <Typography variant="body2" color="text.secondary">
              Request, ride, and completion timeline
            </Typography>
          </Box>
          <Stack direction="row" spacing={1} flexWrap="wrap" useFlexGap>
            <Chip color="warning" size="small" label="Waiting" />
            <Chip color="primary" size="small" label="Riding" />
            <Chip color="success" size="small" label="Complete" />
            <Chip color="secondary" size="small" label="Queue length" />
          </Stack>
        </Stack>
        <Box sx={{ display: 'grid', height: 500, minWidth: 0, overflow: 'hidden', placeItems: 'center' }}>
          {chartRows.length > 0 ? (
            <ResponsiveChartContainer
              height={500}
              margin={{ bottom: 48, left: 56, right: 56, top: 16 }}
              series={[
                // Series carry their own data arrays rather than a shared dataset:
                // mixed bar/line formatters mutate a shared dataset in x-charts v6.
                {
                  color: 'transparent',
                  data: chartRows.map((row) => row.offset),
                  layout: 'horizontal',
                  stack: 'progress',
                  type: 'bar',
                },
                {
                  color: theme.palette.warning.light,
                  data: chartRows.map((row) => row.waiting),
                  label: 'Waiting',
                  layout: 'horizontal',
                  stack: 'progress',
                  type: 'bar',
                },
                {
                  color: theme.palette.primary.main,
                  data: chartRows.map((row) => row.riding),
                  label: 'Riding',
                  layout: 'horizontal',
                  stack: 'progress',
                  type: 'bar',
                },
                {
                  color: theme.palette.success.main,
                  data: chartRows.map((row) => row.complete),
                  label: 'Complete',
                  layout: 'horizontal',
                  stack: 'progress',
                  type: 'bar',
                },
                {
                  color: theme.palette.secondary.main,
                  curve: 'stepAfter',
                  data: queueByTick,
                  label: 'Queue length',
                  showMark: false,
                  type: 'line',
                  yAxisKey: 'queue',
                },
              ]}
              xAxis={[{ data: sim.frames.map((frame) => frame.time), id: 'ticks', max: total, min: 0 }]}
              yAxis={[
                { data: chartRows.map((row) => row.label), id: 'passengers', scaleType: 'band' },
                { id: 'queue', max: peakQueue, min: 0 },
              ]}
            >
              <BarPlot />
              <LinePlot />
              <ChartsXAxis label="Tick" />
              <ChartsYAxis axisId="passengers" label="Passenger #" tickLabelStyle={{ display: 'none' }} />
              <ChartsYAxis axisId="queue" label="Queue length" position="right" />
              <ChartsTooltip />
            </ResponsiveChartContainer>
          ) : (
            <Typography color="text.secondary" variant="body2">
              No passengers have entered yet.
            </Typography>
          )}
        </Box>
      </Stack>
    </Paper>
  );
}
