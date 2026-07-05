import { keyframes } from '@emotion/react';
import { Box, SxProps, Theme } from '@mui/material';
import ArrowDropDownIcon from '@mui/icons-material/ArrowDropDown';
import ArrowDropUpIcon from '@mui/icons-material/ArrowDropUp';
import PersonIcon from '@mui/icons-material/Person';
import { forwardRef } from 'react';
import type { PassengerDefinition } from '../types';

export const passengerEnter = keyframes`
  from {
    opacity: 0;
    transform: translateX(-12px) scale(0.8);
  }
  to {
    opacity: 1;
    transform: translateX(0) scale(1);
  }
`;

export const passengerExit = keyframes`
  from {
    opacity: 1;
    transform: translateX(0) scale(1);
  }
  to {
    opacity: 0;
    transform: translateX(12px) scale(0.8);
  }
`;

function passengerDirectionColor(passenger: PassengerDefinition): 'success' | 'error' {
  return passenger.destination_floor > passenger.start_floor ? 'success' : 'error';
}

function passengerDirection(passenger: PassengerDefinition): 'up' | 'down' {
  return passenger.destination_floor > passenger.start_floor ? 'up' : 'down';
}

export function passengerTooltip(
  passengerId: number,
  passenger: PassengerDefinition | undefined,
  assignedElevatorId: number | null | undefined,
): string {
  if (!passenger) {
    return `#${passengerId}`;
  }
  const elevatorLabel = assignedElevatorId != null ? assignedElevatorId : '-';
  return `#${passenger.id} to ${passenger.destination_floor} [${elevatorLabel}]`;
}

// Direction is also encoded as an arrow badge (not just color) so it reads for color-blind users.
export const DirectionalPersonIcon = forwardRef<
  HTMLDivElement,
  {
    passenger?: PassengerDefinition;
    personFontSize: number;
    badgeSize: number;
    sx?: SxProps<Theme>;
  } & React.HTMLAttributes<HTMLDivElement>
>(({ passenger, personFontSize, badgeSize, sx, ...other }, ref) => {
  const direction = passenger ? passengerDirection(passenger) : undefined;
  const color = passenger ? passengerDirectionColor(passenger) : 'disabled';
  const ArrowIcon = direction === 'down' ? ArrowDropDownIcon : ArrowDropUpIcon;

  return (
    <Box ref={ref} sx={{ position: 'relative', display: 'inline-flex', flexShrink: 0, ...sx }} {...other}>
      <PersonIcon color={color} sx={{ fontSize: personFontSize }} />
      {direction && (
        <ArrowIcon
          sx={(theme) => ({
            position: 'absolute',
            right: -badgeSize * 0.35,
            top: direction === 'up' ? -badgeSize * 0.35 : undefined,
            bottom: direction === 'down' ? -badgeSize * 0.35 : undefined,
            fontSize: badgeSize,
            color: `${color}.main`,
            filter: `drop-shadow(0 0 1.5px ${theme.palette.background.paper})`,
          })}
        />
      )}
    </Box>
  );
});
DirectionalPersonIcon.displayName = 'DirectionalPersonIcon';
