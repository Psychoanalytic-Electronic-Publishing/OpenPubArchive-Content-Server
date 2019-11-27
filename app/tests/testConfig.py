#!/usr/bin/env python
# -*- coding: utf-8 -*-

# base_api = "http://stage.pep.gvpi.net/api"
base_api = "http://127.0.0.1:9100"
JOURNALCOUNT = 77
BOOKCOUNT = 102
VIDEOSOURCECOUNT = 12

# Can use constants for endpoints, which solves consistency in the tests, but I find it
#  harder to read (and I'd need to remove the parameters).  Left just for documentation sake
#  and moved to tests
ENDPOINT_V2_ADMIN_CREATEUSER = "/v2/Admin/CreateUser/"
ENDPOINT_V2_ADMIN_SENDALERTS = "/v2/Admin/SendAlerts/"
ENDPOINT_V2_SESSION_STATUS = "/v2/Session/Status/"
ENDPOINT_V2_SESSION_BASICLOGIN = "/v2/Session/BasicLogin/"
ENDPOINT_V2_WHOAMI = "/v2/Session/WhoAmI/"
ENDPOINT_V2_DATABASE_ALERTS = "/v2/Database/Alerts/"
ENDPOINT_V2_DATABASE_REPORTS = "/v2/Database/Reports/"
ENDPOINT_V2_DOCUMENTS_SUBMISSION = "/v2/Documents/Submission/"
ENDPOINT_V1_TOKEN = "/v1/Token/"
ENDPOINT_V1_STATUS_LOGIN = "/v1/Status/Login/"
ENDPOINT_V2_SESSION_LOGIN = "/v2/Session/Login/"
ENDPOINT_V1_LOGIN = "/v1/Login/"
ENDPOINT_V2_SESSION_LOGOUT = "/v2/Session/Logout/"
ENDPOINT_V1_LOGOUT = "/v1/Logout/"
ENDPOINT_V2_DATABASE_MORELIKETHESE = "/v2/Database/MoreLikeThese/"
ENDPOINT_V1_DATABASE_SEARCHANALYSIS = "/v1/Database/SearchAnalysis/"
ENDPOINT_V1_DATABASE_SEARCH = "/v1/Database/Search/"
ENDPOINT_V1_DATABASE_MOSTDOWNLOADED = "/v1/Database/MostDownloaded/"
ENDPOINT_V1_DATABASE_MOSTCITED = "/v1/Database/MostCited/"
ENDPOINT_V1_DATABASE_WHATSNEW = "/v1/Database/WhatsNew/"
ENDPOINT_V1_METADATA_CONTENTS_SOURCECODE = "/v1/Metadata/Contents/{SourceCode}/"
ENDPOINT_V1_METADATA_CONTENTS_SOURCECODE_SOURCEVOLUME = "/v1/Metadata/Contents/{SourceCode}/{SourceVolume}"
ENDPOINT_V1_METADATA_VIDEOS = "/v1/Metadata/Videos/"
ENDPOINT_V1_METADATA_VIDEOS = "/v1/Metadata/Books/"
ENDPOINT_V1_METADATA_JOURNALS = "/v1/Metadata/Journals/"
ENDPOINT_V1_METADATA_VOLUMES_SOURCECODE = "/v1/Metadata/Volumes/{SourceCode}/"
ENDPOINT_V1_AUTHORS_INDEX_AUTHORNAMEPARTIAL = "/v1/Authors/Index/{authorNamePartial}/"
ENDPOINT_V1_DOCUMENTS_ABSTRACTS_DOCUMENTID = "/v1/Documents/Abstracts/{documentID}/"
ENDPOINT_V2_DOCUMENTS_GLOSSARY_TERMID = "/v2/Documents/Glossary/{term_id}/"
ENDPOINT_V2_DOCUMENTS_DOCUMENT_DOCUMENTID = "/v2/Documents/Document/{documentID}/"
ENDPOINT_V1_DOCUMENTS_DOCUMENTID = "/v1/Documents/{documentID}/"
ENDPOINT_V1_DOCUMENTS_DOWNLOADS_RETFORMAT_DOCUMENTID = "/v1/Documents/Downloads/{retFormat}/{documentID}/"

def base_plus_endpoint_encoded(endpoint):
    ret_val = base_api + endpoint
    return ret_val


