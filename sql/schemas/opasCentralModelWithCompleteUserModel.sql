CREATE TABLE `api_administrative_groups`  (
  `administrative_group_id` int NOT NULL,
  `group_name` varchar(255) CHARACTER SET utf8 COLLATE utf8_general_ci NULL DEFAULT NULL,
  `descriptopn` varchar(255) CHARACTER SET utf8 COLLATE utf8_general_ci NULL DEFAULT NULL,
  PRIMARY KEY (`administrative_group_id`) USING BTREE
) ENGINE = InnoDB CHARACTER SET = utf8 COLLATE = utf8_general_ci COMMENT = 'The classes of administrative users, referened in the api_users table.' ROW_FORMAT = Dynamic;

CREATE TABLE `api_articles`  (
  `art_id` varchar(24) CHARACTER SET latin1 COLLATE latin1_swedish_ci NOT NULL DEFAULT '' COMMENT 'The locator style ID for this article (e.g., APA.004.0109A)',
  `art_doi` varchar(255) CHARACTER SET latin1 COLLATE latin1_swedish_ci NULL DEFAULT NULL COMMENT 'Standard Document Object Identifier if supplied',
  `art_type` varchar(4) CHARACTER SET latin1 COLLATE latin1_swedish_ci NULL DEFAULT '' COMMENT 'Article type, e.g., ART, COM, ERA',
  `art_lang` varchar(255) CHARACTER SET utf8 COLLATE utf8_general_ci NULL DEFAULT NULL COMMENT 'Article language (top level)',
  `art_kwds` varchar(1024) CHARACTER SET utf8 COLLATE utf8_general_ci NULL DEFAULT NULL COMMENT 'Keywords in article as coded',
  `art_auth_mast` text CHARACTER SET utf8 COLLATE utf8_general_ci NULL COMMENT 'Author names per masthead, e.g. Ronnie C. Lesser, Ph.D.',
  `art_auth_citation` text CHARACTER SET utf8 COLLATE utf8_general_ci NULL COMMENT 'The heading/citation style author list, e.g., Lesser, R. C.',
  `art_title` text CHARACTER SET utf8 COLLATE utf8_general_ci NULL COMMENT 'The title for the heading',
  `src_title_abbr` varchar(255) CHARACTER SET utf8 COLLATE utf8_general_ci NULL DEFAULT NULL COMMENT 'Src title bibliogr abbrev style, e.g., Psychoanal. Dial.',
  `src_code` varchar(14) CHARACTER SET latin1 COLLATE latin1_swedish_ci NULL DEFAULT NULL COMMENT 'PEP assigned Journal Code, e.g., IJP',
  `art_year` int NULL DEFAULT NULL COMMENT 'Year of Publication (single year only, reduced from range if there is one)',
  `art_year_str` varchar(20) CHARACTER SET utf8 COLLATE utf8_general_ci NULL DEFAULT NULL COMMENT 'Year of publicaton as in xml',
  `art_vol` int NULL DEFAULT NULL COMMENT 'Volume number for serial Publications',
  `art_vol_str` varchar(20) CHARACTER SET utf8 COLLATE utf8_general_ci NULL DEFAULT NULL COMMENT 'Exact capture of volume number in instance',
  `art_vol_suffix` char(5) CHARACTER SET latin1 COLLATE latin1_swedish_ci NULL DEFAULT NULL COMMENT 'Vol number suffix, e.g., S for supplements',
  `art_issue` char(12) CHARACTER SET latin1 COLLATE latin1_swedish_ci NULL DEFAULT '' COMMENT 'Issue number or designation, e.g., 1, or pilot (or supplement)',
  `art_pgrg` varchar(20) CHARACTER SET latin1 COLLATE latin1_swedish_ci NULL DEFAULT NULL COMMENT 'Page range of article, e.g., 1-22',
  `art_pgstart` varchar(11) CHARACTER SET utf8 COLLATE utf8_general_ci NULL DEFAULT NULL COMMENT 'Starting page number, negative for roman',
  `art_pgend` varchar(11) CHARACTER SET utf8 COLLATE utf8_general_ci NULL DEFAULT NULL COMMENT 'Ending page number, use negative for roman',
  `main_toc_id` varchar(20) CHARACTER SET latin1 COLLATE latin1_swedish_ci NULL DEFAULT NULL COMMENT 'If the source has an instance as a TOC, this is the art_id for the TOC',
  `start_sectname` varchar(255) CHARACTER SET utf8 COLLATE utf8_unicode_ci NULL DEFAULT NULL COMMENT 'When the article starts a new section in the TOC, name',
  `bk_info_xml` text CHARACTER SET utf8 COLLATE utf8_general_ci NULL COMMENT 'The full artbkinfo structure as keyed',
  `bk_title` text CHARACTER SET utf8 COLLATE utf8_general_ci NULL COMMENT 'Title of parent book which contains the article',
  `bk_publisher` varchar(255) CHARACTER SET utf8 COLLATE utf8_unicode_ci NULL DEFAULT '' COMMENT 'Publisher, e.g., Cambridge, MA / London: Harvard Univ. Press',
  `art_citeas_text` text CHARACTER SET utf8 COLLATE utf8_general_ci NULL COMMENT 'Text only format, citeas',
  `art_citeas_xml` text CHARACTER SET utf8 COLLATE utf8_general_ci NULL COMMENT 'Bibliographic style reference for article, in XML',
  `ref_count` int NULL DEFAULT NULL COMMENT 'Number of references in biblio of article',
  `filename` varchar(255) CHARACTER SET latin1 COLLATE latin1_swedish_ci NULL DEFAULT NULL COMMENT 'Filename (only) of source file',
  `filedatetime` char(25) CHARACTER SET latin1 COLLATE latin1_swedish_ci NULL DEFAULT NULL COMMENT 'Modification datetime of Article file used to detect updates needed',
  `preserve` int NULL DEFAULT 0 COMMENT 'Keep this record (probably not to be used)',
  `last_update` timestamp(0) NOT NULL DEFAULT CURRENT_TIMESTAMP(0) ON UPDATE CURRENT_TIMESTAMP(0) COMMENT 'Automatic Timestamp when record changes',
  PRIMARY KEY (`art_id`) USING BTREE,
  UNIQUE INDEX `Primary Key`(`art_id`) USING BTREE,
  UNIQUE INDEX `filename`(`filename`) USING BTREE,
  INDEX `xname`(`art_vol`) USING BTREE,
  INDEX `titlefulltext`(`art_title`(333)) USING BTREE,
  INDEX `yrjrnlcode`(`src_code`, `art_year`) USING BTREE,
  INDEX `voljrnlcode`(`src_code`, `art_vol`) USING BTREE,
  INDEX `authorfulltext`(`art_auth_citation`(255)) USING BTREE,
  INDEX `jrnlCodeIndiv`(`src_code`) USING BTREE,
  FULLTEXT INDEX `hdgtitle`(`art_title`),
  FULLTEXT INDEX `hdgauthor`(`art_auth_citation`),
  FULLTEXT INDEX `xmlref`(`art_citeas_xml`),
  FULLTEXT INDEX `bktitle`(`bk_title`)
) ENGINE = InnoDB CHARACTER SET = utf8 COLLATE = utf8_general_ci COMMENT = 'A PEP journal article, book or book section' ROW_FORMAT = Dynamic;

