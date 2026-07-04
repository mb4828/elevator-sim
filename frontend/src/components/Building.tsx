import { keyframes } from "@emotion/react";
import { alpha, Box, Chip, Paper, Stack, SxProps, Theme, Tooltip, Typography } from "@mui/material";
import ArrowDropDownIcon from "@mui/icons-material/ArrowDropDown";
import ArrowDropUpIcon from "@mui/icons-material/ArrowDropUp";
import RemoveIcon from "@mui/icons-material/Remove";
import PersonIcon from "@mui/icons-material/Person";
import { forwardRef, useEffect, useRef, useState } from "react";
import type { Frame, FrameElevator, FramePassenger, LoadedSimulation, PassengerDefinition } from "../types";

interface Props {
  frame: Frame;
  sim: LoadedSimulation;
}

const passengerEnter = keyframes`
  from {
    opacity: 0;
    transform: translateX(-12px) scale(0.8);
  }
  to {
    opacity: 1;
    transform: translateX(0) scale(1);
  }
`;

const passengerExit = keyframes`
  from {
    opacity: 1;
    transform: translateX(0) scale(1);
  }
  to {
    opacity: 0;
    transform: translateX(12px) scale(0.8);
  }
`;

function passengerDirectionColor(passenger: PassengerDefinition): "success" | "error" {
  return passenger.destination_floor > passenger.start_floor ? "success" : "error";
}

function passengerDirection(passenger: PassengerDefinition): "up" | "down" {
  return passenger.destination_floor > passenger.start_floor ? "up" : "down";
}

// Direction is also encoded as an arrow badge (not just color) so it reads for color-blind users.
const DirectionalPersonIcon = forwardRef<
  HTMLDivElement,
  {
    passenger?: PassengerDefinition;
    personFontSize: number;
    badgeSize: number;
    sx?: SxProps<Theme>;
  } & React.HTMLAttributes<HTMLDivElement>
>(({ passenger, personFontSize, badgeSize, sx, ...other }, ref) => {
  const direction = passenger ? passengerDirection(passenger) : undefined;
  const color = passenger ? passengerDirectionColor(passenger) : "disabled";
  const ArrowIcon = direction === "down" ? ArrowDropDownIcon : ArrowDropUpIcon;

  return (
    <Box ref={ref} sx={{ position: "relative", display: "inline-flex", flexShrink: 0, ...sx }} {...other}>
      <PersonIcon color={color} sx={{ fontSize: personFontSize }} />
      {direction && (
        <ArrowIcon
          sx={(theme) => ({
            position: "absolute",
            right: -badgeSize * 0.35,
            top: direction === "up" ? -badgeSize * 0.35 : undefined,
            bottom: direction === "down" ? -badgeSize * 0.35 : undefined,
            fontSize: badgeSize,
            color: `${color}.main`,
            filter: `drop-shadow(0 0 1.5px ${theme.palette.background.paper})`,
          })}
        />
      )}
    </Box>
  );
});
DirectionalPersonIcon.displayName = "DirectionalPersonIcon";

export default function Building({ frame, sim }: Props) {
  const activeById = Object.fromEntries((frame.passengers ?? []).map((passenger) => [passenger.id, passenger])) as Record<
    number,
    FramePassenger
  >;
  const passengerById = new Map(sim.passengers.map((passenger) => [passenger.id, passenger]));
  const floors = Array.from({ length: sim.floors }, (_, index) => sim.floors - index - 1);
  const elevators = frame.elevators ?? [];
  const laneWidth = 92;
  const shaftWidth = Math.max(116, elevators.length * laneWidth);

  return (
    <Paper variant="outlined" sx={{ height: "100%", minWidth: 0, p: { xs: 2, md: 3 } }}>
      <Stack spacing={2}>
        <Box>
          <Typography variant="h6" component="h2">
            Simulation
          </Typography>
          <Typography variant="body2" color="text.secondary">
            {sim.floors} floors, {elevators.length} car{elevators.length === 1 ? "" : "s"}
          </Typography>
        </Box>
        <Box
          sx={{
            border: 1,
            borderColor: "divider",
            borderRadius: 1,
            overflow: "hidden",
            bgcolor: "background.paper",
            minWidth: 0,
            position: "relative",
          }}
        >
          {floors.map((floor) => (
            <Box
              key={floor}
              sx={{
                display: "grid",
                gridTemplateColumns: {
                  xs: `44px minmax(0, 1fr) ${Math.max(92, elevators.length * 76)}px`,
                  sm: `52px minmax(0, 1fr) ${shaftWidth}px`,
                },
                minHeight: 76,
                borderTop: floor === floors[0] ? 0 : 1,
                borderColor: "divider",
                minWidth: 0,
              }}
            >
              <Box
                sx={{
                  display: "grid",
                  placeItems: "center",
                  bgcolor: "action.hover",
                  borderRight: 1,
                  borderColor: "divider",
                }}
              >
                <Typography variant="subtitle2">F{floor}</Typography>
              </Box>
              <WaitingPassengerIcons
                passengers={sim.passengers.filter(
                  (passenger) => passenger.start_floor === floor && activeById[passenger.id]?.status === "waiting",
                )}
              />
              <Box
                sx={(theme) => ({
                  display: "grid",
                  placeItems: "center",
                  borderLeft: 1,
                  borderColor: "divider",
                  bgcolor: alpha(theme.palette.primary.main, 0.06),
                  minWidth: 0,
                  p: 1,
                })}
              />
            </Box>
          ))}
          <Box
            sx={{
              position: "absolute",
              top: 0,
              right: 0,
              bottom: 0,
              width: { xs: Math.max(92, elevators.length * 76), sm: shaftWidth },
              pointerEvents: "none",
            }}
          >
            {elevators.map((elevator, index) => (
              <ElevatorCar
                elevator={elevator}
                index={index}
                key={elevator.id}
                passengers={(frame.passengers ?? [])
                  .filter((passenger) => passenger.status === "riding" && passenger.elevator_id === elevator.id)
                  .map((passenger) => passengerById.get(passenger.id))
                  .filter((passenger): passenger is PassengerDefinition => Boolean(passenger))}
                totalElevators={elevators.length}
                totalFloors={sim.floors}
              />
            ))}
          </Box>
        </Box>
        <Stack direction="row" spacing={1} flexWrap="wrap" useFlexGap>
          <Chip color="success" size="small" label="Going Up" />
          <Chip color="error" size="small" label="Going Down" />
        </Stack>
      </Stack>
    </Paper>
  );
}

