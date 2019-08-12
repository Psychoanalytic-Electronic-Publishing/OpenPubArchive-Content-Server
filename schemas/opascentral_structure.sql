/*
Navicat MySQL Data Transfer

Source Server         : Raptor1
Source Server Version : 50714
Source Host           : localhost:3306
Source Database       : opascentral

Target Server Type    : MYSQL
Target Server Version : 50714
File Encoding         : 65001

Date: 2019-08-11 13:38:04
*/

SET FOREIGN_KEY_CHECKS=0;

-- ----------------------------
-- Table structure for api_clients
-- ----------------------------
DROP TABLE IF EXISTS `api_clients`;
CREATE TABLE `api_clients` (
  `api_client_id` int(11) NOT NULL,
  `api_client_name` varchar(100) NOT NULL,
  `api_client_key` varchar(255) DEFAULT NULL,
  `last_update` timestamp NOT NULL DEFAULT CURRENT_TIMESTAMP,
  PRIMARY KEY (`api_client_id`),
  UNIQUE KEY `idxClientname` (`api_client_name`)
) ENGINE=InnoDB DEFAULT CHARSET=utf8;

-- ----------------------------
-- Table structure for api_endpoints
-- ----------------------------
DROP TABLE IF EXISTS `api_endpoints`;
CREATE TABLE `api_endpoints` (
  `api_endpoint_id` int(11) NOT NULL AUTO_INCREMENT,
  `endpoint_url` varchar(200) NOT NULL,
  `last_update` timestamp NOT NULL DEFAULT CURRENT_TIMESTAMP,
  PRIMARY KEY (`api_endpoint_id`)
) ENGINE=InnoDB AUTO_INCREMENT=46 DEFAULT CHARSET=utf8 COMMENT='Each unique API endpoint (minus base URL, starting with v1, for example\r\n';

-- ----------------------------
-- Table structure for api_sessions
-- ----------------------------
DROP TABLE IF EXISTS `api_sessions`;
CREATE TABLE `api_sessions` (
  `session_id` varchar(60) NOT NULL,
  `user_id` varchar(60) DEFAULT NULL,
  `username` varchar(255) CHARACTER SET ujis DEFAULT NULL,
  `user_ip` varchar(60) DEFAULT NULL,
  `connected_via` varchar(512) DEFAULT NULL,
  `referrer` varchar(512) DEFAULT NULL,
  `session_start` timestamp NOT NULL,
  `session_end` timestamp NULL DEFAULT NULL,
  `session_expires_time` timestamp NULL DEFAULT NULL,
  `access_token` varchar(1000) DEFAULT NULL COMMENT 'a JWT so could be long',
  `authenticated` tinyint(1) DEFAULT '0',
  `api_client_id` int(11) NOT NULL,
  `updated` timestamp NULL DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP,
  PRIMARY KEY (`session_id`),
  KEY `idxSession` (`session_id`)
) ENGINE=InnoDB DEFAULT CHARSET=utf8;

-- ----------------------------
-- Table structure for api_session_endpoints
-- ----------------------------
DROP TABLE IF EXISTS `api_session_endpoints`;
CREATE TABLE `api_session_endpoints` (
  `session_id` varchar(60) NOT NULL,
  `api_endpoint_id` int(11) NOT NULL,
  `params` varchar(2500) DEFAULT NULL,
  `documentid` varchar(30) DEFAULT NULL,
  `return_status_code` int(11) DEFAULT NULL,
  `return_added_status_message` varchar(255) DEFAULT NULL,
  `last_update` timestamp NOT NULL DEFAULT CURRENT_TIMESTAMP,
  KEY `fk_session_id` (`session_id`)
) ENGINE=InnoDB DEFAULT CHARSET=utf8 COMMENT='all endpoints used in a session, and parameters defining searches, retrievals etc..\r\n\r\n';

