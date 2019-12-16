/*
Navicat MySQL Data Transfer

Source Server         : XPS
Source Server Version : 50726
Source Host           : localhost:3306
Source Database       : opascentral

Target Server Type    : MYSQL
Target Server Version : 50726
File Encoding         : 65001

Date: 2019-11-22 11:46:27
*/

SET FOREIGN_KEY_CHECKS=0;

-- ----------------------------
-- Table structure for api_administrative_groups
-- ----------------------------
DROP TABLE IF EXISTS `api_administrative_groups`;
CREATE TABLE `api_administrative_groups` (
  `administrative_group_id` int(11) NOT NULL,
  `group_name` varchar(255) DEFAULT NULL,
  `descriptopn` varchar(255) DEFAULT NULL,
  PRIMARY KEY (`administrative_group_id`)
) ENGINE=InnoDB DEFAULT CHARSET=utf8;

-- ----------------------------
-- Table structure for api_client_apps
-- ----------------------------
DROP TABLE IF EXISTS `api_client_apps`;
CREATE TABLE `api_client_apps` (
  `api_client_id` int(11) NOT NULL,
  `api_client_name` varchar(100) NOT NULL,
  `api_client_key` varchar(255) DEFAULT NULL,
  `last_update` timestamp NOT NULL DEFAULT CURRENT_TIMESTAMP,
  PRIMARY KEY (`api_client_id`),
  UNIQUE KEY `idxClientname` (`api_client_name`) USING BTREE
) ENGINE=InnoDB DEFAULT CHARSET=utf8 COMMENT='Keep track of keys assigned to clients, but not used in v1 or v2 API as of 20191110';

-- ----------------------------
-- Table structure for api_docviews
-- ----------------------------
DROP TABLE IF EXISTS `api_docviews`;
CREATE TABLE `api_docviews` (
  `user_id` varchar(60) DEFAULT NULL,
  `session_id` varchar(60) DEFAULT NULL,
  `document_id` varchar(255) DEFAULT NULL,
  `type` varchar(255) DEFAULT NULL,
  `datetimechar` varchar(255) DEFAULT NULL,
  `last_update` timestamp NULL DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP,
  KEY `user_id` (`user_id`)
) ENGINE=InnoDB DEFAULT CHARSET=utf8 COMMENT='Track the number of times a document is viewed as an abstract, full-text, PDF, or EPUB.  Somewhat redundate to api_session_endpoints table, but with less extraneous data..';

-- ----------------------------
-- Table structure for api_endpoints
-- ----------------------------
DROP TABLE IF EXISTS `api_endpoints`;
CREATE TABLE `api_endpoints` (
  `api_endpoint_id` int(11) NOT NULL AUTO_INCREMENT,
  `endpoint_url` varchar(200) NOT NULL,
  `last_update` timestamp NOT NULL DEFAULT CURRENT_TIMESTAMP,
  PRIMARY KEY (`api_endpoint_id`)
) ENGINE=InnoDB AUTO_INCREMENT=46 DEFAULT CHARSET=utf8 COMMENT='Each unique API endpoint (minus base URL), starting with v1, for example\r\n';

-- ----------------------------
-- Table structure for api_join_products_to_productbase
-- ----------------------------
DROP TABLE IF EXISTS `api_join_products_to_productbase`;
CREATE TABLE `api_join_products_to_productbase` (
  `product_id` int(11) NOT NULL,
  `basecode` varchar(50) NOT NULL,
  `extra_field` varchar(255) DEFAULT NULL,
  PRIMARY KEY (`product_id`,`basecode`),
  KEY `basecode` (`basecode`) USING BTREE,
  KEY `product_id` (`product_id`) USING BTREE,
  CONSTRAINT `api_join_products_to_productbase_ibfk_1` FOREIGN KEY (`basecode`) REFERENCES `api_productbase` (`basecode`) ON DELETE CASCADE ON UPDATE CASCADE,
  CONSTRAINT `api_join_products_to_productbase_ibfk_2` FOREIGN KEY (`product_id`) REFERENCES `api_products` (`product_id`) ON DELETE CASCADE ON UPDATE CASCADE
) ENGINE=InnoDB DEFAULT CHARSET=utf8;

