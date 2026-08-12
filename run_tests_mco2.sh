#!/usr/bin/env bash
#
# run_tests_mco2.sh - Runs the MCO2 traceroute against the three required hosts.
#
# Prints a labeled banner before each trace and pauses afterward so you can
# take a clean screenshot. All output is saved to traceroute_output.log.
#
# USAGE:
#   sudo ./run_tests_mco2.sh        (raw sockets need root)
#
# Put this script in the SAME folder as traceroute.py.

set -u

PYTHON="python3"
SCRIPT_DIR="$(cd "$(dirname "$0")" && pwd)"
TR="${SCRIPT_DIR}/traceroute.py"
LOGFILE="${SCRIPT_DIR}/traceroute_output.log"

# The three hosts required by the MCO2 specification:
HOST1="google.com"
HOST2="dlsu.instructure.com"
HOST3="www.dlsu.edu.ph"   # bare dlsu.edu.ph has no A record (verified with dig)

banner() {
    echo ""                                                                 | tee -a "$LOGFILE"
    echo "===================================================================" | tee -a "$LOGFILE"
    echo "  $1"                                                             | tee -a "$LOGFILE"
    echo "===================================================================" | tee -a "$LOGFILE"
}

pause() {
    echo ""
    read -rp ">>> Take your screenshot, then press Enter for the next trace... " _
}

run_trace() {
    banner "$1"
    echo "\$ ${PYTHON} traceroute.py $2" | tee -a "$LOGFILE"
    echo "" | tee -a "$LOGFILE"
    "$PYTHON" "$TR" "$2" 2>&1 | tee -a "$LOGFILE"
    pause
}

if [[ $EUID -ne 0 ]]; then
    echo "ERROR: raw sockets need root privileges."
    echo "Re-run with:  sudo $0"
    exit 1
fi

if [[ ! -f "$TR" ]]; then
    echo "ERROR: could not find traceroute.py at: $TR"
    exit 1
fi

: > "$LOGFILE"

echo "MCO2 Traceroute - Test Runner"
echo "Log file: $LOGFILE"
echo "NOTE: a full 30-hop trace with timeouts can take a few minutes."
echo "      The bonus geolocation lookups add a little time per hop."
echo ""
read -rp "Press Enter to begin... " _

run_trace "TRACE 1: ${HOST1}" "$HOST1"
run_trace "TRACE 2: ${HOST2}" "$HOST2"
run_trace "TRACE 3: ${HOST3}" "$HOST3"

banner "ALL TRACES COMPLETE"
echo "A full text transcript was saved to: $LOGFILE"
echo "Now collect your screenshots for the documentation."
