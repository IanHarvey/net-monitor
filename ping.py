#!/usr/bin/env python

# Utility to continuously ping a range of IP addresses and record
# results in a .csv output file.

# This code is placed in the public domain by its author, Ian Harvey
# It comes with NO WARRANTY.

import os, sys, time
import select
import socket
import struct
import re
import site_config
   
class EchoRequest:
    ICMP_ECHO = 8
    def __init__(self, hostname, ident, sequence, payload='\x55' * 56):
        self.hostname = hostname
        self.destAddr = socket.gethostbyname(hostname)
        packet = struct.pack("!BBHHH", self.ICMP_ECHO, 0, 0, ident, sequence) + payload
        checksum = self.getChecksum(packet)
        self.packet = packet[0:2] + struct.pack("!H", checksum) + packet[4:]
        self.ID = (ident << 16) | sequence
        self.delay = None

    @staticmethod 
    def getChecksum(packet):
        if (len(packet) & 1) != 0:
            packet += '\x00'
        csum = sum([ (ord(packet[i+1]) << 8) + ord(packet[i]) for i in range(0, len(packet), 2) ]) & 0xFFFFFFFF
        # Random twiddling, cf. in_cksum() in ping.c
        csum = (csum >> 16) + (csum & 0xFFFF);
        csum += (csum >> 16)
        csum = socket.htons((~csum) & 0xFFFF)
        return csum
        
    def getId(self):
        return self.ID
        
    def send(self, sock):
        self.sendTime = time.time()
        sock.sendto(self.packet, (self.destAddr, 1))

    def checkResponse(self, receiveTime, fromAddr, packet):
        # TODO: Check packet and address
        self.delay = receiveTime - self.sendTime

    def getDelay(self):
        return self.delay

    def show(self):
        if self.delay==None:
            print self.hostname, "did not reply"
        else:
            print self.hostname, "replied in %5.1f ms" % (self.delay*1000.0)

        
class Pinger:
    def __init__(self, timeout=1.0, packet_size=56):
        self.timeout = timeout
        self.packet_size = packet_size
        self.own_id = os.getpid() & 0xFFFF

        self.seq_number = 0
        self.socket = socket.socket(socket.AF_INET, socket.SOCK_RAW, socket.getprotobyname("icmp"))

    #--------------------------------------------------------------------------

    def ping(self, destlist):
        """
Send one ICMP ECHO_REQUEST and receive the response until self.timeout
"""
        reqs = {}
        reqlist = []
        for dest in destlist:
            self.seq_number = (self.seq_number + 1) & 0xFFFF
            req = EchoRequest(dest, self.own_id, self.seq_number, "\x55" * self.packet_size)
            reqs[req.getId()] = req
            reqlist.append(req)

        for req in reqlist:
            req.send(self.socket)

        stopTime = time.time() + self.timeout
                
        while True: # Loop while waiting for packet or timeout
            maxWait = stopTime - time.time()
            if maxWait <= 0.0:
                break

            (inputs, _, _) = select.select([self.socket], [], [], maxWait)
            receiveTime = time.time()

            for sock in inputs:
                (packet, fromAddr) = self.socket.recvfrom(2048)
                (_, _, _, ident, sequence) = struct.unpack("!BBHHH", packet[20:28])

                pkid = (ident << 16) | sequence
                if pkid in reqs:
                    reqs[pkid].checkResponse(receiveTime, fromAddr, packet)
                else:
                    pass
                    #print "Unknown reply from", fromAddr, "ident", hex(pkid)

            # Early exit if we got everybody
            if len([r for r in reqlist if r.getDelay()==None])==0:
                break
                
        return reqlist

class ARP:
    ARP_FILE="/proc/net/arp"
    re_IPV4 = re.compile("(\d+.\d+.\d+.\d+)\s+")
    
    def __init__(self):
        self.reset()

    def reset(self):
        self.arpTable = {}

    def _update(self):
        with open(self.ARP_FILE, "r") as f:
            for line in f:
                m = self.re_IPV4.match(line)
                if m == None:
                    continue
                (ip, hwtype, flags, addr, mask, device) = line.split()
                if flags != "0x0" and addr != "00:00:00:00:00:00":
                    self.arpTable[ip] = addr

    def getMacAddress(self, ip):
        if ip in self.arpTable:
            return self.arpTable[ip]
        self._update()
        return self.arpTable.get(ip, "-")

def doPing(args):
    p = Pinger(timeout=2)
    firstIp = struct.unpack("!L", socket.inet_aton(site_config.first_ip)) [0]
    lastIp = struct.unpack("!L", socket.inet_aton(site_config.last_ip)) [0]

    toDo = [ socket.inet_ntoa(struct.pack("!L", ip)) 
                   for ip in range(firstIp, lastIp+1) ]

    missing = []
    contacted = []
    arp = ARP()

    print "ping.py: Address range", toDo[0], "...", toDo[-1]

    while True:
        if len(toDo) > 0:
            # Try to contact a few
            resplist = p.ping(toDo[0:10])
            toDo = toDo[10:]
            missing += [ r.hostname for r in resplist if r.getDelay()==None ]
            contacted += [ r.hostname for r in resplist if r.getDelay() != None ]
            continue
            
        arp.reset()
        print "\nResults:"
        lines = ""
        (dayNow, timeNow) = time.strftime("%Y%m%d %H%M%S").split()
        for host in contacted:
            resp = p.ping([host]) [0]
            if resp.getDelay() == None:
                print "Lost", host
                continue
            mac = arp.getMacAddress(host)
            line = ",".join([timeNow,host,mac,"%.1f" % (resp.getDelay()*1000)])
            print line
            lines += line + "\n"
        if len(lines) > 0:
            args={ 'date':dayNow, 'time':timeNow }
            fname = site_config.input_file % args
            with open(fname, "a") as f:
                f.write(lines)
            print "Wrote", fname
        print "ping.py Rescanning",
        toDo = missing
        missing = []
        

if __name__ == '__main__':
    doPing(sys.argv[1:])

