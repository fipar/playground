# docker build -t fipar/pt-query-digest .
# docker run -i --name pqd --rm fipar/pt-query-digest  < /usr/local/var/mysql/mingus-slow.log
FROM perl:5.20
RUN cpanm HTTP::Server::Simple::CGI File::Slurper 
COPY ./pt-query-digest /percona-toolkit/pt-query-digest
COPY ./entrypoint /percona-toolkit/entrypoint
WORKDIR /percona-toolkit
CMD [ "perl" , "./entrypoint"]