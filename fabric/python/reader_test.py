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
    'database': 'test'
}


fcnx = mysql.connector.connect(**config)
fcnx.set_property(group='mycluster', mode=fabric.MODE_READWRITE)


while 1:
    try:
        cur = fcnx.cursor()
        cur.execute("select id from test.test limit 1")
        for (id) in cur:
            print id
        time.sleep(1)
    except errors.DatabaseError:
        cnt = 10
        while cnt > 0:
            try:
                print "sleeping 1 second and reconnecting"
                time.sleep(1)
                fcnx.close()
                del fcnx
                fcnx = mysql.connector.connect(**config)
                fcnx.set_property(group='mycluster', mode=fabric.MODE_READWRITE)
                cnt = cnt - 1
            except:
                cnt = cnt - 1
# gives up with mysql.connector.errors.InterfaceError: Reported faulty server to Fabric (2003: Can't connect to MySQL server on 'node2:3306' (111 Connection refused))