-- ----------------------------
-- Table structure for articles
-- ----------------------------
DROP TABLE IF EXISTS `articles`;
CREATE TABLE `articles` (
  `articleID` varchar(24) NOT NULL DEFAULT '' COMMENT 'The PEP locator for this article',
  `arttype` varchar(4) NOT NULL DEFAULT '' COMMENT 'Article type, e.g., ART, COM, ERA',
  `authorMast` text CHARACTER SET utf8 COMMENT 'Author names per masthead, e.g. Ronnie C. Lesser, Ph.D.',
  `hdgauthor` text CHARACTER SET utf8 COMMENT 'The heading style author list, e.g., Lesser, R. C.',
  `hdgtitle` text CHARACTER SET utf8 COMMENT 'The title for the heading',
  `srctitleseries` text CHARACTER SET utf8 COMMENT 'Src title bibliogr abbrev style, e.g., Psychoanal. Dial.',
  `publisher` varchar(255) CHARACTER SET utf8 COLLATE utf8_unicode_ci NOT NULL DEFAULT '' COMMENT 'Publisher, e.g., Cambridge, MA / London: Harvard Univ. Press',
  `jrnlcode` varchar(14) DEFAULT NULL COMMENT 'PEP assigned Journal Code, e.g., IJP',
  `year` int(11) DEFAULT NULL COMMENT 'Year of Publication',
  `vol` int(11) DEFAULT NULL COMMENT 'Volume',
  `volsuffix` char(5) DEFAULT NULL COMMENT 'Vol number suffix, e.g., S for supplements',
  `issue` char(5) NOT NULL DEFAULT '' COMMENT 'Issue number or designation, e.g., 1, or pilot',
  `pgrg` varchar(20) DEFAULT NULL COMMENT 'Page range of article, e.g., 1-22',
  `pgstart` int(11) DEFAULT NULL COMMENT 'Starting page number, negative for roman',
  `pgend` int(11) DEFAULT NULL COMMENT 'Ending page number, use negative for roman',
  `source` varchar(10) DEFAULT NULL COMMENT 'Source date',
  `preserve` int(11) DEFAULT '0',
  `filename` varchar(255) DEFAULT NULL COMMENT 'Path and filename of source file',
  `maintocID` varchar(20) DEFAULT NULL,
  `newsecname` varchar(255) CHARACTER SET utf8 COLLATE utf8_unicode_ci DEFAULT NULL COMMENT 'When the article starts a new section in the TOC, name',
  `bktitle` varchar(255) CHARACTER SET utf8 DEFAULT NULL COMMENT 'Title of parent book which contains the article',
  `bkauthors` varchar(255) CHARACTER SET utf8 DEFAULT NULL COMMENT 'Authors of the parent book',
  `xmlref` text CHARACTER SET utf8 COMMENT 'Bibliographic style reference for article, in XML',
  `references` int(11) DEFAULT NULL,
  `doi` varchar(255) DEFAULT NULL,
  `artkwds` varchar(255) CHARACTER SET utf8 DEFAULT NULL,
  `artlang` varchar(255) CHARACTER SET utf8 DEFAULT NULL,
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
) ENGINE=MyISAM DEFAULT CHARSET=latin1 COMMENT='A PEP journal article, book or book section';

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
  KEY `articleID` (`articleID`) USING HASH,
  KEY `RefersTo` (`rxCode`) USING HASH,
  KEY `altArticleID` (`altArticleID`),
  KEY `titleIndex` (`title`) USING BTREE,
  FULLTEXT KEY `fulreffullText` (`fullRefText`),
  FULLTEXT KEY `titleFullText` (`title`)
) ENGINE=MyISAM DEFAULT CHARSET=latin1 COMMENT='All bibliographic entries within PEP';

-- ----------------------------
-- Table structure for gvpi_doc_viewcounts
-- ----------------------------
DROP TABLE IF EXISTS `gvpi_doc_viewcounts`;
CREATE TABLE `gvpi_doc_viewcounts` (
  `account` varchar(255) DEFAULT NULL,
  `locator` varchar(255) DEFAULT NULL,
  `title` varchar(255) DEFAULT NULL,
  `type` varchar(255) DEFAULT NULL,
  `datetimechar` varchar(255) DEFAULT NULL,
  `timestamp` timestamp NULL DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP
) ENGINE=MyISAM DEFAULT CHARSET=utf8;

-- ----------------------------
-- Table structure for ip_addresses
-- ----------------------------
DROP TABLE IF EXISTS `ip_addresses`;
CREATE TABLE `ip_addresses` (
  `ip_addresses_id` int(11) NOT NULL AUTO_INCREMENT,
  `user_id` int(11) NOT NULL,
  `subsystem_id` int(11) NOT NULL,
  `start_ip_address` bigint(20) NOT NULL,
  `end_ip_address` bigint(20) NOT NULL,
  `modified_by_user_id` int(11) NOT NULL,
  `last_update` timestamp NOT NULL DEFAULT CURRENT_TIMESTAMP,
  PRIMARY KEY (`ip_addresses_id`),
  KEY `idxSubsystemIdUserId` (`subsystem_id`,`user_id`),
  KEY `idxStartIpAddress` (`start_ip_address`),
  KEY `idxEndIpAddress` (`end_ip_address`),
  KEY `idxUserId` (`user_id`),
  KEY `FK_ip_addresses_user_subsystem` (`user_id`,`subsystem_id`),
  CONSTRAINT `fk_ip_addresses_user_subsystem` FOREIGN KEY (`user_id`, `subsystem_id`) REFERENCES `user_subsystem` (`user_id`, `subsystem_id`) ON DELETE CASCADE ON UPDATE CASCADE
) ENGINE=InnoDB AUTO_INCREMENT=28533 DEFAULT CHARSET=utf8;

