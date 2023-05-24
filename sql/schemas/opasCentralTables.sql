/*
 Navicat MySQL Data Transfer

 Source Server         : AWS-RDS-Development
 Source Server Type    : MySQL
 Source Server Version : 80028
 Source Host           : development.c6re6qczl2ae.us-east-1.rds.amazonaws.com:3306
 Source Schema         : opascentral

 Target Server Type    : MySQL
 Target Server Version : 80028
 File Encoding         : 65001

 Date: 22/05/2023 10:44:23
*/

SET NAMES utf8mb4;
SET FOREIGN_KEY_CHECKS = 0;
SET SQL_MODE = 'NO_AUTO_VALUE_ON_ZERO,NO_ZERO_IN_DATE,NO_ZERO_DATE,ERROR_FOR_DIVISION_BY_ZERO,NO_ENGINE_SUBSTITUTION';

-- ----------------------------
-- Table structure for api_articles
-- ----------------------------
DROP TABLE IF EXISTS `api_articles`;
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
  `fullfilename` varchar(255) CHARACTER SET utf8 COLLATE utf8_general_ci NULL DEFAULT NULL COMMENT 'Full Filename with path`',
  `manuscript_date_str` char(40) CHARACTER SET utf8 COLLATE utf8_general_ci NULL DEFAULT NULL COMMENT 'Manuscript date string',
  `last_update` timestamp NOT NULL DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP COMMENT 'Automatic Timestamp when record changes',
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

