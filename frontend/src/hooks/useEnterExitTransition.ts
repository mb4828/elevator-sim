import { useEffect, useRef, useState } from "react";
import type { PassengerDefinition } from "../types";

export interface EnterExitTransition {
  /** IDs to render, including exiting ones until their animation finishes. */
  displayIds: number[];
  /** Passenger data for every displayed ID, retained while an icon exits. */
  displayPassengerMap: Map<number, PassengerDefinition>;
  enteringIds: Set<number>;
  exitingIds: Set<number>;
}

const EXIT_ANIMATION_MS = 180;

/**
 * Tracks which passengers entered or left between renders so icons can play
 * enter/exit animations. Exiting passengers stay in `displayIds` (with their
 * data kept in `displayPassengerMap`) for the animation duration before being
 * dropped.
 */
export function useEnterExitTransition(passengers: PassengerDefinition[]): EnterExitTransition {
  const initialIds = passengers.map((passenger) => passenger.id);
  const initialPassengerMap = new Map(passengers.map((passenger) => [passenger.id, passenger]));
  const previousIds = useRef(initialIds);
  const previousPassengerMap = useRef(initialPassengerMap);
  const [displayIds, setDisplayIds] = useState(initialIds);
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
    }, EXIT_ANIMATION_MS);

    return () => window.clearTimeout(timeout);
  }, [passengers]);

  return { displayIds, displayPassengerMap, enteringIds, exitingIds };
}
