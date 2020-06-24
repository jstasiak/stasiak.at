A semi-paranoid multi-LAN WireGuard VPN
#######################################

:date: 2020-06-24 20:00
:tags: wireguard, networking, security

Introduction
============

I'd had two LAN-s I'd wanted to connect using a VPN and recently a time came to make this happen
(partially forced by the fact that I'd also wanted to set up a robust backup solution, more about this
in a blog post soon).

Now, I'd also heard a lot of interesting things about `WireGuard <https://www.wireguard.com/>`_ from
`Krzysztof Urbaniak <http://urbaniak.me/>`_ (who also helped me considerably with setting this whole
thing up by providing some crucial information and answering my random questions) so I decided to go
with WireGuard.

I have two annoyances to deal with, otherwise it'd have been too easy:

1. I can't install WireGuard on the routers as they aren't supported by modern DD-WRT, OpenWRT or any
   other open router firmware projects.
2. My ISP (the same one at both locations) is terrible. It doesn't support IPv6 (insert meme about it
   being year 2020 already) but it also shares IPv4 addresses between customers, which not only means
   that I can't connect to my devices from the outside (the ISP has a separete, special "business"
   tier for this) but also has the fun consequence that if of my IPv4-address-mates is being naughty
   on the Internet and gets the IP address banned on some service(s) I too am banned now.

