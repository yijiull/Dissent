import os
from remote.remote_execute import unique_execute, execute, connect, run_once, local_execute
import random
import signal
import sys, time
import remote.config as config
from deploy_environment import setup_environment, cleanup_environment
import time
# deployment script for DC

delay = 2
server_n = 1
client_n = 1
k = 5;
connection = 20
server_port = []
client_port = []
ping_client = []

unique_server = config.servers[:1]
#unique_server.append(config.servers[-1])
unique_client = config.servers[:]
print unique_server
print unique_client
for i, host in enumerate(unique_server):
    for idx in range(client_n):
        client_port.append(50230 + idx)

    for idx in range(server_n):
        server_port.append(51230 + idx)

s_ids = []

with open('s_ids') as f:
    for line in f.readlines():
        s_ids.append(line[:-1])

@run_once
def deploy_dc():
    for host in unique_server:
        with connect(host, "dc-eval", False) as r:
            r.execute("git clone https://github.com/dedis/Dissent.git")
            r.execute("cd Dissent; qmake application.pro; make -j")
            r.execute("cd Dissent/conf/local; ln -s ../../dissent .")
    
    with connect(unique_server[0], "dc-eval", False) as r:
        r.execute("cd Dissent; qmake keygen.pro; make -j")


@run_once
def dc_dep():
    unique_execute("apt-get install build-essential g++ gcc cmake libgoogle-glog-dev libsodium-dev qt5-qmake qt5-default libcrypto++-dev -y", is_sudo=True)
    
def remake():
    for host in unique_server:
        with connect(host, "dc-eval", False) as rt:
            rt.execute("sed -i 's/20000/10000/g' Dissent/src/Connections/ConnectionManager.cpp && cd Dissent && qmake application.pro && make -j")


def generate_key():
    with connect(unique_server[0], "dc-eval", False) as r:
    #    print server_n * len(unique_server) + client_n * len(unique_client) * connection 
    #    r.execute("cd Dissent/conf/local && rm -rf keys && ./keygen --nkeys %d" % (server_n * len(unique_server) + client_n * len(unique_server) * connection ) )
    #    r.execute("cd Dissent/conf/local && rm -rf public private; cp -r keys/* .")

        for host in unique_server[1:]:
            with connect(host, "dc-eval", False) as rt:
        	rt.execute("cd Dissent/conf/local && rm -rf keys")
    	for host in unique_server[1:]:
            r.execute("cd Dissent/conf/local; scp -r keys %s@%s:/home/jianyu/%s-dc-eval/Dissent/conf/local/" % (config.user, host, host))
        for host in unique_server[1:]:
            with connect(host, "dc-eval", False) as rt:
        	rt.execute("cd Dissent/conf/local && rm -rf public private ; mv keys/* .")

