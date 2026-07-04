#!/usr/bin/env bash
set -euo pipefail

# Estimate active project time from source file modification times and write the
# result into README.md. Files changed close together are treated as one work
# session; gaps longer than 30 minutes are capped so breaks do not count as
# active work. This is an estimate, not a timer: it depends on filesystem
# timestamps and excludes README.md so this script does not count its own update.

readonly MAX_GAP_SECONDS=$((30 * 60))
readonly README_FILE="README.md"
readonly START_MARKER="<!-- project-time:start -->"
readonly END_MARKER="<!-- project-time:end -->"

repo_root="$(git rev-parse --show-toplevel)"
cd "$repo_root"

file_mtime() {
  stat -f "%m" "$1" 2>/dev/null || stat -c "%Y" "$1" 2>/dev/null
}

timestamps=()
while IFS= read -r -d "" file_path; do
  if [ "$file_path" = "$README_FILE" ]; then
    continue
  fi

  timestamp="$(file_mtime "$file_path" || true)"
  if [ -n "$timestamp" ]; then
    timestamps+=("$timestamp")
  fi
done < <(git ls-files --cached --others --exclude-standard -z)

sorted_timestamps=()
while IFS= read -r timestamp; do
  if [ -n "$timestamp" ]; then
    sorted_timestamps+=("$timestamp")
  fi
done < <(printf "%s\n" "${timestamps[@]}" | sort -n)
timestamps=("${sorted_timestamps[@]}")

total_seconds=0

if [ "${#timestamps[@]}" -gt 0 ]; then
  total_seconds="$MAX_GAP_SECONDS"
  previous_timestamp="${timestamps[0]}"

  for current_timestamp in "${timestamps[@]:1}"; do
    gap_seconds=$((current_timestamp - previous_timestamp))

    if [ "$gap_seconds" -le "$MAX_GAP_SECONDS" ]; then
      total_seconds=$((total_seconds + gap_seconds))
    else
      total_seconds=$((total_seconds + MAX_GAP_SECONDS))
    fi

    previous_timestamp="$current_timestamp"
  done
fi

hours=$((total_seconds / 3600))
minutes=$(((total_seconds % 3600) / 60))
project_time="${hours}h ${minutes}m"

tmp_file="$(mktemp)"
if ! awk \
  -v start_marker="$START_MARKER" \
  -v end_marker="$END_MARKER" \
  -v project_time="$project_time" \
  '{
    start_index = index($0, start_marker)
    end_index = index($0, end_marker)

    if (start_index > 0 && end_index > start_index) {
      replaced = 1
      print substr($0, 1, start_index + length(start_marker) - 1) project_time substr($0, end_index)
      next
    }

    print
  }

  END {
    if (replaced != 1) {
      exit 1
    }
  }' "$README_FILE" > "$tmp_file"; then
  rm "$tmp_file"
  echo "Could not find project time marker in $README_FILE" >&2
  exit 1
fi

mv "$tmp_file" "$README_FILE"
echo "Updated $README_FILE project time to $project_time"