-- ----------------------------
-- Table structure for issn
-- ----------------------------
DROP TABLE IF EXISTS `issn`;
CREATE TABLE `issn` (
  `basecode` varchar(21) CHARACTER SET utf8 NOT NULL DEFAULT '' COMMENT 'Shortened form of the locator',
  `articleID` varchar(24) DEFAULT NULL,
  `active` int(1) DEFAULT NULL,
  `pep_class` set('book','journal','videostream','special','vidostream') DEFAULT '',
  `pep_class_qualifier` set('glossary','works','bookseriesvolume','multivolumebook','multivolumesubbook') DEFAULT '',
  `wall` int(1) DEFAULT '3',
  `mainTOC` varchar(21) DEFAULT '' COMMENT 'Locator for the first instance of this (or the only instance)',
  `first_author` varchar(255) CHARACTER SET utf8 DEFAULT NULL COMMENT 'Needed for KBART, easier than the join, which did lead to some problems since it''s only the first author here',
  `author` varchar(255) CHARACTER SET utf8 DEFAULT NULL,
  `title` varchar(255) CHARACTER SET utf8 DEFAULT NULL COMMENT 'Title of Publication',
  `bibabbrev` varchar(255) CHARACTER SET utf8 DEFAULT NULL COMMENT 'bibliographic Abbreviation',
  `ISSN` varchar(22) DEFAULT NULL COMMENT 'ISSN for Journals only',
  `ISBN-10` varchar(13) DEFAULT NULL,
  `ISBN-13` varchar(17) DEFAULT NULL,
  `pages` int(4) DEFAULT NULL COMMENT 'Number of pages in book',
  `Comment` varchar(255) CHARACTER SET utf8 DEFAULT NULL COMMENT 'use for notes, and "unused" ISBN for books as journals',
  `pepcode` varchar(14) DEFAULT NULL,
  `publisher` varchar(255) CHARACTER SET utf8 DEFAULT NULL,
  `jrnl` tinyint(1) DEFAULT '0' COMMENT '1 if this is a journal, 0 if not',
  `pub_year` int(1) DEFAULT NULL,
  `start_year` int(4) DEFAULT NULL,
  `end_year` int(4) DEFAULT NULL,
  `pep_url` varchar(255) CHARACTER SET utf8 DEFAULT NULL,
  `language` varchar(4) DEFAULT NULL,
  `updated` timestamp NULL DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP,
  `pepversion` int(1) DEFAULT NULL COMMENT 'Version it first appeared in, or planned for',
  `duplicate` varchar(10) DEFAULT NULL COMMENT 'Is this a duplicate (alternative) abbreviation/name (specified)',
  `landing_page` varchar(1024) CHARACTER SET utf8 DEFAULT NULL,
  `coverage_notes` varchar(255) CHARACTER SET utf8 COLLATE utf8_unicode_ci DEFAULT NULL COMMENT 'Added for KBART, explain embargo if necessary',
  `landing_page_intro_html` text CHARACTER SET utf8,
  `landing_page_end_html` text CHARACTER SET utf8,
  `google_books_link` varchar(512) DEFAULT NULL,
  PRIMARY KEY (`basecode`)
) ENGINE=MyISAM DEFAULT CHARSET=latin1 COMMENT='List of PEP ISSNs and ISBNs';

-- ----------------------------
-- Table structure for product
-- ----------------------------
DROP TABLE IF EXISTS `product`;
CREATE TABLE `product` (
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
  KEY `idxParentProductId` (`parent_product_id`),
  KEY `idxSubsystemId` (`subsystem_id`),
  KEY `idxProductLevel` (`product_level`),
  KEY `idxProductAlias` (`product_alias`),
  CONSTRAINT `FK_product_subsystem` FOREIGN KEY (`subsystem_id`) REFERENCES `subsystem` (`subsystem_id`) ON DELETE CASCADE ON UPDATE CASCADE
) ENGINE=InnoDB AUTO_INCREMENT=3824 DEFAULT CHARSET=utf8;

-- ----------------------------
-- Table structure for referrer_urls
-- ----------------------------
DROP TABLE IF EXISTS `referrer_urls`;
CREATE TABLE `referrer_urls` (
  `referrer_urls_id` int(11) NOT NULL AUTO_INCREMENT,
  `user_id` int(11) NOT NULL,
  `subsystem_id` int(11) NOT NULL,
  `referrer_url` varchar(500) NOT NULL,
  `modified_by_user_id` int(11) NOT NULL,
  `last_update` timestamp NOT NULL DEFAULT CURRENT_TIMESTAMP,
  PRIMARY KEY (`referrer_urls_id`),
  KEY `idxSubsystemIdUserId` (`subsystem_id`,`user_id`),
  KEY `idxReferrerUrl` (`referrer_url`(255)),
  KEY `idxUserId` (`user_id`),
  KEY `FK_referrer_urls_user_subsystem` (`user_id`,`subsystem_id`),
  CONSTRAINT `FK_referrer_urls_user_subsystem` FOREIGN KEY (`user_id`, `subsystem_id`) REFERENCES `user_subsystem` (`user_id`, `subsystem_id`) ON DELETE CASCADE ON UPDATE CASCADE
) ENGINE=InnoDB AUTO_INCREMENT=1561 DEFAULT CHARSET=utf8;

-- ----------------------------
-- Table structure for subscriptions
-- ----------------------------
DROP TABLE IF EXISTS `subscriptions`;
CREATE TABLE `subscriptions` (
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
  KEY `idxStartDate` (`start_date`),
  KEY `idxEndDate` (`end_date`),
  KEY `idxProductId` (`product_id`)
) ENGINE=InnoDB DEFAULT CHARSET=utf8;

-- ----------------------------
-- Table structure for subsystem
-- ----------------------------
DROP TABLE IF EXISTS `subsystem`;
CREATE TABLE `subsystem` (
  `subsystem_id` int(11) NOT NULL,
  `subsystem_name` varchar(100) NOT NULL,
  `domain_name` varchar(50) NOT NULL,
  `last_update` timestamp NOT NULL DEFAULT CURRENT_TIMESTAMP,
  PRIMARY KEY (`subsystem_id`),
  UNIQUE KEY `idxSubsystem_name` (`subsystem_name`)
) ENGINE=InnoDB DEFAULT CHARSET=utf8;