CREATE TABLE `api_biblioxml`  (
  `art_id` varchar(24) CHARACTER SET latin1 COLLATE latin1_swedish_ci NOT NULL,
  `bib_local_id` varchar(25) CHARACTER SET latin1 COLLATE latin1_swedish_ci NOT NULL,
  `art_year` int NULL DEFAULT NULL,
  `bib_rx` varchar(30) CHARACTER SET latin1 COLLATE latin1_swedish_ci NULL DEFAULT NULL COMMENT 'This article references...',
  `bib_rxcf` varchar(30) CHARACTER SET utf8 COLLATE utf8_general_ci NULL DEFAULT '0' COMMENT 'This article may be related to...',
  `bib_sourcecode` varchar(24) CHARACTER SET utf8 COLLATE utf8_general_ci NULL DEFAULT 'instance' COMMENT 'If it\'s refcorrections, this record came from the refcorrections table and should not be updated.',
  `bib_authors` varchar(2048) CHARACTER SET utf8 COLLATE utf8_general_ci NULL DEFAULT NULL,
  `bib_articletitle` varchar(1024) CHARACTER SET utf8 COLLATE utf8_general_ci NULL DEFAULT NULL,
  `title` varchar(255) CHARACTER SET latin1 COLLATE latin1_swedish_ci NULL DEFAULT NULL,
  `full_ref_text` text CHARACTER SET utf8 COLLATE utf8_general_ci NULL,
  `bib_sourcetype` varchar(255) CHARACTER SET utf8 COLLATE utf8_general_ci NULL DEFAULT NULL,
  `bib_sourcetitle` varchar(1024) CHARACTER SET utf8 COLLATE utf8_general_ci NULL DEFAULT NULL COMMENT 'Record the journal name as extracted from the XML referennce.  Useful to sort and check reference.',
  `bib_authors_xml` varchar(2048) CHARACTER SET utf8 COLLATE utf8_general_ci NULL DEFAULT NULL,
  `full_ref_xml` text CHARACTER SET utf8 COLLATE utf8_general_ci NULL,
  `bib_pgrg` varchar(24) CHARACTER SET utf8 COLLATE utf8_general_ci NULL DEFAULT NULL,
  `doi` varchar(255) CHARACTER SET utf8 COLLATE utf8_general_ci NULL DEFAULT NULL COMMENT 'Document Object Identifier for this reference',
  `bib_year` varchar(24) CHARACTER SET utf8 COLLATE utf8_general_ci NULL DEFAULT NULL,
  `bib_year_int` int NULL DEFAULT NULL,
  `bib_volume` varchar(24) CHARACTER SET utf8 COLLATE utf8_general_ci NULL DEFAULT NULL,
  `bib_publisher` varchar(255) CHARACTER SET utf8 COLLATE utf8_general_ci NULL DEFAULT NULL,
  `last_update` timestamp(0) NOT NULL DEFAULT CURRENT_TIMESTAMP(0) ON UPDATE CURRENT_TIMESTAMP(0),
  PRIMARY KEY (`art_id`, `bib_local_id`) USING BTREE,
  UNIQUE INDEX `Primary Key`(`art_id`, `bib_local_id`) USING BTREE,
  INDEX `articleID`(`art_id`) USING BTREE,
  INDEX `titleIndex`(`title`) USING BTREE,
  INDEX `RefersTo`(`bib_rx`) USING BTREE,
  FULLTEXT INDEX `fulreffullText`(`full_ref_text`),
  FULLTEXT INDEX `titleFullText`(`title`)
) ENGINE = InnoDB CHARACTER SET = utf8 COLLATE = utf8_general_ci COMMENT = 'All bibliographic entries within PEP' ROW_FORMAT = Dynamic;

CREATE TABLE `api_client_apps`  (
  `api_client_id` int NOT NULL,
  `api_client_name` varchar(100) CHARACTER SET utf8 COLLATE utf8_general_ci NOT NULL,
  `api_client_key` varchar(255) CHARACTER SET utf8 COLLATE utf8_general_ci NULL DEFAULT NULL,
  `last_update` timestamp(0) NOT NULL DEFAULT CURRENT_TIMESTAMP(0) ON UPDATE CURRENT_TIMESTAMP(0),
  PRIMARY KEY (`api_client_id`) USING BTREE,
  UNIQUE INDEX `idxClientname`(`api_client_name`) USING BTREE
) ENGINE = InnoDB CHARACTER SET = utf8 COLLATE = utf8_general_ci COMMENT = 'Keep track of keys assigned to clients, but not used in v1 or v2 API as of 20191110' ROW_FORMAT = Dynamic;

CREATE TABLE `api_client_configs`  (
  `config_id` int NOT NULL AUTO_INCREMENT,
  `client_id` int NULL DEFAULT NULL,
  `session_id` varchar(60) CHARACTER SET utf8 COLLATE utf8_general_ci NOT NULL,
  `config_name` varchar(255) CHARACTER SET utf8 COLLATE utf8_general_ci NOT NULL,
  `config_settings` mediumtext CHARACTER SET utf8 COLLATE utf8_general_ci NULL,
  `last_update` datetime(0) NULL DEFAULT CURRENT_TIMESTAMP(0) ON UPDATE CURRENT_TIMESTAMP(0),
  PRIMARY KEY (`config_id`, `session_id`) USING BTREE,
  UNIQUE INDEX `clientset`(`client_id`, `config_name`) USING BTREE
) ENGINE = InnoDB AUTO_INCREMENT = 353 CHARACTER SET = utf8 COLLATE = utf8_general_ci ROW_FORMAT = Dynamic;

CREATE TABLE `api_docviews`  (
  `user_id` varchar(60) CHARACTER SET utf8 COLLATE utf8_general_ci NOT NULL,
  `session_id` varchar(60) CHARACTER SET utf8 COLLATE utf8_general_ci NOT NULL,
  `document_id` varchar(255) CHARACTER SET latin1 COLLATE latin1_swedish_ci NOT NULL DEFAULT '',
  `type` varchar(255) CHARACTER SET utf8 COLLATE utf8_general_ci NOT NULL,
  `datetimechar` varchar(255) CHARACTER SET utf8 COLLATE utf8_general_ci NOT NULL,
  `last_update` timestamp(0) NULL DEFAULT CURRENT_TIMESTAMP(0) ON UPDATE CURRENT_TIMESTAMP(0),
  INDEX `user_id`(`user_id`) USING BTREE,
  INDEX `session_id`(`session_id`) USING BTREE
) ENGINE = InnoDB CHARACTER SET = utf8 COLLATE = utf8_general_ci COMMENT = 'Track the number of times a document is viewed as an abstract, full-text, PDF, or EPUB.  Somewhat redundate to api_session_endpoints table, but with less extraneous data..' ROW_FORMAT = Dynamic;

CREATE TABLE `api_endpoints`  (
  `api_endpoint_id` int NOT NULL AUTO_INCREMENT,
  `endpoint_url` varchar(200) CHARACTER SET utf8 COLLATE utf8_general_ci NOT NULL,
  `last_update` timestamp(0) NOT NULL DEFAULT CURRENT_TIMESTAMP(0) ON UPDATE CURRENT_TIMESTAMP(0),
  PRIMARY KEY (`api_endpoint_id`) USING BTREE,
  INDEX `api_endpoint_id`(`api_endpoint_id`) USING BTREE
) ENGINE = InnoDB AUTO_INCREMENT = 52 CHARACTER SET = utf8 COLLATE = utf8_general_ci COMMENT = 'Each unique API endpoint (minus base URL), starting with v1, for example\r\n' ROW_FORMAT = Dynamic;

CREATE TABLE `api_join_products_to_productbase`  (
  `product_id` int NOT NULL,
  `basecode` varchar(50) CHARACTER SET utf8 COLLATE utf8_general_ci NOT NULL,
  `extra_field` varchar(255) CHARACTER SET utf8 COLLATE utf8_general_ci NULL DEFAULT NULL,
  PRIMARY KEY (`product_id`, `basecode`) USING BTREE,
  INDEX `basecode`(`basecode`) USING BTREE,
  INDEX `product_id`(`product_id`) USING BTREE
) ENGINE = InnoDB CHARACTER SET = utf8 COLLATE = utf8_general_ci COMMENT = 'A join between products (which consist of combinations of base products, and the base product table (api_productbase)' ROW_FORMAT = Dynamic;

