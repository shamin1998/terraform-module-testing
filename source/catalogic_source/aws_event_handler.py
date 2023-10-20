import datetime
import logging


def lambda_handler(event, context):
    current_time = datetime.datetime.now().time()
    logging.info("Hello from my timer function! The current time is {}".format(current_time))