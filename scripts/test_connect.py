from scripts.connect_to_hosts import connect_to_hosts
hosts = ['172.27.200.200', '172.27.200.201']
connections = connect_to_hosts(hosts, 'admin', 'manolis1')
print(f"Connections: {len(connections)}")