CREATE TABLE `api_productbase`  (
  `basecode` varchar(21) CHARACTER SET utf8 COLLATE utf8_general_ci NOT NULL DEFAULT '' COMMENT 'Shortened form of the locator',
  `articleID` varchar(24) CHARACTER SET latin1 COLLATE latin1_swedish_ci NULL DEFAULT NULL,
  `active` int NULL DEFAULT NULL,
  `pep_class` set('book','journal','videostream','special','vidostream','bookseriessub','bookserieshead') CHARACTER SET latin1 COLLATE latin1_swedish_ci NULL DEFAULT '' COMMENT '\'book\',\'journal\',\'videostream\',\'special\',\'vidostream\',\'bookseriessub\',\'bookserieshead\'',
  `pep_class_qualifier` set('glossary','works','bookseriesvolume','multivolumebook','multivolumesubbook') CHARACTER SET latin1 COLLATE latin1_swedish_ci NULL DEFAULT '' COMMENT '\'glossary\',\'works\',\'bookseriesvolume\',\'multivolumebook\',\'multivolumesubbook\'',
  `wall` int NULL DEFAULT 3,
  `mainTOC` varchar(21) CHARACTER SET latin1 COLLATE latin1_swedish_ci NULL DEFAULT '' COMMENT 'Locator for the first instance of this (or the only instance)',
  `first_author` varchar(255) CHARACTER SET utf8 COLLATE utf8_general_ci NULL DEFAULT NULL COMMENT 'Needed for KBART, easier than the join, which did lead to some problems since it\'s only the first author here',
  `author` varchar(255) CHARACTER SET utf8 COLLATE utf8_general_ci NULL DEFAULT NULL,
  `title` varchar(255) CHARACTER SET utf8 COLLATE utf8_general_ci NULL DEFAULT NULL COMMENT 'Title of Publication',
  `bibabbrev` varchar(255) CHARACTER SET utf8 COLLATE utf8_general_ci NULL DEFAULT NULL COMMENT 'bibliographic Abbreviation',
  `ISSN` varchar(22) CHARACTER SET latin1 COLLATE latin1_swedish_ci NULL DEFAULT NULL COMMENT 'ISSN for Journals only',
  `ISBN-10` varchar(13) CHARACTER SET latin1 COLLATE latin1_swedish_ci NULL DEFAULT NULL,
  `ISBN-13` varchar(17) CHARACTER SET latin1 COLLATE latin1_swedish_ci NULL DEFAULT NULL,
  `pages` int NULL DEFAULT NULL COMMENT 'Number of pages in book',
  `Comment` varchar(255) CHARACTER SET utf8 COLLATE utf8_general_ci NULL DEFAULT NULL COMMENT 'use for notes, and \"unused\" ISBN for books as journals',
  `pepcode` varchar(14) CHARACTER SET latin1 COLLATE latin1_swedish_ci NULL DEFAULT NULL,
  `publisher` varchar(255) CHARACTER SET utf8 COLLATE utf8_general_ci NULL DEFAULT NULL,
  `jrnl` tinyint(1) NULL DEFAULT 0 COMMENT '1 if this is a journal, 0 if not',
  `pub_year` int NULL DEFAULT NULL,
  `start_year` int NULL DEFAULT NULL,
  `end_year` int NULL DEFAULT NULL,
  `pep_url` varchar(255) CHARACTER SET utf8 COLLATE utf8_general_ci NULL DEFAULT NULL,
  `language` varchar(4) CHARACTER SET latin1 COLLATE latin1_swedish_ci NULL DEFAULT NULL,
  `updated` timestamp(0) NULL DEFAULT CURRENT_TIMESTAMP(0) ON UPDATE CURRENT_TIMESTAMP(0),
  `pepversion` int NULL DEFAULT NULL COMMENT 'Version it first appeared in, or planned for',
  `duplicate` varchar(10) CHARACTER SET latin1 COLLATE latin1_swedish_ci NULL DEFAULT NULL COMMENT 'Is this a duplicate (alternative) abbreviation/name (specified)',
  `landing_page` varchar(1024) CHARACTER SET utf8 COLLATE utf8_general_ci NULL DEFAULT NULL,
  `coverage_notes` varchar(255) CHARACTER SET utf8 COLLATE utf8_unicode_ci NULL DEFAULT NULL COMMENT 'Added for KBART, explain embargo if necessary',
  `landing_page_intro_html` text CHARACTER SET utf8 COLLATE utf8_general_ci NULL,
  `landing_page_end_html` text CHARACTER SET utf8 COLLATE utf8_general_ci NULL,
  `google_books_link` varchar(512) CHARACTER SET latin1 COLLATE latin1_swedish_ci NULL DEFAULT NULL,
  PRIMARY KEY (`basecode`) USING BTREE,
  INDEX `basecode`(`basecode`) USING BTREE
) ENGINE = InnoDB CHARACTER SET = utf8 COLLATE = utf8_general_ci COMMENT = 'Each ISSN Product included (from the PEP ISSN Table)\r\n\r\n' ROW_FORMAT = Dynamic;

CREATE TABLE `api_products`  (
  `product_id` int NOT NULL AUTO_INCREMENT,
  `subsystem_id` int NOT NULL DEFAULT 8,
  `product` varchar(200) CHARACTER SET utf8 COLLATE utf8_general_ci NOT NULL,
  `product_level` smallint NOT NULL DEFAULT 0,
  `product_type` varchar(40) CHARACTER SET utf8 COLLATE utf8_general_ci NULL DEFAULT NULL,
  `basecode` varchar(15) CHARACTER SET utf8 COLLATE utf8_general_ci NULL DEFAULT NULL,
  `product_comment` varchar(255) CHARACTER SET utf8 COLLATE utf8_general_ci NULL DEFAULT NULL,
  `free_access` tinyint(1) NOT NULL DEFAULT 0,
  `active` tinyint(1) NOT NULL DEFAULT 0,
  `embargo_length` tinyint(1) NULL DEFAULT NULL,
  `embargo_inverted` tinyint(1) NULL DEFAULT NULL,
  `range_limited` tinyint(1) NOT NULL DEFAULT 0,
  `range_start_year` smallint NOT NULL DEFAULT 0 COMMENT 'first available year (e.g. 0 means start in the first year',
  `range_end_year` smallint NOT NULL DEFAULT 0 COMMENT 'last available year',
  `parent_product_id` int NULL DEFAULT 0,
  `inherit_parent_metadata` tinyint(1) NOT NULL DEFAULT 1,
  `id_type` smallint NULL DEFAULT NULL,
  `counter_service` varchar(100) CHARACTER SET utf8 COLLATE utf8_general_ci NULL DEFAULT NULL,
  `counter_database` varchar(100) CHARACTER SET utf8 COLLATE utf8_general_ci NULL DEFAULT NULL,
  `counter_book` varchar(150) CHARACTER SET utf8 COLLATE utf8_general_ci NULL DEFAULT NULL,
  `counter_journal_collection` varchar(100) CHARACTER SET utf8 COLLATE utf8_general_ci NULL DEFAULT NULL,
  `id_code_1` varchar(50) CHARACTER SET utf8 COLLATE utf8_general_ci NULL DEFAULT NULL,
  `id_code_2` varchar(50) CHARACTER SET utf8 COLLATE utf8_general_ci NULL DEFAULT NULL,
  `group_sort_order` tinyint NULL DEFAULT NULL,
  `hide_in_product_access` tinyint(1) NOT NULL DEFAULT 0,
  `hide_in_report_list` tinyint(1) NOT NULL DEFAULT 0,
  `added_by_user_id` int NOT NULL DEFAULT 10,
  `date_added` datetime(0) NULL DEFAULT NULL,
  `modified_by_user_id` int NOT NULL DEFAULT 10,
  `last_update` timestamp(0) NOT NULL DEFAULT CURRENT_TIMESTAMP(0) ON UPDATE CURRENT_TIMESTAMP(0),
  PRIMARY KEY (`product_id`) USING BTREE,
  INDEX `idxSubsystemId`(`subsystem_id`) USING BTREE,
  INDEX `idxProductLevel`(`product_level`) USING BTREE,
  INDEX `idxParentProductId`(`parent_product_id`) USING BTREE,
  INDEX `basecode`(`basecode`) USING BTREE
) ENGINE = InnoDB AUTO_INCREMENT = 4001 CHARACTER SET = utf8 COLLATE = utf8_general_ci ROW_FORMAT = Dynamic;

