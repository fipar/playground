#!/usr/bin/env python
# testing with MODE_READWRITE so it's easier to simulate a failure

import mysql.connector
from mysql.connector import fabric
from mysql.connector import errors
import time

config = {
    'fabric': {
        'host': '192.168.70.100',
        'port': 8080,
        'username': 'admin',
        'password': 'admin',
        'report_errors': True
    },
    'user': 'fabric',
    'password': 'f4bric',
    'database': 'test',
    'autocommit': 'true'
}


fcnx = None

print "starting loop"
while 1:
    if fcnx == None:
	print "connecting"
        fcnx = mysql.connector.connect(**config)
        fcnx.set_property(group='mycluster', mode=fabric.MODE_READWRITE)
    try:
	print "will run query"
        cur = fcnx.cursor()
        cur.execute("select id, sleep(0.2) from test.test limit 1")
        for (id) in cur:
            print id
	print "will sleep 1 second"
        time.sleep(1)
    except errors.DatabaseError:
        print "sleeping 1 second and reconnecting"
        time.sleep(1)
        del fcnx
        fcnx = mysql.connector.connect(**config)
        fcnx.set_property(group='mycluster', mode=fabric.MODE_READWRITE)
        fcnx.reset_cache()
        try:
            cur = fcnx.cursor()
            cur.execute("select 1")
        except errors.InterfaceError:
            fcnx = mysql.connector.connect(**config)
            fcnx.set_property(group='mycluster', mode=fabric.MODE_READWRITE)
            fcnx.reset_cache()
# gives up with mysql.connector.errors.InterfaceError: Reported faulty server to Fabric (2003: Can't connect to MySQL server on 'node2:3306' (111 Connection refused))