-- ----------------------------
-- Table structure for api_productbase
-- ----------------------------
DROP TABLE IF EXISTS `api_productbase`;
CREATE TABLE `api_productbase` (
  `basecode` varchar(21) NOT NULL DEFAULT '' COMMENT 'Shortened form of the locator',
  `articleID` varchar(24) CHARACTER SET latin1 DEFAULT NULL,
  `active` int(1) DEFAULT NULL,
  `pep_class` set('book','journal','videostream','special','vidostream','bookseriessub') CHARACTER SET latin1 DEFAULT '',
  `pep_class_qualifier` set('glossary','works','bookseriesvolume','multivolumebook','multivolumesubbook') CHARACTER SET latin1 DEFAULT '',
  `wall` int(1) DEFAULT '3',
  `mainTOC` varchar(21) CHARACTER SET latin1 DEFAULT '' COMMENT 'Locator for the first instance of this (or the only instance)',
  `first_author` varchar(255) DEFAULT NULL COMMENT 'Needed for KBART, easier than the join, which did lead to some problems since it''s only the first author here',
  `author` varchar(255) DEFAULT NULL,
  `title` varchar(255) DEFAULT NULL COMMENT 'Title of Publication',
  `bibabbrev` varchar(255) DEFAULT NULL COMMENT 'bibliographic Abbreviation',
  `ISSN` varchar(22) CHARACTER SET latin1 DEFAULT NULL COMMENT 'ISSN for Journals only',
  `ISBN-10` varchar(13) CHARACTER SET latin1 DEFAULT NULL,
  `ISBN-13` varchar(17) CHARACTER SET latin1 DEFAULT NULL,
  `pages` int(4) DEFAULT NULL COMMENT 'Number of pages in book',
  `Comment` varchar(255) DEFAULT NULL COMMENT 'use for notes, and "unused" ISBN for books as journals',
  `pepcode` varchar(14) CHARACTER SET latin1 DEFAULT NULL,
  `publisher` varchar(255) DEFAULT NULL,
  `jrnl` tinyint(1) DEFAULT '0' COMMENT '1 if this is a journal, 0 if not',
  `pub_year` int(1) DEFAULT NULL,
  `start_year` int(4) DEFAULT NULL,
  `end_year` int(4) DEFAULT NULL,
  `pep_url` varchar(255) DEFAULT NULL,
  `language` varchar(4) CHARACTER SET latin1 DEFAULT NULL,
  `updated` timestamp NULL DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP,
  `pepversion` int(1) DEFAULT NULL COMMENT 'Version it first appeared in, or planned for',
  `duplicate` varchar(10) CHARACTER SET latin1 DEFAULT NULL COMMENT 'Is this a duplicate (alternative) abbreviation/name (specified)',
  `landing_page` varchar(1024) DEFAULT NULL,
  `coverage_notes` varchar(255) CHARACTER SET utf8 COLLATE utf8_unicode_ci DEFAULT NULL COMMENT 'Added for KBART, explain embargo if necessary',
  `landing_page_intro_html` text,
  `landing_page_end_html` text,
  `google_books_link` varchar(512) CHARACTER SET latin1 DEFAULT NULL,
  PRIMARY KEY (`basecode`),
  KEY `basecode` (`basecode`)
) ENGINE=InnoDB DEFAULT CHARSET=utf8 COMMENT='Each ISSN Product included (from the PEP ISSN Table)\r\n\r\n';

-- ----------------------------
-- Table structure for api_products
-- ----------------------------
DROP TABLE IF EXISTS `api_products`;
CREATE TABLE `api_products` (
  `product_id` int(11) NOT NULL AUTO_INCREMENT,
  `subsystem_id` int(11) NOT NULL DEFAULT '8',
  `product` varchar(200) NOT NULL,
  `product_level` smallint(6) NOT NULL DEFAULT '0',
  `product_type` varchar(40) DEFAULT NULL,
  `basecode` varchar(15) DEFAULT NULL,
  `product_comment` varchar(255) DEFAULT NULL,
  `free_access` tinyint(1) NOT NULL DEFAULT '0',
  `active` tinyint(1) NOT NULL DEFAULT '0',
  `embargo_length` tinyint(1) DEFAULT NULL,
  `embargo_inverted` tinyint(1) DEFAULT NULL,
  `range_limited` tinyint(1) NOT NULL DEFAULT '0',
  `range_start_date` tinyint(1) NOT NULL DEFAULT '0' COMMENT 'offset from first available year (e.g. 0 means start in the first year, 25 means start in the 26th year)',
  `range_end_date` tinyint(1) NOT NULL DEFAULT '0' COMMENT 'offset from last available year (e.g. -3 is three year wall)',
  `parent_product_id` int(11) DEFAULT '0',
  `inherit_parent_metadata` tinyint(1) NOT NULL DEFAULT '1',
  `id_type` smallint(6) DEFAULT NULL,
  `counter_service` varchar(100) DEFAULT NULL,
  `counter_database` varchar(100) DEFAULT NULL,
  `counter_book` varchar(150) DEFAULT NULL,
  `counter_journal_collection` varchar(100) DEFAULT NULL,
  `id_code_1` varchar(50) DEFAULT NULL,
  `id_code_2` varchar(50) DEFAULT NULL,
  `group_sort_order` int(11) DEFAULT NULL,
  `hide_in_product_access` tinyint(1) NOT NULL DEFAULT '0',
  `hide_in_report_list` tinyint(1) NOT NULL DEFAULT '0',
  `added_by_user_id` int(11) NOT NULL DEFAULT '10',
  `date_added` datetime NOT NULL,
  `modified_by_user_id` int(11) NOT NULL DEFAULT '10',
  `last_update` timestamp NOT NULL DEFAULT CURRENT_TIMESTAMP,
  PRIMARY KEY (`product_id`),
  KEY `idxSubsystemId` (`subsystem_id`) USING BTREE,
  KEY `idxProductLevel` (`product_level`) USING BTREE,
  KEY `idxParentProductId` (`parent_product_id`) USING HASH,
  KEY `basecode` (`basecode`) USING HASH
) ENGINE=InnoDB AUTO_INCREMENT=3824 DEFAULT CHARSET=utf8;

-- ----------------------------
-- Table structure for api_products_closure
-- ----------------------------
DROP TABLE IF EXISTS `api_products_closure`;
CREATE TABLE `api_products_closure` (
  `ancestor_product_id` int(11) NOT NULL,
  `descendent_product_id` int(11) NOT NULL,
  `path_length` int(11) DEFAULT NULL,
  `anc_prod_name` varchar(255) DEFAULT NULL,
  `des_prod_name` varchar(255) DEFAULT NULL
) ENGINE=InnoDB DEFAULT CHARSET=utf8;

