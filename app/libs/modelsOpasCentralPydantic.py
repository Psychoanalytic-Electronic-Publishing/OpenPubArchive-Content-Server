#!/usr/bin/env python
# -*- coding: utf-8 -*-

"""
OpasCentral DB Pydantic Models

NOTE: With the link up to PaDS to handle user accounts, most of these aren't used anymore.

"""
__author__      = "Neil R. Shapiro"
__copyright__   = "Copyright 2019-2021, Psychoanalytic Electronic Publishing"
__license__     = "Apache 2.0"
__version__     = "2019.0620.1"
__status__      = "Development"

# from datetime import datetime, timedelta
from pydantic.main import BaseModel

#class User(BaseModel):  # snake_case names to match DB
    #user_id: int = None
    #username: str = None
    #full_name: str = None
    #email_address: str = None
    #company: str = None
    #modified_by_user_id: int = None
    #enabled: bool = True
    #authorized_peparchive: bool = False
    #authorized_pepcurrent: bool = False
    #admin: bool = False
    #user_agrees_date: datetime = None
    #user_agrees_to_tracking: bool = None
    #user_agrees_to_cookies: bool = None
    #view_parent_user_reports: str = 'n'
    #deleted: bool = False
    #added_by_user_id: int = None
    #added_date: datetime = None
    #last_update: datetime = None

#class UserInDB(User):
    #password: str = None
  
#class UserSubscriptions(UserInDB): # deprecated
    #"""
    #__View vw_user_active_subscriptions__

    #Includes UserInDB and key Subscriptions
      #fields.  Filtered down to "active"
      #subscriptions, enabled and in date.
 
    #User alone is not enough to verify a username
      #since they could be in the database
      #but not have any active subscriptions
      
    #"""
    #product_id: int = None
    #start_date: datetime = None
    #end_date: datetime = None
    #max_concurrency: int = None
    #content_start_date: datetime = None
    #content_end_date: datetime = None
    #perpetual: bool = None
    #referrer: str = None

#class Session(BaseModel):  # subset of sessionInfo [Not used anymore]
    #session_id: str = None
    #user_id: int = None
    #user_ip: str = None
    #connected_via: str = None
    #referrer: str = None
    #session_start: datetime = None
    #session_end: datetime = None
    #session_expires_time: datetime = None
    #access_token: str = None
    #token_type: str = None
    #authenticated: bool = False
    #admin: bool = False
    #keep_active: bool = False
    #api_client_id: int = None            
    
#class Subscriptions(BaseModel): # [Not used anymore]
    #user_id: int = None
    #product_id: int = None
    #start_date: datetime = None
    #end_date: datetime = None
    #max_concurrency: int = None
    #content_start_date: datetime = None
    #content_end_date: datetime = None
    #perpetual: bool = None
    #modified_by_user_id: int = None
    #last_update: datetime = None
    
#class MostCitedArticles(BaseModel): # [Not used anymore from here (local copy in opasDataUpdateStat)]
    #"""
    #__Table vw_stat_cited_crosstab2__

    #A view with rxCode counts derived from the fullbiblioxml table and the articles table
      #for citing sources in one of the date ranges.
    #"""
    #cited_document_id: str = None
    #countAll: int = 0
    #count5: int = 0
    #count10: int = 0
    #count20: int = 0

#class ClientConfigs(BaseModel):
    #config_id: int = 0
    #client_id: int = 0
    #config_name: str = None
    #config_settings: str = None
    #session_id: str
    #last_update: datetime = None

#class Biblioxml(BaseModel):
    #art_id: str = None
    #bib_local_id: str = None 
    #art_year: int = 0
    #bib_rx: str = None
    #bib_rxcf: str = None
    #bib_sourcecode: str = None
    #bib_authors: str = None
    #bib_articletitle: str = None
    #title: str = None
    #full_ref_text: str = None
    #bib_sourcetype: str = None
    #bib_sourcetitle: str = None
    #bib_authors_xml: str = None
    #full_ref_xml: str = None
    #bib_pgrg: str = None
    #doi: str = None
    #bib_year: str = None
    #bib_year_int: int = 0
    #bib_volume: str = None
    #bib_publisher: str = None
    #last_update: datetime = None

# Deleted since article table being deprecated 2020-08-09    
#class MostCitedArticlesWithDetails(MostCitedArticles):
    #"""
    #__Table vw_stat_cited_crosstab_with_details2__ # was MostCitedArticlesWithDetails
    #based on 
    #__Table vw_stat_cited_crosstab2__

    #A view with rxCode counts derived from the fullbiblioxml table and the articles table
      #for citing sources in one of the date ranges.

    #Adds to MostCitedArticles model more of the cited article information for display
    
    #"""
    #hdgauthor: str = None
    #hdgtitle: str = None
    #srctitleseries: str = None
    #year: int = None
    #vol: str = None
    #pgrg: str = None
    
#class Products(BaseModel):
    #product_id: int = None
    #subsystem_id: int = None
    #product: str = None
    #product_level: int = None
    #product_type: str = None
    #basecode: str = None
    #product_comment: str = None
    #free_access: bool = False
    #active: bool = False
    #range_limited: bool = False
    #embargo_length: int = None
    #embargo_inverted: int = None
    #range_start_date: datetime = None
    #range_end_date: datetime = None
    #parent_product_id: int = None
    #inherit_parent_metadata: bool = False
    #id_type: int = None
    #counter_service: str = None
    #counter_database: str = None
    #counter_book: str = None
    #counter_journal_collection: str = None
    #id_code_1: str = None
    #id_code_2: str = None
    #group_sort_order: int = None
    #hide_in_product_access: bool = False
    #hide_in_report_list: bool = False
    #added_by_user_id: int = None
    #date_added: datetime = None
    #modified_by_user_id: int = None
    #last_update: datetime = None
    
class Articles(BaseModel):
    document_id: str = None
    art_views_update: bool = False
    art_views_lastcalyear: int = 0
    art_views_last12mos: int = 0
    art_views_last6mos: int = 0
    art_views_last1mos: int = 0
    art_views_lastweek: int = 0
    art_cited_5: int = 0
    art_cited_10: int = 0
    art_cited_20: int = 0
    art_cited_all: int = 0
    art_id: str = None
    art_doi: str = None
    art_type: str = None
    art_lang: str = None
    art_kwds: str = None
    art_auth_mast: str = None
    art_auth_citation: str = None
    art_title: str = None
    src_title_abbr: str = None
    src_code: str = None
    art_year: int = None
    art_year_str: str = None
    art_vol: int = None
    art_vol_str: str = None
    art_vol_suffix: str = None
    art_issue: str = None
    art_pgrg: str = None
    art_pgstart: str = None
    art_pgend: str = None
    main_toc_id: str = None
    start_sectname: str = None
    bk_info_xml: str = None
    bk_title: str = None
    bk_publisher: str = None
    art_citeas_text: str = None
    art_citeas_xml: str = None
    ref_count: int = None
    filename: str = None
    filedatetime: str = None
    preserve: str = None
    fullfilename: str = None
    manuscript_date_str: str = None
    last_update: str = None
    