"""
MCO2: Traceroute Tool Using ICMP
================================

A simplified traceroute implemented in Python with raw sockets. It sends ICMP
Echo Requests (type 8) toward a destination with an increasing IP time-to-live
(TTL). Each router that decrements the TTL to zero returns an ICMP Time
Exceeded (type 11) message, revealing its IP address; the final destination
answers the Echo Request with an Echo Reply (type 0), ending the trace.

The packet construction and checksum are reused from MCO1 (Custom Ping Utility
Using ICMP), as allowed by the specification.

Features
--------
* Sends ICMP Echo Requests with incrementing TTL values (1 up to MAX_HOPS).
* Receives and decodes ICMP Time Exceeded (11), Destination Unreachable (3),
  and Echo Reply (0) messages.
* Records the IP address and RTT of every responding hop.
* Terminates upon reaching the destination or after MAX_HOPS.
* BONUS - IP geolocation: each responding hop is looked up on ip-api.com and
  its City / Region / Country and Organization (ISP) are displayed.

Usage
-----
    sudo python3 traceroute.py [host]

    host  destination hostname or IP (default: google.com)

Raw sockets require root privileges, so run with sudo.
"""

from socket import *
import os
import sys
import struct
import time
import select
import binascii
import json
import ipaddress
import urllib.request

ICMP_ECHO_REQUEST = 8
MAX_HOPS = 30
TIMEOUT = 2.0
TRIES = 2
GEOLOCATE = True          # BONUS: set False to disable ip-api.com lookups

# The packet that we shall send to each router along the path is the ICMP echo
# request packet, which is exactly what we had used in the ICMP ping exercise.
# We shall use the same packet that we built in the Ping exercise.