-- ----------------------------
-- Table structure for api_product_groups
-- ----------------------------
DROP TABLE IF EXISTS `api_product_groups`;
CREATE TABLE `api_product_groups` (
  `group_id` int(11) DEFAULT NULL,
  `group_name` varchar(255) DEFAULT NULL,
  `level` int(11) DEFAULT NULL,
  `parent_group_id` int(11) DEFAULT NULL,
  `description` varchar(255) DEFAULT NULL
) ENGINE=InnoDB DEFAULT CHARSET=utf8;

-- ----------------------------
-- Table structure for api_sessions
-- ----------------------------
DROP TABLE IF EXISTS `api_sessions`;
CREATE TABLE `api_sessions` (
  `session_id` varchar(60) NOT NULL,
  `user_id` int(11) DEFAULT NULL,
  `username` varchar(255) CHARACTER SET ujis DEFAULT NULL,
  `user_ip` varchar(60) DEFAULT NULL,
  `connected_via` varchar(512) DEFAULT NULL,
  `referrer` varchar(512) DEFAULT NULL,
  `session_start` timestamp NOT NULL,
  `session_end` timestamp NULL DEFAULT NULL,
  `session_expires_time` timestamp NULL DEFAULT NULL,
  `access_token` varchar(1000) DEFAULT NULL COMMENT 'a JWT so could be long',
  `authenticated` tinyint(1) DEFAULT '0',
  `admin` tinyint(1) DEFAULT '0',
  `api_client_id` int(11) NOT NULL,
  `updated` timestamp NULL DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP,
  PRIMARY KEY (`session_id`),
  KEY `idxSession` (`session_id`) USING BTREE,
  KEY `session_user` (`user_id`),
  CONSTRAINT `session_user` FOREIGN KEY (`user_id`) REFERENCES `api_user` (`user_id`) ON DELETE CASCADE ON UPDATE CASCADE
) ENGINE=InnoDB DEFAULT CHARSET=utf8 COMMENT='Each API session with a unique ID creates a session record. ';

-- ----------------------------
-- Table structure for api_session_endpoints
-- ----------------------------
DROP TABLE IF EXISTS `api_session_endpoints`;
CREATE TABLE `api_session_endpoints` (
  `session_id` varchar(60) NOT NULL,
  `api_endpoint_id` int(11) NOT NULL,
  `params` varchar(2500) DEFAULT NULL,
  `item_of_interest` varchar(60) DEFAULT NULL,
  `return_status_code` int(11) DEFAULT NULL,
  `return_added_status_message` varchar(255) DEFAULT NULL,
  `last_update` timestamp NOT NULL DEFAULT CURRENT_TIMESTAMP,
  KEY `fk_session_id` (`session_id`) USING BTREE
) ENGINE=InnoDB DEFAULT CHARSET=utf8 COMMENT='All endpoints called in a session, and parameters defining searches, retrievals etc..\r\n\r\n';

-- ----------------------------
-- Table structure for api_subscriptions
-- ----------------------------
DROP TABLE IF EXISTS `api_subscriptions`;
CREATE TABLE `api_subscriptions` (
  `user_id` int(11) NOT NULL,
  `product_id` int(11) NOT NULL,
  `start_date` datetime NOT NULL,
  `end_date` datetime NOT NULL,
  `max_concurrency` int(11) NOT NULL,
  `perpetual` tinyint(1) NOT NULL DEFAULT '0',
  `modified_by_user_id` int(11) NOT NULL,
  `last_update` timestamp NOT NULL DEFAULT CURRENT_TIMESTAMP,
  PRIMARY KEY (`user_id`,`product_id`),
  KEY `idxStartDate` (`start_date`) USING BTREE,
  KEY `idxEndDate` (`end_date`) USING BTREE,
  KEY `idxProductId` (`product_id`) USING BTREE,
  CONSTRAINT `subscribed_product` FOREIGN KEY (`product_id`) REFERENCES `api_products` (`product_id`) ON DELETE CASCADE ON UPDATE CASCADE,
  CONSTRAINT `subscribed_user` FOREIGN KEY (`user_id`) REFERENCES `api_user` (`user_id`) ON DELETE CASCADE ON UPDATE CASCADE
) ENGINE=InnoDB DEFAULT CHARSET=utf8;