-- ----------------------------
-- Table structure for user
-- ----------------------------
DROP TABLE IF EXISTS `user`;
CREATE TABLE `user` (
  `user_id` int(11) NOT NULL AUTO_INCREMENT,
  `username` varchar(255) NOT NULL,
  `password` varchar(512) NOT NULL,
  `company` varchar(125) DEFAULT NULL,
  `email_address` varchar(65) DEFAULT NULL,
  `modified_by_user_id` int(11) DEFAULT NULL,
  `enabled` tinyint(1) DEFAULT '0',
  `admin` tinyint(1) DEFAULT '0',
  `user_agrees_date` datetime DEFAULT NULL ON UPDATE CURRENT_TIMESTAMP,
  `user_agrees_to_tracking` tinyint(1) DEFAULT '0',
  `user_agrees_to_cookies` tinyint(1) DEFAULT '0',
  `added_date` datetime DEFAULT NULL ON UPDATE CURRENT_TIMESTAMP,
  `last_update` timestamp NOT NULL DEFAULT CURRENT_TIMESTAMP,
  PRIMARY KEY (`user_id`),
  UNIQUE KEY `unique_username` (`username`),
  KEY `idxUsername` (`username`)
) ENGINE=InnoDB AUTO_INCREMENT=119127 DEFAULT CHARSET=utf8;

-- ----------------------------
-- Table structure for user_property_name
-- ----------------------------
DROP TABLE IF EXISTS `user_property_name`;
CREATE TABLE `user_property_name` (
  `user_property_name_id` int(11) NOT NULL AUTO_INCREMENT,
  `subsystem_id` int(11) NOT NULL,
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
  KEY `idxSubsystemId` (`subsystem_id`),
  KEY `FK_user_property_name_ref_user_property_data_type` (`user_property_data_type_id`),
  KEY `FK_user_property_name_ref_user_property_user_access` (`user_property_user_access_id`)
) ENGINE=InnoDB AUTO_INCREMENT=169 DEFAULT CHARSET=utf8;

-- ----------------------------
-- Table structure for user_property_value
-- ----------------------------
DROP TABLE IF EXISTS `user_property_value`;
CREATE TABLE `user_property_value` (
  `user_property_value_id` int(11) NOT NULL AUTO_INCREMENT,
  `user_id` int(11) NOT NULL,
  `user_property_name_id` int(11) NOT NULL,
  `user_property_value` varchar(5000) NOT NULL,
  `modified_by_user_id` int(11) NOT NULL,
  `last_update` timestamp NOT NULL DEFAULT CURRENT_TIMESTAMP,
  PRIMARY KEY (`user_property_value_id`),
  UNIQUE KEY `IX_user_property_value` (`user_id`,`user_property_name_id`),
  KEY `idxUserPropertyNameId` (`user_property_name_id`)
) ENGINE=InnoDB AUTO_INCREMENT=577755 DEFAULT CHARSET=utf8;

-- ----------------------------
-- Table structure for user_subsystem
-- ----------------------------
DROP TABLE IF EXISTS `user_subsystem`;
CREATE TABLE `user_subsystem` (
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
  KEY `idxEmailOptin` (`email_optin`),
  KEY `idxLogActivity` (`hide_activity`),
  KEY `idxParentUserId` (`parent_user_id`),
  KEY `idxAdministrativeGroupId` (`administrative_group_id`),
  KEY `idxDeleted` (`deleted`),
  KEY `FK_user_subsystem_subsystem` (`subsystem_id`)
) ENGINE=InnoDB DEFAULT CHARSET=utf8;

-- ----------------------------
-- View structure for mostcitedarticles
-- ----------------------------
DROP VIEW IF EXISTS `mostcitedarticles`;
CREATE ALGORITHM=UNDEFINED DEFINER=`root`@`localhost` SQL SECURITY DEFINER VIEW `mostcitedarticles` AS select `fullbiblioxml`.`rxCode` AS `rxCode`,count(if((`articles`.`year` > (year(now()) - 5)),`fullbiblioxml`.`articleID`,0)) AS `count5`,count(if((`articles`.`year` > (year(now()) - 10)),`fullbiblioxml`.`articleID`,0)) AS `count10`,count(if((`articles`.`year` > (year(now()) - 20)),`fullbiblioxml`.`articleID`,0)) AS `count20`,count(`fullbiblioxml`.`articleID`) AS `countAll` from (`fullbiblioxml` join `articles`) where ((`fullbiblioxml`.`articleID` = `articles`.`articleID`) and (`fullbiblioxml`.`rxCode` is not null) and (substr(`fullbiblioxml`.`rxCode`,1,3) not in ('ZBK','IPL','SE.','GW.'))) group by `fullbiblioxml`.`rxCode` order by `countAll` desc ;

