library(shiny)

# Define UI for miles per gallon application
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