CREATE TABLE `api_session_endpoints`  (
  `session_id` varchar(60) CHARACTER SET utf8 COLLATE utf8_general_ci NOT NULL,
  `api_endpoint_id` int NOT NULL,
  `api_method` varchar(12) CHARACTER SET utf8 COLLATE utf8_general_ci NULL DEFAULT 'get' COMMENT 'get, put, post, delete, ... Default: get',
  `params` varchar(2500) CHARACTER SET utf8 COLLATE utf8_general_ci NULL DEFAULT NULL,
  `item_of_interest` varchar(60) CHARACTER SET utf8 COLLATE utf8_general_ci NULL DEFAULT NULL,
  `return_status_code` int NULL DEFAULT NULL,
  `return_added_status_message` varchar(255) CHARACTER SET utf8 COLLATE utf8_general_ci NULL DEFAULT NULL,
  `last_update` timestamp(0) NOT NULL DEFAULT CURRENT_TIMESTAMP(0) ON UPDATE CURRENT_TIMESTAMP(0),
  INDEX `fk_session_id`(`session_id`) USING BTREE,
  INDEX `fk_endpoint`(`api_endpoint_id`) USING BTREE
) ENGINE = InnoDB CHARACTER SET = utf8 COLLATE = utf8_general_ci COMMENT = 'All endpoints called in a session, and parameters defining searches, retrievals etc..\r\n\r\n' ROW_FORMAT = Dynamic;

CREATE TABLE `api_sessions`  (
  `session_id` varchar(60) CHARACTER SET utf8 COLLATE utf8_general_ci NOT NULL,
  `user_id` int NULL DEFAULT NULL,
  `username` varchar(255) CHARACTER SET ujis COLLATE ujis_japanese_ci NULL DEFAULT NULL,
  `api_client_id` int NOT NULL,
  `user_ip` varchar(60) CHARACTER SET utf8 COLLATE utf8_general_ci NULL DEFAULT NULL,
  `connected_via` varchar(512) CHARACTER SET utf8 COLLATE utf8_general_ci NULL DEFAULT NULL,
  `referrer` varchar(512) CHARACTER SET utf8 COLLATE utf8_general_ci NULL DEFAULT NULL,
  `session_start` timestamp(0) NOT NULL,
  `session_end` timestamp(0) NULL DEFAULT NULL,
  `session_expires_time` timestamp(0) NULL DEFAULT NULL,
  `access_token` varchar(1000) CHARACTER SET utf8 COLLATE utf8_general_ci NULL DEFAULT NULL COMMENT 'a JWT so could be long',
  `authenticated` tinyint(1) NULL DEFAULT 0,
  `admin` tinyint(1) NOT NULL DEFAULT 0,
  `api_client_session` tinyint(1) NULL DEFAULT NULL,
  `authorized_peparchive` tinyint(1) NULL DEFAULT NULL,
  `authorized_pepcurrent` tinyint(1) NULL DEFAULT NULL,
  `last_update` timestamp(0) NULL DEFAULT CURRENT_TIMESTAMP(0) ON UPDATE CURRENT_TIMESTAMP(0),
  PRIMARY KEY (`session_id`) USING BTREE,
  UNIQUE INDEX `idxSession`(`session_id`) USING BTREE,
  INDEX `session_user`(`user_id`) USING BTREE
) ENGINE = InnoDB CHARACTER SET = utf8 COLLATE = utf8_general_ci COMMENT = 'Each API session with a unique ID creates a session record. ' ROW_FORMAT = Dynamic;

CREATE TABLE `api_subscriptions`  (
  `user_id` int NOT NULL,
  `product_id` int NOT NULL,
  `start_date` datetime(0) NOT NULL,
  `end_date` datetime(0) NOT NULL,
  `max_concurrency` int NOT NULL,
  `perpetual` tinyint(1) NOT NULL DEFAULT 0,
  `modified_by_user_id` int NOT NULL,
  `last_update` timestamp(0) NOT NULL DEFAULT CURRENT_TIMESTAMP(0) ON UPDATE CURRENT_TIMESTAMP(0),
  PRIMARY KEY (`user_id`, `product_id`) USING BTREE,
  INDEX `idxStartDate`(`start_date`) USING BTREE,
  INDEX `idxEndDate`(`end_date`) USING BTREE,
  INDEX `idxProductId`(`product_id`) USING BTREE
) ENGINE = InnoDB CHARACTER SET = utf8 COLLATE = utf8_general_ci ROW_FORMAT = Dynamic;

CREATE TABLE `api_user`  (
  `user_id` int NOT NULL AUTO_INCREMENT,
  `username` varchar(255) CHARACTER SET utf8 COLLATE utf8_general_ci NOT NULL,
  `password` varchar(512) CHARACTER SET utf8 COLLATE utf8_general_ci NOT NULL,
  `full_name` varchar(255) CHARACTER SET utf8 COLLATE utf8_general_ci NULL DEFAULT NULL,
  `company` varchar(125) CHARACTER SET utf8 COLLATE utf8_general_ci NULL DEFAULT NULL,
  `email_address` varchar(65) CHARACTER SET utf8 COLLATE utf8_general_ci NULL DEFAULT NULL,
  `enabled` tinyint(1) NULL DEFAULT 0,
  `authorized_peparchive` tinyint(1) NULL DEFAULT 0,
  `authorized_pepcurrent` tinyint(1) NULL DEFAULT 0,
  `admin` tinyint(1) NULL DEFAULT 0,
  `user_agrees_date` datetime(0) NULL DEFAULT CURRENT_TIMESTAMP(0),
  `user_agrees_to_tracking` tinyint(1) NULL DEFAULT 0,
  `user_agrees_to_cookies` tinyint(1) NULL DEFAULT 0,
  `email_optin` tinyint(1) NOT NULL DEFAULT 1,
  `hide_activity` tinyint(1) NOT NULL DEFAULT 0,
  `parent_user_id` int NOT NULL DEFAULT 0,
  `administrative_group_id` int NOT NULL DEFAULT 64,
  `view_parent_user_reports` tinyint(1) NOT NULL DEFAULT 0,
  `deleted` tinyint(1) NOT NULL DEFAULT 0,
  `modified_by_user_id` int NULL DEFAULT NULL,
  `added_by_user_id` int NULL DEFAULT NULL,
  `added_date` datetime(0) NULL DEFAULT NULL,
  `last_update` timestamp(0) NOT NULL DEFAULT CURRENT_TIMESTAMP(0) ON UPDATE CURRENT_TIMESTAMP(0),
  PRIMARY KEY (`user_id`) USING BTREE,
  UNIQUE INDEX `unique_username`(`username`) USING BTREE,
  INDEX `idxUsername`(`username`) USING BTREE,
  INDEX `user_administrative_group`(`administrative_group_id`) USING BTREE
) ENGINE = InnoDB AUTO_INCREMENT = 119412 CHARACTER SET = utf8 COLLATE = utf8_general_ci COMMENT = 'A list of all authorized users, but the NOT_LOGGED_IN user, with ID=0, as they are not authorized!' ROW_FORMAT = Dynamic;

CREATE TABLE `api_user_ip_ranges`  (
  `ip_addresses_id` int NOT NULL AUTO_INCREMENT,
  `user_id` int NOT NULL,
  `start_ip_address` bigint NOT NULL,
  `end_ip_address` bigint NOT NULL,
  `modified_by_user_id` int NOT NULL,
  `last_update` timestamp(0) NOT NULL DEFAULT CURRENT_TIMESTAMP(0) ON UPDATE CURRENT_TIMESTAMP(0),
  PRIMARY KEY (`ip_addresses_id`) USING BTREE,
  INDEX `idxSubsystemIdUserId`(`user_id`) USING BTREE,
  INDEX `idxStartIpAddress`(`start_ip_address`) USING BTREE,
  INDEX `idxEndIpAddress`(`end_ip_address`) USING BTREE,
  INDEX `idxUserId`(`user_id`) USING BTREE,
  INDEX `FK_ip_addresses_user_subsystem`(`user_id`) USING BTREE
) ENGINE = InnoDB AUTO_INCREMENT = 25024 CHARACTER SET = utf8 COLLATE = utf8_general_ci ROW_FORMAT = Dynamic;

