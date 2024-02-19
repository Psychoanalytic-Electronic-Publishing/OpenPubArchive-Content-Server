
# Configuration file for opasDataLoader
DEFAULT_INPUT_BUILD_PATTERN = "(bKBD3|bSeriesTOC)"
DEFAULT_PRECOMPILED_INPUT_BUILD_PATTERN = "(bEXP_ARCH1)"
# default_process_pattern = "(bKBD3|bSeriesTOC)"
# DEFAULT_DOCTYPE = '<!DOCTYPE pepkbd3 SYSTEM "https://pep-web-includes.s3.amazonaws.com/pepkbd3.dtd">'
DEFAULT_XML_DECLARATION = "<?xml version='1.0' encoding='UTF-8'?>"

# Global variables (for data and instances)
options = None

# Source codes (books/journals) which should store paragraphs
SRC_CODES_TO_INCLUDE_PARAS = ["GW", "SE"]
NON_BOOK_SRC_CODES_FOR_PGX_LINKING = ["GW", "SE"]

# for these codes, do not create update notifications
DATA_UPDATE_PREPUBLICATION_CODES_TO_IGNORE = ["IPL", "ZBK", "NLP", "SE", "GW"] # no update notifications for these codes.

# SmartBuild Exceptions (these have only output builds, no input file to build, this loads output file into file list even with smart build)
SMARTBUILD_EXCEPTIONS = "(ZBK.069)"

# Directory to be excluded from build process
FUTURE_DIRECTORY_NAME = "_PEPFuture"
