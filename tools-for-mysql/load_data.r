# to run: 
# R CMD BATCH ./load_data.r
require(ggplot2)
require(RSQLite)

data <- read.csv("~/src/playground/tools-for-mysql/processlist_data.csv", header=TRUE, sep=",")
drv <- dbDriver("SQLite")
dbfile <- tempfile()
con <- dbConnect(drv, dbname=dbfile)
dbWriteTable(con, "processlist", data)
data_from_processlist <- dbGetQuery(con, "select sample,Command,count(sample) as cnt from processlist group by sample,Command order by sample asc")
png("genplot.png",height=800,width=800)
qplot(data=data_from_processlist, x=ts, y=cnt, color=Command) + theme(panel.grid=element_blank(), panel.background=element_blank(), axis.text.x=element_blank() )
dev.off()