CREATE TABLE `api_user_property_name`  (
  `user_property_name_id` int NOT NULL AUTO_INCREMENT,
  `user_property_name` varchar(50) CHARACTER SET utf8 COLLATE utf8_general_ci NOT NULL,
  `user_property_data_type_id` smallint NOT NULL,
  `sort_order` smallint NOT NULL,
  `user_property_user_access_id` smallint NOT NULL,
  `default_value` varchar(1000) CHARACTER SET utf8 COLLATE utf8_general_ci NULL DEFAULT NULL,
  `display_width` smallint NULL DEFAULT NULL,
  `display_height` smallint NULL DEFAULT NULL,
  `modified_by_user_id` int NOT NULL,
  `last_update` timestamp(0) NOT NULL DEFAULT CURRENT_TIMESTAMP(0) ON UPDATE CURRENT_TIMESTAMP(0),
  PRIMARY KEY (`user_property_name_id`) USING BTREE,
  INDEX `FK_user_property_name_ref_user_property_data_type`(`user_property_data_type_id`) USING BTREE,
  INDEX `FK_user_property_name_ref_user_property_user_access`(`user_property_user_access_id`) USING BTREE
) ENGINE = InnoDB AUTO_INCREMENT = 169 CHARACTER SET = utf8 COLLATE = utf8_general_ci ROW_FORMAT = Dynamic;

CREATE TABLE `api_user_property_value`  (
  `user_property_value_id` int NOT NULL AUTO_INCREMENT,
  `user_id` int NOT NULL,
  `user_property_name_id` int NOT NULL,
  `user_property_value` varchar(5000) CHARACTER SET utf8 COLLATE utf8_general_ci NOT NULL,
  `modified_by_user_id` int NOT NULL,
  `last_update` timestamp(0) NOT NULL DEFAULT CURRENT_TIMESTAMP(0),
  PRIMARY KEY (`user_property_value_id`) USING BTREE,
  UNIQUE INDEX `IX_user_property_value`(`user_id`, `user_property_name_id`) USING BTREE,
  INDEX `idxUserPropertyNameId`(`user_property_name_id`) USING BTREE
) ENGINE = InnoDB AUTO_INCREMENT = 577755 CHARACTER SET = utf8 COLLATE = utf8_general_ci ROW_FORMAT = Dynamic;

CREATE TABLE `api_user_referrer_urls`  (
  `referrer_urls_id` int NOT NULL AUTO_INCREMENT,
  `user_id` int NOT NULL,
  `referrer_url` varchar(500) CHARACTER SET utf8 COLLATE utf8_general_ci NOT NULL,
  `modified_by_user_id` int NOT NULL,
  `last_update` timestamp(0) NOT NULL DEFAULT CURRENT_TIMESTAMP(0) ON UPDATE CURRENT_TIMESTAMP(0),
  PRIMARY KEY (`referrer_urls_id`) USING BTREE,
  INDEX `idxSubsystemIdUserId`(`user_id`) USING BTREE,
  INDEX `idxReferrerUrl`(`referrer_url`(255)) USING BTREE,
  INDEX `idxUserId`(`user_id`) USING BTREE,
  INDEX `FK_referrer_urls_user_subsystem`(`user_id`) USING BTREE
) ENGINE = InnoDB AUTO_INCREMENT = 2001 CHARACTER SET = utf8 COLLATE = utf8_general_ci ROW_FORMAT = Dynamic;

ALTER TABLE `api_docviews` ADD CONSTRAINT `api_docviews_ibfk_1` FOREIGN KEY (`session_id`) REFERENCES `api_sessions` (`session_id`) ON DELETE RESTRICT ON UPDATE RESTRICT;
ALTER TABLE `api_join_products_to_productbase` ADD CONSTRAINT `api_join_products_to_productbase_ibfk_1` FOREIGN KEY (`basecode`) REFERENCES `api_productbase` (`basecode`) ON DELETE CASCADE ON UPDATE CASCADE;
ALTER TABLE `api_join_products_to_productbase` ADD CONSTRAINT `api_join_products_to_productbase_ibfk_2` FOREIGN KEY (`product_id`) REFERENCES `api_products` (`product_id`) ON DELETE CASCADE ON UPDATE CASCADE;
ALTER TABLE `api_session_endpoints` ADD CONSTRAINT `fk_endpoint` FOREIGN KEY (`api_endpoint_id`) REFERENCES `api_endpoints` (`api_endpoint_id`) ON DELETE RESTRICT ON UPDATE RESTRICT;
ALTER TABLE `api_session_endpoints` ADD CONSTRAINT `fk_session` FOREIGN KEY (`session_id`) REFERENCES `api_sessions` (`session_id`) ON DELETE CASCADE ON UPDATE CASCADE;
ALTER TABLE `api_subscriptions` ADD CONSTRAINT `subscribed_product` FOREIGN KEY (`product_id`) REFERENCES `api_products` (`product_id`) ON DELETE CASCADE ON UPDATE CASCADE;
ALTER TABLE `api_subscriptions` ADD CONSTRAINT `subscribed_user` FOREIGN KEY (`user_id`) REFERENCES `api_user` (`user_id`) ON DELETE CASCADE ON UPDATE CASCADE;
ALTER TABLE `api_user` ADD CONSTRAINT `user_administrative_group` FOREIGN KEY (`administrative_group_id`) REFERENCES `api_administrative_groups` (`administrative_group_id`) ON DELETE CASCADE ON UPDATE CASCADE;
ALTER TABLE `api_user_ip_ranges` ADD CONSTRAINT `ip_user` FOREIGN KEY (`user_id`) REFERENCES `api_user` (`user_id`) ON DELETE CASCADE ON UPDATE CASCADE;
ALTER TABLE `api_user_property_value` ADD CONSTRAINT `property_name` FOREIGN KEY (`user_property_name_id`) REFERENCES `api_user_property_name` (`user_property_name_id`) ON DELETE CASCADE ON UPDATE CASCADE;
ALTER TABLE `api_user_property_value` ADD CONSTRAINT `property_user` FOREIGN KEY (`user_id`) REFERENCES `api_user` (`user_id`) ON DELETE CASCADE ON UPDATE CASCADE;
ALTER TABLE `api_user_referrer_urls` ADD CONSTRAINT `referral_url_user` FOREIGN KEY (`user_id`) REFERENCES `api_user` (`user_id`) ON DELETE CASCADE ON UPDATE CASCADE;

CREATE ALGORITHM = UNDEFINED DEFINER = `root`@`localhost` SQL SECURITY DEFINER VIEW `vw_api_productbase` AS select `api_productbase`.`basecode` AS `basecode`,`api_productbase`.`articleID` AS `articleID`,`api_productbase`.`active` AS `active`,`api_productbase`.`pep_class` AS `product_type`,`api_productbase`.`pep_class_qualifier` AS `product_type_qualifier`,`api_productbase`.`wall` AS `embargo`,`api_productbase`.`mainTOC` AS `mainTOC`,`api_productbase`.`first_author` AS `first_author`,`api_productbase`.`author` AS `author`,`api_productbase`.`title` AS `title`,`api_productbase`.`bibabbrev` AS `bibabbrev`,`api_productbase`.`ISSN` AS `ISSN`,`api_productbase`.`ISBN-10` AS `ISBN-10`,`api_productbase`.`ISBN-13` AS `ISBN-13`,`api_productbase`.`pages` AS `pages`,`api_productbase`.`Comment` AS `Comment`,`api_productbase`.`pepcode` AS `pepcode`,`api_productbase`.`publisher` AS `publisher`,`api_productbase`.`jrnl` AS `jrnl`,`api_productbase`.`pub_year` AS `pub_year`,`api_productbase`.`start_year` AS `start_year`,`api_productbase`.`end_year` AS `end_year`,`api_productbase`.`pep_url` AS `pep_url`,`api_productbase`.`language` AS `language`,`api_productbase`.`updated` AS `updated`,`api_productbase`.`pepversion` AS `pepversion`,`api_productbase`.`duplicate` AS `duplicate`,`api_productbase`.`landing_page` AS `landing_page`,`api_productbase`.`coverage_notes` AS `coverage_notes`,`api_productbase`.`landing_page_intro_html` AS `landing_page_intro_html`,`api_productbase`.`landing_page_end_html` AS `landing_page_end_html`,`api_productbase`.`google_books_link` AS `google_books_link` from `api_productbase`;

