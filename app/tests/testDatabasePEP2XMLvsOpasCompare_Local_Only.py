#!/usr/bin/env python
# -*- coding: utf-8 -*-

import unittest
from .utilityCompareTables import compareTables
import localsecrets
# import opasCentralDBLib
# import opasGenSupportLib as opasgenlib

from localsecrets import STAGE_DB_HOST, STAGE2PROD_PW, STAGE2PROD_USER, PRODUCTION_DB_HOST, AWSDEV_DB_HOST 
DEV_DBHOST = "localhost"
DEV_DBUSER = "root"
DEV_DBPW = ""

def compare_tables(db_tables=None):

    def_db_tables = [{"name": "[api_productbase, issn_productbase]", "key": "basecode"}
    ]
    
    if db_tables is None:
        db_tables = def_db_tables

    #  open databases
    try:
        dev_ocd_opas = compareTables.opasCentralDBMini(host=DEV_DBHOST, password=DEV_DBPW, user=DEV_DBUSER)
        dev_ocd_build = compareTables.opasCentralDBMini(host=DEV_DBHOST, password=DEV_DBPW, user=DEV_DBUSER, dbname=localsecrets.DBNAME)

    except Exception as e:
        logger.error(f"Cannot open stage or production databases: {e}.  Terminating without changes")
    else:
        pass
    
    total_diffs = 0       
    for db_table in db_tables:
        sql1 = f"""SELECT * from {db_table['name'][0]} ORDER BY {db_table['key']} ASC;"""
        sql2 = f"""SELECT * from {db_table['name'][1]} ORDER BY {db_table['key']} ASC;"""

        try:
            print (80*"=")
            print (f"Evaluating table: {db_table['name']}")
            opas_row_count, opas_tbl = dev_ocd_opas.get_table_sql(sql1)
            build_row_count, build_tbl = dev_ocd_build.get_table_sql(sql2)
            
            if opas_row_count != build_row_count:
                print (f"\t{db_table['name']} differs!")
                continue
            else:
                row_count = opas_row_count
                print (f"\tRow counts (localdev, awsdev, stage, prod): {(opas_row_count, awsdev_row_count, stage_row_count, prod_row_count)}")
            
            dev_col_count = len(opas_tbl[0])
            opas_col_count = len(awsdev_tbl[0])
            prod_col_count = len(prod_tbl[0])
            
            diffs = 0
            coldiffs = 0
            if stage_col_count != dev_col_count:
                print (f"Stage column count {stage_col_count} different than LocalDev column count {dev_col_count}.")
                coldiffs += 1
            if stage_col_count != awsdev_col_count:
                print (f"Stage column count {stage_col_count} different than AWSDev column count {awsdev_col_count}.")
                coldiffs += 1
            if stage_col_count != prod_col_count:
                print (f"Stage column count {stage_col_count} different than Prod column count {prod_col_count}.")
                coldiffs += 1

            if coldiffs > 0:
                print ("Column count differences.  Stopping compare.")
            else:
                for n in range(row_count):
                    if opas_tbl[n] != stage_tbl[n]:
                        print (f"\tLocalDev vs Stage: {db_table['name']} row {n} differs! Key: {opas_tbl[n][0]}")
                        for item in range(len(stage_tbl[n])):
                            if opas_tbl[n][item] !=  stage_tbl[n][item]:
                                print (f"\t\tCol {item} LocalDev: {opas_tbl[n][item]}")
                                print (f"\t\tCol {item} Stage: {stage_tbl[n][item]}")
                                print (f"\t\t{40*'-'}")
                        #print (f"\t\tDev: {dev_tbl[n]}")
                        #print (f"\t\tStage: {stage_tbl[n]}")
                        diffs += 1
                    if stage_tbl[n] != awsdev_tbl[n]:
                        print (f"\tStage vs AWS Dev: {db_table['name']} row {n} differs! Key:  {opas_tbl[n][0]}")
                        for item in range(len(stage_tbl[n])):
                            if awsdev_tbl[n][item] !=  stage_tbl[n][item]:
                                if awsdev_tbl[n][item] is not None:
                                    if is_date_time(awsdev_tbl[n][item]):
                                        continue
                                print (f"\t\tCol {item} Dev: {awsdev_tbl[n][item]}")
                                print (f"\t\tCol {item} Stage: {stage_tbl[n][item]}")
                                print (f"\t\t{40*'-'}")
                        #print (f"\t\tStage: {stage_tbl[n]}")
                        #print (f"\t\tAWSDev: {awsdev_tbl[n]}")
                        diffs += 1
                    if stage_tbl[n] != prod_tbl[n]:
                        print (f"\tStage vs Prod: {db_table['name']} row {n} differs!")
                        for item in range(len(stage_tbl[n])):
                            if prod_tbl[n][item] != stage_tbl[n][item]:
                                if is_date_time(awsdev_tbl[n][item]):
                                    pass
                                else:
                                    print (f"\t\tCol {item} Dev: {prod_tbl[n][item]}")
                                    print (f"\t\tCol {item} Stage: {stage_tbl[n][item]}")
                                    print (f"\t\t{40*'-'}")
                        #print (f"\t\tStage: {stage_tbl[n]}")
                        #print (f"\t\tProd: {prod_tbl[n]}")
                        diffs += 1
                    if diffs > 10:
                        print (f"{diffs} row differences found; compare was discontinued.")
                        break

            if diffs == 0 and coldiffs == 0:
                print(f"\t{db_table['name']} Tables are the same.")
            else:
                print(f"\t{db_table['name']} Tables Differ.  Row diff Count: {diffs}")
    
            total_diffs += diffs
            
        except IndexError:
            pass # column count difference
        
        except Exception as e:
            print (f"Error: {e}")

    return total_diffs

class TestDoBuildVsProductionDatabaseCompare(unittest.TestCase):
    """
    Runs the database compare program, which makes sure the configured tables
      are the same across development, test, and production databases
    
    """

    def test_1a(self):
        """
        """
        ret_val = compareTables.compare_tables()
        if ret_val > 0:
            print (80*"=")
            print (30*"*FINAL*")
            print ("Table differences found!")
        assert(ret_val == 0)
        
    def test_2(self):
        ret_val = compareTables.compare_critical_columns("api_productbase","basecode", "active")
        assert(ret_val == 0)


if __name__ == '__main__':
    unittest.main()
    print ("Tests Complete.")