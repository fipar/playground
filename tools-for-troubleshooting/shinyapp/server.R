library(shiny)
library(ggplot2)

# Define server logic required to plot various variables against mpg
shinyServer(function(input, output) {
    ranges <- reactiveValues(x = NULL, y = NULL)

    mongostat <- read.table("~/tmp/mongostat_curated",header=FALSE,sep=" ")
    environment <- environment()
    ggplot(mongostat[], aes(x=mongostat[,17],y=mongostat[,2])) + geom_point() 
    output$mongostatPlot <- renderPlot({
       # plot(mongostat[,17], mongostat[,2])
        ggplot(mongostat[], aes(x=mongostat[,17],y=mongostat[,2]), environment = environment) + geom_point() + coord_cartesian(xlim=ranges$x, ylim=ranges$y)
    })
    # When a double-click happens, check if there's a brush on the plot.
    # If so, zoom to the brush bounds; if not, reset the zoom.
    observeEvent(input$mongostat_dblclick, {
      brush <- input$mongostat_brush
      if (!is.null(brush)) {
        ranges$x <- c(brush$xmin, brush$xmax)
        ranges$y <- c(brush$ymin, brush$ymax)

      } else {
        ranges$x <- NULL
        ranges$y <- NULL
      }
    })
    
})
