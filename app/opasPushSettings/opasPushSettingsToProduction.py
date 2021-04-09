#!/usr/bin/env python
# -*- coding: utf-8 -*-

__author__      = "Neil R. Shapiro"
__copyright__   = "Copyright 2021, Psychoanalytic Electronic Publishing"
__license__     = "Apache 2.0"
__version__     = "2021.0409.1"
__status__      = "Development"

programNameShort = "opasPushSettings"

print( f"""
        {programNameShort} - Open Publications-Archive Server (OPAS) - Push Settings to Production
    
        Settings in the database are created under the Admin on Stage.
        This program copies them from the Stage database to the Production database
        
        """
)

import sys
sys.path.append('../libs')
sys.path.append('../config')
sys.path.append('../libs/configLib')
from fastapi import HTTPException
import starlette.status as httpCodes

import logging
logger = logging.getLogger(__name__)
from optparse import OptionParser

import localsecrets
import opasCentralDBLib
from opasConfig import CLIENT_CONFIGS

# until it's in localsecrets on AWS, check here
try:
    STAGE_DB_HOST = localsecrets.STAGE_DB_HOST
    PRODUCTION_DB_HOST = localsecrets.PRODUCTION_DB_HOST
    
    # use dev server for testing!
    # PRODUCTION_DB_HOST = "development.c6re6qczl2ae.us-east-1.rds.amazonaws.com"
    STAGE_PW = localsecrets.STAGE2PROD_PW[0]
    PROD_PW = localsecrets.STAGE2PROD_PW[1]
    STAGE_USER = localsecrets.STAGE2PROD_USER[0]
    PROD_USER = localsecrets.STAGE2PROD_USER[1]
except:
    msg = f"DB addresses need to be defined."
    logger.error(msg)
    raise HTTPException(
        status_code=httpCodes.HTTP_424_FAILED_DEPENDENCY,
        detail=msg
    )

def main():
    #  open databases
    try:
        stage_ocd = opasCentralDBLib.opasCentralDB(host=STAGE_DB_HOST, password=STAGE_PW, user=STAGE_USER)
        production_ocd = opasCentralDBLib.opasCentralDB(host=PRODUCTION_DB_HOST, password=PROD_PW, user=PROD_USER)
    except Exception as e:
        logger.error(f"Cannot open stage or production databases: {e}.  Terminating without changes")
    else:
        client_id = "2"
        if not stage_ocd.open_connection(caller_name="opasPushSettings"):
            raise Exception(f"Stage DB Connection Error: {STAGE_DB_HOST}")

        if not production_ocd.open_connection(caller_name="opasPushSettings"):
            raise Exception(f"Production DB Connection Error: {PRODUCTION_DB_HOST}")
            
        for config in CLIENT_CONFIGS:
            logger.info(f"Reading '{config}' from Staging DB")
            client_config = stage_ocd.get_client_config(client_id=client_id, client_config_name=config)
            # get old production config as backup
            production_config = production_ocd.get_client_config(client_id=client_id, client_config_name=config)
            if client_config is not None:
                curr_client_config_list_item = client_config.configList[0]
                client_config_settings = curr_client_config_list_item.configSettings
                logger.info(f"{config}: {client_config_settings}")
                if options.preview_bool:
                    logger.info(f"Preview mode...if non-preview Will copy `{config}` to Production DB")
                else:
                    try:
                        logger.info(f"replacing prod {config}:{production_config.configList[0].configSettings}")
                        production_ocd.save_client_config_item(session_id=curr_client_config_list_item.session_id,
                                                               client_id=curr_client_config_list_item.api_client_id, 
                                                               client_configuration_item=curr_client_config_list_item,
                                                               replace=True)
                    except Exception as e:
                        logger.error(f"Cannot write to production database {e}.  Terminating without changes")
                    else:
                        logger.info(f"Wrote `{config}` to Production DB ({PRODUCTION_DB_HOST})")
            else:
                logger.warning(f"Cannot find settings for {config} for client: {client_id}.")
                
     
        stage_ocd.close_connection(caller_name="opasPushSettings")
        production_ocd.close_connection(caller_name="opasPushSettings")

    print ("Run terminating")

# -------------------------------------------------------------------------------------------------------
# run it!

if __name__ == "__main__":
    global options  # so the information can be used in support functions
    options = None
    parser = OptionParser(usage="%prog [options] - Opas Push Settings", version=f"%prog ver. {__version__}")
    parser.add_option("-p", "--preview", action="store_true", dest="preview_bool", default=False,
                      help="Option to preview copy action, without actually copying.")
    parser.add_option("-l", "--loglevel", dest="logLevel", default=logging.ERROR,
                      help="Level at which events should be logged (DEBUG, INFO, WARNING, ERROR")
    parser.add_option("--test", dest="testmode", action="store_true", default=False,
                      help="Run Doctests")

    (options, args) = parser.parse_args()
    
    if options.testmode:
        import doctest
        doctest.testmod()
        print ("Fini. SolrXMLPEPWebLoad Tests complete.")
        sys.exit()
    
    main()
    