# BikeAlerts
**Get emailed when bikes are back in stock**

### Background
It's 2022. The bike supply chain is still messed up and you're in dire need for some summer wheels. This code scrapes bike manufacturer websites (starting with Canyon) that sell direct to consumer in order to get alerted quickly when a bike you're looking for is in stock. 
This was a fun side project to get more familiar with using Azure Functions. It's still very much in ad-hoc mode and could benefit from being generalized to various manufacturers, different customer requests, and a customer on-boarding process. 

### How it works
The code works by grabbing html content from bike manufactuer's website using requests/BeautifulSoup, parsing out bike sizes and availabiliies we're looking for with regex, and then sending an email to customers who want to be alerted when a certain size is in stock for a given model. It's hosted in Azure and runs every 5 minutes using Azure Functions CRON scheduler.

