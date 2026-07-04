import { useCallback, useEffect, useMemo, useState } from "react";
import { Alert, Box, Container, Paper, Stack, Typography } from "@mui/material";
import Building from "./components/Building";
import ProgressChart from "./components/ProgressChart";
import StatsPanel from "./components/StatsPanel";
import SimulationToolbar from "./components/SimulationToolbar";
import { getStats, parseSimulation } from "./simulation";
import type { LoadedSimulation } from "./types";

export default function App() {
  const [sim, setSim] = useState<LoadedSimulation | null>(null);
  const [tick, setTick] = useState(0);
  const [loadError, setLoadError] = useState("");
  const [playbackRate, setPlaybackRate] = useState<1 | 2 | null>(null);
  const lastTick = sim ? sim.frames.length - 1 : 0;
  const frame = sim?.frames[tick] ?? null;
  const stats = useMemo(() => (sim ? getStats(sim, tick) : null), [sim, tick]);

  const stepStart = useCallback(() => {
    setPlaybackRate(null);
    setTick(0);
  }, []);

  const stepBack = useCallback(() => {
    setPlaybackRate(null);
    setTick((value) => Math.max(0, value - 1));
  }, []);

  const stepForward = useCallback(() => {
    setPlaybackRate(null);
    setTick((value) => Math.min(lastTick, value + 1));
  }, [lastTick]);

  const stepEnd = useCallback(() => {
    setPlaybackRate(null);
    setTick(lastTick);
  }, [lastTick]);

  useEffect(() => {
    if (!playbackRate || !sim) return undefined;

    const interval = window.setInterval(() => {
      setTick((value) => {
        if (value >= lastTick) {
          setPlaybackRate(null);
          return value;
        }

        const nextTick = Math.min(lastTick, value + 1);
        if (nextTick >= lastTick) {
          setPlaybackRate(null);
        }
        return nextTick;
      });
    }, 1000 / playbackRate);

    return () => window.clearInterval(interval);
  }, [lastTick, playbackRate, sim]);

  useEffect(() => {
    const handleKeyDown = (event: KeyboardEvent) => {
      if (!sim || isEditableTarget(event.target)) return;

      if (event.key === "ArrowLeft") {
        event.preventDefault();
        if (event.shiftKey) {
          stepStart();
        } else {
          stepBack();
        }
        return;
      }

      if (event.key === "ArrowRight") {
        event.preventDefault();
        if (event.shiftKey) {
          stepEnd();
        } else {
          stepForward();
        }
        return;
      }

      if (event.key === " ") {
        event.preventDefault();
        setPlaybackRate((value) => (value ? null : tick < lastTick ? 1 : null));
      }
    };

    window.addEventListener("keydown", handleKeyDown);
    return () => window.removeEventListener("keydown", handleKeyDown);
  }, [lastTick, sim, stepBack, stepEnd, stepForward, stepStart, tick]);

  const handleFileLoad = (file: File) => {
    const reader = new FileReader();
    reader.onload = () => {
      try {
        const parsed = parseSimulation(JSON.parse(String(reader.result)));
        setSim(parsed);
        setTick(0);
        setPlaybackRate(null);
        setLoadError("");
      } catch (error) {
        setLoadError(error instanceof Error ? error.message : "Could not load simulation file.");
      }
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
            playbackRate={playbackRate}
            tick={tick}
            onFileLoad={handleFileLoad}
            onPause={() => setPlaybackRate(null)}
            onPlay={(rate) => setPlaybackRate(rate)}
            onStepBack={stepBack}
            onStepForward={stepForward}
            onStepStart={stepStart}
            onStepEnd={stepEnd}
          />

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
                {loadError && <Alert severity="error">{loadError}</Alert>}
              </Stack>
            </Paper>
          )}
        </Stack>
      </Container>
    </Box>
  );
}

function isEditableTarget(target: EventTarget | null): boolean {
  if (!(target instanceof HTMLElement)) return false;
  const tagName = target.tagName.toLowerCase();
  return tagName === "input" || tagName === "textarea" || tagName === "select" || target.isContentEditable;
}