def init():
    for host in unique_server:
        with connect(host, "dc-eval", False) as rt:
            rt.execute("cd Dissent/conf/local; rm *conf *log")
    # generate server.conf
    #os.system("ls ../Dissent/conf/local/private/* | awk -F / '{print $6}' | sort > all_ids")
    all_ids = []
    with open("all_ids") as f:
        for line in f.readlines():
            all_ids.append(line[:-1])
    print len(all_ids)
    info = "[general]\n"
    info += "local_nodes=1\n"
    info += "remote_endpoints="
    for i in range(len(unique_server)):
        for j in range(server_n):
            if i == len(unique_server) - 1 and j == server_n - 1:
                info += "\"tcp://%s:%s\"\n\n" % (unique_server[i], server_port[j])
            else:
                info += "\"tcp://%s:%s\"," % (unique_server[i], server_port[j])
    info += "server_ids="
    for i in range(len(unique_server)):
        for j in range(server_n):
            if i == len(unique_server) - 1 and j == server_n - 1:
                info += "\"%s\"\n\n" % (s_ids[i * server_n + j])
                #info += "\"%s\"\n\n" % (all_ids[i * server_n + j])
            else:
                #info += "\"%s\"," % (all_ids[i * server_n + j])
                info += "\"%s\"," % (s_ids[i * server_n + j])
    info += "round_type=\"null/csdcnet\"\n"
    #info += "round_type=\"null/csdcnet\"\n"
    info += "auth=true\n"
    info += "path_to_private_keys=private\n"
    info += "path_to_public_keys=public\n\n"
    info += "console=false\n"\
            "exit_tunnel=true\n"\
            "multithreading=true\n\n"

    for i in range(len(unique_server)):
        for idx in range(server_n):
            server_conf = "server%d.conf" % (i * server_n + idx)
	    sid = i*server_n + idx
            print "server %d" % (sid)
            with open(server_conf, 'w') as f:
                f.write(info)
                f.write("local_endpoints=\"tcp://%s:%s\"\n" % (unique_server[i], server_port[idx]))
                f.write("local_id=\"%s\"\n" % (s_ids[sid]))
                #f.write("local_id=\"%s\"\n" % (all_ids[sid]))
                f.write("log=\"server%d.log\"\n" % (sid))
	    with connect(unique_server[i], "dc-eval", False) as r:
            	r.put(server_conf, "Dissent/conf/local/" + server_conf)
    # generate client.conf
    info = "[general]\n"
    info += "local_nodes=%d\n" % (connection)
    info += "remote_endpoints="
    for i in range(len(unique_server)):
        for j in range(server_n):
            if i == len(unique_server) - 1 and j == server_n - 1:
                info += "\"tcp://%s:%s\"\n\n" % (unique_server[i], server_port[j])
            else:
                info += "\"tcp://%s:%s\"," % (unique_server[i], server_port[j])
    info += "server_ids="
    for i in range(len(unique_server)):
        for j in range(server_n):
            if i == len(unique_server) - 1 and j == server_n - 1:
                info += "\"%s\"\n\n" % (s_ids[i * server_n + j])
                #info += "\"%s\"\n\n" % (all_ids[i * server_n + j])
            else:
                #info += "\"%s\"," % (all_ids[i * server_n + j])
                info += "\"%s\"," % (s_ids[i * server_n + j])
    info += "round_type=\"null/csdcnet\"\n"
    info += "path_to_private_keys=private\n"
    info += "path_to_public_keys=public\n\n"
    info += "exit_tunnel=false\n"\
            "multithreading=true\n\n"
    #info += "web_server_url=http://127.0.0.1:8080\nentry_tunnel_url = \"tcp://127.0.0.1:8081\"\n"
    cnt = 0
    all_ids = [x for x in (set(all_ids) - set(s_ids))]
    for i in range(len(unique_client)):
        for j in range(client_n):
            cid = (i * client_n + j) * connection
            client_conf = "client%d.conf" % (i * client_n + j)
            with open(client_conf, 'w') as f:
                f.write(info)
    		f.write("auth=true\n")
		if i == len(unique_client):
		#if i == len(unique_client) - 1:
		    f.write("console=true\n")
                else:
		    f.write("console=false\n")
    		f.write("web_server_url=http://127.0.0.1:%d\nentry_tunnel_url = \"tcp://127.0.0.1:%d\"\n" % (8080 + j, 7080 + j))
                f.write("local_endpoints=\"tcp://127.0.0.1:%s\"\n" % (client_port[j]))
                while all_ids[cnt] in s_ids:
                    print cnt
		    cnt += 1
                f.write("local_id=\"%s\"" % (all_ids[cnt]))
                cnt += 1
                #f.write("local_id=\"%s\"" % (all_ids[server_n * len(unique_server) + cid]))
		print "client %d" % (server_n * len(unique_server) + cid)
                for k in range(1, connection):
                    while all_ids[cnt] in s_ids:
                        print cnt
		        cnt += 1
                    f.write(", \"%s\"" % (all_ids[cnt]))
                    cnt += 1
		    print "client %d" % (server_n * len(unique_server) + cid + k)
                f.write("\n")
                f.write("log=\"clients%d.log\"\n" % (cid / connection))
            with connect(unique_client[i], "dc-eval", False) as r:
                r.put(client_conf, "Dissent/conf/local/" + client_conf)
    #os.system("rm *conf")


def sample(client_k):
    temp = []
    for host in unique_client:
        for j in client_n:
            temp.append((host, client_port[j]))
     ping_client = set(random.sample(temp, k=client_k)


def run_all():
    # server
    for i in range(len(unique_server)):
        #time.sleep(1)
        with connect(unique_server[i], "dc-eval", False) as r:
            for j in range(server_n): 
                r.execute("cd Dissent/conf/local ; rm *log; ./dissent server%d.conf &> /dev/null &" % (i*server_n + j))
    
    time.sleep(2)
    # client
    session_id = 0;
    for i in range(len(unique_client)):
        with connect(unique_client[i], "dc-eval", False) as r:
            for j in range(client_n):
                if (unique_client[i], client_port[j]) in ping_client:
                    r.execute("cd Dissent/conf/local ; rm *log ; ./dissent client%d.conf %d" % (i*client_n + j, (i*client_n + j), session_id))
                else:
                    r.execute("cd Dissent/conf/local ; rm *log ; ./dissent client%d.conf" % (i*client_n + j, (i*client_n + j)))

    #time.sleep(delay)
    setup_environment()

def signal_handler(sig, frame):
    unique_execute("killall dissent", will_wait=False)
    cleanup_environment()
    sys.exit(0)


signal.signal(signal.SIGINT, signal_handler)

dc_dep()
deploy_dc()

#unique_execute("killall dissent", will_wait=False)
#unique_execute("sed -i 's/10000/20000/g' Dissent/src/Connections/ConnectionManager.cpp && cd Dissent && qmake application.pro && make -j", will_wait=False)
#remake()

#generate_key()
#init()
run_all()
print "done"
time.sleep(1000000)