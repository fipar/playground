# to run: 
# R CMD BATCH ./load_data.r
require(RMySQL)
require(ggplot2)
con <- dbConnect(MySQL(), user="msandbox", password="msandbox", dbname="r_input", host="127.0.0.1", port=5527)
data_from_processlist <- dbGetQuery(con, "select ts,Command,count(pk) as cnt from processlist_captures group by ts,Command order by ts asc;")
png("genplot.png",height=800,width=800)
qplot(data=data_from_processlist, x=ts, y=cnt, color=Command) + theme(panel.grid=element_blank(), panel.background=element_blank(), axis.text.x=element_blank() )
dev.off()
