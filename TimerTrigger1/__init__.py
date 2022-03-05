import datetime
import logging

import azure.functions as func
from source.ScrapeAndEmail import scrape_then_email

def main(mytimer: func.TimerRequest) -> None:
    scrape_then_email()
    print("Ran BikeAlerts Azure Function")