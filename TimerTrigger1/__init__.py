import datetime
import logging
from pathlib import Path
import azure.functions as func
from source.ScrapeAndEmail import scrape_then_email
from source.configure_service_principal import configure_service_principal

def main(mytimer: func.TimerRequest) -> None:

    # Set OS environemnt variables needed to auth with Azure KeyVault
    base_path = Path(__file__).parent
    file_path = (base_path / "../configs/ServicePrincipalKeys.json").resolve()
    configure_service_principal(file_path)
    logging.info("configured SP")
    # Run scraping and email report out
    scrape_then_email()
    logging.info("Ran BikeAlerts Azure Function")