-- ----------------------------
-- Table structure for api_user
-- ----------------------------
DROP TABLE IF EXISTS `api_user`;
CREATE TABLE `api_user` (
  `user_id` int(11) NOT NULL AUTO_INCREMENT,
  `username` varchar(255) NOT NULL,
  `password` varchar(512) NOT NULL,
  `full_name` varchar(255) DEFAULT NULL,
  `company` varchar(125) DEFAULT NULL,
  `email_address` varchar(65) DEFAULT NULL,
  `enabled` tinyint(1) DEFAULT '0',
  `admin` tinyint(1) DEFAULT '0',
  `user_agrees_date` datetime DEFAULT CURRENT_TIMESTAMP,
  `user_agrees_to_tracking` tinyint(1) DEFAULT '0',
  `user_agrees_to_cookies` tinyint(1) DEFAULT '0',
  `email_optin` tinyint(1) NOT NULL DEFAULT '1',
  `hide_activity` tinyint(1) NOT NULL DEFAULT '0',
  `parent_user_id` int(11) NOT NULL DEFAULT '0',
  `administrative_group_id` int(11) NOT NULL DEFAULT '64',
  `view_parent_user_reports` tinyint(1) NOT NULL DEFAULT '0',
  `deleted` tinyint(1) NOT NULL DEFAULT '0',
  `modified_by_user_id` int(11) DEFAULT NULL,
  `added_by_user_id` int(11) DEFAULT NULL,
  `added_date` datetime DEFAULT NULL,
  `last_update` timestamp NOT NULL DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP,
  PRIMARY KEY (`user_id`),
  UNIQUE KEY `unique_username` (`username`) USING BTREE,
  KEY `idxUsername` (`username`) USING BTREE,
  KEY `user_administrative_group` (`administrative_group_id`),
  CONSTRAINT `user_administrative_group` FOREIGN KEY (`administrative_group_id`) REFERENCES `api_administrative_groups` (`administrative_group_id`) ON DELETE CASCADE ON UPDATE CASCADE
) ENGINE=InnoDB AUTO_INCREMENT=119127 DEFAULT CHARSET=utf8 COMMENT='A list of all authorized users, and the NOT_LOGGED_IN user, with ID=0';

-- ----------------------------
-- Table structure for api_user_ip_ranges
-- ----------------------------
DROP TABLE IF EXISTS `api_user_ip_ranges`;
CREATE TABLE `api_user_ip_ranges` (
  `ip_addresses_id` int(11) NOT NULL AUTO_INCREMENT,
  `user_id` int(11) NOT NULL,
  `start_ip_address` bigint(20) NOT NULL,
  `end_ip_address` bigint(20) NOT NULL,
  `modified_by_user_id` int(11) NOT NULL,
  `last_update` timestamp NOT NULL DEFAULT CURRENT_TIMESTAMP,
  PRIMARY KEY (`ip_addresses_id`),
  KEY `idxSubsystemIdUserId` (`user_id`) USING BTREE,
  KEY `idxStartIpAddress` (`start_ip_address`) USING BTREE,
  KEY `idxEndIpAddress` (`end_ip_address`) USING BTREE,
  KEY `idxUserId` (`user_id`) USING BTREE,
  KEY `FK_ip_addresses_user_subsystem` (`user_id`) USING BTREE,
  CONSTRAINT `ip_user` FOREIGN KEY (`user_id`) REFERENCES `api_user` (`user_id`) ON DELETE CASCADE ON UPDATE CASCADE
) ENGINE=InnoDB AUTO_INCREMENT=25024 DEFAULT CHARSET=utf8;

-- ----------------------------
-- Table structure for api_user_property_name
-- ----------------------------
DROP TABLE IF EXISTS `api_user_property_name`;
CREATE TABLE `api_user_property_name` (
  `user_property_name_id` int(11) NOT NULL AUTO_INCREMENT,
  `user_property_name` varchar(50) NOT NULL,
  `user_property_data_type_id` smallint(6) NOT NULL,
  `sort_order` smallint(6) NOT NULL,
  `user_property_user_access_id` smallint(6) NOT NULL,
  `default_value` varchar(1000) DEFAULT NULL,
  `display_width` smallint(6) DEFAULT NULL,
  `display_height` smallint(6) DEFAULT NULL,
  `modified_by_user_id` int(11) NOT NULL,
  `last_update` timestamp NOT NULL DEFAULT CURRENT_TIMESTAMP,
  PRIMARY KEY (`user_property_name_id`),
  KEY `FK_user_property_name_ref_user_property_data_type` (`user_property_data_type_id`) USING BTREE,
  KEY `FK_user_property_name_ref_user_property_user_access` (`user_property_user_access_id`) USING BTREE
) ENGINE=InnoDB AUTO_INCREMENT=169 DEFAULT CHARSET=utf8;

-- ----------------------------
-- Table structure for api_user_property_value
-- ----------------------------
DROP TABLE IF EXISTS `api_user_property_value`;
CREATE TABLE `api_user_property_value` (
  `user_property_value_id` int(11) NOT NULL AUTO_INCREMENT,
  `user_id` int(11) NOT NULL,
  `user_property_name_id` int(11) NOT NULL,
  `user_property_value` varchar(5000) NOT NULL,
  `modified_by_user_id` int(11) NOT NULL,
  `last_update` timestamp NOT NULL DEFAULT CURRENT_TIMESTAMP,
  PRIMARY KEY (`user_property_value_id`),
  UNIQUE KEY `IX_user_property_value` (`user_id`,`user_property_name_id`) USING BTREE,
  KEY `idxUserPropertyNameId` (`user_property_name_id`) USING BTREE,
  CONSTRAINT `property_name` FOREIGN KEY (`user_property_name_id`) REFERENCES `api_user_property_name` (`user_property_name_id`) ON DELETE CASCADE ON UPDATE CASCADE,
  CONSTRAINT `property_user` FOREIGN KEY (`user_id`) REFERENCES `api_user` (`user_id`) ON DELETE CASCADE ON UPDATE CASCADE
) ENGINE=InnoDB AUTO_INCREMENT=577755 DEFAULT CHARSET=utf8;