CREATE ALGORITHM = UNDEFINED DEFINER = `root`@`localhost` SQL SECURITY DEFINER VIEW `vw_api_sourceinfodb` AS select `api_productbase`.`basecode` AS `pepsrccode`,`api_productbase`.`basecode` AS `basecode`,`api_productbase`.`active` AS `active`,`api_productbase`.`bibabbrev` AS `sourcetitleabbr`,`api_productbase`.`jrnl` AS `source`,`api_productbase`.`start_year` AS `start_year`,`api_productbase`.`end_year` AS `end_year`,`api_productbase`.`pep_url` AS `pep_url`,`api_productbase`.`language` AS `language`,`api_productbase`.`title` AS `sourcetitlefull`,`api_productbase`.`pep_class` AS `product_type`,`api_productbase`.`pep_class_qualifier` AS `product_type_qualifier`,`api_productbase`.`wall` AS `embargo`,`api_productbase`.`mainTOC` AS `mainTOC`,`api_productbase`.`author` AS `author`,`api_productbase`.`updated` AS `updated`,`api_productbase`.`landing_page` AS `landing_page`,`api_productbase`.`google_books_link` AS `google_books_link`,`api_productbase`.`pepversion` AS `pepversion`,`api_productbase`.`publisher` AS `publisher`,`api_productbase`.`ISSN` AS `ISSN`,`api_productbase`.`ISBN-10` AS `ISBN-10`,`api_productbase`.`ISBN-13` AS `ISBN-13`,`api_productbase`.`pages` AS `pages`,`api_productbase`.`articleID` AS `articleID`,`api_productbase`.`first_author` AS `first_author`,`api_productbase`.`bibabbrev` AS `bibabbrev`,`api_productbase`.`Comment` AS `Comment`,`api_productbase`.`pepcode` AS `pepcode`,`api_productbase`.`pub_year` AS `pub_year`,`api_productbase`.`duplicate` AS `duplicate`,`api_productbase`.`coverage_notes` AS `coverage_notes`,`api_productbase`.`landing_page_intro_html` AS `landing_page_intro_html`,`api_productbase`.`landing_page_end_html` AS `landing_page_end_html` from `api_productbase`;

CREATE ALGORITHM = UNDEFINED DEFINER = `root`@`localhost` SQL SECURITY DEFINER VIEW `vw_api_user` AS select `api_user`.`user_id` AS `user_id`,`api_user`.`username` AS `username`,`api_user`.`full_name` AS `full_name`,`api_user`.`company` AS `company`,`api_user`.`email_address` AS `email_address`,`api_user`.`enabled` AS `enabled`,`api_user`.`parent_user_id` AS `parent_user_id`,`api_user`.`password` AS `password`,`api_user`.`user_agrees_date` AS `user_agrees_date`,`api_user`.`user_agrees_to_tracking` AS `user_agrees_to_tracking`,`api_user`.`user_agrees_to_cookies` AS `user_agrees_to_cookies`,`api_user`.`admin` AS `admin`,`api_user`.`email_optin` AS `email_optin`,`api_user`.`administrative_group_id` AS `administrative_group_id` from `api_user`;

CREATE ALGORITHM = UNDEFINED DEFINER = `root`@`localhost` SQL SECURITY DEFINER VIEW `vw_latest_session_activity` AS select `api_session_endpoints`.`session_id` AS `session_id`,max(`api_session_endpoints`.`last_update`) AS `latest_activity` from `api_session_endpoints` group by `api_session_endpoints`.`session_id` order by max(`api_session_endpoints`.`last_update`) desc;

CREATE ALGORITHM = UNDEFINED DEFINER = `root`@`localhost` SQL SECURITY DEFINER VIEW `vw_products_flattened` AS select `product`.`product_id` AS `child_product_id`,`product`.`product` AS `child_product`,`product`.`basecode` AS `child_basecode`,`product`.`product_level` AS `child_product_level`,`parent`.`product_id` AS `parent_product_id`,`parent`.`product` AS `parent_product`,`parent`.`basecode` AS `parent_basecode`,`parent`.`product_level` AS `parent_product_level`,`product`.`inherit_parent_metadata` AS `inherit_parent_metadata` from (`api_products` `parent` join `api_products` `product` on(((`parent`.`product_level` = 1) and (`product`.`parent_product_id` = `parent`.`product_id`)))) union select `product`.`product_id` AS `child_product_id`,`product`.`product` AS `child_product`,`product`.`basecode` AS `child_basecode`,`product`.`product_level` AS `child_product_level`,`parent`.`product_id` AS `parent_product_id`,`parent`.`product` AS `parent_product`,`parent`.`basecode` AS `parent_basecode`,`parent`.`product_level` AS `parent_product_level`,`product`.`inherit_parent_metadata` AS `inherit_parent_metadata` from (`api_products` `parent` join `api_products` `product` on(((`parent`.`product_level` = 2) and (`product`.`parent_product_id` = `parent`.`product_id`)))) union select `product`.`product_id` AS `child_product_id`,`product`.`product` AS `child_product`,`product`.`basecode` AS `child_basecode`,`product`.`product_level` AS `child_product_level`,`parent`.`product_id` AS `parent_product_id`,`parent`.`product` AS `parent_product`,`parent`.`basecode` AS `parent_basecode`,`parent`.`product_level` AS `parent_product_level`,`product`.`inherit_parent_metadata` AS `inherit_parent_metadata` from (`api_products` `parent` join `api_products` `product` on(((`parent`.`product_level` = 3) and (`product`.`parent_product_id` = `parent`.`product_id`))));

CREATE ALGORITHM = UNDEFINED DEFINER = `root`@`localhost` SQL SECURITY DEFINER VIEW `vw_reports_document_views` AS select `api_docviews`.`document_id` AS `document_id`,any_value(`api_docviews`.`type`) AS `view_type`,count(0) AS `views` from (`api_docviews` join `api_user`) where ((`api_docviews`.`type` = 'Document') and (`api_user`.`user_id` = `api_docviews`.`user_id`)) group by `api_docviews`.`document_id`;

CREATE ALGORITHM = UNDEFINED DEFINER = `root`@`localhost` SQL SECURITY DEFINER VIEW `vw_reports_session_activity` AS select `api_session_endpoints`.`session_id` AS `session_id`,`api_user`.`username` AS `global_uid`,`api_sessions`.`connected_via` AS `connected_via`,`api_sessions`.`referrer` AS `referrer`,`api_sessions`.`session_start` AS `session_start`,`api_sessions`.`session_end` AS `session_end`,`api_session_endpoints`.`item_of_interest` AS `item_of_interest`,`api_endpoints`.`endpoint_url` AS `endpoint`,`api_session_endpoints`.`params` AS `params`,`api_session_endpoints`.`return_status_code` AS `return_status_code`,`api_session_endpoints`.`return_added_status_message` AS `return_added_status_message`,`api_session_endpoints`.`last_update` AS `last_update` from (((`api_user` join `api_sessions` on((`api_sessions`.`user_id` = `api_user`.`user_id`))) join `api_session_endpoints` on((`api_session_endpoints`.`session_id` = `api_sessions`.`session_id`))) join `api_endpoints` on((`api_endpoints`.`api_endpoint_id` = `api_session_endpoints`.`api_endpoint_id`))) order by `api_session_endpoints`.`last_update` desc;

CREATE ALGORITHM = UNDEFINED DEFINER = `root`@`localhost` SQL SECURITY DEFINER VIEW `vw_reports_user_searches` AS select `api_user`.`username` AS `global_uid`,`api_session_endpoints`.`session_id` AS `session_id`,`api_sessions`.`session_start` AS `session_start`,`api_session_endpoints`.`item_of_interest` AS `item_of_interest`,`api_endpoints`.`endpoint_url` AS `endpoint`,`api_session_endpoints`.`params` AS `params`,`api_session_endpoints`.`return_status_code` AS `return_status_code`,`api_session_endpoints`.`return_added_status_message` AS `return_added_status_message`,`api_session_endpoints`.`last_update` AS `last_update` from (((`api_user` join `api_sessions` on((`api_sessions`.`user_id` = `api_user`.`user_id`))) join `api_session_endpoints` on((`api_session_endpoints`.`session_id` = `api_sessions`.`session_id`))) join `api_endpoints` on((`api_endpoints`.`api_endpoint_id` = `api_session_endpoints`.`api_endpoint_id`))) order by `api_endpoints`.`last_update` desc;