-- ----------------------------
-- View structure for mostcitedarticleswithdetails
-- ----------------------------
DROP VIEW IF EXISTS `mostcitedarticleswithdetails`;
CREATE ALGORITHM=UNDEFINED DEFINER=`root`@`localhost` SQL SECURITY DEFINER VIEW `mostcitedarticleswithdetails` AS select `mostcitedarticles`.`rxCode` AS `rxCode`,`mostcitedarticles`.`count5` AS `count5`,`mostcitedarticles`.`count10` AS `count10`,`mostcitedarticles`.`count20` AS `count20`,`mostcitedarticles`.`countAll` AS `countAll`,`articles`.`hdgauthor` AS `hdgauthor`,`articles`.`hdgtitle` AS `hdgtitle`,`articles`.`srctitleseries` AS `srctitleseries`,`articles`.`year` AS `year`,`articles`.`vol` AS `vol`,`articles`.`pgrg` AS `pgrg` from (`mostcitedarticles` join `articles` on((`mostcitedarticles`.`rxCode` = `articles`.`articleID`))) order by `mostcitedarticles`.`countAll` desc ;

-- ----------------------------
-- View structure for product_family
-- ----------------------------
DROP VIEW IF EXISTS `product_family`;
CREATE ALGORITHM=UNDEFINED DEFINER=`root`@`localhost` SQL SECURITY DEFINER VIEW `product_family` AS select `product_parent`.`product` AS `parent_product`,`product`.`product` AS `product`,`product`.`product_description` AS `product_description`,`product_parent`.`product_description` AS `parent_product_description` from (`product` join `product_parent` on((`product_parent`.`product_id` = `product`.`parent_product_id`))) order by `product_parent`.`product` ;

-- ----------------------------
-- View structure for user_active_subscriptions
-- ----------------------------
DROP VIEW IF EXISTS `user_active_subscriptions`;
CREATE ALGORITHM=UNDEFINED DEFINER=`root`@`localhost` SQL SECURITY DEFINER VIEW `user_active_subscriptions` AS select `user`.`user_id` AS `user_id`,`user`.`username` AS `username`,`user`.`company` AS `company`,`user`.`enabled` AS `enabled`,`user`.`last_update` AS `last_update`,`subscriptions`.`start_date` AS `start_date`,`subscriptions`.`end_date` AS `end_date`,`subscriptions`.`max_concurrency` AS `max_concurrency`,`subscriptions`.`product_id` AS `product_id`,`product`.`product` AS `product`,`product`.`product_description` AS `product_description`,`user`.`admin` AS `admin`,`user`.`password` AS `password` from ((`user` join `subscriptions` on((`subscriptions`.`user_id` = `user`.`user_id`))) join `product` on((`subscriptions`.`product_id` = `product`.`product_id`))) where (((`user`.`enabled` = TRUE) and (`subscriptions`.`end_date` > now())) or (`subscriptions`.`perpetual` = TRUE)) order by `user`.`last_update` desc ;

-- ----------------------------
-- View structure for user_subscriptions
-- ----------------------------
DROP VIEW IF EXISTS `user_subscriptions`;
CREATE ALGORITHM=UNDEFINED DEFINER=`root`@`localhost` SQL SECURITY DEFINER VIEW `user_subscriptions` AS select `user`.`username` AS `username`,`user`.`user_id` AS `user_id`,`user`.`enabled` AS `enabled`,`product`.`product` AS `product`,`product`.`product_description` AS `product_description`,`product`.`parent_product_id` AS `parent_product_id`,`product`.`product_id` AS `product_id`,`subscriptions`.`start_date` AS `start_date`,`subscriptions`.`end_date` AS `end_date`,`subscriptions`.`max_concurrency` AS `max_concurrency`,`subscriptions`.`perpetual` AS `perpetual` from ((`user` join `subscriptions` on((`subscriptions`.`user_id` = `user`.`user_id`))) join `product` on((`subscriptions`.`product_id` = `product`.`product_id`))) ;

-- ----------------------------
-- View structure for vw_active_sessions
-- ----------------------------
DROP VIEW IF EXISTS `vw_active_sessions`;
CREATE ALGORITHM=UNDEFINED DEFINER=`root`@`localhost` SQL SECURITY DEFINER VIEW `vw_active_sessions` AS select `api_sessions`.`session_id` AS `session_id`,`api_sessions`.`user_id` AS `user_id`,`api_sessions`.`username` AS `username`,`api_sessions`.`user_ip` AS `user_ip`,`api_sessions`.`connected_via` AS `connected_via`,`api_sessions`.`referrer` AS `referrer`,`api_sessions`.`session_start` AS `session_start`,`api_sessions`.`session_end` AS `session_end`,`api_sessions`.`session_expires_time` AS `session_expires_time`,`api_sessions`.`access_token` AS `access_token`,`api_sessions`.`authenticated` AS `authenticated`,`api_sessions`.`api_client_id` AS `api_client_id`,`api_sessions`.`updated` AS `updated` from `api_sessions` where ((`api_sessions`.`user_id` <> 0) and isnull(`api_sessions`.`session_end`)) order by `api_sessions`.`session_start` desc ;

-- ----------------------------
-- View structure for vw_api_session_endpoints_with_descriptor
-- ----------------------------
DROP VIEW IF EXISTS `vw_api_session_endpoints_with_descriptor`;
CREATE ALGORITHM=UNDEFINED DEFINER=`root`@`localhost` SQL SECURITY DEFINER VIEW `vw_api_session_endpoints_with_descriptor` AS select `api_session_endpoints`.`session_id` AS `session_id`,`api_session_endpoints`.`api_endpoint_id` AS `api_endpoint_id`,`api_session_endpoints`.`params` AS `params`,`api_session_endpoints`.`documentid` AS `documentid`,`api_session_endpoints`.`return_status_code` AS `return_status_code`,`api_session_endpoints`.`return_added_status_message` AS `return_added_status_message`,`api_session_endpoints`.`last_update` AS `last_update`,`api_endpoints`.`endpoint_url` AS `endpoint_url` from (`api_endpoints` join `api_session_endpoints` on((`api_session_endpoints`.`api_endpoint_id` = `api_endpoints`.`api_endpoint_id`))) ;

