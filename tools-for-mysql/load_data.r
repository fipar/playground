con <- dbConnect(MySQL(), user="msandbox", password="msandbox", dbname="r_input", host="127.0.0.1", port=5527)
data_from_processlist <- dbGetQuery(con, "select ts,Command,count(pk) as cnt from processlist_captures group by ts,Command order by ts asc;")
qplot(data=data_from_processlist, x=ts, y=cnt, color=Command)