CREATE ALGORITHM = UNDEFINED DEFINER = `root`@`localhost` SQL SECURITY DEFINER VIEW `vw_stat_cited_crosstab` AS select `r0`.`cited_document_id` AS `cited_document_id`,any_value(coalesce(`r1`.`count5`,0)) AS `count5`,any_value(coalesce(`r2`.`count10`,0)) AS `count10`,any_value(coalesce(`r3`.`count20`,0)) AS `count20`,any_value(coalesce(`r4`.`countAll`,0)) AS `countAll` from ((((((select distinct `opascentral`.`api_biblioxml`.`art_id` AS `articleID`,`opascentral`.`api_biblioxml`.`bib_local_id` AS `internalID`,`opascentral`.`api_biblioxml`.`full_ref_xml` AS `fullReference`,`opascentral`.`api_biblioxml`.`bib_rx` AS `cited_document_id` from `opascentral`.`api_biblioxml`)) `r0` left join `opascentral`.`vw_stat_cited_in_last_5_years` `r1` on((`r1`.`cited_document_id` = `r0`.`cited_document_id`))) left join `opascentral`.`vw_stat_cited_in_last_10_years` `r2` on((`r2`.`cited_document_id` = `r0`.`cited_document_id`))) left join `opascentral`.`vw_stat_cited_in_last_20_years` `r3` on((`r3`.`cited_document_id` = `r0`.`cited_document_id`))) left join `opascentral`.`vw_stat_cited_in_all_years` `r4` on((`r4`.`cited_document_id` = `r0`.`cited_document_id`))) where ((`r0`.`cited_document_id` is not null) and (`r0`.`cited_document_id` <> 'None') and (substr(`r0`.`cited_document_id`,1,3) not in ('ZBK','IPL','SE.','GW.'))) group by `r0`.`cited_document_id` order by `countAll` desc;

CREATE ALGORITHM = UNDEFINED DEFINER = `root`@`localhost` SQL SECURITY DEFINER VIEW `vw_stat_cited_crosstab_with_details` AS select `vw_stat_cited_crosstab`.`cited_document_id` AS `cited_document_id`,`vw_stat_cited_crosstab`.`count5` AS `count5`,`vw_stat_cited_crosstab`.`count10` AS `count10`,`vw_stat_cited_crosstab`.`count20` AS `count20`,`vw_stat_cited_crosstab`.`countAll` AS `countAll`,`opascentral`.`api_articles`.`art_auth_citation` AS `hdgauthor`,`opascentral`.`api_articles`.`art_title` AS `hdgtitle`,`opascentral`.`api_articles`.`src_title_abbr` AS `srctitleseries`,`opascentral`.`api_articles`.`src_code` AS `source_code`,`opascentral`.`api_articles`.`art_year` AS `year`,`opascentral`.`api_articles`.`art_vol` AS `vol`,`opascentral`.`api_articles`.`art_pgrg` AS `pgrg`,`opascentral`.`api_articles`.`art_id` AS `art_id`,`opascentral`.`api_articles`.`art_citeas_text` AS `art_citeas_text` from (`opascentral`.`vw_stat_cited_crosstab` join `opascentral`.`api_articles` on((`vw_stat_cited_crosstab`.`cited_document_id` = `opascentral`.`api_articles`.`art_id`))) order by `vw_stat_cited_crosstab`.`countAll` desc;

CREATE ALGORITHM = UNDEFINED DEFINER = `root`@`localhost` SQL SECURITY DEFINER VIEW `vw_stat_cited_in_all_years` AS select `api_biblioxml`.`bib_rx` AS `cited_document_id`,count(0) AS `countAll` from `api_biblioxml` where ((`api_biblioxml`.`bib_rx` is not null) and (`api_biblioxml`.`bib_rx` <> '') and (substr(`api_biblioxml`.`bib_rx`,1,3) not in ('ZBK','IPL','SE.','GW.'))) group by `api_biblioxml`.`bib_rx` order by `countAll` desc;

CREATE ALGORITHM = UNDEFINED DEFINER = `root`@`localhost` SQL SECURITY DEFINER VIEW `vw_stat_cited_in_last_10_years` AS select `api_biblioxml`.`bib_rx` AS `cited_document_id`,count(0) AS `count10` from (`api_biblioxml` join `api_articles` `citing_article`) where ((`api_biblioxml`.`art_id` = `citing_article`.`art_id`) and (`api_biblioxml`.`bib_rx` is not null) and (`api_biblioxml`.`bib_rx` <> '') and (`citing_article`.`art_year` > (year(now()) - 10)) and (substr(`api_biblioxml`.`bib_rx`,1,3) not in ('ZBK','IPL','SE.','GW.'))) group by `api_biblioxml`.`bib_rx` order by `count10` desc;

CREATE ALGORITHM = UNDEFINED DEFINER = `root`@`localhost` SQL SECURITY DEFINER VIEW `vw_stat_cited_in_last_20_years` AS select `api_biblioxml`.`bib_rx` AS `cited_document_id`,count(0) AS `count20` from (`api_biblioxml` join `api_articles` `citing_article`) where ((`api_biblioxml`.`art_id` = `citing_article`.`art_id`) and (`api_biblioxml`.`bib_rx` is not null) and (`api_biblioxml`.`bib_rx` <> '') and (`citing_article`.`art_year` > (year(now()) - 20)) and (substr(`api_biblioxml`.`bib_rx`,1,3) not in ('ZBK','IPL','SE.','GW.'))) group by `api_biblioxml`.`bib_rx` order by `count20` desc;

CREATE ALGORITHM = UNDEFINED DEFINER = `root`@`localhost` SQL SECURITY DEFINER VIEW `vw_stat_cited_in_last_5_years` AS select `api_biblioxml`.`bib_rx` AS `cited_document_id`,count(0) AS `count5` from (`api_biblioxml` join `api_articles` `citing_article`) where ((`api_biblioxml`.`art_id` = `citing_article`.`art_id`) and (`api_biblioxml`.`bib_rx` is not null) and (`api_biblioxml`.`bib_rx` <> '') and (`citing_article`.`art_year` > (year(now()) - 5)) and (substr(`api_biblioxml`.`bib_rx`,1,3) not in ('ZBK','IPL','SE.','GW.'))) group by `api_biblioxml`.`bib_rx` order by `count5` desc;

CREATE ALGORITHM = UNDEFINED DEFINER = `root`@`localhost` SQL SECURITY DEFINER VIEW `vw_stat_docviews_crosstab` AS select `r0`.`document_id` AS `document_id`,any_value(max(`r0`.`last_viewed`)) AS `last_viewed`,any_value(coalesce(`r1`.`views`,0)) AS `lastweek`,any_value(coalesce(`r2`.`views`,0)) AS `lastmonth`,any_value(coalesce(`r3`.`views`,0)) AS `last6months`,any_value(coalesce(`r5`.`views`,0)) AS `last12months`,any_value(coalesce(`r4`.`views`,0)) AS `lastcalyear` from (((((((select distinct `opascentral`.`api_docviews`.`document_id` AS `document_id`,`opascentral`.`api_docviews`.`last_update` AS `last_viewed` from `opascentral`.`api_docviews` where (`opascentral`.`api_docviews`.`type` = 'Document'))) `r0` left join `opascentral`.`vw_stat_docviews_lastweek` `r1` on((`r1`.`document_id` = `r0`.`document_id`))) left join `opascentral`.`vw_stat_docviews_lastmonth` `r2` on((`r2`.`document_id` = `r0`.`document_id`))) left join `opascentral`.`vw_stat_docviews_lastsixmonths` `r3` on((`r3`.`document_id` = `r0`.`document_id`))) left join `opascentral`.`vw_stat_docviews_lastcalyear` `r4` on((`r4`.`document_id` = `r0`.`document_id`))) left join `opascentral`.`vw_stat_docviews_last12months` `r5` on((`r5`.`document_id` = `r0`.`document_id`))) where ((`r0`.`document_id` is not null) and (`r0`.`document_id` <> 'None')) group by `r0`.`document_id`;

