#!/bin/bash
# Fix Docker bypassing UFW
# Allow only specific IP (201.172.239.196) to access ports 80 and 443

# Flush existing DOCKER-USER rules
iptables -F DOCKER-USER

# Allow all traffic from docker0 interface (needed for builds)
iptables -A DOCKER-USER -i docker0 -j ACCEPT

# Allow established connections
iptables -A DOCKER-USER -m conntrack --ctstate RELATED,ESTABLISHED -j ACCEPT

# Allow from localhost
iptables -A DOCKER-USER -i lo -j ACCEPT

# Allow specific IP to access ports 443 and 80
iptables -A DOCKER-USER -p tcp --dport 443 -s 201.172.239.196 -j ACCEPT
iptables -A DOCKER-USER -p tcp --dport 80 -s 201.172.239.196 -j ACCEPT

# Drop all other external access to ports 80 and 443
iptables -A DOCKER-USER -p tcp --dport 80 -j DROP
iptables -A DOCKER-USER -p tcp --dport 443 -j DROP

# Allow everything else (for other Docker services)
iptables -A DOCKER-USER -j RETURN

echo "✅ Docker ports 80/443 accessible only from 201.172.239.196"
echo "   All other external access blocked"