-- ----------------------------
-- View structure for vw_document_views_crosstab
-- ----------------------------
DROP VIEW IF EXISTS `vw_document_views_crosstab`;
CREATE ALGORITHM=UNDEFINED DEFINER=`root`@`localhost` SQL SECURITY DEFINER VIEW `vw_document_views_crosstab` AS select `r0`.`documentid` AS `documentid`,`r1`.`views` AS `lastweek`,`r2`.`views` AS `lastmonth`,`r3`.`views` AS `last6months`,`r4`.`views` AS `lastcalyear` from ((((((select distinct `opascentral`.`api_session_endpoints`.`documentid` AS `documentid` from `opascentral`.`api_session_endpoints`)) `r0` left join `opascentral`.`vw_docviews_lastweek` `r1` on((`r1`.`documentid` = `r0`.`documentid`))) left join `opascentral`.`vw_docviews_lastmonth` `r2` on((`r2`.`documentid` = `r0`.`documentid`))) left join `opascentral`.`vw_docviews_lastsixmonths` `r3` on((`r3`.`documentid` = `r0`.`documentid`))) left join `opascentral`.`vw_docviews_lastcalyear` `r4` on((`r4`.`documentid` = `r0`.`documentid`))) where (`r0`.`documentid` is not null) ;

-- ----------------------------
-- View structure for vw_docviews_lastcalyear
-- ----------------------------
DROP VIEW IF EXISTS `vw_docviews_lastcalyear`;
CREATE ALGORITHM=UNDEFINED DEFINER=`root`@`localhost` SQL SECURITY DEFINER VIEW `vw_docviews_lastcalyear` AS select `api_session_endpoints`.`documentid` AS `documentid`,count(0) AS `views` from `api_session_endpoints` where (year(`api_session_endpoints`.`last_update`) = (year(now()) - 1)) group by `api_session_endpoints`.`documentid` ;

-- ----------------------------
-- View structure for vw_docviews_lastmonth
-- ----------------------------
DROP VIEW IF EXISTS `vw_docviews_lastmonth`;
CREATE ALGORITHM=UNDEFINED DEFINER=`root`@`localhost` SQL SECURITY DEFINER VIEW `vw_docviews_lastmonth` AS select `api_session_endpoints`.`documentid` AS `documentid`,count(0) AS `views` from `api_session_endpoints` where (`api_session_endpoints`.`last_update` > (now() - interval 1 month)) group by `api_session_endpoints`.`documentid` ;

-- ----------------------------
-- View structure for vw_docviews_lastsixmonths
-- ----------------------------
DROP VIEW IF EXISTS `vw_docviews_lastsixmonths`;
CREATE ALGORITHM=UNDEFINED DEFINER=`root`@`localhost` SQL SECURITY DEFINER VIEW `vw_docviews_lastsixmonths` AS select `api_session_endpoints`.`documentid` AS `documentid`,count(0) AS `views` from `api_session_endpoints` where (`api_session_endpoints`.`last_update` > (now() - interval 6 month)) group by `api_session_endpoints`.`documentid` ;

-- ----------------------------
-- View structure for vw_docviews_lastweek
-- ----------------------------
DROP VIEW IF EXISTS `vw_docviews_lastweek`;
CREATE ALGORITHM=UNDEFINED DEFINER=`root`@`localhost` SQL SECURITY DEFINER VIEW `vw_docviews_lastweek` AS select `api_session_endpoints`.`documentid` AS `documentid`,count(0) AS `views` from `api_session_endpoints` where (`api_session_endpoints`.`last_update` > (now() - interval 7 day)) group by `api_session_endpoints`.`documentid` ;

-- ----------------------------
-- View structure for vw_latest_session_activity
-- ----------------------------
DROP VIEW IF EXISTS `vw_latest_session_activity`;
CREATE ALGORITHM=UNDEFINED DEFINER=`root`@`localhost` SQL SECURITY DEFINER VIEW `vw_latest_session_activity` AS select `api_session_endpoints`.`session_id` AS `session_id`,max(`api_session_endpoints`.`last_update`) AS `latest_activity` from `api_session_endpoints` group by `api_session_endpoints`.`session_id` order by max(`api_session_endpoints`.`last_update`) desc ;

-- ----------------------------
-- View structure for vw_most_document_views
-- ----------------------------
DROP VIEW IF EXISTS `vw_most_document_views`;
CREATE ALGORITHM=UNDEFINED DEFINER=`root`@`localhost` SQL SECURITY DEFINER VIEW `vw_most_document_views` AS select `vw_docviews_crosstab`.`articleID` AS `articleID`,`vw_docviews_crosstab`.`views` AS `views`,`vw_docviews_crosstab`.`last_update` AS `last_update`,`articles`.`xmlref` AS `xmlref`,`articles`.`hdgauthor` AS `hdgauthor`,`articles`.`hdgtitle` AS `hdgtitle`,`articles`.`arttype` AS `arttype`,`articles`.`year` AS `year`,`articles`.`vol` AS `vol`,`articles`.`issue` AS `issue`,`articles`.`pgrg` AS `pgrg` from (`vw_docviews_crosstab` join `articles` on((convert(`articles`.`articleID` using utf8) = `vw_docviews_crosstab`.`articleID`))) order by `vw_docviews_crosstab`.`views` desc ;

