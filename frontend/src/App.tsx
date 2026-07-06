import { useMemo, useState } from "react";
import { Alert, Box, Container, Paper, Stack, Typography } from "@mui/material";
import Building from "./components/Building";
import ProgressChart from "./components/ProgressChart";
import StatsPanel from "./components/StatsPanel";
import SimulationToolbar from "./components/SimulationToolbar";
import { usePlayback } from "./hooks/usePlayback";
import { useKeyboardControls } from "./hooks/useKeyboardControls";
import { getStats, parseSimulation } from "./logic";
import type { LoadedSimulation } from "./logic";

export default function App() {
  const [sim, setSim] = useState<LoadedSimulation | null>(null);
  const [loadedFileName, setLoadedFileName] = useState("");
  const [loadError, setLoadError] = useState("");
  const lastTick = sim ? sim.frames.length - 1 : 0;

  const playback = usePlayback(lastTick, Boolean(sim));
  const { tick, playbackRate, play, pause, togglePlay, stepStart, stepBack, stepForward, stepEnd, reset } = playback;

  const frame = sim?.frames[tick] ?? null;
  const stats = useMemo(() => (sim ? getStats(sim, tick) : null), [sim, tick]);

  useKeyboardControls({
    enabled: Boolean(sim),
    onStepStart: stepStart,
    onStepBack: stepBack,
    onStepForward: stepForward,
    onStepEnd: stepEnd,
    onTogglePlay: togglePlay,
  });

  const handleFileLoad = (file: File) => {
    const reader = new FileReader();
    reader.onload = () => {
      try {
        const parsed = parseSimulation(JSON.parse(String(reader.result)));
        setSim(parsed);
        setLoadedFileName(file.name);
        reset();
        setLoadError("");
      } catch (error) {
        setLoadError(error instanceof Error ? error.message : "Could not load simulation file.");
      }
    };
    reader.onerror = () => {
      setLoadError(`Could not read ${file.name}.`);
    };
    reader.readAsText(file);
  };

  return (
    <Box sx={{ minHeight: "100vh", bgcolor: "grey.100", py: { xs: 2, md: 4 } }}>
      <Container maxWidth="xl">
        <Stack spacing={3}>
          <SimulationToolbar
            lastTick={lastTick}
            loaded={Boolean(sim)}
            loadedFileName={loadedFileName}
            playbackRate={playbackRate}
            tick={tick}
            onFileLoad={handleFileLoad}
            onPause={pause}
            onPlay={play}
            onStepBack={stepBack}
            onStepForward={stepForward}
            onStepStart={stepStart}
            onStepEnd={stepEnd}
          />

          {loadError && <Alert severity="error">{loadError}</Alert>}

          {sim && frame && stats ? (
            <>
              <Box
                sx={{
                  display: "grid",
                  gridTemplateColumns: { xs: "minmax(0, 1fr)", lg: "minmax(0, 1fr) minmax(280px, 360px)" },
                  gap: 3,
                  minWidth: 0,
                  width: "100%",
                }}
              >
                <Building frame={frame} sim={sim} />
                <StatsPanel lastTick={lastTick} stats={stats} />
              </Box>
              <ProgressChart sim={sim} tick={frame.time} />
            </>
          ) : (
            <Paper
              variant="outlined"
              sx={{
                display: "grid",
                minHeight: 360,
                placeItems: "center",
                px: 3,
                py: 6,
                textAlign: "center",
              }}
            >
              <Stack spacing={1.5} alignItems="center" maxWidth={520}>
                <Typography variant="h5" component="h1">
                  Load a simulation output JSON file
                </Typography>
                <Typography color="text.secondary">
                  The viewer runs entirely in the browser and derives all stats from the loaded frames.
                </Typography>
              </Stack>
            </Paper>
          )}
        </Stack>
      </Container>
    </Box>
  );
}