-- ----------------------------
-- Table structure for api_articles_removed
-- ----------------------------
DROP TABLE IF EXISTS `api_articles_removed`;
CREATE TABLE `api_articles_removed`  (
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
  `fullfilename` varchar(255) CHARACTER SET utf8 COLLATE utf8_general_ci NULL DEFAULT NULL COMMENT 'Full Filename with path',
  `manuscript_date_str` char(40) CHARACTER SET utf8 COLLATE utf8_general_ci NULL DEFAULT NULL COMMENT 'Manuscript date string',
  `last_update` timestamp NOT NULL DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP COMMENT 'Automatic Timestamp when record changes',
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

-- ----------------------------
-- Table structure for api_biblioxml2
-- ----------------------------
DROP TABLE IF EXISTS `api_biblioxml2`;
CREATE TABLE `api_biblioxml2`  (
  `art_id` varchar(24) CHARACTER SET latin1 COLLATE latin1_swedish_ci NOT NULL,
  `ref_local_id` varchar(25) CHARACTER SET latin1 COLLATE latin1_swedish_ci NOT NULL,
  `art_year` int NULL DEFAULT NULL,
  `ref_rx` varchar(30) CHARACTER SET latin1 COLLATE latin1_swedish_ci NULL DEFAULT NULL COMMENT 'This article references...',
  `ref_rx_confidence` double NOT NULL DEFAULT 0 COMMENT 'A value of 1 will never be automatically replaced',
  `ref_rxcf` varchar(255) CHARACTER SET utf8 COLLATE utf8_general_ci NULL DEFAULT NULL COMMENT 'This article may be related to...',
  `ref_rxcf_confidence` double NOT NULL DEFAULT 0 COMMENT 'A value of 1 will never be automatically replaced',
  `ref_sourcecode` varchar(24) CHARACTER SET utf8 COLLATE utf8_general_ci NULL DEFAULT NULL COMMENT 'If it\'s refcorrections, this record came from the refcorrections table and should not be updated.',
  `ref_link_source` varchar(24) CHARACTER SET utf8 COLLATE utf8_general_ci NULL DEFAULT NULL,
  `ref_authors` varchar(2048) CHARACTER SET utf8 COLLATE utf8_general_ci NULL DEFAULT NULL,
  `ref_title` varchar(1024) CHARACTER SET utf8 COLLATE utf8_general_ci NULL DEFAULT NULL,
  `ref_text` text CHARACTER SET utf8 COLLATE utf8_general_ci NULL,
  `ref_sourcetype` varchar(255) CHARACTER SET utf8 COLLATE utf8_general_ci NULL DEFAULT NULL,
  `ref_sourcetitle` varchar(1024) CHARACTER SET utf8 COLLATE utf8_swedish_ci NULL DEFAULT NULL COMMENT 'Record the journal name as extracted from the XML referennce.  Useful to sort and check reference.',
  `ref_authors_xml` varchar(2048) CHARACTER SET utf8 COLLATE utf8_general_ci NULL DEFAULT NULL,
  `ref_xml` text CHARACTER SET utf8 COLLATE utf8_general_ci NULL,
  `ref_pgrg` varchar(24) CHARACTER SET utf8 COLLATE utf8_general_ci NULL DEFAULT NULL,
  `ref_doi` varchar(255) CHARACTER SET utf8 COLLATE utf8_general_ci NULL DEFAULT NULL COMMENT 'Document Object Identifier for this reference',
  `ref_year` varchar(24) CHARACTER SET utf8 COLLATE utf8_general_ci NULL DEFAULT NULL,
  `ref_year_int` int NULL DEFAULT NULL,
  `ref_volume` varchar(24) CHARACTER SET utf8 COLLATE utf8_general_ci NULL DEFAULT NULL,
  `ref_publisher` varchar(255) CHARACTER SET utf8 COLLATE utf8_general_ci NULL DEFAULT NULL,
  `skip_reason` varchar(40) CHARACTER SET utf8 COLLATE utf8_general_ci NULL DEFAULT NULL,
  `skip_incremental_scans` tinyint(1) NULL DEFAULT NULL,
  `last_update` timestamp NOT NULL DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP,
  PRIMARY KEY (`art_id`, `ref_local_id`) USING BTREE,
  UNIQUE INDEX `Primary Key`(`art_id`, `ref_local_id`) USING BTREE,
  INDEX `articleID`(`art_id`) USING BTREE,
  INDEX `RefersTo`(`ref_rx`) USING BTREE,
  FULLTEXT INDEX `fulreffullText`(`ref_text`),
  FULLTEXT INDEX `full_ref_xml`(`ref_xml`)
) ENGINE = InnoDB CHARACTER SET = utf8 COLLATE = utf8_general_ci COMMENT = 'All bibliographic entries within PEP' ROW_FORMAT = Dynamic;

-- ----------------------------
-- Table structure for api_client_apps
-- ----------------------------
DROP TABLE IF EXISTS `api_client_apps`;
CREATE TABLE `api_client_apps`  (
  `api_client_id` int NOT NULL,
  `api_client_name` varchar(100) CHARACTER SET utf8 COLLATE utf8_general_ci NOT NULL,
  `api_client_key` varchar(255) CHARACTER SET utf8 COLLATE utf8_general_ci NULL DEFAULT NULL,
  `last_update` timestamp NOT NULL DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP,
  PRIMARY KEY (`api_client_id`) USING BTREE,
  UNIQUE INDEX `idxClientname`(`api_client_name`) USING BTREE
) ENGINE = InnoDB CHARACTER SET = utf8 COLLATE = utf8_general_ci COMMENT = 'Keep track of keys assigned to clients, but not used in v1 or v2 API as of 20191110' ROW_FORMAT = Dynamic;

-- ----------------------------
-- Table structure for api_client_configs
-- ----------------------------
DROP TABLE IF EXISTS `api_client_configs`;
CREATE TABLE `api_client_configs`  (
  `config_id` int NOT NULL AUTO_INCREMENT,
  `client_id` int NULL DEFAULT NULL,
  `session_id` varchar(60) CHARACTER SET utf8 COLLATE utf8_general_ci NOT NULL,
  `config_name` varchar(255) CHARACTER SET utf8mb4 COLLATE utf8mb4_0900_ai_ci NOT NULL,
  `config_settings` longtext CHARACTER SET utf8mb4 COLLATE utf8mb4_0900_ai_ci NULL,
  `last_update` datetime NULL DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP,
  PRIMARY KEY (`config_id`, `session_id`) USING BTREE,
  UNIQUE INDEX `clientset`(`client_id`, `config_name`) USING BTREE
) ENGINE = InnoDB AUTO_INCREMENT = 450 CHARACTER SET = utf8mb4 COLLATE = utf8mb4_0900_ai_ci COMMENT = 'Client specific configuration information' ROW_FORMAT = Dynamic;

-- ----------------------------
-- Table structure for api_docviews
-- ----------------------------
DROP TABLE IF EXISTS `api_docviews`;
CREATE TABLE `api_docviews`  (
  `user_id` varchar(60) CHARACTER SET utf8 COLLATE utf8_general_ci NOT NULL COMMENT 'user_id that viewed the document',
  `session_id` varchar(60) CHARACTER SET utf8 COLLATE utf8_general_ci NOT NULL COMMENT 'session_id that viewed the document',
  `document_id` varchar(255) CHARACTER SET latin1 COLLATE latin1_swedish_ci NOT NULL DEFAULT '' COMMENT 'document (article id) viewed',
  `type` varchar(255) CHARACTER SET utf8 COLLATE utf8_general_ci NOT NULL COMMENT 'type of document viewed',
  `datetimechar` varchar(255) CHARACTER SET utf8 COLLATE utf8_general_ci NOT NULL COMMENT 'character based date-time viewed',
  `last_update` timestamp NULL DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP COMMENT 'when this record was updated',
  `id` bigint UNSIGNED NOT NULL AUTO_INCREMENT COMMENT 'auto increment id field for PaDS reports to distinguish records where the time is exactly the same',
  PRIMARY KEY (`id`) USING BTREE,
  INDEX `user_id`(`user_id`) USING BTREE,
  INDEX `session_id`(`session_id`) USING BTREE
) ENGINE = InnoDB AUTO_INCREMENT = 3537 CHARACTER SET = utf8 COLLATE = utf8_general_ci COMMENT = 'Track the number of times a document is viewed as an abstract, full-text, PDF, or EPUB.  Somewhat redundate to api_session_endpoints table, but with less extraneous data..' ROW_FORMAT = Dynamic;

-- ----------------------------
-- Table structure for api_endpoints
-- ----------------------------
DROP TABLE IF EXISTS `api_endpoints`;
CREATE TABLE `api_endpoints`  (
  `api_endpoint_id` int NOT NULL AUTO_INCREMENT,
  `endpoint_url` varchar(200) CHARACTER SET utf8 COLLATE utf8_general_ci NOT NULL,
  `last_update` timestamp NOT NULL DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP,
  PRIMARY KEY (`api_endpoint_id`) USING BTREE,
  INDEX `api_endpoint_id`(`api_endpoint_id`) USING BTREE
) ENGINE = InnoDB AUTO_INCREMENT = 56 CHARACTER SET = utf8 COLLATE = utf8_general_ci COMMENT = 'Each unique API endpoint (minus base URL), starting with v1, for example\r\n' ROW_FORMAT = Dynamic;

-- ----------------------------
-- Table structure for api_messages
-- ----------------------------
DROP TABLE IF EXISTS `api_messages`;
CREATE TABLE `api_messages`  (
  `msg_num_code` int NULL DEFAULT NULL COMMENT 'Code for access',
  `msg_language` char(6) CHARACTER SET utf8 COLLATE utf8_general_ci NULL DEFAULT 'EN' COMMENT 'Language of message',
  `msg_sym_code` varchar(128) CHARACTER SET utf8 COLLATE utf8_general_ci NULL DEFAULT NULL COMMENT 'Symbolic Message Code, e.g., ACCESSLIMITED_401_UNAUTHORIZED',
  `msg_text` text CHARACTER SET utf8 COLLATE utf8_general_ci NULL COMMENT 'Text of the message',
  `last_update` timestamp NOT NULL DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP COMMENT 'Record update time',
  UNIQUE INDEX `primary_combo`(`msg_language`, `msg_num_code`) USING BTREE
) ENGINE = InnoDB CHARACTER SET = utf8 COLLATE = utf8_general_ci ROW_FORMAT = Dynamic;

-- ----------------------------
-- Table structure for api_productbase
-- ----------------------------
DROP TABLE IF EXISTS `api_productbase`;
CREATE TABLE `api_productbase`  (
  `basecode` varchar(21) CHARACTER SET latin1 COLLATE latin1_swedish_ci NOT NULL DEFAULT '' COMMENT 'Shortened form of the locator',
  `articleID` varchar(24) CHARACTER SET latin1 COLLATE latin1_swedish_ci NULL DEFAULT NULL COMMENT 'PEP article ID for books only',
  `active` int NULL DEFAULT NULL COMMENT 'Currently being used in PEP-Web',
  `splitbook` int NULL DEFAULT NULL COMMENT '1 if split book',
  `pep_class` set('book','journal','videostream','special','vidostream','bookseriessub','bookserieshead') CHARACTER SET latin1 COLLATE latin1_swedish_ci NULL DEFAULT '' COMMENT '\'book\',\'journal\',\'videostream\',\'special\',\'vidostream\',\'bookseriessub\',\'bookserieshead\'',
  `pep_class_qualifier` set('glossary','works','bookseriesvolume','multivolumebook','multivolumesubbook') CHARACTER SET latin1 COLLATE latin1_swedish_ci NULL DEFAULT '' COMMENT '\'glossary\',\'works\',\'bookseriesvolume\',\'multivolumebook\',\'multivolumesubbook\'',
  `accessClassification` varchar(255) CHARACTER SET utf8 COLLATE utf8_general_ci NULL DEFAULT NULL,
  `wall` int NULL DEFAULT 3 COMMENT 'Number of years embargoed by Publisher',
  `mainTOC` varchar(21) CHARACTER SET latin1 COLLATE latin1_swedish_ci NULL DEFAULT '' COMMENT 'Locator (ArticleID) for the first instance of this (or the only instance)',
  `first_author` varchar(255) CHARACTER SET utf8 COLLATE utf8_general_ci NULL DEFAULT NULL COMMENT 'Needed for KBART, easier than the join, which did lead to some problems since it\'s only the first author here',
  `author` varchar(255) CHARACTER SET utf8 COLLATE utf8_general_ci NULL DEFAULT NULL COMMENT 'Author where applicable (e.g., Books)',
  `title` varchar(255) CHARACTER SET utf8 COLLATE utf8_general_ci NULL DEFAULT NULL COMMENT 'Title of Publication',
  `bibabbrev` varchar(255) CHARACTER SET utf8 COLLATE utf8_general_ci NULL DEFAULT NULL COMMENT 'bibliographic Abbreviation',
  `ISSN` varchar(22) CHARACTER SET latin1 COLLATE latin1_swedish_ci NULL DEFAULT NULL COMMENT 'ISSN for Journals only',
  `ISBN-10` varchar(13) CHARACTER SET latin1 COLLATE latin1_swedish_ci NULL DEFAULT NULL COMMENT 'ISBN 10 digit',
  `ISBN-13` varchar(17) CHARACTER SET latin1 COLLATE latin1_swedish_ci NULL DEFAULT NULL COMMENT 'ISBN 13 digit',
  `pages` int NULL DEFAULT NULL COMMENT 'Number of pages in book',
  `Comment` varchar(255) CHARACTER SET utf8 COLLATE utf8_general_ci NULL DEFAULT NULL COMMENT 'use for notes, and \"unused\" ISBN for books as journals',
  `pepcode` varchar(14) CHARACTER SET latin1 COLLATE latin1_swedish_ci NULL DEFAULT NULL COMMENT 'PEP Code/Abbreviation (first part of Article IDs)',
  `publisher` varchar(255) CHARACTER SET utf8 COLLATE utf8_general_ci NULL DEFAULT NULL COMMENT 'Title Publisher',
  `jrnl` tinyint(1) NULL DEFAULT 0 COMMENT '1 if this is a journal, 0 if not',
  `pub_year` int NULL DEFAULT NULL COMMENT 'Publication Year',
  `start_year` int NULL DEFAULT NULL COMMENT 'First Year of Serial Publication',
  `end_year` int NULL DEFAULT NULL COMMENT 'Last Year of Serial Publication (if applicable)',
  `pep_url` varchar(255) CHARACTER SET utf8 COLLATE utf8_general_ci NULL DEFAULT NULL COMMENT 'URL for this product on PEP-Web',
  `language` varchar(4) CHARACTER SET latin1 COLLATE latin1_swedish_ci NULL DEFAULT NULL COMMENT 'Primary Language',
  `updated` timestamp NULL DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP COMMENT 'Last date of this record update',
  `pepversion` int NULL DEFAULT NULL COMMENT 'Version it first appeared in, or planned for',
  `duplicate` varchar(10) CHARACTER SET latin1 COLLATE latin1_swedish_ci NULL DEFAULT NULL COMMENT 'Is this a duplicate (alternative) abbreviation/name (specified)',
  `landing_page` varchar(1024) CHARACTER SET utf8 COLLATE utf8_general_ci NULL DEFAULT NULL COMMENT 'Pub source URL',
  `coverage_notes` varchar(255) CHARACTER SET utf8 COLLATE utf8_unicode_ci NULL DEFAULT NULL COMMENT 'Originally planned, but deprecared',
  `google_books_link` varchar(512) CHARACTER SET latin1 COLLATE latin1_swedish_ci NULL DEFAULT NULL COMMENT 'Originally planned, but deprecared',
  `charcount_stat_name` varchar(255) CHARACTER SET latin1 COLLATE latin1_swedish_ci NULL DEFAULT NULL COMMENT 'name or group name for stat count',
  `charcount_stat_start_year` int NULL DEFAULT NULL COMMENT 'First year to use for counts',
  `charcount_stat_group_str` varchar(1024) CHARACTER SET latin1 COLLATE latin1_swedish_ci NULL DEFAULT NULL COMMENT '\'APA\',\'BAP\',\'BIP\',\'PDPSY\',\'JAA\',\'IJP\',\'IRP\',\'AIM\',\'AJP\',\'AJRPP\',\'ANIJP-DE\',\'ANIJP-TR\',\'ANIJP-FR\',\'ANIJP-IT\',\'ANRP\',\'AOP\',\'APM\',\'APS\',\'BAFC\',\'BJP\',\'CFP\',\'CJP\',\'DR\',\'FA\',\'FD\',\'GAP\',\'IFP\',\'IJAPS\',\'IJPSP\',\'IMAGO\',\'IZPA\',\'JBP\',\'JCP\',\'JCPTX\',\'JICAP\',\'JOAP\',\'JPPF\',\'LU-AM\',\'MPSA\',\'NP\',\'OPUS\',\'PAH\',\'PAQ\',\'PCS\',\'PCT\',\'PD\',\'PI\',\'PPERSP\',\'PPSY\',\'PPTX\',\'PSABEW\',\'PSAR\',\'PSP\',\'PSU\',\'PSW\',\'RBP\',\'REVAPA\',\'RIP\',\'RPP-CS\',\'RPSA\',\'RRP\',\'SGS\',\'SPR\',\'TVPA\',\'ZPSAP\',\'\'',
  `charcount_stat_group_count` int NULL DEFAULT NULL COMMENT 'Number of codes in group',
  PRIMARY KEY (`basecode`) USING BTREE,
  INDEX `basecode`(`basecode`) USING BTREE
) ENGINE = InnoDB CHARACTER SET = utf8 COLLATE = utf8_general_ci COMMENT = 'Each ISSN Product included (from the PEP ISSN Table)\r\n\r\n' ROW_FORMAT = Dynamic;

-- ----------------------------
-- Table structure for api_session_endpoints
-- ----------------------------
DROP TABLE IF EXISTS `api_session_endpoints`;
CREATE TABLE `api_session_endpoints`  (
  `session_id` varchar(60) CHARACTER SET utf8 COLLATE utf8_general_ci NOT NULL COMMENT 'session_id that accessed this endpoint',
  `api_endpoint_id` int NOT NULL COMMENT 'endpoint_id that was accessed',
  `api_method` varchar(12) CHARACTER SET utf8 COLLATE utf8_general_ci NULL DEFAULT 'get' COMMENT 'get, put, post, delete, ... Default: get',
  `params` varchar(2500) CHARACTER SET utf8 COLLATE utf8_general_ci NULL DEFAULT NULL COMMENT 'parameters added to endpoint for access',
  `item_of_interest` varchar(1024) CHARACTER SET utf8 COLLATE utf8_general_ci NULL DEFAULT NULL COMMENT 'specific item of interest, e.g., article id',
  `return_status_code` int NULL DEFAULT NULL COMMENT 'status code returned by endpoint',
  `return_added_status_message` varchar(255) CHARACTER SET utf8 COLLATE utf8_general_ci NULL DEFAULT NULL COMMENT 'additional message returned',
  `last_update` timestamp NOT NULL DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP COMMENT 'time record was added or updated',
  `id` bigint UNSIGNED NOT NULL AUTO_INCREMENT COMMENT 'auto increment id field for PaDS reports to distinguish records where the time is exactly the same',
  PRIMARY KEY (`id`) USING BTREE,
  INDEX `fk_session_id`(`session_id`) USING BTREE,
  INDEX `fk_endpoint`(`api_endpoint_id`) USING BTREE,
  CONSTRAINT `fk_endpoint` FOREIGN KEY (`api_endpoint_id`) REFERENCES `api_endpoints` (`api_endpoint_id`) ON DELETE RESTRICT ON UPDATE RESTRICT
) ENGINE = InnoDB AUTO_INCREMENT = 324205 CHARACTER SET = utf8 COLLATE = utf8_general_ci COMMENT = 'All endpoints called in a session, and parameters defining searches, retrievals etc..\r\n\r\n' ROW_FORMAT = Dynamic;

-- ----------------------------
-- Table structure for api_session_endpoints_not_logged_in
-- ----------------------------
DROP TABLE IF EXISTS `api_session_endpoints_not_logged_in`;
CREATE TABLE `api_session_endpoints_not_logged_in`  (
  `session_id` varchar(60) CHARACTER SET utf8 COLLATE utf8_general_ci NOT NULL COMMENT 'session_id that accessed this endpoint',
  `api_endpoint_id` int NOT NULL COMMENT 'endpoint_id that was accessed',
  `api_method` varchar(12) CHARACTER SET utf8 COLLATE utf8_general_ci NULL DEFAULT 'get' COMMENT 'get, put, post, delete, ... Default: get',
  `params` varchar(2500) CHARACTER SET utf8 COLLATE utf8_general_ci NULL DEFAULT NULL COMMENT 'parameters added to endpoint for access',
  `item_of_interest` varchar(1024) CHARACTER SET utf8 COLLATE utf8_general_ci NULL DEFAULT NULL COMMENT 'specific item of interest, e.g., article id',
  `return_status_code` int NULL DEFAULT NULL COMMENT 'status code returned by endpoint',
  `return_added_status_message` varchar(255) CHARACTER SET utf8 COLLATE utf8_general_ci NULL DEFAULT NULL COMMENT 'additional message returned',
  `last_update` timestamp NOT NULL DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP COMMENT 'time record was added or updated',
  `id` bigint UNSIGNED NOT NULL AUTO_INCREMENT COMMENT 'auto increment id field for PaDS reports to distinguish records where the time is exactly the same',
  PRIMARY KEY (`id`) USING BTREE,
  INDEX `fk_session_id`(`session_id`) USING BTREE,
  INDEX `fk_endpoint`(`api_endpoint_id`) USING BTREE,
  INDEX `fk_last_update`(`last_update`) USING BTREE,
  CONSTRAINT `api_session_endpoints_not_logged_in_ibfk_1` FOREIGN KEY (`api_endpoint_id`) REFERENCES `api_endpoints` (`api_endpoint_id`) ON DELETE RESTRICT ON UPDATE RESTRICT
) ENGINE = InnoDB AUTO_INCREMENT = 8088019 CHARACTER SET = utf8 COLLATE = utf8_general_ci COMMENT = 'All endpoints called in a session, and parameters defining searches, retrievals etc..\r\n\r\n' ROW_FORMAT = Dynamic;

-- ----------------------------
-- Table structure for api_sessions
-- ----------------------------
DROP TABLE IF EXISTS `api_sessions`;
CREATE TABLE `api_sessions`  (
  `session_id` varchar(60) CHARACTER SET utf8 COLLATE utf8_general_ci NOT NULL,
  `user_id` int NULL DEFAULT NULL,
  `admin` tinyint(1) NOT NULL DEFAULT 0,
  `api_client_id` int NOT NULL,
  `authenticated` tinyint(1) NULL DEFAULT 0,
  `authorized_peparchive` tinyint(1) NULL DEFAULT NULL,
  `authorized_pepcurrent` tinyint(1) NULL DEFAULT NULL,
  `confirmed_unauthenticated` tinyint(1) NULL DEFAULT NULL,
  `has_subscription` tinyint(1) NULL DEFAULT NULL,
  `is_valid_login` tinyint(1) NULL DEFAULT NULL,
  `is_valid_username` tinyint(1) NULL DEFAULT NULL,
  `username` varchar(255) CHARACTER SET ujis COLLATE ujis_japanese_ci NULL DEFAULT NULL,
  `user_type` varchar(255) CHARACTER SET utf8 COLLATE utf8_general_ci NULL DEFAULT NULL,
  `session_start` timestamp NOT NULL,
  `session_end` timestamp NULL DEFAULT NULL,
  `session_expires_time` timestamp NULL DEFAULT NULL,
  `last_update` timestamp NULL DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP,
  `api_direct_login` int NULL DEFAULT 0,
  PRIMARY KEY (`session_id`) USING BTREE,
  UNIQUE INDEX `idxSession`(`session_id`) USING BTREE,
  INDEX `session_user`(`user_id`) USING BTREE
) ENGINE = InnoDB CHARACTER SET = utf8 COLLATE = utf8_general_ci COMMENT = 'Each API session with a unique ID creates a session record. ' ROW_FORMAT = Dynamic;

-- ----------------------------
-- Table structure for article_tracker
-- ----------------------------
DROP TABLE IF EXISTS `article_tracker`;
CREATE TABLE `article_tracker`  (
  `art_id` varchar(24) CHARACTER SET latin1 COLLATE latin1_swedish_ci NOT NULL DEFAULT '' COMMENT 'The locator style ID for this article (e.g., APA.004.0109A)',
  `date_inserted` timestamp NOT NULL DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP COMMENT 'Automatic Timestamp when record changes',
  PRIMARY KEY (`art_id`) USING BTREE,
  UNIQUE INDEX `article_id`(`art_id`) USING BTREE COMMENT 'Keep track of any article we\'ve already seen'
) ENGINE = InnoDB CHARACTER SET = utf8 COLLATE = utf8_general_ci COMMENT = 'Track articles by article ID (document ID) as they are added to the table to assist in determining new articles.' ROW_FORMAT = Dynamic;

-- ----------------------------
-- Table structure for artstat
-- ----------------------------
DROP TABLE IF EXISTS `artstat`;
CREATE TABLE `artstat`  (
  `articleID` varchar(24) CHARACTER SET latin1 COLLATE latin1_swedish_ci NOT NULL DEFAULT '',
  `Citations` int NULL DEFAULT NULL,
  `References` int NULL DEFAULT NULL,
  `RefLinks` int NULL DEFAULT NULL,
  `PgxJumps` int NULL DEFAULT NULL,
  `Figures` int NULL DEFAULT NULL,
  `Poems` int NULL DEFAULT NULL,
  `Tables` int NULL DEFAULT NULL,
  `Pages` int NULL DEFAULT NULL,
  `Footnotes` int NULL DEFAULT NULL,
  `Quotes` int NULL DEFAULT NULL,
  `Dreams` int NULL DEFAULT NULL,
  `Dialogs` int NULL DEFAULT NULL,
  `Paragraphs` int NULL DEFAULT NULL,
  `Words` int NULL DEFAULT NULL,
  `Chars` int NULL DEFAULT NULL,
  `NonspaceChars` int NULL DEFAULT NULL,
  `updated` timestamp NULL DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP COMMENT 'The date the record was loaded to the database',
  `createTime` datetime NULL DEFAULT NULL COMMENT 'The date the instance was first built (processed)',
  `modTime` datetime NULL DEFAULT NULL COMMENT 'The date the instance was last built (processed)',
  `PubYear` varchar(8) CHARACTER SET latin1 COLLATE latin1_swedish_ci NULL DEFAULT NULL,
  `glossaryDict` mediumtext CHARACTER SET utf8 COLLATE utf8_general_ci NULL,
  PRIMARY KEY (`articleID`) USING BTREE,
  UNIQUE INDEX `Prmy`(`articleID`) USING BTREE
) ENGINE = MyISAM AUTO_INCREMENT = 1 CHARACTER SET = latin1 COLLATE = latin1_swedish_ci COMMENT = 'Various statistics on PEP articles, compiled via PEPStats' ROW_FORMAT = Dynamic;

-- ----------------------------
-- Table structure for opasloader_glossary_group_ids
-- ----------------------------
DROP TABLE IF EXISTS `opasloader_glossary_group_ids`;
CREATE TABLE `opasloader_glossary_group_ids`  (
  `group_id` varchar(255) CHARACTER SET latin1 COLLATE latin1_swedish_ci NOT NULL,
  `glossary_group` varchar(255) CHARACTER SET latin1 COLLATE latin1_swedish_ci NOT NULL DEFAULT '',
  `updated` timestamp NULL DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP,
  `protect` smallint NOT NULL DEFAULT 0 COMMENT 'If it\'s tuned (1), it won\'t be overwritten',
  `MarkedForDeletion` smallint NOT NULL DEFAULT 0,
  PRIMARY KEY (`group_id`) USING BTREE,
  UNIQUE INDEX `glossary_group_name`(`glossary_group`) USING BTREE
) ENGINE = MyISAM AUTO_INCREMENT = 1 CHARACTER SET = latin1 COLLATE = latin1_swedish_ci COMMENT = 'Each row is a unique group with a hash-based ID.' ROW_FORMAT = Dynamic;

-- ----------------------------
-- Table structure for opasloader_glossary_terms
-- ----------------------------
DROP TABLE IF EXISTS `opasloader_glossary_terms`;
CREATE TABLE `opasloader_glossary_terms`  (
  `group_id` varchar(255) CHARACTER SET latin1 COLLATE latin1_swedish_ci NULL DEFAULT NULL,
  `term` varchar(255) CHARACTER SET utf8 COLLATE utf8_general_ci NOT NULL DEFAULT '',
  `termcount` int NOT NULL DEFAULT 0,
  `sourceinstance` varchar(44) CHARACTER SET latin1 COLLATE latin1_swedish_ci NOT NULL DEFAULT '',
  `sourcekey` varchar(66) CHARACTER SET latin1 COLLATE latin1_swedish_ci NOT NULL COMMENT 'source instance plus count',
  `source` varchar(44) CHARACTER SET latin1 COLLATE latin1_swedish_ci NOT NULL DEFAULT '' COMMENT 'PEP Source  e.g., ZBK063',
  `regex` varchar(1024) CHARACTER SET utf8 COLLATE utf8_general_ci NULL DEFAULT NULL,
  `regex_tuned` smallint NULL DEFAULT NULL COMMENT 'If it\'s tuned (1), it won\'t be overwritten',
  `regex_ignore` smallint NULL DEFAULT NULL,
  `see` varchar(128) CHARACTER SET latin1 COLLATE latin1_swedish_ci NULL DEFAULT NULL COMMENT 'If filled in, this is the term that has the definition.  This is not the same as See ALSO.  ',
  `xmlsource` longtext CHARACTER SET latin1 COLLATE latin1_swedish_ci NULL,
  `updated` timestamp NULL DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP,
  PRIMARY KEY (`term`, `sourcekey`) USING BTREE,
  INDEX `groupid`(`group_id`) USING BTREE,
  INDEX `term`(`term`) USING BTREE
) ENGINE = MyISAM AUTO_INCREMENT = 1 CHARACTER SET = latin1 COLLATE = latin1_swedish_ci COMMENT = 'Each row is a term found in one of the glossaries.' ROW_FORMAT = Dynamic;

-- ----------------------------
-- Table structure for opasloader_gwpageconcordance
-- ----------------------------
DROP TABLE IF EXISTS `opasloader_gwpageconcordance`;
CREATE TABLE `opasloader_gwpageconcordance`  (
  `SrcName` varchar(20) CHARACTER SET latin1 COLLATE latin1_swedish_ci NOT NULL DEFAULT 'SE' COMMENT 'The first edition of PEP\'s SE',
  `SrcEditionInfo` varchar(20) CHARACTER SET latin1 COLLATE latin1_swedish_ci NOT NULL DEFAULT 'Strachey',
  `SrcVol` int NULL DEFAULT NULL,
  `SrcPgNum` int NULL DEFAULT NULL,
  `GWVol` varchar(11) CHARACTER SET latin1 COLLATE latin1_swedish_ci NULL DEFAULT NULL,
  `GWFirstPgNum` int NULL DEFAULT NULL,
  `GWLastPgNum` int NULL DEFAULT NULL,
  `PublicationYear` varchar(40) CHARACTER SET latin1 COLLATE latin1_swedish_ci NULL DEFAULT NULL COMMENT 'This was part of the Nachtr. concordance only',
  `Comments` varchar(80) CHARACTER SET latin1 COLLATE latin1_swedish_ci NULL DEFAULT '' COMMENT 'Watch for special notes here',
  `updated` timestamp NULL DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP
) ENGINE = MyISAM AUTO_INCREMENT = 1 CHARACTER SET = latin1 COLLATE = latin1_swedish_ci COMMENT = 'Page to page mapping, GW and SE' ROW_FORMAT = Dynamic;

-- ----------------------------
-- Table structure for opasloader_gwseparaconcordance
-- ----------------------------
DROP TABLE IF EXISTS `opasloader_gwseparaconcordance`;
CREATE TABLE `opasloader_gwseparaconcordance`  (
  `GWArticleID` varchar(255) CHARACTER SET latin1 COLLATE latin1_swedish_ci NULL DEFAULT NULL,
  `GWID` varchar(255) CHARACTER SET latin1 COLLATE latin1_swedish_ci NULL DEFAULT NULL,
  `SEArticleID` varchar(255) CHARACTER SET latin1 COLLATE latin1_swedish_ci NULL DEFAULT NULL,
  `SEID` varchar(255) CHARACTER SET latin1 COLLATE latin1_swedish_ci NULL DEFAULT NULL,
  `Comments` varchar(255) CHARACTER SET latin1 COLLATE latin1_swedish_ci NULL DEFAULT NULL,
  `updated` datetime NULL DEFAULT NULL
) ENGINE = MyISAM AUTO_INCREMENT = 1 CHARACTER SET = latin1 COLLATE = latin1_swedish_ci COMMENT = 'Holds the corresponding IDs for SE and GW paragraphs' ROW_FORMAT = Dynamic;

-- ----------------------------
-- Table structure for opasloader_gwtitleconcordance
-- ----------------------------
DROP TABLE IF EXISTS `opasloader_gwtitleconcordance`;
CREATE TABLE `opasloader_gwtitleconcordance`  (
  `ConcordanceKey` varchar(13) CHARACTER SET latin1 COLLATE latin1_swedish_ci NOT NULL DEFAULT '',
  `PubYear` double NOT NULL DEFAULT 0,
  `SETitle` varchar(122) CHARACTER SET latin1 COLLATE latin1_swedish_ci NULL DEFAULT NULL,
  `SELocator` varchar(24) CHARACTER SET latin1 COLLATE latin1_swedish_ci NOT NULL DEFAULT '',
  `GWTitle` varchar(124) CHARACTER SET latin1 COLLATE latin1_swedish_ci NULL DEFAULT NULL,
  `GWLocator` varchar(24) CHARACTER SET latin1 COLLATE latin1_swedish_ci NOT NULL DEFAULT '',
  `updated` timestamp NULL DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP,
  PRIMARY KEY (`PubYear`, `SELocator`, `GWLocator`) USING BTREE
) ENGINE = MyISAM AUTO_INCREMENT = 1 CHARACTER SET = latin1 COLLATE = latin1_swedish_ci COMMENT = 'Title mapping btw GW and SE \r\nAccessed by PEPArticleRelations.py' ROW_FORMAT = Dynamic;

-- ----------------------------
-- Table structure for opasloader_splitbookpages
-- ----------------------------
DROP TABLE IF EXISTS `opasloader_splitbookpages`;
CREATE TABLE `opasloader_splitbookpages`  (
  `articleIDbase` varchar(10) CHARACTER SET latin1 COLLATE latin1_swedish_ci NOT NULL DEFAULT '',
  `articleID` varchar(24) CHARACTER SET latin1 COLLATE latin1_swedish_ci NOT NULL DEFAULT '',
  `pagenumber` varchar(64) CHARACTER SET latin1 COLLATE latin1_swedish_ci NOT NULL DEFAULT '',
  `bibliopage` tinyint(1) NULL DEFAULT 0,
  `tocpage` tinyint(1) NULL DEFAULT 0,
  `filename` varchar(255) CHARACTER SET latin1 COLLATE latin1_swedish_ci NULL DEFAULT NULL,
  `last_update` timestamp NOT NULL DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP COMMENT 'Automatic Timestamp when record changes',
  PRIMARY KEY (`articleID`, `pagenumber`) USING BTREE,
  INDEX `articlebase`(`articleIDbase`) USING BTREE
) ENGINE = MyISAM AUTO_INCREMENT = 1 CHARACTER SET = utf8 COLLATE = utf8_general_ci COMMENT = 'Map of pages to instances for all split books' ROW_FORMAT = Dynamic;

-- ----------------------------
-- Table structure for opasloader_splitbookpages_static
-- ----------------------------
DROP TABLE IF EXISTS `opasloader_splitbookpages_static`;
CREATE TABLE `opasloader_splitbookpages_static`  (
  `articleIDbase` varchar(10) CHARACTER SET latin1 COLLATE latin1_swedish_ci NOT NULL DEFAULT '',
  `articleID` varchar(24) CHARACTER SET latin1 COLLATE latin1_swedish_ci NOT NULL DEFAULT '',
  `pagenumber` varchar(64) CHARACTER SET latin1 COLLATE latin1_swedish_ci NOT NULL DEFAULT '',
  `bibliopage` tinyint(1) NULL DEFAULT 0,
  `tocpage` tinyint(1) NULL DEFAULT 0,
  `filename` varchar(255) CHARACTER SET latin1 COLLATE latin1_swedish_ci NULL DEFAULT NULL,
  PRIMARY KEY (`articleID`, `pagenumber`) USING BTREE,
  INDEX `articlebase`(`articleIDbase`) USING BTREE
) ENGINE = MyISAM AUTO_INCREMENT = 1 CHARACTER SET = latin1 COLLATE = latin1_swedish_ci COMMENT = 'Map of pages to instances for all split books' ROW_FORMAT = Dynamic;

SET FOREIGN_KEY_CHECKS = 1;
