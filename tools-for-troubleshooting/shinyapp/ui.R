library(shiny)

# Define UI for miles per gallon application
shinyUI(fluidPage(

    # Application title
    titlePanel("mongostat metrics"),
    verticalLayout(
        plotOutput("mongostatPlot")
    )
))
