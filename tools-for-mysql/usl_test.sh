#!/bin/bash

cat <<EOF>$$.R 
require(usl)
library(ggplot2)
threads <- c(20,40,60,80)
data_default_schema <- data.frame(
  threads,
  tps <- c(4.308,7.269,8.992,3.992)
)

usl.model <- usl(tps ~ threads, data_default_schema)
threads_to_predict=c(70,100,120)
predicted_data <- predict(usl.model, data.frame(threads=threads_to_predict))
df <- data.frame(threads=threads_to_predict, tps=predicted_data)

png("model_default_schema.png",height=800,width=800)
plot(usl.model)
dev.off()
png("model_default_schema_predicted.png",height=800,width=800)
ggplot(df, aes(x = threads, y = tps)) + geom_point() + geom_point(data=usl.model\$frame)
dev.off()

EOF

R CMD BATCH $$.R

cat <<EOF>$$.R
require(usl)
library(ggplot2)
threads <- c(20,40,60,80)
data_archive_schema <- data.frame(
  threads,
  tps <- c(3.967,7.987,9.031,4.977)
)

usl.model <- usl(tps ~ threads, data_archive_schema)
threads_to_predict=c(70,100,120)
predicted_data <- predict(usl.model, data.frame(threads=threads_to_predict))
df <- data.frame(threads=threads_to_predict, tps=predicted_data)

png("model_archive_schema.png",height=800,width=800)
plot(usl.model)
dev.off()
png("model_archive_schema_predicted.png",height=800,width=800)
ggplot(df, aes(x = threads, y = tps)) + geom_point() + geom_point(data=usl.model\$frame)
dev.off()

EOF

R CMD BATCH $$.R
rm -f $$.$