CREATE ALGORITHM = UNDEFINED DEFINER = `root`@`localhost` SQL SECURITY DEFINER VIEW `vw_stat_docviews_last12months` AS select `api_docviews`.`document_id` AS `document_id`,count(0) AS `views` from `api_docviews` where ((`api_docviews`.`datetimechar` > (now() - interval 12 month)) and (`api_docviews`.`type` = 'Document')) group by `api_docviews`.`document_id`;

CREATE ALGORITHM = UNDEFINED DEFINER = `root`@`localhost` SQL SECURITY DEFINER VIEW `vw_stat_docviews_lastcalyear` AS select `api_docviews`.`document_id` AS `document_id`,count(0) AS `views` from `api_docviews` where ((year(`api_docviews`.`datetimechar`) = (year(now()) - 1)) and (`api_docviews`.`type` = 'Document')) group by `api_docviews`.`document_id`;

CREATE ALGORITHM = UNDEFINED DEFINER = `root`@`localhost` SQL SECURITY DEFINER VIEW `vw_stat_docviews_lastmonth` AS select `api_docviews`.`document_id` AS `document_id`,count(0) AS `views` from `api_docviews` where ((`api_docviews`.`datetimechar` > (now() - interval 1 month)) and (`api_docviews`.`type` = 'Document')) group by `api_docviews`.`document_id`;

CREATE ALGORITHM = UNDEFINED DEFINER = `root`@`localhost` SQL SECURITY DEFINER VIEW `vw_stat_docviews_lastsixmonths` AS select `api_docviews`.`document_id` AS `document_id`,count(0) AS `views` from `api_docviews` where ((`api_docviews`.`datetimechar` > (now() - interval 6 month)) and (`api_docviews`.`type` = 'Document')) group by `api_docviews`.`document_id`;

CREATE ALGORITHM = UNDEFINED DEFINER = `root`@`localhost` SQL SECURITY DEFINER VIEW `vw_stat_docviews_lastweek` AS select `api_docviews`.`document_id` AS `document_id`,any_value(`api_docviews`.`type`) AS `view_type`,count(0) AS `views` from `api_docviews` where ((`api_docviews`.`datetimechar` > (now() - interval 7 day)) and (`api_docviews`.`type` = 'Document')) group by `api_docviews`.`document_id`;

CREATE ALGORITHM = UNDEFINED DEFINER = `root`@`localhost` SQL SECURITY DEFINER VIEW `vw_stat_most_viewed` AS select `vw_stat_docviews_crosstab`.`document_id` AS `document_id`,`vw_stat_docviews_crosstab`.`last_viewed` AS `last_viewed`,coalesce(`vw_stat_docviews_crosstab`.`lastweek`,0) AS `lastweek`,coalesce(`vw_stat_docviews_crosstab`.`lastmonth`,0) AS `lastmonth`,coalesce(`vw_stat_docviews_crosstab`.`last6months`,0) AS `last6months`,coalesce(`vw_stat_docviews_crosstab`.`last12months`,0) AS `last12months`,coalesce(`vw_stat_docviews_crosstab`.`lastcalyear`,0) AS `lastcalyear`,`opascentral`.`api_articles`.`art_auth_citation` AS `hdgauthor`,`opascentral`.`api_articles`.`art_title` AS `hdgtitle`,`opascentral`.`api_articles`.`src_title_abbr` AS `srctitleseries`,`opascentral`.`api_articles`.`bk_publisher` AS `publisher`,`opascentral`.`api_articles`.`src_code` AS `source_code`,`opascentral`.`api_articles`.`art_year` AS `pubyear`,`opascentral`.`api_articles`.`art_vol` AS `vol`,`opascentral`.`api_articles`.`art_pgrg` AS `pgrg`,`opascentral`.`api_productbase`.`pep_class` AS `source_type`,`opascentral`.`api_articles`.`preserve` AS `preserve`,`opascentral`.`api_articles`.`filename` AS `filename`,`opascentral`.`api_articles`.`bk_title` AS `bktitle`,`opascentral`.`api_articles`.`bk_info_xml` AS `bk_info_xml`,`opascentral`.`api_articles`.`art_citeas_xml` AS `xmlref`,`opascentral`.`api_articles`.`art_citeas_text` AS `textref`,`opascentral`.`api_articles`.`art_auth_mast` AS `authorMast`,`opascentral`.`api_articles`.`art_issue` AS `issue`,`opascentral`.`api_articles`.`last_update` AS `last_update` from ((`opascentral`.`vw_stat_docviews_crosstab` join `opascentral`.`api_articles` on((`opascentral`.`api_articles`.`art_id` = `vw_stat_docviews_crosstab`.`document_id`))) left join `opascentral`.`api_productbase` on((`opascentral`.`api_articles`.`src_code` = `opascentral`.`api_productbase`.`pepcode`)));

CREATE ALGORITHM = UNDEFINED DEFINER = `root`@`localhost` SQL SECURITY DEFINER VIEW `vw_stat_to_update_solr_docviews` AS select `r0`.`document_id` AS `document_id`,any_value(max(`r0`.`last_viewed`)) AS `last_viewed`,any_value(coalesce(`r1`.`views`,0)) AS `lastweek`,any_value(coalesce(`r2`.`views`,0)) AS `lastmonth`,any_value(coalesce(`r3`.`views`,0)) AS `last6months`,any_value(coalesce(`r5`.`views`,0)) AS `last12months`,any_value(coalesce(`r4`.`views`,0)) AS `lastcalyear` from (((((((select distinct `opascentral`.`api_docviews`.`document_id` AS `document_id`,`opascentral`.`api_docviews`.`last_update` AS `last_viewed` from `opascentral`.`api_docviews` where (`opascentral`.`api_docviews`.`type` = 'Document'))) `r0` left join `opascentral`.`vw_stat_docviews_lastweek` `r1` on((`r1`.`document_id` = `r0`.`document_id`))) left join `opascentral`.`vw_stat_docviews_lastmonth` `r2` on((`r2`.`document_id` = `r0`.`document_id`))) left join `opascentral`.`vw_stat_docviews_lastsixmonths` `r3` on((`r3`.`document_id` = `r0`.`document_id`))) left join `opascentral`.`vw_stat_docviews_lastcalyear` `r4` on((`r4`.`document_id` = `r0`.`document_id`))) left join `opascentral`.`vw_stat_docviews_last12months` `r5` on((`r5`.`document_id` = `r0`.`document_id`))) where ((`r0`.`document_id` is not null) and (`r0`.`document_id` <> 'None') and (`r1`.`views` > 0)) group by `r0`.`document_id`;

CREATE ALGORITHM = UNDEFINED DEFINER = `root`@`localhost` SQL SECURITY DEFINER VIEW `vw_user_active_subscriptions` AS select `api_user`.`user_id` AS `user_id`,`api_user`.`username` AS `username`,`api_user`.`company` AS `company`,`api_user`.`enabled` AS `enabled`,`api_user`.`last_update` AS `last_update`,`api_subscriptions`.`start_date` AS `start_date`,`api_subscriptions`.`end_date` AS `end_date`,`api_subscriptions`.`max_concurrency` AS `max_concurrency`,`api_subscriptions`.`product_id` AS `product_id`,`api_products`.`product` AS `product`,`api_user`.`admin` AS `admin`,`api_user`.`password` AS `password` from ((`api_user` join `api_subscriptions` on((`api_subscriptions`.`user_id` = `api_user`.`user_id`))) join `api_products` on((`api_subscriptions`.`product_id` = `api_products`.`product_id`))) where (((`api_user`.`enabled` = TRUE) and (`api_subscriptions`.`end_date` > now())) or (`api_subscriptions`.`perpetual` = TRUE));

CREATE ALGORITHM = UNDEFINED DEFINER = `root`@`localhost` SQL SECURITY DEFINER VIEW `vw_user_referred` AS select `api_user`.`user_id` AS `user_id`,`api_user`.`username` AS `username`,`api_user`.`enabled` AS `enabled`,`api_user`.`company` AS `company`,`api_user`.`email_address` AS `email_address`,`api_user_referrer_urls`.`referrer_url` AS `referrer_url` from (`api_user` left join `api_user_referrer_urls` on((`api_user_referrer_urls`.`user_id` = `api_user`.`user_id`))) order by `api_user`.`user_id`;