function WaitingPassengerIcons({ passengers }: { passengers: PassengerDefinition[] }) {
  const passengerMap = new Map(passengers.map((passenger) => [passenger.id, passenger]));
  const previousIds = useRef(passengers.map((passenger) => passenger.id));
  const [displayIds, setDisplayIds] = useState(previousIds.current);
  const [enteringIds, setEnteringIds] = useState<Set<number>>(new Set());
  const [exitingIds, setExitingIds] = useState<Set<number>>(new Set());

  useEffect(() => {
    const nextIds = passengers.map((passenger) => passenger.id);
    const previousIdSet = new Set(previousIds.current);
    const nextIdSet = new Set(nextIds);
    const entering = nextIds.filter((id) => !previousIdSet.has(id));
    const exiting = previousIds.current.filter((id) => !nextIdSet.has(id));

    if (entering.length === 0 && exiting.length === 0) {
      previousIds.current = nextIds;
      return;
    }

    setEnteringIds(new Set(entering));
    setExitingIds(new Set(exiting));
    setDisplayIds([...nextIds, ...exiting]);

    const timeout = window.setTimeout(() => {
      setDisplayIds(nextIds);
      setEnteringIds(new Set());
      setExitingIds(new Set());
      previousIds.current = nextIds;
    }, 180);

    return () => window.clearTimeout(timeout);
  }, [passengers]);

  return (
    <Stack direction="row" flexWrap="wrap" gap={0.5} alignContent="center" sx={{ minWidth: 0, p: 1 }}>
      {displayIds.map((passengerId) => {
        const passenger = passengerMap.get(passengerId);
        const isEntering = enteringIds.has(passengerId);
        const isExiting = exitingIds.has(passengerId);

        return (
          <Tooltip
            key={passengerId}
            title={
              passenger
                ? `Passenger ${passenger.id} to F${passenger.destination_floor}`
                : `Passenger ${passengerId}`
            }
          >
            <DirectionalPersonIcon
              passenger={passenger}
              personFontSize={20}
              badgeSize={17}
              sx={{
                animation: isExiting
                  ? `${passengerExit} 180ms ease-in forwards`
                  : isEntering
                    ? `${passengerEnter} 180ms ease-out`
                    : undefined,
              }}
            />
          </Tooltip>
        );
      })}
    </Stack>
  );
}