-- ----------------------------
-- View structure for vw_most_viewed
-- ----------------------------
DROP VIEW IF EXISTS `vw_most_viewed`;
CREATE ALGORITHM=UNDEFINED DEFINER=`root`@`localhost` SQL SECURITY DEFINER VIEW `vw_most_viewed` AS select `api_session_endpoints`.`documentid` AS `articleID`,`api_session_endpoints`.`last_update` AS `last_update`,`articles`.`hdgauthor` AS `hdgauthor`,`articles`.`hdgtitle` AS `hdgtitle`,`articles`.`srctitleseries` AS `srctitleseries`,`articles`.`year` AS `pubYear`,`articles`.`jrnlcode` AS `jrnlcode`,count(`api_session_endpoints`.`documentid`) AS `views` from (`api_session_endpoints` join `articles`) where (`api_session_endpoints`.`documentid` = convert(`articles`.`articleID` using utf8)) group by `api_session_endpoints`.`documentid` order by `views` desc ;

-- ----------------------------
-- View structure for vw_opas_sources
-- ----------------------------
DROP VIEW IF EXISTS `vw_opas_sources`;
CREATE ALGORITHM=UNDEFINED DEFINER=`root`@`localhost` SQL SECURITY DEFINER VIEW `vw_opas_sources` AS select `issn`.`basecode` AS `base_code`,`issn`.`pepcode` AS `src_code`,`issn`.`articleID` AS `art_id`,`issn`.`active` AS `active`,`issn`.`pep_class` AS `src_type`,`issn`.`pep_class_qualifier` AS `src_type_qualifier`,`issn`.`wall` AS `embargo_yrs`,`issn`.`mainTOC` AS `toc_instance`,`issn`.`first_author` AS `first_author`,`issn`.`author` AS `author`,`issn`.`title` AS `title`,`issn`.`bibabbrev` AS `bib_abbrev`,`issn`.`ISSN` AS `ISSN`,`issn`.`ISBN-10` AS `ISBN-10`,`issn`.`ISBN-13` AS `ISBN-13`,`issn`.`pages` AS `pages`,`issn`.`Comment` AS `Comment`,`issn`.`publisher` AS `publisher`,`issn`.`jrnl` AS `jrnl`,`issn`.`pub_year` AS `pub_year`,`issn`.`start_year` AS `start_year`,`issn`.`end_year` AS `end_year`,`issn`.`pep_url` AS `pep_url`,`issn`.`language` AS `language`,`issn`.`pepversion` AS `added_year`,`issn`.`duplicate` AS `duplicate`,`issn`.`landing_page` AS `landing_page`,`issn`.`coverage_notes` AS `coverage_notes`,`issn`.`landing_page_intro_html` AS `landing_page_intro_html`,`issn`.`landing_page_end_html` AS `landing_page_end_html`,`issn`.`google_books_link` AS `google_books_link`,`issn`.`updated` AS `updated` from `issn` ;

-- ----------------------------
-- View structure for vw_product_parent
-- ----------------------------
DROP VIEW IF EXISTS `vw_product_parent`;
CREATE ALGORITHM=UNDEFINED DEFINER=`root`@`localhost` SQL SECURITY DEFINER VIEW `vw_product_parent` AS select `parent`.`product` AS `parent_product`,`product`.`product_level` AS `product_level`,`product`.`inherit_parent_metadata` AS `inherit_parent_metadata`,`product`.`product_alias` AS `product_alias`,`product`.`id_type` AS `id_type`,`product`.`counter_service` AS `counter_service`,`product`.`product` AS `product` from (`product` left join `product` `parent` on((`parent`.`product_id` = `product`.`parent_product_id`))) order by `product`.`product_level`,`parent`.`product`,`product`.`product` ;

-- ----------------------------
-- View structure for vw_referrer_users
-- ----------------------------
DROP VIEW IF EXISTS `vw_referrer_users`;
CREATE ALGORITHM=UNDEFINED DEFINER=`root`@`localhost` SQL SECURITY DEFINER VIEW `vw_referrer_users` AS select `referrer_urls`.`referrer_url` AS `referrer_url`,`product`.`product` AS `product`,`user`.`enabled` AS `enabled`,`user`.`username` AS `username`,`user`.`company` AS `company`,`subscriptions`.`max_concurrency` AS `max_concurrency`,`subscriptions`.`perpetual` AS `perpetual`,`subscriptions`.`user_id` AS `user_id`,`user`.`email_address` AS `email_address`,`subscriptions`.`product_id` AS `product_id`,`referrer_urls`.`last_update` AS `referrer_last_update` from (((`subscriptions` join `referrer_urls` on((`referrer_urls`.`user_id` = `subscriptions`.`user_id`))) join `user` on((`user`.`user_id` = `subscriptions`.`user_id`))) join `product` on((`product`.`product_id` = `subscriptions`.`product_id`))) ;

