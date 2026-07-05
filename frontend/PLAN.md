# Elevator Simulation Visualizer — Build Plan

A single-page React + MUI app that loads a simulation `output.json` and lets you
step through it tick by tick, with a building visualization on the left, live
stats on the right, and a per-passenger progress chart docked across the bottom
(see WIREFRAME.html)

---

## 1. Stack

- **React** (function components + hooks). No router, no global state library —
  one top-level component holding state is enough.
- **MUI (@mui/material)** for the shell: `AppBar` / `Toolbar`, `IconButton`,
  `Button`, `Typography`, `Paper`, `Divider`, `Tooltip`. Icons from
  `@mui/icons-material` (`FirstPage`, `ChevronLeft`, `ChevronRight`, `LastPage`,
  `UploadFile`).
- Use the horizontal bar chart component contained within MUI to make the passenger progress chart
- Everything is derived from the loaded file on the client; nothing is fetched.

---

## 2. Data model (what's in output.json)

Top level:
```
{
  version, floors, elevators:[{id,capacity}], passengers:[…], frames:[…]
}
```

- **passengers** (static definitions): `{ id, request_time, start_floor, destination_floor }`
- **frames** (one per tick): `{ time, complete, elevators:[…], passengers:[…] }`
  - each frame `elevator`: `{ id, floor, direction: idle|up|down, phase: moving|stopping|picking_up|dropping_off, passenger_count }`
  - each frame `passenger`: `{ id, status: waiting|riding, elevator_id }`

**Key insight:** a frame's `passengers` array only lists passengers who are
currently **active** (waiting or riding). Before their `request_time` they're
absent; once dropped off (complete) they disappear again. So "transported" and
all the timing stats must be *derived*, not read directly.

Sample file: 4 floors (0–3), 1 car (capacity 10), 50 passengers, 213 ticks (0–212).

---

## 3. Derived data (compute once, on file load)

Precompute a per-passenger journey table by scanning frames a single time:

- `requestTime` — from the passenger definition.
- `boardTime` — the first tick where that passenger's status is `riding`.
- `completeTime` — (last tick the passenger appears) + 1.
- `waitTime = boardTime - requestTime`
- `rideTime = completeTime - requestTime`  ← full journey, request → arrival

Store as `journeys[id] = { requestTime, boardTime, completeTime, waitTime, rideTime, start, dest }`.

This table drives both the chart and the min/avg/max stats, and never changes as
you step — only the *cutoff tick* changes.

---

## 4. State & stepping

```js
const [sim, setSim]   = useState(null);  // parsed file + derived journeys
const [tick, setTick] = useState(0);     // index into frames
```

Toolbar actions:
- **Skip to start** → `setTick(0)`
- **Back** → `setTick(t => Math.max(0, t-1))`
- **Forward** → `setTick(t => Math.min(last, t+1))`
- **Skip to end** → `setTick(frames.length-1)`

Load: `<input type="file">` (hidden, triggered by the Load button) →
`FileReader` → `JSON.parse` → build journeys → `setSim(...)`, `setTick(0)`.

The current frame is just `sim.frames[tick]`.

---

## 5. Stats panel (right)

All computed for the current `tick` from the frame + journey table. Everything is
counted in **ticks**.

- **Tick** — `frame.time`
- **Transported** — passengers with `completeTime <= tick`
- **Riding** — frame passengers with `status === 'riding'`
- **Waiting** — frame passengers with `status === 'waiting'`
- **Peak queue** — running max of the waiting count over ticks `0…tick`
- **Wait min / avg / max** — over passengers who have **boarded** by `tick`
  (`boardTime <= tick`), using `waitTime`
- **Ride min / avg / max** — over passengers **completed** by `tick`
  (`completeTime <= tick`), using `rideTime`

(Note: "queue size" was dropped because it's identical to "waiting"; "peak
queue" stays as the historical high-water mark.)

---

## 6. Building visualization (left)

- Floors stacked top-down: **F3 … F0**. Each floor is a row with: floor label,
  a waiting area (passengers whose `start_floor` is this floor and status
  `waiting`), and a shaft cell on the right.
- The **car** renders inside the shaft cell of the elevator's current `floor`.
  Riding passengers are drawn as filled dots inside the car.
- Waiting passengers = hollow dots; riding = filled dots.
- Show the car's `direction` (▲/▼/idle) and `phase` as a small caption.
- Optional next step: put a tiny destination arrow/number on each dot.
- Use a CSS transition so the cars slide up and down between ticks

---

## 7. Passenger progress chart (bottom dock)

One horizontal bar per passenger, laid on the simulation time axis
(`0 … frames.length`). For each passenger, up to three segments:

- **waiting** — from `requestTime` to `min(boardTime, tick)` — hatched
- **riding** — from `boardTime` to `min(completeTime, tick)` — blue
- **complete** — a small cap at `completeTime` — solid dark

Segments are positioned as `left: t0/total%`, `width: (t1-t0)/total%`. Only draw
what has happened up to the current `tick`, so the chart "fills in" as you step.
The list scrolls to hold all 50 passengers. A vertical playhead line at
`tick/total%` is a nice touch.

---

## 8. Component breakdown

```
<App>
  <Toolbar/>            // load + skip-start / back / forward / skip-end + "tick N / M"
  <div class=body>
    <Building sim tick/>   // floors, shaft, car, passenger dots
    <StatsPanel sim tick/> // the derived numbers from §5
  </div>
  <ProgressChart sim tick/> // §7
</App>
```

Keep `App` as the single source of truth (`sim`, `tick`); pass both down as
props. All the heavy computation is pure functions of `(sim, tick)`, so the UI
stays trivial and fast even at 200+ ticks.

---

## 9. Suggested build order

1. Toolbar + file load → get `sim` into state, log it.
2. Journey precompute (§3) + stats panel (§5) — easiest to verify against the file.
3. Stepping controls wired to `tick`.
4. Building visualization (§6).
5. Progress chart (§7).
6. Polish: tooltips, empty state before a file is loaded, keyboard arrows for step.

The attached `WIREFRAME.html` is only a structural reference. Use MUI components,
theme tokens, and idiomatic `sx` styling for the production UI rather than
copying wireframe CSS values.
