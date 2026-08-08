# MCO2: Traceroute Tool Using ICMP

A simplified traceroute network diagnostic tool written in pure Python using raw
sockets. It maps the path packets take to a destination by sending ICMP Echo
Requests with an increasing time-to-live (TTL): each router that decrements the
TTL to zero reveals itself with an ICMP Time Exceeded message, and the final
destination ends the trace by answering with an ICMP Echo Reply.

## Overview

The program builds on our MCO1 submission (Custom Ping Utility Using ICMP): the
ICMP packet construction and Internet checksum are reused directly, as permitted
by the specification. What is new in MCO2 is the TTL loop and the classification
of the three ICMP message types that a traceroute must understand:

| ICMP Type | Meaning                  | What the program does                    |
| --------- | ------------------------ | ---------------------------------------- |
| 11        | Time Exceeded            | Records the intermediate router and RTT  |
| 3         | Destination Unreachable  | Reports it and stops probing             |
| 0         | Echo Reply               | Destination reached — trace complete     |

## Features

- Sends ICMP Echo Requests with incrementing TTL values (1 up to `MAX_HOPS`, 30).
- Receives and decodes ICMP Time Exceeded (11), Destination Unreachable (3), and
  Echo Reply (0) messages.
- Records and displays each hop's number, RTT in milliseconds, and IP address.
- Retries each hop (`TRIES`, 2) and prints `*  *  *` when a hop never answers.
- Terminates upon reaching the destination or after the maximum TTL.
- **Bonus — IP Geolocation:** each responding hop is looked up on ip-api.com and
  its City, Region, Country, and Organization (ISP/hosting provider) are shown
  beside the IP. Private addresses (e.g. your home router) are detected locally
  and labeled `[Private network]`; results are cached per IP; lookup failures
  degrade gracefully without affecting the trace.

## Requirements

- Linux (developed and tested on **Fedora Linux 44**)
- **Python 3** (tested on Python 3.14.6); standard library only, no external packages
- **Root / administrator privileges** — raw sockets require them, so run with `sudo`
- Internet access for the geolocation bonus (the trace itself works without it)

## Project Files

| File                      | Description                                                      |
| ------------------------- | ---------------------------------------------------------------- |
| `traceroute.py`           | The completed traceroute tool (main program).                    |
| `run_tests_mco2.sh`       | Runs the three required traces with labeled output and a log.    |
| `traceroute_output.log`   | Text transcript produced by the test runner (generated at runtime). |
| `MCO2_Documentation.md`   | Documentation scaffold (screenshots, bonus write-up, declaration). |
| `README.md`               | This file.                                                       |

## Usage

```bash
sudo python3 traceroute.py [host]
```

**Arguments**

- `host` — destination hostname or IP address (default: `google.com`)

**Examples**

```bash
sudo python3 traceroute.py google.com
sudo python3 traceroute.py dlsu.instructure.com
sudo python3 traceroute.py dlsu.edu.ph
```

### Example output

```
Traceroute to google.com [142.251.220.142], 30 hops max:

  1    rtt=  1.52 ms    192.168.1.1      [Private network]
  2    rtt=  5.83 ms    100.85.0.1       [Private network]
  3    *  *  *    Request timed out.
  4    rtt=  6.10 ms    210.213.134.40   [Makati, NCR, Philippines - PLDT]
  ...
  8    rtt=  7.31 ms    142.251.220.142  [Singapore, Singapore - Google LLC]

Trace complete: reached 142.251.220.142 in 8 hops.
```

(Addresses, RTTs, and locations above are illustrative — your route will differ.)

## Running the Test Suite

`run_tests_mco2.sh` traces the three hosts required by the specification
(`google.com`, `dlsu.instructure.com`, `dlsu.edu.ph`), printing a banner before
each trace and pausing so you can capture a screenshot. Everything is also saved
to `traceroute_output.log`.

```bash
chmod +x run_tests_mco2.sh
sudo ./run_tests_mco2.sh
```

Note: a full 30-hop trace where many hops time out can take a few minutes —
that is normal, especially for cloud-hosted destinations that suppress ICMP.

## How It Works

1. **Build the probe** — `build_packet()` constructs the same ICMP Echo Request
   used in MCO1: an 8-byte header (type 8, code 0, checksum, id, sequence)
   followed by an 8-byte timestamp payload, with the RFC 1071 checksum computed
   over the whole packet.
2. **Limit its lifetime** — before sending, the IP TTL is set on the socket with
   `setsockopt(IPPROTO_IP, IP_TTL, ...)`. A packet with TTL *n* survives exactly
   *n* router hops.
3. **Listen for the answer** — when a router discards the expired packet it
   sends back ICMP Time Exceeded (type 11); its source address is that router.
   The ICMP type is read from byte 20 of the received datagram (the first byte
   after the 20-byte IP header).
4. **Measure RTT** — a timer started at send time is stopped when the reply
   arrives; the difference is the hop's round-trip time.
5. **Repeat and terminate** — the TTL increases hop by hop until the destination
   itself answers with an Echo Reply (type 0) or `MAX_HOPS` is reached.

## Implementation Notes

- The provided skeleton required repairs before it could run: the `checksum`
  body was empty, the response-classification block had broken indentation and a
  misplaced `return`, and the timeout path printed a message but still blocked
  on `recvfrom`. These were fixed while keeping the skeleton's structure and
  variable names.
- On loopback (e.g. tracing `127.0.0.1`), a raw ICMP socket also receives its
  *own outgoing Echo Request*. The receive loop therefore reads until a packet
  that is not our type-8 request arrives, within the timeout window.
- Geolocation uses only the standard library (`urllib.request`, `ipaddress`,
  `json`) and the free ip-api.com endpoint, staying under its 45 requests/minute
  limit via per-IP caching (a trace has at most 30 hops).

## Deliverables

- [x] Modified source code (`traceroute.py`)
- [ ] Screenshots of the three traces (google.com, dlsu.instructure.com, dlsu.edu.ph)
- [ ] Declaration of Tools and AI Use (with prompts)
- [ ] References

## References

- Postel, J. (1981). *RFC 792: Internet Control Message Protocol.* IETF.
  https://www.rfc-editor.org/rfc/rfc792
- Malkin, G. (1993). *RFC 1393: Traceroute Using an IP Option.* IETF.
  https://www.rfc-editor.org/rfc/rfc1393
- Python Software Foundation. *socket / struct / ipaddress* modules, Python 3
  documentation. https://docs.python.org/3/library/socket.html
- IP-API. *IP Geolocation API documentation.* https://ip-api.com/docs
- Kurose, J. F., & Ross, K. W. (2021). *Computer Networking: A Top-Down Approach*
  (8th ed.). Pearson. (ICMP Ping / Traceroute Labs.)
