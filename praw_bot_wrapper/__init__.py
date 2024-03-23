import logging
from .bot import run, stream_handler, outage_recovery_handler, handle_praw_errors

logging.getLogger(__package__).addHandler(logging.NullHandler())