Fortunately I have always-on devices in both of those networks and they both perform server-like roles
already and I have access to an VM with a public IP address (I mean who doesn't these days) so all's
well, it's just few more moving parts.

So, the situation before setting up a VPN looks like this:

* An VM with a public IP address
* LAN 1 (network ``192.168.1.0/24``) and within the LAN:

  * Router 1 (``192.168.1.1``)
  * Server 1 (``192.168.1.2``)
* LAN 2 (network ``192.168.2.0/24``) and within the LAN:

  * Router 2 (``192.168.2.1``)
  * Server 2 (``192.168.2.2``)

Both Router 1 and Router 2 are the default gateways of their respective networks.


WireGuard Installation
======================

The VM, Server 1 and Server 2 all run reasonably modern Debian or its derivatives (Raspbian, Ubuntu)
with (for better or for worse) systemd, so WireGuard installation and tunnel setup look almost the
same on all three of those devices.

All of those systems have WireGuard in their repositories, so a mere

::

    apt install wireguard

is enough to get WireGuard installed.

Setting up a tunnel
===================

First, let's enable IP forwarding because we'll be routing stuff. We need to modify
``/etc/sysctl.conf`` to have ``net.ipv4.ip_forward=1`` present and activate the configuration::

    # Modify the files in an editor of your choice here
    ...

    # Confirm the configuration is there
    root@vm:~# cat /etc/sysctl.conf | grep net.ipv4.ip_forward
    net.ipv4.ip_forward=1

    root@server1:~# cat /etc/sysctl.conf | grep net.ipv4.ip_forward
    net.ipv4.ip_forward=1

    root@server2:~# cat /etc/sysctl.conf | grep net.ipv4.ip_forward
    net.ipv4.ip_forward=1

    # Activate the forwarding
    root@vm:~# sysctl -p
    root@server1:~# sysctl -p
    root@server2:~# sysctl -p

(I only need IPv4 so I'll leave IPv6-related configuration as an exercise for the reader).

    
First we need to generate WireGuard keypairs (the ``umask`` calls are there so that other users
and other users' processes can't read the keys. Yes, those are trusted machines running trusted
software and only accessed by trusted people. Call me paranoid, but I like practicing both
`layered security <https://en.wikipedia.org/wiki/Layered_security>`_ and `princinple of least
privilege <https://en.wikipedia.org/wiki/Principle_of_least_privilege>`_ because they offer
substantial benefits in case of a security incident)::

    root@vm:~# umask 077 && \
        wg genkey | tee vm-privatekey | wg vm-pubkey > vm-publickey

    root@server1:~# umask 077 && \
        wg genkey | tee server1-privatekey | wg server1-pubkey > server1-publickey

    root@server2:~# umask 077 && \
        wg genkey | tee server2-privatekey | wg server2-pubkey > server2-publickey

Now, the tunnel configuration. WireGuard configuration files look like this::

    [Interface]
    # Our private key
    PrivateKey = ...

    # Our address within the tunnel
    Address = ...

    # Optional port for listening, random by default
    ListenPort = ...

    # Optional commands to run after the tunnel is set up and torn down
    PostUp = ...
    PostDown = ...

    [Peer]
    # The public key of the other peer
    PublicKey = ...

    # Networks that we can reach through the peer (more below)
    AllowedIPs = ...

    # Optional address of the other peer, if we don't have a public
    # IP address we need the other peer to have it and to specify it here
    Endpoint = ...

    # This enables sending keepalive packets every n seconds. If you're
    # behind a terrible NAT (or NAT, for short), a bad firewall or otherwise
    # using a terrible ISP (like I do) you likely need this. 0 by default,
    # WireGuard documentation recommends 25 seconds if this needs a value.
    PersistentKeepalive = ...

Side note: the piece of information that really helped me understand how to interpret and
work with ``AllowedIPs`` is the following phrase from `How to easily configure WireGuard
by Stavros Korokithakis <https://www.stavros.io/posts/how-to-configure-wireguard/>`_ (which links
to `the relevant part of WireGuard documentation <https://www.wireguard.com/#cryptokey-routing>`_):

    Briefly, the AllowedIPs setting acts as a routing table when sending, and an ACL when receiving. 

You'll soon see how this combines with other pieces. Given the information above I have the following
configuration files (stored in a standard ``/etc/wireguard/wg0.conf`` location on every of the three
nodes):

Server 1::

    [Interface]
    PrivateKey = <the content of server1-privatekey>
    Address = 10.0.0.1/24

    [Peer]
    PublicKey = <the content of vm-publickey>
    AllowedIPs = 10.0.0.0/24
    Endpoint = <public IP of VM>:51820
    PersistentKeepalive = 25

Server 2::

    [Interface]
    PrivateKey = <the content of server2-privatekey>
    Address = 10.0.0.2/24

    [Peer]
    PublicKey = <the content of vm-publickey>
    AllowedIPs = 10.0.0.0/24
    Endpoint = <public IP of VM>:51820
    PersistentKeepalive = 25

VM::

    [Interface]
    Address = 10.0.0.3/24
    ListenPort = 51820
    PrivateKey = <the content of vm-privatekey>

    [Peer]
    # Server 1
    AllowedIPs = 10.0.0.1/32
    PublicKey = <the content of server1-publickey>

    [Peer]
    # Server 2
    AllowedIPs = 10.0.0.2/32
    PublicKey = <the content of server2-publickey>

Now let's enable the tunnel by running the following command on all three nodes (thanks to the
``wg-quick`` systemd helper it'll be persistent)::

    systemctl enable wg-quick@wg0

Let's test it now.

Server 1 -> VM communication::

    root@server1:~# ping -c 1 10.0.0.3
    PING 10.0.0.3 (10.0.0.3) 56(84) bytes of data.
    64 bytes from 10.0.0.3: icmp_seq=1 ttl=64 time=8.59 ms

    --- 10.0.0.3 ping statistics ---
    1 packets transmitted, 1 received, 0% packet loss, time 0ms
    rtt min/avg/max/mdev = 8.586/8.586/8.586/0.000 ms

Server 2 -> VM communication::

    root@server2:~# ping -c 1 10.0.0.3
    PING 10.0.0.3 (10.0.0.3) 56(84) bytes of data.
    64 bytes from 10.0.0.3: icmp_seq=1 ttl=64 time=8.74 ms

    --- 10.0.0.3 ping statistics ---
    1 packets transmitted, 1 received, 0% packet loss, time 0ms
    rtt min/avg/max/mdev = 8.743/8.743/8.743/0.000 ms

Server 1 -> Server 2 communication::

    root@server1:~# ping -c 1 10.0.0.2
    PING 10.0.0.2 (10.0.0.2) 56(84) bytes of data.
    64 bytes from 10.0.0.2: icmp_seq=1 ttl=63 time=16.3 ms

    --- 10.0.0.2 ping statistics ---
    1 packets transmitted, 1 received, 0% packet loss, time 0ms
    rtt min/avg/max/mdev = 16.251/16.251/16.251/0.000 ms

Server 2 -> Server 1 communication::

    root@server2:~# ping -c 1 10.0.0.1
    PING 10.0.0.1 (10.0.0.1) 56(84) bytes of data.
    64 bytes from 10.0.0.1: icmp_seq=1 ttl=63 time=17.2 ms

    --- 10.0.0.1 ping statistics ---
    1 packets transmitted, 1 received, 0% packet loss, time 0ms
    rtt min/avg/max/mdev = 17.160/17.160/17.160/0.000 ms

So we have basic communication working and the timings are good.

We have to go deeper
====================

Now that we have a tunnel set up the obvious thing would be to:

* Add ``192.168.1.0/24`` (LAN 1) to ``AllowedIPs`` of the ``10.0.0.1`` peer (Server 1) on VM
* Add ``192.168.2.0/24`` (LAN 2) to ``AllowedIPs`` of the ``10.0.0.2`` peer (Server 2) on VM
* Add ``192.168.1.0/24`` (LAN 1) to ``AllowedIPs`` of the ``10.0.0.3`` peer (VM) on Server 2
* Add ``192.168.2.0/24`` (LAN 2) to ``AllowedIPs`` of the ``10.0.0.3`` peer (VM) on Server 1
* Add a route passing all traffic directed to ``192.168.1.0/24`` (LAN 1) to ``192.168.2.2``
  (Server 2) on Router 1
* Add a route passing all traffic directed to ``192.168.2.0/24`` (LAN 2) to ``192.168.1.2``
  (Server 1) on Router 2
* Set ``10.0.0.1`` as gateway to ``192.168.1.0/24`` (LAN 1)
* Set ``10.0.0.2`` as gateway to ``192.168.2.0/24`` (LAN 2)

There's one issue with this setup: the VM peer is on equal rights with Server 1 and Server 2
and participates in routing the unencrypted traffic between the LAN-s. "So what?", I hear you
say, "You already trust the VM with some sensitive data, I bet, and networks should really be
trusted anyway". That's 100% correct. And yet I like to put multiple layers of security
between me and absolute pwnage.

I thought about this for a few minutes and figured, since I can directly address Server 2 from
Server 1 and vice versa I can establish another network with only two peers involved (Server 2
connecting directly to Server 1 and Server 1 to Server 2). I asked Krzysztof (as he's way more
fluent in networking) about setting up a tunnel inside a tunnel and the answer wasn't a strong
"this is insane" so I went ahead with this.

Digging a tunnel inside another tunnel
======================================

This turned out to be pretty straightforward. First we need to generate a new set of keypairs::

    root@server1:~# umask 077 && \
        wg genkey | tee server1-privatekey2 | wg server1-pubkey2 > server1-publickey2

    root@server2:~# umask 077 && \
        wg genkey | tee server2-privatekey2 | wg server2-pubkey2 > server2-publickey2


Since we can access Server 1 via ``10.0.0.1`` and Server 2 via ``10.0.0.2`` the following
configuration of a second tunnel is possible (``/etc/wireguard/wg1.conf``):

Server 1::

    [Interface]
    PrivateKey = <the content of server1-privatekey2>
    Address = 10.0.1.1/24
    ListenPort = 51820

    [Peer]
    PublicKey = <the content of server2-publickey2>
    AllowedIPs = 10.0.1.2/24
    Endpoint = 10.0.0.2:51820
    PersistentKeepalive = 25

Server 2::

    [Interface]
    PrivateKey = <the content of server2-privatekey2>
    Address = 10.0.1.2/24
    ListenPort = 51820

    [Peer]
    PublicKey = <the content of server1-publickey2>
    AllowedIPs = 10.0.1.1/24
    Endpoint = 10.0.0.1:51820
    PersistentKeepalive = 25

OK, let's activate the tunnel (run this on both Server 1 and Server 2)...

::

    systemctl enable wg-quick@wg0

...and verify it's working

Server 1 -> Server 2 via the internal tunnel::

    root@server1:~# ping -c 1 10.0.1.2
    PING 10.0.1.2 (10.0.1.2) 56(84) bytes of data.
    64 bytes from 10.0.1.2: icmp_seq=1 ttl=64 time=17.2 ms

    --- 10.0.1.2 ping statistics ---
    1 packets transmitted, 1 received, 0% packet loss, time 0ms
    rtt min/avg/max/mdev = 17.231/17.231/17.231/0.000 ms

Server 2 -> Server 1 via the internal tunnel::

    root@server2:~# ping -c 1 10.0.1.1
    PING 10.0.1.1 (10.0.1.1) 56(84) bytes of data.
    64 bytes from 10.0.1.1: icmp_seq=1 ttl=64 time=17.4 ms

    --- 10.0.1.1 ping statistics ---
    1 packets transmitted, 1 received, 0% packet loss, time 0ms
    rtt min/avg/max/mdev = 17.440/17.440/17.440/0.000 ms

Good! We have Server 1 <-> Server 2 communication that's encrypted as far as VM is concerned – VM
can shut the communication down but it can't intercept unencrypted traffic or inject traffic of
its own into LAN-s.

On to routing
=============

We're almost there. From the point of view of Server 1 we want the Server 2 peer to be able to send us
traffic from LAN 2 and we want to send LAN 2 traffic to Server 2. Same thing in the opposite direction.
We also want to enable forwarding in our firewall configuration, just in case it's denied by default
(and I will be), we'll use the ``PostUp`` and ``PostUp`` WireGuard settings to achieve that. So the
relevant parts of ``/etc/wireguard/wg1.conf`` will read (``eth0`` is the physical interface on both
Server 1 and Server 2):

Server 1::

    [Interface]
    ...
    PostUp = iptables -A FORWARD -i wg1 -j ACCEPT; iptables -A FORWARD -i eth0 -j ACCEPT
    PostDown = iptables -D FORWARD -i wg1 -j ACCEPT; iptables -D FORWARD -i eth0 -j ACCEPT

    [Peer]
    ...
    AllowedIPs = 10.0.1.2/24, 192.168.2.0/24

Server 2::

    [Interface]
    ...
    PostUp = iptables -A FORWARD -i wg1 -j ACCEPT; iptables -A FORWARD -i eth0 -j ACCEPT
    PostDown = iptables -D FORWARD -i wg1 -j ACCEPT; iptables -D FORWARD -i eth0 -j ACCEPT

    [Peer]
    ...
    AllowedIPs = 10.0.1.1/24, 192.168.1.0/24

Let's restart the tunnel to activate the changes (ignore the errors this time – the ``iptables -D``
commands will try to remove firewall rules that aren't there yet, it'll just happen once)::

    wg-quick down wg1; wg-quick up wg1

Now we need to set up some routes on the routers:

* On Router 1 – traffic with destination ``10.0.1.0/24`` or ``192.168.2.0/24`` goes to ``192.168.1.2``
* On Router 2 – traffic with destination ``10.0.1.0/24`` or ``192.168.1.0/24`` goes to ``192.168.2.2``

The configuration is complete now!

Pinging a device in LAN 2 from LAN 1 (device with address ``192.168.1.3``)::

    % ping -c 1 192.168.2.5
    PING 192.168.2.5 (192.168.2.5): 56 data bytes
    64 bytes from 192.168.2.5: icmp_seq=0 ttl=62 time=20.453 ms

    --- 192.168.2.5 ping statistics ---
    1 packets transmitted, 1 packets received, 0.0% packet loss
    round-trip min/avg/max/stddev = 20.453/20.453/20.453/0.000 ms

The other way, LAN 2 (device with address ``192.168.2.5``) -> LAN 1::

    % ping -c 1 192.168.1.3
    PING 192.168.1.3 (192.168.1.3): 56 data bytes
    64 bytes from 192.168.1.3: icmp_seq=0 ttl=62 time=19.743 ms

    --- 192.168.1.3 ping statistics ---
    1 packets transmitted, 1 packets received, 0.0% packet loss
    round-trip min/avg/max/stddev = 19.743/19.743/19.743/0.000 ms

Summary
=======

I hope this explanation is thorough enough that it can help others set up something similar, which I'd
really recommend – WireGuard is awesome. There's one thing that I left for later and it's about connecting
to the VPN from the outside, from my phone or from my laptop when I'm away from the LAN-s.

I'll write another post about this as it's an important use case for me – I'd like to be able to use
`Pi-Hole <https://pi-hole.net/>`_ servers I have set up in both LAN-s (I don't care about routing the
actual traffic through the VPN when accessing the public Internet) from arbitrary networks.

I've been using the setup described in this post for more than half a year now and it's been rock solid.
