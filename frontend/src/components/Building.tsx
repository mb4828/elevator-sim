import { alpha, Box, Chip, Paper, Stack, Tooltip, Typography } from '@mui/material';
import { useEffect, useRef, useState } from 'react';
import type { Frame, FramePassenger, LoadedSimulation, PassengerDefinition } from '../types';
import ElevatorCar from './ElevatorCar';
import { DirectionalPersonIcon, passengerEnter, passengerExit, passengerTooltip } from './PassengerIcon';

interface Props {
  frame: Frame;
  sim: LoadedSimulation;
}

export default function Building({ frame, sim }: Props) {
  const activeById = Object.fromEntries(
    (frame.passengers ?? []).map((passenger) => [passenger.id, passenger]),
  ) as Record<number, FramePassenger>;
  const passengerById = new Map(sim.passengers.map((passenger) => [passenger.id, passenger]));
  const assignedElevatorById = new Map(
    (frame.passengers ?? []).map((passenger) => [passenger.id, passenger.elevator_id]),
  );
  const floors = Array.from({ length: sim.floors }, (_, index) => sim.floors - index - 1);
  const elevators = frame.elevators ?? [];
  const laneWidth = 92;
  const shaftWidth = Math.max(116, elevators.length * laneWidth);

  return (
    <Paper variant="outlined" sx={{ height: '100%', minWidth: 0, p: { xs: 2, md: 3 } }}>
      <Stack spacing={2}>
        <Box>
          <Typography variant="h6" component="h2">
            Simulation
          </Typography>
          <Typography variant="body2" color="text.secondary">
            {sim.floors} floors, {elevators.length} car{elevators.length === 1 ? '' : 's'}
          </Typography>
        </Box>
        <Box
          sx={{
            border: 1,
            borderColor: 'divider',
            borderRadius: 1,
            overflow: 'hidden',
            bgcolor: 'background.paper',
            minWidth: 0,
            position: 'relative',
          }}
        >
          {floors.map((floor) => (
            <Box
              key={floor}
              sx={{
                display: 'grid',
                gridTemplateColumns: {
                  xs: `44px minmax(0, 1fr) ${Math.max(92, elevators.length * 76)}px`,
                  sm: `52px minmax(0, 1fr) ${shaftWidth}px`,
                },
                minHeight: 76,
                borderTop: floor === floors[0] ? 0 : 1,
                borderColor: 'divider',
                minWidth: 0,
              }}
            >
              <Box
                sx={{
                  display: 'grid',
                  placeItems: 'center',
                  bgcolor: 'action.hover',
                  borderRight: 1,
                  borderColor: 'divider',
                }}
              >
                <Typography variant="subtitle2">F{floor}</Typography>
              </Box>
              <WaitingPassengerIcons
                passengers={sim.passengers.filter(
                  (passenger) => passenger.start_floor === floor && activeById[passenger.id]?.status === 'waiting',
                )}
                assignedElevatorById={assignedElevatorById}
              />
              <Box
                sx={(theme) => ({
                  display: 'grid',
                  placeItems: 'center',
                  borderLeft: 1,
                  borderColor: 'divider',
                  bgcolor: alpha(theme.palette.primary.main, 0.06),
                  minWidth: 0,
                  p: 1,
                })}
              />
            </Box>
          ))}
          <Box
            sx={{
              position: 'absolute',
              top: 0,
              right: 0,
              bottom: 0,
              width: { xs: Math.max(92, elevators.length * 76), sm: shaftWidth },
              pointerEvents: 'none',
            }}
          >
            {elevators.map((elevator, index) => (
              <ElevatorCar
                elevator={elevator}
                index={index}
                key={elevator.id}
                passengers={(frame.passengers ?? [])
                  .filter((passenger) => passenger.status === 'riding' && passenger.elevator_id === elevator.id)
                  .map((passenger) => passengerById.get(passenger.id))
                  .filter((passenger): passenger is PassengerDefinition => Boolean(passenger))}
                assignedElevatorById={assignedElevatorById}
                totalElevators={elevators.length}
                totalFloors={sim.floors}
              />
            ))}
          </Box>
        </Box>
      </Stack>
    </Paper>
  );
}

function WaitingPassengerIcons({
  passengers,
  assignedElevatorById,
}: {
  passengers: PassengerDefinition[];
  assignedElevatorById: Map<number, number | null | undefined>;
}) {
  const initialPassengerMap = new Map(passengers.map((passenger) => [passenger.id, passenger]));
  const previousIds = useRef(passengers.map((passenger) => passenger.id));
  const previousPassengerMap = useRef(initialPassengerMap);
  const [displayIds, setDisplayIds] = useState(previousIds.current);
  const [displayPassengerMap, setDisplayPassengerMap] = useState(initialPassengerMap);
  const [enteringIds, setEnteringIds] = useState<Set<number>>(new Set());
  const [exitingIds, setExitingIds] = useState<Set<number>>(new Set());

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
    setEnteringIds(new Set(entering));
    setExitingIds(new Set(exiting));
    setDisplayIds([...nextIds, ...exiting]);

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
    <Stack
      direction="row"
      flexWrap="wrap"
      gap={0.5}
      alignContent="center"
      justifyContent="flex-end"
      sx={{ minWidth: 0, p: 1 }}
    >
      {displayIds.map((passengerId) => {
        const passenger = displayPassengerMap.get(passengerId);
        const isEntering = enteringIds.has(passengerId);
        const isExiting = exitingIds.has(passengerId);

        return (
          <Tooltip
            key={passengerId}
            title={passengerTooltip(passengerId, passenger, assignedElevatorById.get(passengerId))}
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
