#!/usr/bin/env python
#
# -----------------------------------------------------------------------------

import logging

# from . import config

def setup_logger(mode):
    pass


# Create a custom logger
logger = logging.getLogger("base-api")
logger.setLevel(logging.DEBUG)  # Can be DEBUG, INFO, WARNING, ERROR

# Create console handler
console_handler = logging.StreamHandler()
console_handler.setLevel(logging.DEBUG)

# Set formatter
formatter = logging.Formatter(
    "%(asctime)s - %(message)s"
)
console_handler.setFormatter(formatter)

# Add handler to logger
logger.addHandler(console_handler)



"""
print(f"Using LogName |{config.LogName}|")

logging.basicConfig(filename=config.LogName,
                    filemode='a',
                    format='%(asctime)s  %(levelname)-8s  %(message)s',
                    level=logging.INFO,
                    datefmt='%Y-%m-%d %H:%M:%S')
"""
