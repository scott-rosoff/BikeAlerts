import datetime
import logging
from pathlib import Path
import azure.functions as func
from source.ScrapeAndEmail import scrape_in_stock_models, send_email_report
from source.configure_service_principal import configure_service_principal
import pandas 

def main(mytimer: func.TimerRequest) -> None:

    # Set OS environemnt variables needed to auth with Azure KeyVault
    base_path = Path(__file__).parent
    file_path = (base_path / "../configs/ServicePrincipalKeys.json").resolve()
    configure_service_principal(file_path)
    logging.info("configured SP")

    # Run scraping to find in stock models
    in_stock_models = scrape_in_stock_models()
    logging.info("Ran Scraping")

    send_email_report(in_stock_models)
    logging.info("Finished Azure Function")