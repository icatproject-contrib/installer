#!/usr/bin/env python
import threading
import platform
import shlex
import subprocess
import StringIO
import getpass
import sys
import os
import tempfile

def execute(prog, argString):
        
    print '"'+prog+'"', argString 
    if platform.system() == "Windows":
        cmd = [prog] + argString.split()
        proc = subprocess.Popen(cmd, shell=True, stdout=subprocess.PIPE, stderr=subprocess.PIPE)
    else:
        cmd = [prog] + shlex.split(argString)
        proc = subprocess.Popen(cmd, stdout=subprocess.PIPE, stderr=subprocess.PIPE)
    stringOut = StringIO.StringIO()

    mstdout = Tee(proc.stdout, stringOut)
    mstdout.start()
    stringErr = StringIO.StringIO()
    mstderr = Tee(proc.stderr, stringErr)
    mstderr.start()
    rc = proc.wait()

    mstdout.join()
    mstderr.join()

    out = stringOut.getvalue().strip()
    stringOut.close()

    err = stringErr.getvalue().strip()
    stringErr.close()

    return out, err, rc

class Tee(threading.Thread):
    
    def __init__(self, inst, *out):
        threading.Thread.__init__(self)
        self.inst = inst
        self.out = out
        
    def run(self):
        while 1:
            line = self.inst.readline()
            if not line: break
            for out in self.out:
                out.write(line)

def abort(msg):
    """Print to stderr and stop with exit 1"""
    print >> sys.stderr, msg, "\n"
    sys.exit(1)

def executeGood(prog, argString):
    out, err, rc = execute(prog, argString)
    if rc:
        abort(err)
    return out

def asadmin(argString):
    return executeGood(asadminCmd, argString)

glassfish, password = sys.argv[1:]

asadminCmd = os.path.join(glassfish, "bin", "asadmin")

dummy, tfile = tempfile.mkstemp()
a = open(tfile, "w")
a.write("AS_ADMIN_PASSWORD=" + password)
a.close()

config = os.path.join(glassfish, "glassfish", "domains", "domain1", "config")

print asadmin("delete-domain domain1")
print asadmin("-W " + tfile + " --user admin create-domain --savelogin domain1")
print asadmin("start-domain")
print asadmin("enable-secure-admin")
print asadmin("stop-domain")
print asadmin("start-domain")
print asadmin('set server.http-service.access-log.format="common"')
print asadmin('set server.http-service.access-logging-enabled=true')
print asadmin('set server.thread-pools.thread-pool.http-thread-pool.max-thread-pool-size=128')
print asadmin('set configs.config.server-config.cdi-service.enable-implicit-cdi=false')
print asadmin('set server.ejb-container.property.disable-nonportable-jndi-names="true"')
print asadmin('delete-ssl --type http-listener http-listener-2')
print asadmin('delete-network-listener http-listener-2')
print asadmin('create-network-listener --listenerport 8181 --protocol http-listener-2 http-listener-2')
print asadmin('create-ssl --type http-listener --certname s1as --ssl3enabled=false --ssl3tlsciphers +SSL_RSA_WITH_RC4_128_MD5,+SSL_RSA_WITH_RC4_128_SHA http-listener-2')
##executeGood("keytool", "-export -keystore " + os.path.join(config, "keystore.jks") + " -file " + os.path.join(config, "cert") + " -storepass changeit -alias s1as")
