#!/bin/bash
service mysql stop
rm -rf /var/lib/mysql/*
cp -rv /backup/* /var/lib/mysql/ 
chown -R mysql.mysql /var/lib/mysql/ 
service mysql start

