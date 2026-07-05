import { keyframes } from '@emotion/react';
import { Box, SxProps, Theme } from '@mui/material';
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

// Direction is also encoded via the destination floor number (not just color) so it reads for
// color-blind users; it sits superscript for up and subscript for down.
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

  return (
    <Box ref={ref} sx={{ position: 'relative', display: 'inline-flex', flexShrink: 0, ...sx }} {...other}>
      <PersonIcon color={color} sx={{ fontSize: personFontSize }} />
      {direction && passenger && (
        <Box
          component="span"
          sx={(theme) => ({
            position: 'absolute',
            right: -badgeSize * 0.3,
            top: direction === 'up' ? -badgeSize * 0.3 : undefined,
            bottom: direction === 'down' ? -badgeSize * 0.3 : undefined,
            fontSize: badgeSize * 0.6,
            lineHeight: 1,
            fontWeight: 700,
            color: `${color}.main`,
            textShadow: `0 0 1.5px ${theme.palette.background.paper}, 0 0 1.5px ${theme.palette.background.paper}`,
          })}
        >
          {passenger.destination_floor}
        </Box>
      )}
    </Box>
  );
});
DirectionalPersonIcon.displayName = 'DirectionalPersonIcon';
