import datetime
import logging

import azure.functions as func
from source.test_function import test_print

def main(mytimer: func.TimerRequest) -> None:
    test_print()