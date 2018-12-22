from mininet.topo import Topo
from mininet.net import Mininet
from mininet.node import Node
from mininet.log import setLogLevel, info
from mininet.cli import CLI
from mininet.link import TCLink
from mininet.node import CPULimitedHost
from time import sleep
import time
import os

class LinuxRouter( Node ):
    "A Node with IP forwarding enabled."

    def config( self, **params ):
        super( LinuxRouter, self).config( **params )
        # Enable forwarding on the router
        self.cmd( 'sysctl net.ipv4.ip_forward=1' )

    def terminate( self ):
        self.cmd( 'sysctl net.ipv4.ip_forward=0' )
        super( LinuxRouter, self ).terminate()


class NetworkTopo( Topo ):
    "A LinuxRouter connecting three IP subnets"

    def build( self, **_opts ):
        router = self.addNode( 'R1', cls=LinuxRouter, ip='10.14.1.1/24')
        h1     = self.addHost( 'h1', ip='10.14.1.2/24')
        h2     = self.addHost( 'h2', ip='10.14.2.2/24')
        h3     = self.addHost( 'h3', ip='10.14.3.2/24')

    	#Koneksi antar host dengan router
    	self.addLink( h1, router, intfName2='R1-eth1', bw = 50)
    	self.addLink( h2, router, intfName2='R1-eth2', bw = 50)
       	self.addLink( h3, router, intfName2='R1-eth3', bw = 5, delay = '100ms', use_htb=True, max_queue_size=10)

def run():
    "Test linux router"

    os.system('mn -c')
    topo = NetworkTopo()

    net = Mininet( topo=topo, link=TCLink, host=CPULimitedHost )
    net.start()
    net[ 'h1' ].cmd('sysctl -w net.ipv4.tcp_congestion_control=vegas')
    net[ 'h2' ].cmd('sysctl -w net.ipv4.tcp_congestion_control=reno')

    net[ 'R1' ].cmd('ip addr add 10.14.1.1/24 brd + dev R1-eth1')
    net[ 'R1' ].cmd('ip addr add 10.14.2.1/24 brd + dev R1-eth2')
    net[ 'R1' ].cmd('ip addr add 10.14.3.1/24 brd + dev R1-eth3')

    net[ 'h1' ].cmd('ip route add default via 10.14.1.1')
    net[ 'h2' ].cmd('ip route add default via 10.14.2.1')
    net[ 'h3' ].cmd('ip route add default via 10.14.3.1')

    h1, h2, h3 = net.get('h1','h2','h3')
    h3.cmd('iperf -s&')
    h1.cmd('iperf -c 10.14.3.2 -i 1 -n 2M&')
    h2.cmd('iperf -c 10.14.3.2 -i 1 -n 2M&')

    time.sleep(35)
    h3.cmdPrint('fg')  
    h1.cmdPrint('fg')
    h2.cmdPrint('fg')

    info( net[ 'R1' ].cmd( 'route' ))
    
    net.pingAll()
    CLI( net )    
    net.stop()

if __name__ == '__main__':
    setLogLevel( 'info' )
    run()