-- ----------------------------
-- Table structure for api_user_referrer_urls
-- ----------------------------
DROP TABLE IF EXISTS `api_user_referrer_urls`;
CREATE TABLE `api_user_referrer_urls` (
  `referrer_urls_id` int(11) NOT NULL AUTO_INCREMENT,
  `user_id` int(11) NOT NULL,
  `referrer_url` varchar(500) NOT NULL,
  `modified_by_user_id` int(11) NOT NULL,
  `last_update` timestamp NOT NULL DEFAULT CURRENT_TIMESTAMP,
  PRIMARY KEY (`referrer_urls_id`),
  KEY `idxSubsystemIdUserId` (`user_id`) USING BTREE,
  KEY `idxReferrerUrl` (`referrer_url`(255)) USING BTREE,
  KEY `idxUserId` (`user_id`) USING BTREE,
  KEY `FK_referrer_urls_user_subsystem` (`user_id`) USING BTREE,
  CONSTRAINT `referral_url_user` FOREIGN KEY (`user_id`) REFERENCES `api_user` (`user_id`) ON DELETE CASCADE ON UPDATE CASCADE
) ENGINE=InnoDB AUTO_INCREMENT=2001 DEFAULT CHARSET=utf8;

-- ----------------------------
-- Table structure for articles
-- ----------------------------
DROP TABLE IF EXISTS `articles`;
CREATE TABLE `articles` (
  `articleID` varchar(24) CHARACTER SET latin1 NOT NULL DEFAULT '' COMMENT 'The PEP locator for this article',
  `arttype` varchar(4) CHARACTER SET latin1 NOT NULL DEFAULT '' COMMENT 'Article type, e.g., ART, COM, ERA',
  `authorMast` text COMMENT 'Author names per masthead, e.g. Ronnie C. Lesser, Ph.D.',
  `hdgauthor` text COMMENT 'The heading style author list, e.g., Lesser, R. C.',
  `hdgtitle` text COMMENT 'The title for the heading',
  `srctitleseries` text COMMENT 'Src title bibliogr abbrev style, e.g., Psychoanal. Dial.',
  `publisher` varchar(255) CHARACTER SET utf8 COLLATE utf8_unicode_ci NOT NULL DEFAULT '' COMMENT 'Publisher, e.g., Cambridge, MA / London: Harvard Univ. Press',
  `jrnlcode` varchar(14) CHARACTER SET latin1 DEFAULT NULL COMMENT 'PEP assigned Journal Code, e.g., IJP',
  `year` int(11) DEFAULT NULL COMMENT 'Year of Publication',
  `vol` int(11) DEFAULT NULL COMMENT 'Volume',
  `volsuffix` char(5) CHARACTER SET latin1 DEFAULT NULL COMMENT 'Vol number suffix, e.g., S for supplements',
  `issue` char(5) CHARACTER SET latin1 NOT NULL DEFAULT '' COMMENT 'Issue number or designation, e.g., 1, or pilot',
  `pgrg` varchar(20) CHARACTER SET latin1 DEFAULT NULL COMMENT 'Page range of article, e.g., 1-22',
  `pgstart` int(11) DEFAULT NULL COMMENT 'Starting page number, negative for roman',
  `pgend` int(11) DEFAULT NULL COMMENT 'Ending page number, use negative for roman',
  `source` varchar(10) CHARACTER SET latin1 DEFAULT NULL COMMENT 'Source date',
  `preserve` int(11) DEFAULT '0',
  `filename` varchar(255) CHARACTER SET latin1 DEFAULT NULL COMMENT 'Path and filename of source file',
  `maintocID` varchar(20) CHARACTER SET latin1 DEFAULT NULL,
  `newsecname` varchar(255) CHARACTER SET utf8 COLLATE utf8_unicode_ci DEFAULT NULL COMMENT 'When the article starts a new section in the TOC, name',
  `bktitle` varchar(255) DEFAULT NULL COMMENT 'Title of parent book which contains the article',
  `bkauthors` varchar(255) DEFAULT NULL COMMENT 'Authors of the parent book',
  `xmlref` text COMMENT 'Bibliographic style reference for article, in XML',
  `references` int(11) DEFAULT NULL,
  `doi` varchar(255) CHARACTER SET latin1 DEFAULT NULL,
  `artkwds` varchar(255) DEFAULT NULL,
  `artlang` varchar(255) DEFAULT NULL,
  `updated` timestamp NOT NULL DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP,
  PRIMARY KEY (`articleID`),
  UNIQUE KEY `Primary Key` (`articleID`) USING HASH,
  UNIQUE KEY `filename` (`filename`) USING BTREE,
  KEY `xname` (`vol`) USING BTREE,
  KEY `titlefulltext` (`hdgtitle`(333)) USING BTREE,
  KEY `yrjrnlcode` (`jrnlcode`,`year`) USING BTREE,
  KEY `voljrnlcode` (`jrnlcode`,`vol`) USING BTREE,
  KEY `authorfulltext` (`hdgauthor`(255)) USING BTREE,
  KEY `jrnlCodeIndiv` (`jrnlcode`) USING BTREE,
  FULLTEXT KEY `hdgtitle` (`hdgtitle`),
  FULLTEXT KEY `hdgauthor` (`hdgauthor`),
  FULLTEXT KEY `xmlref` (`xmlref`),
  FULLTEXT KEY `bktitle` (`bktitle`)
) ENGINE=InnoDB DEFAULT CHARSET=utf8 COMMENT='A PEP journal article, book or book section';