function ElevatorCar({
  elevator,
  index,
  passengers,
  totalElevators,
  totalFloors,
}: {
  elevator: FrameElevator;
  index: number;
  passengers: PassengerDefinition[];
  totalElevators: number;
  totalFloors: number;
}) {
  const floorIndexFromTop = totalFloors - elevator.floor - 1;
  const laneCenter = ((index + 0.5) / totalElevators) * 100;

  return (
    <Paper
      elevation={4}
      sx={{
        position: "absolute",
        top: `calc(${floorIndexFromTop * (100 / totalFloors)}% + ${50 / totalFloors}%)`,
        left: `${laneCenter}%`,
        width: { xs: 70, sm: 84 },
        height: 68,
        display: "grid",
        justifyItems: "center",
        gap: 0.25,
        gridTemplateRows: "20px 22px 12px",
        overflow: "hidden",
        p: 0.75,
        border: 2,
        borderColor: "primary.main",
        bgcolor: "background.paper",
        color: "text.primary",
        pointerEvents: "auto",
        transform: "translate(-50%, -50%)",
        transition: "top 280ms ease-in-out, transform 280ms ease-in-out",
        willChange: "top, transform",
      }}
    >
      <DirectionIndicator direction={elevator.direction} />
      <ElevatorPassengerIcons passengers={passengers} />
      <Typography
        variant="caption"
        color="text.secondary"
        textAlign="center"
        sx={{
          fontSize: "0.625rem",
          lineHeight: 1,
          maxWidth: "100%",
          overflow: "hidden",
          textOverflow: "ellipsis",
          whiteSpace: "nowrap",
        }}
      >
        {elevator.phase.replace(/_/g, " ")}
      </Typography>
    </Paper>
  );
}

function ElevatorPassengerIcons({ passengers }: { passengers: PassengerDefinition[] }) {
  const initialPassengerMap = new Map(passengers.map((passenger) => [passenger.id, passenger]));
  const previousIds = useRef(passengers.map((passenger) => passenger.id));
  const previousPassengerMap = useRef(initialPassengerMap);
  const [displayIds, setDisplayIds] = useState(previousIds.current);
  const [displayPassengerMap, setDisplayPassengerMap] = useState(initialPassengerMap);
  const [enteringIds, setEnteringIds] = useState<Set<number>>(new Set());
  const [exitingIds, setExitingIds] = useState<Set<number>>(new Set());
  const visibleCount = Math.max(1, displayIds.length);
  const iconSize = Math.max(12, Math.min(20, 58 / visibleCount + 8));
  const iconOverlap = visibleCount > 1 ? -Math.max(0, (iconSize * visibleCount - 58) / (visibleCount - 1)) : 0;

  useEffect(() => {
    const nextIds = passengers.map((passenger) => passenger.id);
    const nextPassengerMap = new Map(passengers.map((passenger) => [passenger.id, passenger]));
    const previousIdSet = new Set(previousIds.current);
    const nextIdSet = new Set(nextIds);
    const entering = nextIds.filter((id) => !previousIdSet.has(id));
    const exiting = previousIds.current.filter((id) => !nextIdSet.has(id));

    if (entering.length === 0 && exiting.length === 0) {
      previousIds.current = nextIds;
      previousPassengerMap.current = nextPassengerMap;
      return;
    }

    const mergedPassengerMap = new Map([...previousPassengerMap.current, ...nextPassengerMap]);
    setDisplayPassengerMap(mergedPassengerMap);
    setDisplayIds([...nextIds, ...exiting]);
    setEnteringIds(new Set(entering));
    setExitingIds(new Set(exiting));

    const timeout = window.setTimeout(() => {
      setDisplayIds(nextIds);
      setDisplayPassengerMap(nextPassengerMap);
      setEnteringIds(new Set());
      setExitingIds(new Set());
      previousIds.current = nextIds;
      previousPassengerMap.current = nextPassengerMap;
    }, 180);

    return () => window.clearTimeout(timeout);
  }, [passengers]);

  return (
    <Box
      sx={{
        alignItems: "center",
        display: "flex",
        height: 22,
        justifyContent: "center",
        maxWidth: "100%",
        minWidth: 0,
        overflow: "visible",
        whiteSpace: "nowrap",
      }}
    >
      {displayIds.map((passengerId, index) => {
        const passenger = displayPassengerMap.get(passengerId);
        const isEntering = enteringIds.has(passengerId);
        const isExiting = exitingIds.has(passengerId);

        return (
          <Tooltip
            key={passengerId}
            title={
              passenger
                ? `Passenger ${passenger.id} to F${passenger.destination_floor}`
                : `Passenger ${passengerId}`
            }
          >
            <DirectionalPersonIcon
              passenger={passenger}
              personFontSize={iconSize}
              badgeSize={Math.max(13, iconSize * 0.85)}
              sx={{
                animation: isExiting
                  ? `${passengerExit} 180ms ease-in forwards`
                  : isEntering
                    ? `${passengerEnter} 180ms ease-out`
                    : undefined,
                ml: index > 0 ? `${iconOverlap}px` : 0,
              }}
            />
          </Tooltip>
        );
      })}
    </Box>
  );
}

function DirectionIndicator({ direction }: { direction: string }) {
  if (direction === "up") {
    return <ArrowDropUpIcon color="success" fontSize="medium" />;
  }

  if (direction === "down") {
    return <ArrowDropDownIcon color="error" fontSize="medium" />;
  }

  return (
    <RemoveIcon color="disabled" fontSize="small" />
  );
}
