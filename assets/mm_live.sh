#!/bin/bash
# Live Movie Moments dashboard — refreshes every 5s
MM_DIR="/c/Users/neilh/Downloads/MOVIE_MOMENTS"
ASSETS="/c/Users/neilh/youtube-tool/assets"
DONE="$ASSETS/mm_uploaded.txt"

echo -e "\033]0;Movie Moments LIVE STATUS\007"
while true; do
  clear
  echo "============================================================"
  echo "   MOVIE MOMENTS EDITS — LIVE PRODUCTION STATUS"
  echo "   $(date '+%Y-%m-%d %H:%M:%S')   (refresh 5s, Ctrl+C to close)"
  echo "============================================================"
  echo
  echo "  [1] MOVIE_MOMENTS FOLDER (pending publish)"
  echo "  ---------------------------------------------------------"
  n=0
  for f in "$MM_DIR"/*.mp4; do
    [ -e "$f" ] || continue
    n=$((n+1))
    base=$(basename "$f")
    sz=$(du -h "$f" | cut -f1)
    dur=$(ffprobe -v error -show_entries format=duration -of csv=p=0 "$f" 2>/dev/null | cut -d. -f1)
    mm=$(( ${dur:-0} / 60 )); ss=$(( ${dur:-0} % 60 ))
    flag="OK"
    [ "${dur:-0}" -lt 110 ] && flag=">> TOO SHORT (${mm}:${ss} < 1:50) - rebuilding"
    printf "   %-55s %7s  %s\n" "$base" "$sz" "$flag"
  done
  [ $n -eq 0 ] && echo "   (empty - all published or building)"
  echo
  echo "  [2] PUBLISHED LOG (mm_uploaded.txt)"
  echo "  ---------------------------------------------------------"
  total=$(grep -c . "$DONE" 2>/dev/null || echo 0)
  echo "   Total uploads recorded: $total"
  tail -5 "$DONE" 2>/dev/null | sed 's/^/   - /'
  echo
  echo "  [3] PRODUCTION PROCESSES"
  echo "  ---------------------------------------------------------"
  ps -W 2>/dev/null | grep -i python | awk '{print "   python.exe  PID", $1}' | head -10
  echo
  echo "  [4] RECENT BUILD OUTPUT (last OK/ERR lines)"
  echo "  ---------------------------------------------------------"
  for jf in /c/Users/neilh/AppData/Local/Temp/devin.exe-overflows/*/content.txt; do :; done
  tail -400 /c/Users/neilh/AppData/Local/Temp/devin.exe-overflows/shell-*/content.txt 2>/dev/null \
    | grep -E "OK |ERR |trailer:|done|SKIP|uploading" | tail -8 | sed 's/^/   /'
  echo
  echo "============================================================"
  sleep 5
done