-- ----------------------------
-- Table structure for fullbiblioxml
-- ----------------------------
DROP TABLE IF EXISTS `fullbiblioxml`;
CREATE TABLE `fullbiblioxml` (
  `articleID` varchar(24) NOT NULL,
  `internalID` varchar(25) NOT NULL,
  `fullReference` text CHARACTER SET utf8,
  `rxCode` varchar(30) DEFAULT NULL,
  `rxConfidence` double NOT NULL DEFAULT '0' COMMENT 'A value of 1 will never be automatically replaced',
  `updated` timestamp NOT NULL DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP,
  `fullRefText` text CHARACTER SET utf8,
  `source` varchar(24) CHARACTER SET utf8 DEFAULT 'instance' COMMENT 'If it''s refcorrections, this record came from the refcorrections table and should not be updated.',
  `journal` varchar(255) CHARACTER SET utf8 DEFAULT NULL COMMENT 'Record the journal name as extracted from the XML referennce.  Useful to sort and check reference.',
  `booktitle` varchar(255) CHARACTER SET utf8 COLLATE utf8_unicode_ci DEFAULT NULL,
  `title` varchar(255) DEFAULT NULL,
  `normalizedjournal` varchar(255) CHARACTER SET utf8 DEFAULT NULL,
  `altArticleID` varchar(255) CHARACTER SET utf8 DEFAULT NULL,
  `doi` varchar(255) CHARACTER SET utf8 DEFAULT NULL COMMENT 'Document Object Identifier for this reference',
  `relatedRXCode` varchar(30) DEFAULT NULL,
  `relatedRXConfidence` double NOT NULL DEFAULT '0',
  PRIMARY KEY (`articleID`,`internalID`),
  UNIQUE KEY `Primary Key` (`articleID`,`internalID`) USING BTREE,
  KEY `articleID` (`articleID`) USING BTREE,
  KEY `altArticleID` (`altArticleID`) USING BTREE,
  KEY `titleIndex` (`title`) USING BTREE,
  KEY `RefersTo` (`rxCode`) USING HASH,
  FULLTEXT KEY `fulreffullText` (`fullRefText`),
  FULLTEXT KEY `titleFullText` (`title`)
) ENGINE=InnoDB DEFAULT CHARSET=latin1 COMMENT='All bibliographic entries within PEP';

-- ----------------------------
-- Table structure for xxx_gvpi_product
-- ----------------------------
DROP TABLE IF EXISTS `xxx_gvpi_product`;
CREATE TABLE `xxx_gvpi_product` (
  `product_id` int(11) NOT NULL AUTO_INCREMENT,
  `subsystem_id` int(11) NOT NULL,
  `product` varchar(200) NOT NULL,
  `product_description` varchar(1000) DEFAULT NULL,
  `parent_product_id` int(11) NOT NULL DEFAULT '0',
  `product_level` smallint(6) NOT NULL DEFAULT '0',
  `inherit_parent_metadata` tinyint(1) NOT NULL DEFAULT '1',
  `document_url` varchar(200) NOT NULL,
  `product_alias` varchar(100) DEFAULT NULL,
  `email_id` int(11) NOT NULL,
  `id_type` smallint(6) DEFAULT NULL,
  `counter_service` varchar(100) DEFAULT NULL,
  `counter_database` varchar(100) DEFAULT NULL,
  `counter_book` varchar(150) DEFAULT NULL,
  `counter_journal_collection` varchar(100) DEFAULT NULL,
  `id_code_1` varchar(50) DEFAULT NULL,
  `id_code_2` varchar(50) DEFAULT NULL,
  `id_code_3` varchar(50) DEFAULT NULL,
  `id_code_4` varchar(50) DEFAULT NULL,
  `publisher` varchar(50) DEFAULT NULL,
  `platform` varchar(50) DEFAULT NULL,
  `content_start_date_allowed` tinyint(1) NOT NULL DEFAULT '0',
  `content_end_date_allowed` tinyint(1) NOT NULL DEFAULT '0',
  `content_metadata_key` varchar(64) DEFAULT NULL,
  `content_start_date_flag` smallint(6) DEFAULT NULL,
  `content_end_date_flag` smallint(6) DEFAULT NULL,
  `perpetual_flag` smallint(6) DEFAULT NULL,
  `group_sort_order` int(11) DEFAULT NULL,
  `hide_in_product_access` tinyint(1) NOT NULL DEFAULT '0',
  `hide_in_report_list` tinyint(1) NOT NULL DEFAULT '0',
  `added_by_user_id` int(11) NOT NULL,
  `date_added` datetime NOT NULL,
  `modified_by_user_id` int(11) NOT NULL,
  `last_update` timestamp NOT NULL DEFAULT CURRENT_TIMESTAMP,
  PRIMARY KEY (`product_id`),
  KEY `idxParentProductId` (`parent_product_id`) USING BTREE,
  KEY `idxSubsystemId` (`subsystem_id`) USING BTREE,
  KEY `idxProductLevel` (`product_level`) USING BTREE,
  KEY `idxProductAlias` (`product_alias`) USING BTREE,
  CONSTRAINT `xxx_gvpi_product_ibfk_1` FOREIGN KEY (`subsystem_id`) REFERENCES `xxx_subsystem` (`subsystem_id`) ON DELETE CASCADE ON UPDATE CASCADE
) ENGINE=InnoDB AUTO_INCREMENT=3824 DEFAULT CHARSET=utf8;

