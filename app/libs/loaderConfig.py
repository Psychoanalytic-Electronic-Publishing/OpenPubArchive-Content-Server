
# Configuration file for opasDataLoader
default_build_pattern = "(bEXP_ARCH1|bSeriesTOC)"
default_process_pattern = "(bKBD3|bSeriesTOC)"

# Global variables (for data and instances)
options = None

# Source codes (books/journals) which should store paragraphs
SRC_CODES_TO_INCLUDE_PARAS = ["GW", "SE"]

# for these codes, do not create update notifications
DATA_UPDATE_PREPUBLICATION_CODES_TO_IGNORE = ["IPL", "ZBK", "NLP", "SE", "GW"] # no update notifications for these codes.

