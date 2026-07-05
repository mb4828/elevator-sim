import { alpha, Box, Paper, Theme, Tooltip, Typography } from '@mui/material';
import RemoveIcon from '@mui/icons-material/Remove';
import { PlayArrow } from '@mui/icons-material';
import { useEffect, useRef, useState } from 'react';
import type { FrameElevator, PassengerDefinition } from '../types';
import { DirectionalPersonIcon, passengerEnter, passengerExit, passengerTooltip } from './PassengerIcon';

export default function ElevatorCar({
  elevator,
  index,
  passengers,
  assignedElevatorById,
  totalElevators,
  totalFloors,
}: {
  elevator: FrameElevator;
  index: number;
  passengers: PassengerDefinition[];
  assignedElevatorById: Map<number, number | null | undefined>;
  totalElevators: number;
  totalFloors: number;
}) {
  const floorIndexFromTop = totalFloors - elevator.floor - 1;
  const laneCenter = ((index + 0.5) / totalElevators) * 100;

  return (
    <Paper
      elevation={4}
      sx={{
        position: 'absolute',
        top: `calc(${floorIndexFromTop * (100 / totalFloors)}% + ${50 / totalFloors}%)`,
        left: `${laneCenter}%`,
        width: { xs: 70, sm: 84 },
        height: 68,
        display: 'grid',
        justifyItems: 'center',
        gap: 0.25,
        gridTemplateRows: '20px 22px 12px',
        overflow: 'hidden',
        p: 0.75,
        border: 2,
        borderColor: 'primary.main',
        bgcolor: 'background.paper',
        color: 'text.primary',
        pointerEvents: 'auto',
        transform: 'translate(-50%, -50%)',
        transition: 'top 280ms ease-in-out, transform 280ms ease-in-out',
        willChange: 'top, transform',
      }}
    >
      <DirectionIndicator direction={elevator.direction} />
      <ElevatorPassengerIcons passengers={passengers} assignedElevatorById={assignedElevatorById} />
      <Typography
        variant="caption"
        color="text.secondary"
        textAlign="center"
        sx={{
          fontSize: '0.625rem',
          lineHeight: 1,
          maxWidth: '100%',
          overflow: 'hidden',
          textOverflow: 'ellipsis',
          whiteSpace: 'nowrap',
        }}
      >
        {elevator.phase.replace(/_/g, ' ')}
      </Typography>
      <ElevatorDoors open={elevator.phase === 'picking_up' || elevator.phase === 'dropping_off'} />
    </Paper>
  );
}

function ElevatorDoors({ open }: { open: boolean }) {
  const doorSx = (side: 'left' | 'right') => (theme: Theme) => ({
    position: 'absolute' as const,
    top: 0,
    bottom: 0,
    [side]: 0,
    width: '50%',
    bgcolor: theme.palette.grey[200],
    borderLeft: side === 'right' ? `1px solid ${theme.palette.grey[300]}` : undefined,
    borderRight: side === 'left' ? `1px solid ${theme.palette.grey[300]}` : undefined,
    pointerEvents: 'none' as const,
    transition: 'transform 260ms ease-in-out',
    transform: open ? `translateX(${side === 'left' ? '-' : ''}100%)` : 'translateX(0)',
    zIndex: -1,
  });

  return (
    <>
      <Box sx={doorSx('left')} />
      <Box sx={doorSx('right')} />
    </>
  );
}

function ElevatorPassengerIcons({
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
        alignItems: 'center',
        display: 'flex',
        height: 22,
        justifyContent: 'center',
        maxWidth: '100%',
        minWidth: 0,
        overflow: 'visible',
        whiteSpace: 'nowrap',
      }}
    >
      {displayIds.map((passengerId, index) => {
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
  if (direction === 'up') {
    return <PlayArrow color="success" fontSize="medium" style={{ rotate: '-90deg' }} />;
  }

  if (direction === 'down') {
    return <PlayArrow color="error" fontSize="medium" style={{ rotate: '90deg' }} />;
  }

  return <RemoveIcon color="disabled" fontSize="small" />;
}
