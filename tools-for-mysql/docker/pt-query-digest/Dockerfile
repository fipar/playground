# docker build -t fipar/pt-query-digest .
# docker run -i --name pqd --rm fipar/pt-query-digest  < /usr/local/var/mysql/mingus-slow.log
FROM perl:5.20
COPY ./pt-query-digest /percona-toolkit/pt-query-digest
WORKDIR /percona-toolkit
CMD [ "perl" , "./pt-query-digest"]