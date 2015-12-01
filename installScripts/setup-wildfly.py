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
import shutil
import zipfile
import stat
import time
import socket
import urllib2

ver = "wildfly-10.0.0.CR4"

def execute(cmd):
        
    print cmd
    if platform.system() == "Windows": 
        cmd = cmd.split()
        proc = subprocess.Popen(cmd, shell=True, stdout=subprocess.PIPE, stderr=subprocess.PIPE)
    else:
        cmd = shlex.split(cmd)
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

def executeGood(cmd):
    out, err, rc = execute(cmd)
    if rc or err:
        abort(out + err)
    return out

def jbossCmd(cmd):
    out, err, rc = execute (jboss + '"' + cmd + '"')
    if rc or err:
        abort(out + err)
    return out

args = sys.argv[1:]
if len(args) > 0:
    wf = args[0]
else:
    wf = raw_input("Parent directory of wildfly installation: ")

wf = os.path.abspath(os.path.expanduser(wf))

if not os.path.exists(wf):
    abort("Specified path does not exist")

if not os.path.isdir(os.path.expanduser("~/bin")):
    abort("Please create a bin directory in your home directory")
    
for nm in ["eclipselink-2.6.1.jar", "module.xml", "mysql-connector-java-5.1.30-bin.jar", "wildfly-10.0.0.CR4.zip" ]:
    if not os.path.exists(nm):
        response = urllib2.urlopen("http://icatproject.org/misc/install/" + nm, timeout=5)
        content = response.read()
        f = open(nm, 'w')
        f.write(content)
        f.close()

mode = "N"
if os.path.exists(os.path.join(wf, ver)):
    while True:
        mode = raw_input("This version of wildfly is already installed Overwrite [O] or Quit [Q]: ").upper() 
        if mode in "ORQ": break

if mode == "Q": exit(0)
    
if len(args) > 1:
    password = args[1]
else:
    password = getpass.getpass("Desired admin password: ")

bin = os.path.join(wf, "wildfly", "bin")
jboss = os.path.join(bin, "jboss-cli.sh -c ")
exe = os.path.join(bin, "jboss-cli.sh")
if os.path.exists(exe):
    out, err, rc = execute(jboss + 'shutdown')

if mode == "O": 
    shutil.rmtree(os.path.join(wf, ver))

executeGood("unzip " + ver + ".zip -d " + wf)
try:
    os.symlink(os.path.join(wf, ver), os.path.join(wf, "wildfly"))
except:
    pass
fqdn = socket.getfqdn()
try:
    os.remove("keystore.jks")
except:
    pass
print executeGood('keytool -genkeypair -alias smfisher.esc.rl.ac.uk -keyalg RSA -keysize 2048 -validity 10950 -keystore keystore.jks -keypass changeit -storepass changeit -dname "CN=' + fqdn + '"')
shutil.move("keystore.jks", os.path.join(wf, "wildfly", "standalone", "configuration"))

shutil.copy("eclipselink-2.6.1.jar", os.path.join(wf, "wildfly/modules/system/layers/base/org/eclipse/persistence/main"))
shutil.copy("module.xml", os.path.join(wf, "wildfly/modules/system/layers/base/org/eclipse/persistence/main"))
for d in ["config", "logs", "data"]:
    try:
        p = os.path.join(wf, "wildfly", d)
        os.makedirs(p)
        print "Created", p
    except OSError:
        if not os.path.isdir(p):raise

exe = os.path.join(os.path.expanduser("~/bin"), "wildfly")
f = open(exe, "w")
f.write("#!/bin/sh\n")
f.write("cd " + os.path.join(wf, "wildfly", "config") + "\n")
f.write("nohup " + os.path.join(bin, "standalone.sh") + " -c standalone-full.xml > ../logs/console.out 2>&1 &\n")
f.close()
os.chmod(exe, os.stat(exe).st_mode | stat.S_IEXEC)

print executeGood(exe)

print "Wait for it to start..."
time.sleep(5)

print executeGood(os.path.join(bin, "add-user.sh") + " -u admin -p " + password)
print jbossCmd("deploy --force mysql-connector-java-5.1.30-bin.jar")
print jbossCmd("/system-property=eclipselink.archive.factory:add(value=org.jipijapa.eclipselink.JBossArchiveFactoryImpl)")
print jbossCmd("/subsystem=webservices:write-attribute(name=statistics-enabled,value=true)")
print jbossCmd("/subsystem=messaging-activemq/server=default:write-attribute(name=security-enabled,value=false)")
print jbossCmd("/subsystem=logging:write-attribute(name=add-logging-api-dependencies,value=false)")
print jbossCmd("/core-service=management/security-realm=ssl-realm/:add()")
print jbossCmd("/core-service=management/security-realm=ssl-realm/server-identity=ssl/:add(keystore-path=keystore.jks, keystore-relative-to=jboss.server.config.dir, keystore-password=changeit, alias=" + fqdn + ", key-password=changeit)")
print jbossCmd("/subsystem=undertow/server=default-server/https-listener=https/:add(socket-binding=https, security-realm=ssl-realm)")
print jbossCmd("/socket-binding-group=standard-sockets/socket-binding=https:write-attribute(name=port,value=${jboss.https.port:8181})")
print jbossCmd("/interface=public:write-attribute(name=inet-address)")
print jbossCmd("/interface=public:write-attribute(name=any-address, value=true)")
print jbossCmd('reload')




