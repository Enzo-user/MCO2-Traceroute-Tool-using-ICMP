# MCO2: Traceroute Tool Using ICMP — Documentation

**Student 1:** Lorenzo Enrique Suerte

**Student 2:** Christian Gabriel Sanidad

**Section:** S04

**Date:** _[Fill in]_

---

## 1. Overview

This document presents the test cases for a custom traceroute tool implemented in
Python using raw sockets. The program sends ICMP Echo Requests toward a destination
with an increasing time-to-live (TTL). Each router that decrements the TTL to zero
returns an ICMP Time Exceeded (type 11) message revealing its IP address; the final
destination answers with an ICMP Echo Reply (type 0), which ends the trace. For every
hop the program records and displays the hop number, round-trip time (RTT) in
milliseconds, and the responding IP address.

The ICMP packet construction and checksum are reused from our MCO1 submission
(Custom Ping Utility Using ICMP), as permitted by the specification.

**Bonus implemented — IP Geolocation:** each responding hop is looked up via the
ip-api.com service and its City, Region, Country, and Organization (ISP) are shown
beside the IP address.

**Test environment:** Windows 11 (25H2), Python 3.12.10. All tests were run from an
Administrator terminal because raw sockets require elevated privileges. Windows
Defender Firewall was configured to allow inbound ICMP replies for the duration of
the tests, per the assignment reminders.

---

## 2. Test Cases

### 2.1 Trace 1 — google.com

Command: `python traceroute.py google.com`

_[Insert screenshot here]_

**Description:** _[Describe: resolved IP, number of hops to reach the destination,
notable hops (your home router first, then ISP routers), any timed-out hops shown
as * * *, and the geolocation info displayed. Confirm the trace terminated with
"Trace complete" on an Echo Reply.]_

### 2.2 Trace 2 — dlsu.instructure.com

Command: `python traceroute.py dlsu.instructure.com`

_[Insert screenshot here]_

**Description:** _[Describe results as above. Instructure is hosted on cloud
infrastructure (typically AWS), which the geolocation Organization field should
reveal. Note: some cloud hosts do not answer ICMP Echo Requests — if the trace ends
with repeated * * * rows up to 30 hops, state that the destination suppresses ICMP
replies while the intermediate hops were still recorded.]_

### 2.3 Trace 3 — dlsu.edu.ph

Command: `python traceroute.py dlsu.edu.ph`

_[Insert screenshot here]_

**Description:** _[Describe results as above. As a Philippine host, the route should
stay comparatively short and the geolocation should show Philippine networks —
contrast this with the international routes of the other two traces.]_

---

## 3. Bonus: IP Geolocation — Implementation

For each hop that responds with an IP address, the program queries the free
ip-api.com JSON endpoint:

```
http://ip-api.com/json/<hop-ip>?fields=status,city,regionName,country,org
```

Implementation details:

- The lookup is done with Python's standard-library `urllib.request` (no external
  packages needed) with a 3-second timeout.
- The City, Region, and Country are joined into a location string, and the
  Organization (ISP or hosting provider) is appended after a dash, e.g.
  `[Quezon City, NCR, Philippines - Philippine Long Distance Telephone Co.]`.
- **Private addresses** (e.g. `192.168.x.x`, the first hop through a home router)
  are detected with the `ipaddress` module and labeled `[Private network]` without
  wasting an API call — private addresses have no public geolocation.
- **Caching:** results are cached per IP in a dictionary, so repeated hops cost only
  one request. With at most 30 hops per trace, this stays well within ip-api.com's
  free-tier limit of 45 requests per minute.
- **Graceful degradation:** any lookup failure (no internet for the API, timeout,
  rate limit) prints `[Geo lookup unavailable]` and never affects the trace itself.

_[Insert screenshot showing geolocation output here, if not already visible in the
Section 2 screenshots]_

---

## 4. Declaration of Tools and AI Use

**Tools used**

- Operating System: Windows 11 (25H2)
- Programming Language: Python 3.12.10
- Terminal: _[e.g. Windows Terminal / Command Prompt (run as administrator)]_
- Text editor / IDE: VS Code
- Screenshot tool: _[e.g. Snipping Tool (Win+Shift+S)]_
- AI assistant: Claude (Anthropic)

**How AI was used**

_[Describe accurately how Claude was used for MCO2 — e.g.: Claude was used to
complete the fill-in sections of the provided traceroute skeleton, repair syntax
errors in the skeleton's response-handling structure, adapt the MCO1 packet
construction for reuse, implement the IP geolocation bonus, and draft this
documentation. Adjust to reflect your actual workflow.]_

**Prompts used**

> _(Replace/extend with your exact prompts.)_

1. "My professor mentioned we could reuse the submitted MCO1 Source code for our
   MCO2 output. Here are the specs for MCO2. Create the required deliverables for
   MCO2. I would also like you to test the modified source code for MCO2 through
   Wireshark like what you did earlier when validating my MCO1 submission."

---

## 5. References

1. Postel, J. (1981). *RFC 792: Internet Control Message Protocol.* Internet
   Engineering Task Force. https://www.rfc-editor.org/rfc/rfc792
2. Malkin, G. (1993). *RFC 1393: Traceroute Using an IP Option.* Internet
   Engineering Task Force. https://www.rfc-editor.org/rfc/rfc1393
3. Python Software Foundation. *socket — Low-level networking interface.* Python 3
   documentation. https://docs.python.org/3/library/socket.html
4. Python Software Foundation. *struct — Interpret bytes as packed binary data.*
   Python 3 documentation. https://docs.python.org/3/library/struct.html
5. Python Software Foundation. *ipaddress — IPv4/IPv6 manipulation library.*
   Python 3 documentation. https://docs.python.org/3/library/ipaddress.html
6. IP-API. *IP Geolocation API documentation.* https://ip-api.com/docs
7. Kurose, J. F., & Ross, K. W. (2021). *Computer Networking: A Top-Down Approach*
   (8th ed.). Pearson. (ICMP Ping / Traceroute Labs.)