-- ----------------------------
-- Table structure for xxx_gvpi_subscriptions
-- ----------------------------
DROP TABLE IF EXISTS `xxx_gvpi_subscriptions`;
CREATE TABLE `xxx_gvpi_subscriptions` (
  `user_id` int(11) NOT NULL,
  `client_id` int(11) NOT NULL,
  `product_id` int(11) NOT NULL,
  `start_date` datetime NOT NULL,
  `end_date` datetime NOT NULL,
  `max_concurrency` int(11) NOT NULL,
  `perpetual` tinyint(1) NOT NULL DEFAULT '0',
  `modified_by_user_id` int(11) NOT NULL,
  `last_update` timestamp NOT NULL DEFAULT CURRENT_TIMESTAMP,
  PRIMARY KEY (`user_id`,`client_id`,`product_id`),
  KEY `idxStartDate` (`start_date`) USING BTREE,
  KEY `idxEndDate` (`end_date`) USING BTREE,
  KEY `idxProductId` (`product_id`) USING BTREE,
  CONSTRAINT `xxx_gvpi_subscriptions_ibfk_1` FOREIGN KEY (`product_id`) REFERENCES `api_products` (`product_id`) ON DELETE CASCADE ON UPDATE CASCADE
) ENGINE=InnoDB DEFAULT CHARSET=utf8;

-- ----------------------------
-- Table structure for xxx_gvpi_user_ip_addresses
-- ----------------------------
DROP TABLE IF EXISTS `xxx_gvpi_user_ip_addresses`;
CREATE TABLE `xxx_gvpi_user_ip_addresses` (
  `ip_addresses_id` int(11) NOT NULL AUTO_INCREMENT,
  `user_id` int(11) NOT NULL,
  `subsystem_id` int(11) NOT NULL,
  `start_ip_address` bigint(20) NOT NULL,
  `end_ip_address` bigint(20) NOT NULL,
  `modified_by_user_id` int(11) NOT NULL,
  `last_update` timestamp NOT NULL DEFAULT CURRENT_TIMESTAMP,
  PRIMARY KEY (`ip_addresses_id`),
  KEY `idxSubsystemIdUserId` (`subsystem_id`,`user_id`) USING BTREE,
  KEY `idxStartIpAddress` (`start_ip_address`) USING BTREE,
  KEY `idxEndIpAddress` (`end_ip_address`) USING BTREE,
  KEY `idxUserId` (`user_id`) USING BTREE,
  KEY `FK_ip_addresses_user_subsystem` (`user_id`,`subsystem_id`) USING BTREE,
  CONSTRAINT `xxx_gvpi_user_ip_addresses_ibfk_1` FOREIGN KEY (`user_id`, `subsystem_id`) REFERENCES `xxx_user_subsystem` (`user_id`, `subsystem_id`) ON DELETE CASCADE ON UPDATE CASCADE
) ENGINE=InnoDB AUTO_INCREMENT=28533 DEFAULT CHARSET=utf8;

-- ----------------------------
-- Table structure for xxx_referrer_urls
-- ----------------------------
DROP TABLE IF EXISTS `xxx_referrer_urls`;
CREATE TABLE `xxx_referrer_urls` (
  `referrer_urls_id` int(11) NOT NULL AUTO_INCREMENT,
  `user_id` int(11) NOT NULL,
  `referrer_url` varchar(500) NOT NULL,
  `modified_by_user_id` int(11) NOT NULL,
  `last_update` timestamp NOT NULL DEFAULT CURRENT_TIMESTAMP,
  PRIMARY KEY (`referrer_urls_id`) USING BTREE,
  KEY `idxSubsystemIdUserId` (`user_id`) USING BTREE,
  KEY `idxReferrerUrl` (`referrer_url`(255)) USING BTREE,
  KEY `idxUserId` (`user_id`) USING BTREE,
  KEY `FK_referrer_urls_user_subsystem` (`user_id`) USING BTREE
) ENGINE=InnoDB AUTO_INCREMENT=1561 DEFAULT CHARSET=utf8;

-- ----------------------------
-- Table structure for xxx_subsystem
-- ----------------------------
DROP TABLE IF EXISTS `xxx_subsystem`;
CREATE TABLE `xxx_subsystem` (
  `subsystem_id` int(11) NOT NULL,
  `subsystem_name` varchar(100) NOT NULL,
  `domain_name` varchar(50) NOT NULL,
  `last_update` timestamp NOT NULL DEFAULT CURRENT_TIMESTAMP,
  PRIMARY KEY (`subsystem_id`),
  UNIQUE KEY `idxSubsystem_name` (`subsystem_name`) USING BTREE
) ENGINE=InnoDB DEFAULT CHARSET=utf8;

