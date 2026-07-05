import { Box, Chip, Paper, Stack, Typography, useTheme } from '@mui/material';
import { BarChart } from '@mui/x-charts/BarChart';
import type { LoadedSimulation } from '../types';

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
      label: `#${journey.id}`,
      offset: journey.requestTime,
      riding: journey.boardTime !== null && tick >= journey.boardTime ? Math.max(0, rideEnd - journey.boardTime) : 0,
      waiting: tick >= journey.requestTime ? Math.max(0, waitEnd - journey.requestTime) : 0,
    };
  });

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
          </Stack>
        </Stack>
        <Box sx={{ display: 'grid', height: 500, minWidth: 0, overflow: 'hidden', placeItems: 'center' }}>
          {chartRows.length > 0 ? (
            <BarChart
              dataset={chartRows}
              height={500}
              layout="horizontal"
              margin={{ bottom: 48, left: 56, right: 24, top: 16 }}
              series={[
                { color: 'transparent', dataKey: 'offset', stack: 'progress' },
                { color: theme.palette.warning.light, dataKey: 'waiting', label: 'Waiting', stack: 'progress' },
                { color: theme.palette.primary.main, dataKey: 'riding', label: 'Riding', stack: 'progress' },
                { color: theme.palette.success.main, dataKey: 'complete', label: 'Complete', stack: 'progress' },
              ]}
              slotProps={{
                legend: { hidden: true },
              }}
              xAxis={[{ label: 'Tick', max: total, min: 0 }]}
              yAxis={[
                {
                  dataKey: 'label',
                  label: 'Passenger #',
                  scaleType: 'band',
                  tickLabelStyle: { display: 'none' },
                },
              ]}
            />
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
