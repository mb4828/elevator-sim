import { ChangeEvent, useRef } from 'react';
import { AppBar, Box, Button, Divider, IconButton, Paper, Stack, Toolbar, Tooltip, Typography } from '@mui/material';
import ChevronLeftIcon from '@mui/icons-material/ChevronLeft';
import ChevronRightIcon from '@mui/icons-material/ChevronRight';
import FastForwardIcon from '@mui/icons-material/FastForward';
import FirstPageIcon from '@mui/icons-material/FirstPage';
import LastPageIcon from '@mui/icons-material/LastPage';
import PauseIcon from '@mui/icons-material/Pause';
import PlayArrowIcon from '@mui/icons-material/PlayArrow';
import UploadFileIcon from '@mui/icons-material/UploadFile';
import type { ReactElement } from 'react';

interface Props {
  lastTick: number;
  loaded: boolean;
  playbackRate: 1 | 2 | null;
  tick: number;
  onFileLoad: (file: File) => void;
  onPause: () => void;
  onPlay: (rate: 1 | 2) => void;
  onStepBack: () => void;
  onStepEnd: () => void;
  onStepForward: () => void;
  onStepStart: () => void;
}

export default function SimulationToolbar({
  lastTick,
  loaded,
  playbackRate,
  tick,
  onFileLoad,
  onPause,
  onPlay,
  onStepBack,
  onStepEnd,
  onStepForward,
  onStepStart,
}: Props) {
  const inputRef = useRef<HTMLInputElement | null>(null);

  const handleFileChange = (event: ChangeEvent<HTMLInputElement>) => {
    const file = event.target.files?.[0];
    if (file) onFileLoad(file);
    event.target.value = '';
  };
  const pauseDisabled = !playbackRate;
  const playDisabled = !loaded || tick === lastTick || playbackRate === 1;
  const play2xDisabled = !loaded || tick === lastTick || playbackRate === 2;
  const startDisabled = !loaded || tick === 0;
  const endDisabled = !loaded || tick === lastTick;

  return (
    <Paper elevation={2} sx={{ overflow: 'hidden' }}>
      <AppBar position="static" color="primary" elevation={0}>
        <Toolbar
          sx={{
            flexWrap: 'wrap',
            gap: 1.5,
            minHeight: { xs: 72, sm: 64 },
            py: 1,
          }}
        >
          <input ref={inputRef} hidden type="file" accept="application/json,.json" onChange={handleFileChange} />
          <Typography variant="h6" component="div" sx={{ mr: { xs: 0, md: 2 }, flexGrow: { xs: 1, md: 0 } }}>
            Elevator Simulation Visualizer
          </Typography>
          <Button
            color="inherit"
            variant="outlined"
            startIcon={<UploadFileIcon />}
            onClick={() => inputRef.current?.click()}
          >
            Load log.json
          </Button>
          <Box sx={{ flexGrow: 1, display: { xs: 'none', md: 'block' } }} />
          <Stack direction="row" spacing={0.5}>
            <ControlTooltip disabled={pauseDisabled} title="Pause (Space)">
              <IconButton color="inherit" disabled={pauseDisabled} onClick={onPause}>
                <PauseIcon />
              </IconButton>
            </ControlTooltip>
            <ControlTooltip disabled={playDisabled} title="Play (Space)">
              <IconButton
                color={playbackRate === 1 ? 'secondary' : 'inherit'}
                disabled={playDisabled}
                onClick={() => onPlay(1)}
              >
                <PlayArrowIcon />
              </IconButton>
            </ControlTooltip>
            <ControlTooltip disabled={play2xDisabled} title="Play 2x">
              <IconButton
                color={playbackRate === 2 ? 'secondary' : 'inherit'}
                disabled={play2xDisabled}
                onClick={() => onPlay(2)}
              >
                <FastForwardIcon />
              </IconButton>
            </ControlTooltip>
            <Divider flexItem orientation="vertical" sx={{ borderColor: 'grey.300', opacity: 0.85 }} />
            <ControlTooltip disabled={startDisabled} title="Skip to start (Shift + ←)">
              <IconButton color="inherit" disabled={startDisabled} onClick={onStepStart}>
                <FirstPageIcon />
              </IconButton>
            </ControlTooltip>
            <ControlTooltip disabled={startDisabled} title="Step back (←)">
              <IconButton color="inherit" disabled={startDisabled} onClick={onStepBack}>
                <ChevronLeftIcon />
              </IconButton>
            </ControlTooltip>
            <ControlTooltip disabled={endDisabled} title="Step forward (→)">
              <IconButton color="inherit" disabled={endDisabled} onClick={onStepForward}>
                <ChevronRightIcon />
              </IconButton>
            </ControlTooltip>
            <ControlTooltip disabled={endDisabled} title="Skip to end (Shift + →)">
              <IconButton color="inherit" disabled={endDisabled} onClick={onStepEnd}>
                <LastPageIcon />
              </IconButton>
            </ControlTooltip>
          </Stack>
        </Toolbar>
      </AppBar>
    </Paper>
  );
}

function ControlTooltip({ children, disabled, title }: { children: ReactElement; disabled: boolean; title: string }) {
  if (disabled) {
    return children;
  }

  return <Tooltip title={title}>{children}</Tooltip>;
}
