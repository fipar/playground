library(shiny)

shinyUI(fluidPage(

    # Application title
    titlePanel("mongostat metrics"),
    verticalLayout(
        plotOutput("mongostatPlot",
           dblclick="mongostat_dblclick",
           brush=brushOpts(
             id = "mongostat_brush",
             resetOnNew = TRUE
          ))
    )
))
