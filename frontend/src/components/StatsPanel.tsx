import { keyframes } from '@emotion/react';
import { Box, Chip, List, ListItem, ListItemText, Paper, Stack, Typography } from '@mui/material';
import type { ChipProps } from '@mui/material';
import type { StatSummary, Stats } from '../logic';

interface Props {
  lastTick: number;
  stats: Stats;
}

function formatSummary(summary: StatSummary | null): string {
  if (!summary) return 'n/a';
  return [summary.min, summary.avg, summary.max].map((value) => value.toFixed(2)).join('/');
}

const statValuePulse = keyframes`
  0% {
    transform: translateY(2px) scale(0.96);
    opacity: 0.72;
  }
  100% {
    transform: translateY(0) scale(1);
    opacity: 1;
  }
`;

export default function StatsPanel({ lastTick, stats }: Props) {
  const rows: Array<{ color?: ChipProps['color']; label: string; value: number | string }> = [
    { label: 'Tick', value: `${stats.tick} / ${lastTick}` },
    { color: 'warning', label: 'Waiting', value: stats.waiting },
    { color: 'primary', label: 'Riding', value: stats.riding },
    { color: 'success', label: 'Complete', value: stats.transported },
    { label: 'Peak queue', value: stats.peakQueue },
    { label: 'Wait min/avg/max', value: formatSummary(stats.waitSummary) },
    { label: 'Total min/avg/max', value: formatSummary(stats.totalSummary) },
  ];

  return (
    <Paper variant="outlined" sx={{ height: '100%', minWidth: 0, p: { xs: 2, md: 3 } }}>
      <Stack spacing={2}>
        <Box>
          <Typography variant="h6" component="h2">
            Live Stats
          </Typography>
          <Typography variant="body2" color="text.secondary">
            Tick by tick summary
          </Typography>
        </Box>
        <List disablePadding>
          {rows.map(({ color, label, value }, index) => (
            <ListItem
              disableGutters
              key={label}
              sx={{
                display: 'flex',
                gap: 2,
                justifyContent: 'space-between',
                minHeight: 52,
                borderBottom: index < rows.length - 1 ? 1 : 0,
                borderColor: 'divider',
              }}
            >
              <ListItemText primary={label} primaryTypographyProps={{ variant: 'body2' }} sx={{ minWidth: 0 }} />
              <Chip
                key={`${label}-${value}`}
                color={color}
                label={value}
                size="small"
                sx={{
                  animation: `${statValuePulse} 180ms ease-out`,
                  flexShrink: 0,
                  transformOrigin: 'center',
                }}
              />
            </ListItem>
          ))}
        </List>
      </Stack>
    </Paper>
  );
}