def checksum(source):
    """Standard Internet checksum (RFC 1071) - reused from the MCO1 ping lab.

    Computed over the ICMP header (checksum field zeroed) plus payload, in
    Python 3 style: `source` is a bytes object, whose items are already ints.
    """
    csum = 0
    countTo = (len(source) // 2) * 2
    count = 0

    while count < countTo:
        thisVal = source[count + 1] * 256 + source[count]
        csum = csum + thisVal
        csum = csum & 0xffffffff
        count = count + 2
    if countTo < len(source):
        csum = csum + source[len(source) - 1]
        csum = csum & 0xffffffff
    csum = (csum >> 16) + (csum & 0xffff)
    csum = csum + (csum >> 16)
    answer = ~csum
    answer = answer & 0xffff
    answer = answer >> 8 | (answer << 8 & 0xff00)
    return answer


def build_packet():
    """Build one complete ICMP Echo Request packet (header + timestamp data).

    Same construction as sendOnePing() in MCO1: make a header with a zero
    checksum, append the timestamp payload, compute the real checksum over
    header+data, then rebuild the header with the checksum filled in.
    The packet is returned, not sent.
    """
    myChecksum = 0
    myID = os.getpid() & 0xFFFF

    # Make the header in a similar way to the ping exercise.
    header = struct.pack("bbHHh", ICMP_ECHO_REQUEST, 0, myChecksum, myID, 1)
    data = struct.pack("d", time.time())

    # Append checksum to the header.
    myChecksum = checksum(header + data)
    if sys.platform == 'darwin':
        myChecksum = htons(myChecksum) & 0xffff
    else:
        myChecksum = htons(myChecksum)
    header = struct.pack("bbHHh", ICMP_ECHO_REQUEST, 0, myChecksum, myID, 1)

    # Don't send the packet yet, just return the final packet in this function.
    packet = header + data
    return packet


# --------------------------------------------------------------------------
# BONUS: IP geolocation via ip-api.com
# --------------------------------------------------------------------------
_geo_cache = {}


def get_geo(ip):
    """Return 'City, Region, Country - Organization' for a hop IP (BONUS).

    Private/reserved addresses are labeled locally without an API call.
    Results are cached so repeated hops cost one request. Failures degrade
    gracefully to an empty string so the trace itself is never affected.
    """
    if not GEOLOCATE:
        return ""
    if ip in _geo_cache:
        return _geo_cache[ip]

    try:
        if ipaddress.ip_address(ip).is_private:
            geo = "[Private network]"
            _geo_cache[ip] = geo
            return geo
    except ValueError:
        return ""

    url = ("http://ip-api.com/json/%s?fields=status,city,regionName,country,org"
           % ip)
    try:
        with urllib.request.urlopen(url, timeout=3) as resp:
            info = json.loads(resp.read().decode())
        if info.get("status") == "success":
            place = ", ".join(x for x in
                              (info.get("city"), info.get("regionName"),
                               info.get("country")) if x)
            org = info.get("org") or ""
            geo = "[%s%s]" % (place, (" - " + org) if org else "")
        else:
            geo = "[Location unknown]"
    except Exception:
        geo = "[Geo lookup unavailable]"

    _geo_cache[ip] = geo
    return geo


def get_route(hostname):
    """Trace the route to `hostname`, printing hop number, RTT, IP, and geo."""
    destAddr = gethostbyname(hostname)
    print("Traceroute to %s [%s], %d hops max:" % (hostname, destAddr, MAX_HOPS))
    print("")

    for ttl in range(1, MAX_HOPS + 1):
        reached = False
        printed = False

        for tries in range(TRIES):
            # Fill in start
            # Make a raw socket named mySocket
            mySocket = socket(AF_INET, SOCK_RAW, getprotobyname("icmp"))
            # Fill in end
            mySocket.setsockopt(IPPROTO_IP, IP_TTL, struct.pack('I', ttl))
            mySocket.settimeout(TIMEOUT)
            try:
                d = build_packet()
                mySocket.sendto(d, (destAddr, 0))
                t = time.time()
                startedSelect = time.time()
                whatReady = select.select([mySocket], [], [], TIMEOUT)
                howLongInSelect = (time.time() - startedSelect)

                if whatReady[0] == []:   # Timeout on this try
                    continue

                # A raw ICMP socket also sees our OWN Echo Request when it is
                # looped back (e.g. tracing 127.0.0.1), so keep reading until
                # a packet that is not our outgoing type-8 request arrives.
                timeLeft = TIMEOUT
                while True:
                    recvPacket, addr = mySocket.recvfrom(1024)
                    timeReceived = time.time()
                    if recvPacket[20] != ICMP_ECHO_REQUEST:
                        break                      # a real answer
                    timeLeft = TIMEOUT - (timeReceived - t)
                    if timeLeft <= 0:
                        raise timeout()
                    whatReady = select.select([mySocket], [], [], timeLeft)
                    if whatReady[0] == []:
                        raise timeout()

            except timeout:
                continue

            else:
                # Fill in start
                # Fetch the icmp type from the IP packet: the ICMP header
                # begins right after the 20-byte IP header, and its first
                # byte is the Type field.
                types, code = struct.unpack("bb", recvPacket[20:22])
                # Fill in end

                rtt_ms = (timeReceived - t) * 1000
                geo = get_geo(addr[0])

                if types == 11:
                    # Time Exceeded: an intermediate router.
                    print(" %2d    rtt=%6.2f ms    %-15s  %s"
                          % (ttl, rtt_ms, addr[0], geo))
                    printed = True
                    break

                elif types == 3:
                    # Destination Unreachable.
                    print(" %2d    rtt=%6.2f ms    %-15s  %s  "
                          "(Destination Unreachable, code %d)"
                          % (ttl, rtt_ms, addr[0], geo, code))
                    printed = True
                    reached = True     # no point probing further
                    break

                elif types == 0:
                    # Echo Reply: the final destination answered.
                    print(" %2d    rtt=%6.2f ms    %-15s  %s"
                          % (ttl, rtt_ms, addr[0], geo))
                    print("")
                    print("Trace complete: reached %s in %d hops." % (addr[0], ttl))
                    printed = True
                    reached = True
                    break

                else:
                    print(" %2d    unexpected ICMP type %d from %s"
                          % (ttl, types, addr[0]))
                    printed = True
                    break

            finally:
                mySocket.close()

        if not printed:
            print(" %2d    *  *  *    Request timed out." % ttl)

        if reached:
            return

    print("")
    print("Trace incomplete: maximum of %d hops reached." % MAX_HOPS)


if __name__ == '__main__':
    target = sys.argv[1] if len(sys.argv) > 1 else "google.com"
    get_route(target)
