import { Box, Paper, Theme, Tooltip, Typography } from '@mui/material';
import RemoveIcon from '@mui/icons-material/Remove';
import { PlayArrow } from '@mui/icons-material';
import type { Direction, FrameElevator, PassengerDefinition } from '../logic';
import { useEnterExitTransition } from '../hooks/useEnterExitTransition';
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
      <DirectionIndicator direction={elevator.direction} targetFloor={elevator.target_floor} />
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
      <ElevatorDoors open={elevator.phase === 'loading' || elevator.phase === 'unloading'} />
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
  const { displayIds, displayPassengerMap, enteringIds, exitingIds } = useEnterExitTransition(passengers);
  const visibleCount = Math.max(1, displayIds.length);
  const iconSize = Math.max(12, Math.min(20, 58 / visibleCount + 8));
  const iconOverlap = visibleCount > 1 ? -Math.max(0, (iconSize * visibleCount - 58) / (visibleCount - 1)) : 0;

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

function DirectionIndicator({ direction, targetFloor }: { direction: Direction; targetFloor: number | null }) {
  if (direction !== 'up' && direction !== 'down') {
    return <RemoveIcon color="disabled" fontSize="small" />;
  }

  return (
    <Box sx={{ position: 'relative', display: 'inline-flex' }}>
      <PlayArrow
        color={direction === 'up' ? 'success' : 'error'}
        fontSize="large"
        style={{ rotate: direction === 'up' ? '-90deg' : '90deg', position: 'relative', top: '-8px' }}
      />
      {targetFloor != null && (
        <Box
          component="span"
          sx={{
            position: 'absolute',
            inset: 0,
            display: 'flex',
            alignItems: 'center',
            justifyContent: 'center',
            fontSize: 9,
            lineHeight: 1,
            fontWeight: 700,
            color: 'common.white',
          }}
        >
          {targetFloor}
        </Box>
      )}
    </Box>
  );
}