-- ----------------------------
-- View structure for vw_stat_most_viewed
-- ----------------------------
DROP VIEW IF EXISTS `vw_stat_most_viewed`;
CREATE ALGORITHM=UNDEFINED DEFINER=`root`@`localhost` SQL SECURITY DEFINER VIEW `vw_stat_most_viewed` AS select `vw_document_views_crosstab`.`documentid` AS `documentid`,`vw_document_views_crosstab`.`lastweek` AS `lastweek`,`vw_document_views_crosstab`.`lastmonth` AS `lastmonth`,`vw_document_views_crosstab`.`last6months` AS `last6months`,`vw_document_views_crosstab`.`lastcalyear` AS `lastcalyear`,`opascentral`.`articles`.`hdgauthor` AS `hdgauthor`,`opascentral`.`articles`.`hdgtitle` AS `hdgtitle`,`opascentral`.`articles`.`srctitleseries` AS `srctitleseries`,`opascentral`.`articles`.`publisher` AS `publisher`,`opascentral`.`articles`.`jrnlcode` AS `jrnlcode`,`opascentral`.`articles`.`year` AS `year`,`opascentral`.`articles`.`vol` AS `vol`,`opascentral`.`articles`.`pgrg` AS `pgrg`,`opascentral`.`articles`.`source` AS `source`,`opascentral`.`articles`.`preserve` AS `preserve`,`opascentral`.`articles`.`filename` AS `filename`,`opascentral`.`articles`.`bktitle` AS `bktitle`,`opascentral`.`articles`.`bkauthors` AS `bkauthors`,`opascentral`.`articles`.`xmlref` AS `xmlref` from (`opascentral`.`vw_document_views_crosstab` join `opascentral`.`articles` on((convert(`opascentral`.`articles`.`articleID` using utf8) = `vw_document_views_crosstab`.`documentid`))) ;

-- ----------------------------
-- View structure for vw_user_referred
-- ----------------------------
DROP VIEW IF EXISTS `vw_user_referred`;
CREATE ALGORITHM=UNDEFINED DEFINER=`root`@`localhost` SQL SECURITY DEFINER VIEW `vw_user_referred` AS select `user`.`user_id` AS `user_id`,`user`.`username` AS `username`,`referrer_urls`.`referrer_url` AS `referrer_url`,`referrer_urls`.`modified_by_user_id` AS `modified_by_user_id`,`referrer_urls`.`last_update` AS `last_update`,`user`.`enabled` AS `enabled`,`user`.`company` AS `company`,`user`.`email_address` AS `email_address` from (`user` join `referrer_urls` on((`referrer_urls`.`user_id` = `user`.`user_id`))) ;

-- ----------------------------
-- View structure for vw_user_referrer_account_management
-- ----------------------------
DROP VIEW IF EXISTS `vw_user_referrer_account_management`;
CREATE ALGORITHM=UNDEFINED DEFINER=`root`@`localhost` SQL SECURITY DEFINER VIEW `vw_user_referrer_account_management` AS select `referrer_urls`.`referrer_url` AS `referrer_url`,`user`.`enabled` AS `enabled`,`user`.`username` AS `username`,`user`.`company` AS `company`,`user`.`email_address` AS `email_address`,`user`.`user_agrees_date` AS `user_agrees_date`,`user`.`user_agrees_to_tracking` AS `user_agrees_to_tracking`,`user`.`user_agrees_to_cookies` AS `user_agrees_to_cookies`,`user`.`added_date` AS `added_date`,`user`.`last_update` AS `last_update`,`user`.`admin` AS `admin` from (`user` join `referrer_urls` on((`referrer_urls`.`user_id` = `user`.`user_id`))) ;

-- ----------------------------
-- View structure for vw_user_session_activity
-- ----------------------------
DROP VIEW IF EXISTS `vw_user_session_activity`;
CREATE ALGORITHM=UNDEFINED DEFINER=`root`@`localhost` SQL SECURITY DEFINER VIEW `vw_user_session_activity` AS select `user`.`username` AS `username`,`user`.`company` AS `company`,`user`.`enabled` AS `enabled`,`api_sessions`.`user_ip` AS `user_ip`,`api_sessions`.`connected_via` AS `connected_via`,`api_sessions`.`referrer` AS `referrer`,`api_sessions`.`session_start` AS `session_start`,`api_sessions`.`session_end` AS `session_end`,`api_endpoints`.`endpoint_url` AS `endpoint_url`,`api_session_endpoints`.`params` AS `params`,`api_session_endpoints`.`documentid` AS `documentid`,`api_session_endpoints`.`return_status_code` AS `return_status_code`,`api_session_endpoints`.`return_added_status_message` AS `return_added_status_message`,`api_session_endpoints`.`last_update` AS `last_update`,`api_session_endpoints`.`session_id` AS `session_id` from (((`user` join `api_sessions` on((`api_sessions`.`user_id` = `user`.`user_id`))) join `api_session_endpoints` on((`api_session_endpoints`.`session_id` = `api_sessions`.`session_id`))) join `api_endpoints` on((`api_endpoints`.`api_endpoint_id` = `api_session_endpoints`.`api_endpoint_id`))) order by `api_session_endpoints`.`last_update` desc ;
SET FOREIGN_KEY_CHECKS=1;