-- ----------------------------
-- Table structure for xxx_user_subsystem
-- ----------------------------
DROP TABLE IF EXISTS `xxx_user_subsystem`;
CREATE TABLE `xxx_user_subsystem` (
  `user_id` int(11) NOT NULL,
  `subsystem_id` int(11) NOT NULL,
  `email_optin` char(1) NOT NULL DEFAULT 'n',
  `hide_activity` char(1) NOT NULL,
  `parent_user_id` int(11) NOT NULL,
  `administrative_group_id` int(11) NOT NULL,
  `view_parent_user_reports` char(1) NOT NULL DEFAULT 'n',
  `deleted` char(1) NOT NULL DEFAULT 'a',
  `added_by_user_id` int(11) NOT NULL DEFAULT '1',
  `date_added` timestamp NOT NULL DEFAULT CURRENT_TIMESTAMP,
  `modified_by_user_id` int(11) NOT NULL,
  `last_update` timestamp NOT NULL DEFAULT CURRENT_TIMESTAMP,
  PRIMARY KEY (`user_id`,`subsystem_id`),
  KEY `idxEmailOptin` (`email_optin`) USING BTREE,
  KEY `idxLogActivity` (`hide_activity`) USING BTREE,
  KEY `idxParentUserId` (`parent_user_id`) USING BTREE,
  KEY `idxAdministrativeGroupId` (`administrative_group_id`) USING BTREE,
  KEY `idxDeleted` (`deleted`) USING BTREE,
  KEY `FK_user_subsystem_subsystem` (`subsystem_id`) USING BTREE
) ENGINE=InnoDB DEFAULT CHARSET=utf8;

-- ----------------------------
-- Table structure for xxx__gvpi_user
-- ----------------------------
DROP TABLE IF EXISTS `xxx__gvpi_user`;
CREATE TABLE `xxx__gvpi_user` (
  `user_id` int(11) NOT NULL AUTO_INCREMENT,
  `username` varchar(50) NOT NULL,
  `password` varchar(50) NOT NULL,
  `company` varchar(125) DEFAULT NULL,
  `email_address` varchar(65) DEFAULT NULL,
  `modified_by_user_id` int(11) NOT NULL,
  `last_update` timestamp NOT NULL DEFAULT CURRENT_TIMESTAMP,
  PRIMARY KEY (`user_id`) USING BTREE,
  KEY `idxUsername` (`username`) USING BTREE
) ENGINE=InnoDB AUTO_INCREMENT=119120 DEFAULT CHARSET=utf8;

-- ----------------------------
-- Table structure for xxx__gvpi_user_subsystem
-- ----------------------------
DROP TABLE IF EXISTS `xxx__gvpi_user_subsystem`;
CREATE TABLE `xxx__gvpi_user_subsystem` (
  `user_id` int(11) NOT NULL,
  `subsystem_id` int(11) NOT NULL,
  `email_optin` char(1) NOT NULL DEFAULT 'n',
  `hide_activity` char(1) NOT NULL,
  `parent_user_id` int(11) NOT NULL,
  `administrative_group_id` int(11) NOT NULL,
  `view_parent_user_reports` char(1) NOT NULL DEFAULT 'n',
  `deleted` char(1) NOT NULL DEFAULT 'a',
  `added_by_user_id` int(11) NOT NULL DEFAULT '1',
  `date_added` timestamp NOT NULL DEFAULT CURRENT_TIMESTAMP,
  `modified_by_user_id` int(11) NOT NULL,
  `last_update` timestamp NOT NULL DEFAULT CURRENT_TIMESTAMP,
  PRIMARY KEY (`user_id`,`subsystem_id`),
  KEY `idxEmailOptin` (`email_optin`) USING BTREE,
  KEY `idxLogActivity` (`hide_activity`) USING BTREE,
  KEY `idxParentUserId` (`parent_user_id`) USING BTREE,
  KEY `idxAdministrativeGroupId` (`administrative_group_id`) USING BTREE,
  KEY `idxDeleted` (`deleted`) USING BTREE,
  KEY `FK_user_subsystem_subsystem` (`subsystem_id`) USING BTREE
) ENGINE=InnoDB DEFAULT CHARSET=utf8;

-- ----------------------------
-- Table structure for xxx__user_subsystem
-- ----------------------------
DROP TABLE IF EXISTS `xxx__user_subsystem`;
CREATE TABLE `xxx__user_subsystem` (
  `user_id` int(11) NOT NULL,
  `subsystem_id` int(11) NOT NULL,
  `email_optin` char(1) NOT NULL DEFAULT 'n',
  `hide_activity` char(1) NOT NULL,
  `parent_user_id` int(11) NOT NULL,
  `administrative_group_id` int(11) NOT NULL,
  `view_parent_user_reports` char(1) NOT NULL DEFAULT 'n',
  `deleted` char(1) NOT NULL DEFAULT 'a',
  `added_by_user_id` int(11) NOT NULL DEFAULT '1',
  `date_added` timestamp NOT NULL DEFAULT CURRENT_TIMESTAMP,
  `modified_by_user_id` int(11) NOT NULL,
  `last_update` timestamp NOT NULL DEFAULT CURRENT_TIMESTAMP,
  PRIMARY KEY (`user_id`,`subsystem_id`) USING BTREE,
  KEY `idxEmailOptin` (`email_optin`) USING BTREE,
  KEY `idxLogActivity` (`hide_activity`) USING BTREE,
  KEY `idxParentUserId` (`parent_user_id`) USING BTREE,
  KEY `idxAdministrativeGroupId` (`administrative_group_id`) USING BTREE,
  KEY `idxDeleted` (`deleted`) USING BTREE,
  KEY `FK_user_subsystem_subsystem` (`subsystem_id`) USING BTREE
) ENGINE=InnoDB DEFAULT CHARSET=utf8;

