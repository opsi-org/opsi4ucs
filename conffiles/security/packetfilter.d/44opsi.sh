/sbin/iptables -A INPUT -p "tcp"  --dport 4447 -j ACCEPT
/sbin/iptables -A INPUT -p "udp"  --dport 69 -j ACCEPT
