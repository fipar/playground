library(shiny)
library(ggplot2)

# Define server logic required to plot various variables against mpg
shinyServer(function(input, output) {
    mongostat <- read.table("~/tmp/mongostat_curated",header=FALSE,sep=" ")
    environment <- environment()
    ggplot(mongostat[], aes(x=mongostat[,17],y=mongostat[,2])) + geom_point() 
    output$mongostatPlot <- renderPlot({
       # plot(mongostat[,17], mongostat[,2])
        ggplot(mongostat[], aes(x=mongostat[,17],y=mongostat[,2]), environment = environment) + geom_point() 
    })
})
