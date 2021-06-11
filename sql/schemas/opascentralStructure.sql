/*
 Navicat MySQL Data Transfer

 Source Server         : AWS-RDS-Prod-Production
 Source Server Type    : MySQL
 Source Server Version : 80017
 Source Host           : production.c6re6qczl2ae.us-east-1.rds.amazonaws.com:3306
 Source Schema         : opascentral

 Target Server Type    : MySQL
 Target Server Version : 80017
 File Encoding         : 65001

 Date: 11/06/2021 17:16:53
*/

SET NAMES utf8mb4;
SET FOREIGN_KEY_CHECKS = 0;

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
  `art_year` int(11) NULL DEFAULT NULL COMMENT 'Year of Publication (single year only, reduced from range if there is one)',
  `art_year_str` varchar(20) CHARACTER SET utf8 COLLATE utf8_general_ci NULL DEFAULT NULL COMMENT 'Year of publicaton as in xml',
  `art_vol` int(11) NULL DEFAULT NULL COMMENT 'Volume number for serial Publications',
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
  `ref_count` int(11) NULL DEFAULT NULL COMMENT 'Number of references in biblio of article',
  `filename` varchar(255) CHARACTER SET latin1 COLLATE latin1_swedish_ci NULL DEFAULT NULL COMMENT 'Filename (only) of source file',
  `filedatetime` char(25) CHARACTER SET latin1 COLLATE latin1_swedish_ci NULL DEFAULT NULL COMMENT 'Modification datetime of Article file used to detect updates needed',
  `preserve` int(11) NULL DEFAULT 0 COMMENT 'Keep this record (probably not to be used)',
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
-- Table structure for api_articles_bak
-- ----------------------------
DROP TABLE IF EXISTS `api_articles_bak`;
CREATE TABLE `api_articles_bak`  (
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
  `art_year` int(11) NULL DEFAULT NULL COMMENT 'Year of Publication (single year only, reduced from range if there is one)',
  `art_year_str` varchar(20) CHARACTER SET utf8 COLLATE utf8_general_ci NULL DEFAULT NULL COMMENT 'Year of publicaton as in xml',
  `art_vol` int(11) NULL DEFAULT NULL COMMENT 'Volume number for serial Publications',
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
  `ref_count` int(11) NULL DEFAULT NULL COMMENT 'Number of references in biblio of article',
  `filename` varchar(255) CHARACTER SET latin1 COLLATE latin1_swedish_ci NULL DEFAULT NULL COMMENT 'Filename (only) of source file',
  `filedatetime` char(25) CHARACTER SET latin1 COLLATE latin1_swedish_ci NULL DEFAULT NULL COMMENT 'Modification datetime of Article file used to detect updates needed',
  `preserve` int(11) NULL DEFAULT 0 COMMENT 'Keep this record (probably not to be used)',
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
-- Table structure for api_biblioxml
-- ----------------------------
DROP TABLE IF EXISTS `api_biblioxml`;
CREATE TABLE `api_biblioxml`  (
  `art_id` varchar(24) CHARACTER SET latin1 COLLATE latin1_swedish_ci NOT NULL,
  `bib_local_id` varchar(25) CHARACTER SET latin1 COLLATE latin1_swedish_ci NOT NULL,
  `art_year` int(11) NULL DEFAULT NULL,
  `bib_rx` varchar(30) CHARACTER SET latin1 COLLATE latin1_swedish_ci NULL DEFAULT NULL COMMENT 'This article references...',
  `bib_rxcf` varchar(30) CHARACTER SET utf8 COLLATE utf8_general_ci NULL DEFAULT '0' COMMENT 'This article may be related to...',
  `bib_sourcecode` varchar(24) CHARACTER SET utf8 COLLATE utf8_general_ci NULL DEFAULT 'instance' COMMENT 'If its refcorrections, this record came from the refcorrections table and should not be updated.',
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
  `bib_year_int` int(255) NULL DEFAULT NULL,
  `bib_volume` varchar(24) CHARACTER SET utf8 COLLATE utf8_general_ci NULL DEFAULT NULL,
  `bib_publisher` varchar(255) CHARACTER SET utf8 COLLATE utf8_general_ci NULL DEFAULT NULL,
  `last_update` timestamp NOT NULL DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP,
  PRIMARY KEY (`art_id`, `bib_local_id`) USING BTREE,
  UNIQUE INDEX `Primary Key`(`art_id`, `bib_local_id`) USING BTREE,
  INDEX `articleID`(`art_id`) USING BTREE,
  INDEX `titleIndex`(`title`) USING BTREE,
  INDEX `RefersTo`(`bib_rx`) USING BTREE,
  FULLTEXT INDEX `fulreffullText`(`full_ref_text`),
  FULLTEXT INDEX `titleFullText`(`title`)
) ENGINE = InnoDB CHARACTER SET = utf8 COLLATE = utf8_general_ci COMMENT = 'All bibliographic entries within PEP' ROW_FORMAT = Dynamic;

-- ----------------------------
-- Table structure for api_biblioxml_bak
-- ----------------------------
DROP TABLE IF EXISTS `api_biblioxml_bak`;
CREATE TABLE `api_biblioxml_bak`  (
  `art_id` varchar(24) CHARACTER SET latin1 COLLATE latin1_swedish_ci NOT NULL,
  `bib_local_id` varchar(25) CHARACTER SET latin1 COLLATE latin1_swedish_ci NOT NULL,
  `art_year` int(11) NULL DEFAULT NULL,
  `bib_rx` varchar(30) CHARACTER SET latin1 COLLATE latin1_swedish_ci NULL DEFAULT NULL COMMENT 'This article references...',
  `bib_rxcf` varchar(30) CHARACTER SET utf8 COLLATE utf8_general_ci NULL DEFAULT '0' COMMENT 'This article may be related to...',
  `bib_sourcecode` varchar(24) CHARACTER SET utf8 COLLATE utf8_general_ci NULL DEFAULT 'instance' COMMENT 'If its refcorrections, this record came from the refcorrections table and should not be updated.',
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
  `bib_year_int` int(255) NULL DEFAULT NULL,
  `bib_volume` varchar(24) CHARACTER SET utf8 COLLATE utf8_general_ci NULL DEFAULT NULL,
  `bib_publisher` varchar(255) CHARACTER SET utf8 COLLATE utf8_general_ci NULL DEFAULT NULL,
  `last_update` timestamp NOT NULL DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP,
  PRIMARY KEY (`art_id`, `bib_local_id`) USING BTREE,
  UNIQUE INDEX `Primary Key`(`art_id`, `bib_local_id`) USING BTREE,
  INDEX `articleID`(`art_id`) USING BTREE,
  INDEX `titleIndex`(`title`) USING BTREE,
  INDEX `RefersTo`(`bib_rx`) USING BTREE,
  FULLTEXT INDEX `fulreffullText`(`full_ref_text`),
  FULLTEXT INDEX `titleFullText`(`title`)
) ENGINE = InnoDB CHARACTER SET = utf8 COLLATE = utf8_general_ci COMMENT = 'All bibliographic entries within PEP' ROW_FORMAT = Dynamic;

-- ----------------------------
-- Table structure for api_client_apps
-- ----------------------------
DROP TABLE IF EXISTS `api_client_apps`;
CREATE TABLE `api_client_apps`  (
  `api_client_id` int(11) NOT NULL COMMENT 'Assigned ID for client app',
  `api_client_name` varchar(100) CHARACTER SET utf8 COLLATE utf8_general_ci NOT NULL COMMENT 'Identifying name for client',
  `api_client_key` varchar(255) CHARACTER SET utf8 COLLATE utf8_general_ci NULL DEFAULT NULL COMMENT 'Key for client to access API',
  `last_update` timestamp NOT NULL DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP COMMENT 'Last update of this record',
  PRIMARY KEY (`api_client_id`) USING BTREE,
  UNIQUE INDEX `idxClientname`(`api_client_name`) USING BTREE
) ENGINE = InnoDB CHARACTER SET = utf8 COLLATE = utf8_general_ci COMMENT = 'Keep track of keys assigned to clients, but not used in v1 or v2 API as of 20191110' ROW_FORMAT = Dynamic;

-- ----------------------------
-- Table structure for api_client_configs
-- ----------------------------
DROP TABLE IF EXISTS `api_client_configs`;
CREATE TABLE `api_client_configs`  (
  `config_id` int(11) NOT NULL AUTO_INCREMENT COMMENT 'assigned config id for this record',
  `client_id` int(11) NULL DEFAULT NULL COMMENT 'client id for this record',
  `session_id` varchar(60) CHARACTER SET utf8 COLLATE utf8_general_ci NOT NULL COMMENT 'session id that created this record',
  `config_name` varchar(255) CHARACTER SET utf8mb4 COLLATE utf8mb4_0900_ai_ci NOT NULL COMMENT 'client known name for the use of this configuration.  May be language related, e.g., en-en, de-de',
  `config_settings` longtext CHARACTER SET utf8mb4 COLLATE utf8mb4_0900_ai_ci NULL COMMENT 'client specific settings (typically JSON)',
  `last_update` datetime NULL DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP,
  PRIMARY KEY (`config_id`, `session_id`) USING BTREE,
  UNIQUE INDEX `clientset`(`client_id`, `config_name`) USING BTREE
) ENGINE = InnoDB AUTO_INCREMENT = 451 CHARACTER SET = utf8mb4 COLLATE = utf8mb4_0900_ai_ci COMMENT = 'Client specific configuration information' ROW_FORMAT = Dynamic;

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
  INDEX `user_id`(`user_id`) USING BTREE,
  INDEX `session_id`(`session_id`) USING BTREE,
  CONSTRAINT `api_docviews_ibfk_1` FOREIGN KEY (`session_id`) REFERENCES `api_sessions` (`session_id`) ON DELETE CASCADE ON UPDATE CASCADE
) ENGINE = InnoDB CHARACTER SET = utf8 COLLATE = utf8_general_ci COMMENT = 'Track the number of times a document is viewed as an abstract, full-text, PDF, or EPUB.  Somewhat redundate to api_session_endpoints table, but with less extraneous data..' ROW_FORMAT = Dynamic;

-- ----------------------------
-- Table structure for api_endpoints
-- ----------------------------
DROP TABLE IF EXISTS `api_endpoints`;
CREATE TABLE `api_endpoints`  (
  `api_endpoint_id` int(11) NOT NULL AUTO_INCREMENT COMMENT 'assigned id number for this endpoint',
  `endpoint_url` varchar(200) CHARACTER SET utf8 COLLATE utf8_general_ci NOT NULL COMMENT 'url declared for this endpoint',
  `last_update` timestamp NOT NULL DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP,
  PRIMARY KEY (`api_endpoint_id`) USING BTREE,
  INDEX `api_endpoint_id`(`api_endpoint_id`) USING BTREE
) ENGINE = InnoDB AUTO_INCREMENT = 53 CHARACTER SET = utf8 COLLATE = utf8_general_ci COMMENT = 'Each unique API endpoint (minus base URL), starting with v1, for example\r\n' ROW_FORMAT = Dynamic;

-- ----------------------------
-- Table structure for api_productbase
-- ----------------------------
DROP TABLE IF EXISTS `api_productbase`;
CREATE TABLE `api_productbase`  (
  `basecode` varchar(21) CHARACTER SET utf8 COLLATE utf8_general_ci NOT NULL DEFAULT '' COMMENT 'Shortened form of the locator',
  `articleID` varchar(24) CHARACTER SET latin1 COLLATE latin1_swedish_ci NULL DEFAULT NULL COMMENT 'PEP article ID for books only',
  `active` int(1) NULL DEFAULT NULL COMMENT 'Currently being used in PEP-Web',
  `pep_class` set('book','journal','videostream','special','vidostream','bookseriessub','bookserieshead') CHARACTER SET latin1 COLLATE latin1_swedish_ci NULL DEFAULT '' COMMENT '\'book\',\'journal\',\'videostream\',\'special\',\'vidostream\',\'bookseriessub\',\'bookserieshead\'',
  `pep_class_qualifier` set('glossary','works','bookseriesvolume','multivolumebook','multivolumesubbook') CHARACTER SET latin1 COLLATE latin1_swedish_ci NULL DEFAULT '' COMMENT '\'glossary\',\'works\',\'bookseriesvolume\',\'multivolumebook\',\'multivolumesubbook\'',
  `wall` int(1) NULL DEFAULT 3 COMMENT 'Number of years embargoed by Publisher',
  `mainTOC` varchar(21) CHARACTER SET latin1 COLLATE latin1_swedish_ci NULL DEFAULT '' COMMENT 'Locator (ArticleID) for the first instance of this (or the only instance)',
  `first_author` varchar(255) CHARACTER SET utf8 COLLATE utf8_general_ci NULL DEFAULT NULL COMMENT 'Needed for KBART, easier than the join, which did lead to some problems since its only the first author here',
  `author` varchar(255) CHARACTER SET utf8 COLLATE utf8_general_ci NULL DEFAULT NULL COMMENT 'Author where applicable (e.g., Books)',
  `title` varchar(255) CHARACTER SET utf8 COLLATE utf8_general_ci NULL DEFAULT NULL COMMENT 'Title of Publication',
  `bibabbrev` varchar(255) CHARACTER SET utf8 COLLATE utf8_general_ci NULL DEFAULT NULL COMMENT 'bibliographic Abbreviation',
  `ISSN` varchar(22) CHARACTER SET latin1 COLLATE latin1_swedish_ci NULL DEFAULT NULL COMMENT 'ISSN for Journals only',
  `ISBN-10` varchar(13) CHARACTER SET latin1 COLLATE latin1_swedish_ci NULL DEFAULT NULL COMMENT 'ISBN 10 digit',
  `ISBN-13` varchar(17) CHARACTER SET latin1 COLLATE latin1_swedish_ci NULL DEFAULT NULL COMMENT 'ISBN 13 digit',
  `pages` int(4) NULL DEFAULT NULL COMMENT 'Number of pages in book',
  `Comment` varchar(255) CHARACTER SET utf8 COLLATE utf8_general_ci NULL DEFAULT NULL COMMENT 'use for notes, and \"unused\" ISBN for books as journals',
  `pepcode` varchar(14) CHARACTER SET latin1 COLLATE latin1_swedish_ci NULL DEFAULT NULL COMMENT 'PEP Code/Abbreviation (first part of Article IDs)',
  `publisher` varchar(255) CHARACTER SET utf8 COLLATE utf8_general_ci NULL DEFAULT NULL COMMENT 'Title Publisher',
  `jrnl` tinyint(1) NULL DEFAULT 0 COMMENT '1 if this is a journal, 0 if not',
  `pub_year` int(1) NULL DEFAULT NULL COMMENT 'Publication Year',
  `start_year` int(4) NULL DEFAULT NULL COMMENT 'First Year of Serial Publication',
  `end_year` int(4) NULL DEFAULT NULL COMMENT 'Last Year of Serial Publication (if applicable)',
  `pep_url` varchar(255) CHARACTER SET utf8 COLLATE utf8_general_ci NULL DEFAULT NULL COMMENT 'URL for this product on PEP-Web',
  `language` varchar(4) CHARACTER SET latin1 COLLATE latin1_swedish_ci NULL DEFAULT NULL COMMENT 'Primary Language',
  `updated` timestamp NULL DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP COMMENT 'Last date of this record update',
  `pepversion` int(1) NULL DEFAULT NULL COMMENT 'Version it first appeared in, or planned for',
  `duplicate` varchar(10) CHARACTER SET latin1 COLLATE latin1_swedish_ci NULL DEFAULT NULL COMMENT 'Is this a duplicate (alternative) abbreviation/name (specified)',
  `landing_page` varchar(1024) CHARACTER SET utf8 COLLATE utf8_general_ci NULL DEFAULT NULL COMMENT 'Originally planned, but deprecared',
  `coverage_notes` varchar(255) CHARACTER SET utf8 COLLATE utf8_unicode_ci NULL DEFAULT NULL COMMENT 'Originally planned, but deprecared',
  `landing_page_intro_html` text CHARACTER SET utf8 COLLATE utf8_general_ci NULL COMMENT 'Originally planned, but deprecared',
  `landing_page_end_html` text CHARACTER SET utf8 COLLATE utf8_general_ci NULL COMMENT 'Originally planned, but deprecared',
  `google_books_link` varchar(512) CHARACTER SET latin1 COLLATE latin1_swedish_ci NULL DEFAULT NULL COMMENT 'Originally planned, but deprecared',
  PRIMARY KEY (`basecode`) USING BTREE,
  INDEX `basecode`(`basecode`) USING BTREE
) ENGINE = InnoDB CHARACTER SET = utf8 COLLATE = utf8_general_ci COMMENT = 'Each ISSN Product included (from the PEP ISSN Table)\r\n\r\n' ROW_FORMAT = Dynamic;

-- ----------------------------
-- Table structure for api_session_endpoints
-- ----------------------------
DROP TABLE IF EXISTS `api_session_endpoints`;
CREATE TABLE `api_session_endpoints`  (
  `session_id` varchar(60) CHARACTER SET utf8 COLLATE utf8_general_ci NOT NULL COMMENT 'session_id that accessed this endpoint',
  `api_endpoint_id` int(11) NOT NULL COMMENT 'endpoint_id that was accessed',
  `api_method` varchar(12) CHARACTER SET utf8 COLLATE utf8_general_ci NULL DEFAULT 'get' COMMENT 'get, put, post, delete, ... Default: get',
  `params` varchar(2500) CHARACTER SET utf8 COLLATE utf8_general_ci NULL DEFAULT NULL COMMENT 'parameters added to endpoint for access',
  `item_of_interest` varchar(1024) CHARACTER SET utf8 COLLATE utf8_general_ci NULL DEFAULT NULL COMMENT 'specific item of interest, e.g., article id',
  `return_status_code` int(11) NULL DEFAULT NULL COMMENT 'status code returned by endpoint',
  `return_added_status_message` varchar(255) CHARACTER SET utf8 COLLATE utf8_general_ci NULL DEFAULT NULL COMMENT 'additional message returned',
  `last_update` timestamp NOT NULL DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP,
  `id` int(255) NOT NULL AUTO_INCREMENT,
  PRIMARY KEY (`id`) USING BTREE,
  INDEX `fk_session_id`(`session_id`) USING BTREE,
  INDEX `fk_endpoint`(`api_endpoint_id`) USING BTREE,
  CONSTRAINT `fk_endpoint` FOREIGN KEY (`api_endpoint_id`) REFERENCES `api_endpoints` (`api_endpoint_id`) ON DELETE RESTRICT ON UPDATE RESTRICT
) ENGINE = InnoDB AUTO_INCREMENT = 274514 CHARACTER SET = utf8 COLLATE = utf8_general_ci COMMENT = 'All endpoints called in a session, and parameters defining searches, retrievals etc..\r\n\r\n' ROW_FORMAT = Dynamic;

-- ----------------------------
-- Table structure for api_sessions
-- ----------------------------
DROP TABLE IF EXISTS `api_sessions`;
CREATE TABLE `api_sessions`  (
  `session_id` varchar(60) CHARACTER SET utf8 COLLATE utf8_general_ci NOT NULL COMMENT 'assigned session id',
  `user_id` int(11) NULL DEFAULT NULL COMMENT 'user id attached to this session',
  `admin` tinyint(1) NOT NULL DEFAULT 0 COMMENT 'user data from PaDS - is this user an admin',
  `api_client_id` int(11) NOT NULL COMMENT 'api client attached to this session',
  `authenticated` tinyint(1) NULL DEFAULT 0 COMMENT 'user data from PaDS - is user authenticated',
  `authorized_peparchive` tinyint(1) NULL DEFAULT 0 COMMENT 'user data from PaDS - does user have access to peparchive',
  `authorized_pepcurrent` tinyint(1) NULL DEFAULT 0 COMMENT 'user data from PaDS - does user have access to pepcurrent',
  `confirmed_unauthenticated` tinyint(1) NULL DEFAULT 0,
  `has_subscription` tinyint(1) NULL DEFAULT 0 COMMENT 'user data from PaDS - does user have any subscription',
  `is_valid_login` tinyint(1) NULL DEFAULT 0 COMMENT 'user data from PaDS - is user logged in',
  `is_valid_username` tinyint(1) NULL DEFAULT 0 COMMENT 'user data from PaDS - is this a valid user name',
  `username` varchar(255) CHARACTER SET utf8 COLLATE utf8_general_ci NULL DEFAULT 'NotLoggedIn' COMMENT 'user data from PaDS - what is the users username',
  `user_type` varchar(255) CHARACTER SET utf8 COLLATE utf8_general_ci NULL DEFAULT 'Individual' COMMENT 'user data from PaDS - what type of user is this',
  `session_start` timestamp NOT NULL COMMENT 'user data from PaDS - what time did this session start',
  `session_end` timestamp NULL DEFAULT NULL COMMENT 'user data from PaDS - what time did this session end',
  `session_expires_time` timestamp NULL DEFAULT NULL COMMENT 'user data from PaDS - what time does this session expire',
  `last_update` timestamp NULL DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP,
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
  UNIQUE INDEX `article_id`(`art_id`) USING BTREE COMMENT 'Keep track of any article weve already seen'
) ENGINE = InnoDB CHARACTER SET = utf8mb4 COLLATE = utf8mb4_0900_ai_ci COMMENT = 'Track articles by article ID (document ID) as they are added to the table to assist in determining new articles.' ROW_FORMAT = Dynamic;

-- ----------------------------
-- Table structure for article_tracker_bak
-- ----------------------------
DROP TABLE IF EXISTS `article_tracker_bak`;
CREATE TABLE `article_tracker_bak`  (
  `art_id` varchar(24) CHARACTER SET latin1 COLLATE latin1_swedish_ci NOT NULL DEFAULT '' COMMENT 'The locator style ID for this article (e.g., APA.004.0109A)',
  `date_inserted` timestamp NOT NULL DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP COMMENT 'Automatic Timestamp when record changes',
  PRIMARY KEY (`art_id`) USING BTREE,
  UNIQUE INDEX `article_id`(`art_id`) USING BTREE COMMENT 'Keep track of any article weve already seen'
) ENGINE = InnoDB CHARACTER SET = utf8mb4 COLLATE = utf8mb4_0900_ai_ci ROW_FORMAT = Dynamic;

-- ----------------------------
-- View structure for vw_active_sessions
-- ----------------------------
DROP VIEW IF EXISTS `vw_active_sessions`;
CREATE ALGORITHM = UNDEFINED SQL SECURITY DEFINER VIEW `vw_active_sessions` AS select `api_sessions`.`session_id` AS `session_id`,`api_sessions`.`user_id` AS `user_id`,`api_sessions`.`username` AS `username`,`api_sessions`.`session_start` AS `session_start`,`api_sessions`.`session_end` AS `session_end`,`api_sessions`.`session_expires_time` AS `session_expires_time`,`api_sessions`.`authenticated` AS `authenticated`,`api_sessions`.`api_client_id` AS `api_client_id`,`api_sessions`.`last_update` AS `last_update` from `api_sessions` where ((`api_sessions`.`user_id` <> 0) and (`api_sessions`.`session_end` is null)) order by `api_sessions`.`session_start` desc;

-- ----------------------------
-- View structure for vw_api_absviews_from_endpoint_log
-- ----------------------------
DROP VIEW IF EXISTS `vw_api_absviews_from_endpoint_log`;
CREATE ALGORITHM = UNDEFINED SQL SECURITY DEFINER VIEW `vw_api_absviews_from_endpoint_log` AS select `api_sessions`.`user_id` AS `user_id`,`api_session_endpoints`.`session_id` AS `session_id`,`api_session_endpoints`.`item_of_interest` AS `document_id`,'Abstract' AS `type`,`api_session_endpoints`.`last_update` AS `datetimechar`,`api_session_endpoints`.`last_update` AS `last_update` from (`api_session_endpoints` join `api_sessions` on((`api_session_endpoints`.`session_id` = `api_sessions`.`session_id`))) where ((`api_session_endpoints`.`return_added_status_message` like '%(Abstract Only)%') or (`api_session_endpoints`.`api_endpoint_id` = 30));

-- ----------------------------
-- View structure for vw_api_productbase
-- ----------------------------
DROP VIEW IF EXISTS `vw_api_productbase`;
CREATE ALGORITHM = UNDEFINED SQL SECURITY DEFINER VIEW `vw_api_productbase` AS select `api_productbase`.`basecode` AS `basecode`,`api_productbase`.`articleID` AS `articleID`,`api_productbase`.`active` AS `active`,`api_productbase`.`pep_class` AS `product_type`,`api_productbase`.`pep_class_qualifier` AS `product_type_qualifier`,`api_productbase`.`wall` AS `embargo`,`api_productbase`.`mainTOC` AS `mainTOC`,`api_productbase`.`first_author` AS `first_author`,`api_productbase`.`author` AS `author`,`api_productbase`.`title` AS `title`,`api_productbase`.`bibabbrev` AS `bibabbrev`,`api_productbase`.`ISSN` AS `ISSN`,`api_productbase`.`ISBN-10` AS `ISBN-10`,`api_productbase`.`ISBN-13` AS `ISBN-13`,`api_productbase`.`pages` AS `pages`,`api_productbase`.`Comment` AS `Comment`,`api_productbase`.`pepcode` AS `pepcode`,`api_productbase`.`publisher` AS `publisher`,`api_productbase`.`jrnl` AS `jrnl`,`api_productbase`.`pub_year` AS `pub_year`,`api_productbase`.`start_year` AS `start_year`,`api_productbase`.`end_year` AS `end_year`,`api_productbase`.`pep_url` AS `pep_url`,`api_productbase`.`language` AS `language`,`api_productbase`.`updated` AS `updated`,`api_productbase`.`pepversion` AS `pepversion`,`api_productbase`.`duplicate` AS `duplicate`,`api_productbase`.`landing_page` AS `landing_page`,`api_productbase`.`coverage_notes` AS `coverage_notes`,`api_productbase`.`landing_page_intro_html` AS `landing_page_intro_html`,`api_productbase`.`landing_page_end_html` AS `landing_page_end_html`,`api_productbase`.`google_books_link` AS `google_books_link` from `api_productbase`;

-- ----------------------------
-- View structure for vw_api_productbase_instance_counts
-- ----------------------------
DROP VIEW IF EXISTS `vw_api_productbase_instance_counts`;
CREATE ALGORITHM = UNDEFINED SQL SECURITY DEFINER VIEW `vw_api_productbase_instance_counts` AS select `api_productbase`.`basecode` AS `basecode`,`api_productbase`.`articleID` AS `articleID`,`api_productbase`.`active` AS `active`,`vw_instance_counts_books`.`instances` AS `instances`,`api_productbase`.`pep_class` AS `product_type`,`api_productbase`.`pep_class_qualifier` AS `product_type_qualifier`,`api_productbase`.`wall` AS `embargo`,`api_productbase`.`mainTOC` AS `mainTOC`,`api_productbase`.`first_author` AS `first_author`,`api_productbase`.`author` AS `author`,`api_productbase`.`title` AS `title`,`api_productbase`.`bibabbrev` AS `bibabbrev`,`api_productbase`.`ISSN` AS `ISSN`,`api_productbase`.`ISBN-10` AS `ISBN-10`,`api_productbase`.`ISBN-13` AS `ISBN-13`,`api_productbase`.`pages` AS `pages`,`api_productbase`.`Comment` AS `Comment`,`api_productbase`.`pepcode` AS `pepcode`,`api_productbase`.`publisher` AS `publisher`,`api_productbase`.`jrnl` AS `jrnl`,`api_productbase`.`pub_year` AS `pub_year`,`api_productbase`.`start_year` AS `start_year`,`api_productbase`.`end_year` AS `end_year`,`api_productbase`.`pep_url` AS `pep_url`,`api_productbase`.`language` AS `language`,`api_productbase`.`updated` AS `updated`,`api_productbase`.`pepversion` AS `pepversion`,`api_productbase`.`duplicate` AS `duplicate`,`api_productbase`.`landing_page` AS `landing_page`,`api_productbase`.`coverage_notes` AS `coverage_notes`,`api_productbase`.`landing_page_intro_html` AS `landing_page_intro_html`,`api_productbase`.`landing_page_end_html` AS `landing_page_end_html`,`api_productbase`.`google_books_link` AS `google_books_link` from (`api_productbase` join `vw_instance_counts_books`) where (`api_productbase`.`basecode` = convert(`vw_instance_counts_books`.`basecode` using utf8)) union select `api_productbase`.`basecode` AS `basecode`,`api_productbase`.`articleID` AS `articleID`,`api_productbase`.`active` AS `active`,`vw_instance_counts_src`.`instances` AS `instances`,`api_productbase`.`pep_class` AS `product_type`,`api_productbase`.`pep_class_qualifier` AS `product_type_qualifier`,`api_productbase`.`wall` AS `embargo`,`api_productbase`.`mainTOC` AS `mainTOC`,`api_productbase`.`first_author` AS `first_author`,`api_productbase`.`author` AS `author`,`api_productbase`.`title` AS `title`,`api_productbase`.`bibabbrev` AS `bibabbrev`,`api_productbase`.`ISSN` AS `ISSN`,`api_productbase`.`ISBN-10` AS `ISBN-10`,`api_productbase`.`ISBN-13` AS `ISBN-13`,`api_productbase`.`pages` AS `pages`,`api_productbase`.`Comment` AS `Comment`,`api_productbase`.`pepcode` AS `pepcode`,`api_productbase`.`publisher` AS `publisher`,`api_productbase`.`jrnl` AS `jrnl`,`api_productbase`.`pub_year` AS `pub_year`,`api_productbase`.`start_year` AS `start_year`,`api_productbase`.`end_year` AS `end_year`,`api_productbase`.`pep_url` AS `pep_url`,`api_productbase`.`language` AS `language`,`api_productbase`.`updated` AS `updated`,`api_productbase`.`pepversion` AS `pepversion`,`api_productbase`.`duplicate` AS `duplicate`,`api_productbase`.`landing_page` AS `landing_page`,`api_productbase`.`coverage_notes` AS `coverage_notes`,`api_productbase`.`landing_page_intro_html` AS `landing_page_intro_html`,`api_productbase`.`landing_page_end_html` AS `landing_page_end_html`,`api_productbase`.`google_books_link` AS `google_books_link` from (`api_productbase` join `vw_instance_counts_src`) where ((`api_productbase`.`basecode` <> 'OFFSITE') and (`api_productbase`.`basecode` = convert(`vw_instance_counts_src`.`basecode` using utf8))) order by `instances` desc;

-- ----------------------------
-- View structure for vw_api_sourceinfodb
-- ----------------------------
DROP VIEW IF EXISTS `vw_api_sourceinfodb`;
CREATE ALGORITHM = UNDEFINED SQL SECURITY DEFINER VIEW `vw_api_sourceinfodb` AS select `api_productbase`.`basecode` AS `pepsrccode`,`api_productbase`.`basecode` AS `basecode`,`api_productbase`.`active` AS `active`,`api_productbase`.`bibabbrev` AS `sourcetitleabbr`,`api_productbase`.`jrnl` AS `source`,`api_productbase`.`start_year` AS `start_year`,`api_productbase`.`end_year` AS `end_year`,`api_productbase`.`pep_url` AS `pep_url`,`api_productbase`.`language` AS `language`,`api_productbase`.`title` AS `sourcetitlefull`,`api_productbase`.`pep_class` AS `product_type`,`api_productbase`.`pep_class_qualifier` AS `product_type_qualifier`,`api_productbase`.`wall` AS `embargo`,`api_productbase`.`mainTOC` AS `mainTOC`,`api_productbase`.`author` AS `author`,`api_productbase`.`updated` AS `updated`,`api_productbase`.`landing_page` AS `landing_page`,`api_productbase`.`google_books_link` AS `google_books_link`,`api_productbase`.`pepversion` AS `pepversion`,`api_productbase`.`publisher` AS `publisher`,`api_productbase`.`ISSN` AS `ISSN`,`api_productbase`.`ISBN-10` AS `ISBN-10`,`api_productbase`.`ISBN-13` AS `ISBN-13`,`api_productbase`.`pages` AS `pages`,`api_productbase`.`articleID` AS `articleID`,`api_productbase`.`first_author` AS `first_author`,`api_productbase`.`bibabbrev` AS `bibabbrev`,`api_productbase`.`Comment` AS `Comment`,`api_productbase`.`pepcode` AS `pepcode`,`api_productbase`.`pub_year` AS `pub_year`,`api_productbase`.`duplicate` AS `duplicate`,`api_productbase`.`coverage_notes` AS `coverage_notes`,`api_productbase`.`landing_page_intro_html` AS `landing_page_intro_html`,`api_productbase`.`landing_page_end_html` AS `landing_page_end_html` from `api_productbase`;

-- ----------------------------
-- View structure for vw_api_volume_limits
-- ----------------------------
DROP VIEW IF EXISTS `vw_api_volume_limits`;
CREATE ALGORITHM = UNDEFINED SQL SECURITY DEFINER VIEW `vw_api_volume_limits` AS select `api_articles`.`src_code` AS `src_code`,min(`api_articles`.`art_vol`) AS `min(art_vol)`,max(`api_articles`.`art_vol`) AS `max(art_vol)` from `api_articles` group by `api_articles`.`src_code`;

-- ----------------------------
-- View structure for vw_instance_counts_books
-- ----------------------------
DROP VIEW IF EXISTS `vw_instance_counts_books`;
CREATE ALGORITHM = UNDEFINED SQL SECURITY DEFINER VIEW `vw_instance_counts_books` AS select concat(`api_articles`.`src_code`,convert(lpad(`api_articles`.`art_vol`,3,'0') using latin1)) AS `basecode`,`api_articles`.`src_code` AS `src_code`,`api_articles`.`art_vol` AS `art_vol`,count(0) AS `instances` from `api_articles` where (`api_articles`.`src_code` in ('ZBK','IPL','NLP','GW','SE')) group by `api_articles`.`src_code`,`api_articles`.`art_vol`;

-- ----------------------------
-- View structure for vw_instance_counts_src
-- ----------------------------
DROP VIEW IF EXISTS `vw_instance_counts_src`;
CREATE ALGORITHM = UNDEFINED SQL SECURITY DEFINER VIEW `vw_instance_counts_src` AS select `api_articles`.`src_code` AS `basecode`,`api_articles`.`src_code` AS `src_code`,`api_articles`.`art_vol` AS `art_vol`,count(0) AS `instances` from `api_articles` group by `api_articles`.`src_code`;

-- ----------------------------
-- View structure for vw_latest_session_activity
-- ----------------------------
DROP VIEW IF EXISTS `vw_latest_session_activity`;
CREATE ALGORITHM = UNDEFINED SQL SECURITY DEFINER VIEW `vw_latest_session_activity` AS select `api_session_endpoints`.`session_id` AS `session_id`,max(`api_session_endpoints`.`last_update`) AS `latest_activity` from `api_session_endpoints` group by `api_session_endpoints`.`session_id` order by max(`api_session_endpoints`.`last_update`) desc;

-- ----------------------------
-- View structure for vw_reports_abstract_views_from_endpoint_log
-- ----------------------------
DROP VIEW IF EXISTS `vw_reports_abstract_views_from_endpoint_log`;
CREATE ALGORITHM = UNDEFINED SQL SECURITY DEFINER VIEW `vw_reports_abstract_views_from_endpoint_log` AS select `vw_api_absviews_from_endpoint_log`.`document_id` AS `abstract_id`,any_value(`vw_api_absviews_from_endpoint_log`.`type`) AS `view_type`,count(0) AS `views`,min(`vw_api_absviews_from_endpoint_log`.`datetimechar`) AS `mindate`,max(`vw_api_absviews_from_endpoint_log`.`datetimechar`) AS `maxdate` from `vw_api_absviews_from_endpoint_log` where (`vw_api_absviews_from_endpoint_log`.`type` = 'Abstract') group by `vw_api_absviews_from_endpoint_log`.`document_id`;

-- ----------------------------
-- View structure for vw_reports_document_activity
-- ----------------------------
DROP VIEW IF EXISTS `vw_reports_document_activity`;
CREATE ALGORITHM = UNDEFINED SQL SECURITY DEFINER VIEW `vw_reports_document_activity` AS select `api_docviews`.`user_id` AS `user_id`,`api_docviews`.`session_id` AS `session_id`,`api_docviews`.`document_id` AS `document_id`,`api_docviews`.`type` AS `type`,`api_docviews`.`last_update` AS `last_update` from `api_docviews`;

-- ----------------------------
-- View structure for vw_reports_document_views
-- ----------------------------
DROP VIEW IF EXISTS `vw_reports_document_views`;
CREATE ALGORITHM = UNDEFINED SQL SECURITY DEFINER VIEW `vw_reports_document_views` AS select `api_docviews`.`document_id` AS `document_id`,any_value(`api_docviews`.`type`) AS `view_type`,count(0) AS `views` from `api_docviews` where (`api_docviews`.`type` = 'Document') group by `api_docviews`.`document_id`;

-- ----------------------------
-- View structure for vw_reports_session_activity
-- ----------------------------
DROP VIEW IF EXISTS `vw_reports_session_activity`;
CREATE ALGORITHM = UNDEFINED SQL SECURITY DEFINER VIEW `vw_reports_session_activity` AS select `api_sessions`.`user_id` AS `global_uid`,`api_session_endpoints`.`session_id` AS `session_id`,`api_sessions`.`session_start` AS `session_start`,`api_sessions`.`session_end` AS `session_end`,`api_session_endpoints`.`item_of_interest` AS `item_of_interest`,`api_endpoints`.`endpoint_url` AS `endpoint`,`api_session_endpoints`.`params` AS `params`,`api_session_endpoints`.`return_status_code` AS `return_status_code`,`api_session_endpoints`.`return_added_status_message` AS `return_added_status_message`,`api_session_endpoints`.`last_update` AS `last_update`,`api_session_endpoints`.`id` AS `session_activity_id` from ((`api_sessions` join `api_session_endpoints` on((`api_session_endpoints`.`session_id` = `api_sessions`.`session_id`))) join `api_endpoints` on((`api_endpoints`.`api_endpoint_id` = `api_session_endpoints`.`api_endpoint_id`)));

-- ----------------------------
-- View structure for vw_reports_user_searches
-- ----------------------------
DROP VIEW IF EXISTS `vw_reports_user_searches`;
CREATE ALGORITHM = UNDEFINED SQL SECURITY DEFINER VIEW `vw_reports_user_searches` AS select `api_sessions`.`user_id` AS `user_id`,`api_session_endpoints`.`session_id` AS `session_id`,`api_sessions`.`session_start` AS `session_start`,`api_session_endpoints`.`item_of_interest` AS `item_of_interest`,`api_endpoints`.`endpoint_url` AS `endpoint`,`api_session_endpoints`.`params` AS `params`,`api_session_endpoints`.`return_status_code` AS `return_status_code`,`api_session_endpoints`.`return_added_status_message` AS `return_added_status_message`,`api_session_endpoints`.`last_update` AS `last_update`,`api_session_endpoints`.`id` AS `session_activity_id` from ((`api_sessions` join `api_session_endpoints` on((`api_session_endpoints`.`session_id` = `api_sessions`.`session_id`))) join `api_endpoints` on((`api_endpoints`.`api_endpoint_id` = `api_session_endpoints`.`api_endpoint_id`))) where (`api_session_endpoints`.`api_endpoint_id` = 41);

-- ----------------------------
-- View structure for vw_stat_cited_crosstab
-- ----------------------------
DROP VIEW IF EXISTS `vw_stat_cited_crosstab`;
CREATE ALGORITHM = UNDEFINED SQL SECURITY DEFINER VIEW `vw_stat_cited_crosstab` AS select `r0`.`cited_document_id` AS `cited_document_id`,any_value(coalesce(`r1`.`count5`,0)) AS `count5`,any_value(coalesce(`r2`.`count10`,0)) AS `count10`,any_value(coalesce(`r3`.`count20`,0)) AS `count20`,any_value(coalesce(`r4`.`countAll`,0)) AS `countAll` from (((((select distinct `api_biblioxml`.`art_id` AS `articleID`,`api_biblioxml`.`bib_local_id` AS `internalID`,`api_biblioxml`.`full_ref_xml` AS `fullReference`,`api_biblioxml`.`bib_rx` AS `cited_document_id` from `api_biblioxml`) `r0` left join `vw_stat_cited_in_last_5_years` `r1` on((`r1`.`cited_document_id` = `r0`.`cited_document_id`))) left join `vw_stat_cited_in_last_10_years` `r2` on((`r2`.`cited_document_id` = `r0`.`cited_document_id`))) left join `vw_stat_cited_in_last_20_years` `r3` on((`r3`.`cited_document_id` = `r0`.`cited_document_id`))) left join `vw_stat_cited_in_all_years` `r4` on((`r4`.`cited_document_id` = `r0`.`cited_document_id`))) where ((`r0`.`cited_document_id` is not null) and (`r0`.`cited_document_id` <> 'None') and (substr(`r0`.`cited_document_id`,1,3) not in ('ZBK','IPL','SE.','GW.'))) group by `r0`.`cited_document_id` order by `countAll` desc;

-- ----------------------------
-- View structure for vw_stat_cited_crosstab_with_details
-- ----------------------------
DROP VIEW IF EXISTS `vw_stat_cited_crosstab_with_details`;
CREATE ALGORITHM = UNDEFINED SQL SECURITY DEFINER VIEW `vw_stat_cited_crosstab_with_details` AS select `vw_stat_cited_crosstab`.`cited_document_id` AS `cited_document_id`,`vw_stat_cited_crosstab`.`count5` AS `count5`,`vw_stat_cited_crosstab`.`count10` AS `count10`,`vw_stat_cited_crosstab`.`count20` AS `count20`,`vw_stat_cited_crosstab`.`countAll` AS `countAll`,`api_articles`.`art_auth_citation` AS `hdgauthor`,`api_articles`.`art_title` AS `hdgtitle`,`api_articles`.`src_title_abbr` AS `srctitleseries`,`api_articles`.`src_code` AS `source_code`,`api_articles`.`art_year` AS `year`,`api_articles`.`art_vol` AS `vol`,`api_articles`.`art_pgrg` AS `pgrg`,`api_articles`.`art_id` AS `art_id`,`api_articles`.`art_citeas_text` AS `art_citeas_text` from (`vw_stat_cited_crosstab` join `api_articles` on((`vw_stat_cited_crosstab`.`cited_document_id` = `api_articles`.`art_id`))) order by `vw_stat_cited_crosstab`.`countAll` desc;

-- ----------------------------
-- View structure for vw_stat_cited_in_all_years
-- ----------------------------
DROP VIEW IF EXISTS `vw_stat_cited_in_all_years`;
CREATE ALGORITHM = UNDEFINED SQL SECURITY DEFINER VIEW `vw_stat_cited_in_all_years` AS select `api_biblioxml`.`bib_rx` AS `cited_document_id`,count(0) AS `countAll` from `api_biblioxml` where ((`api_biblioxml`.`bib_rx` is not null) and (`api_biblioxml`.`bib_rx` <> '') and (substr(`api_biblioxml`.`bib_rx`,1,3) not in ('ZBK','IPL','SE.','GW.'))) group by `api_biblioxml`.`bib_rx` order by `countAll` desc;

-- ----------------------------
-- View structure for vw_stat_cited_in_last_10_years
-- ----------------------------
DROP VIEW IF EXISTS `vw_stat_cited_in_last_10_years`;
CREATE ALGORITHM = UNDEFINED SQL SECURITY DEFINER VIEW `vw_stat_cited_in_last_10_years` AS select `api_biblioxml`.`bib_rx` AS `cited_document_id`,count(0) AS `count10` from (`api_biblioxml` join `api_articles` `citing_article`) where ((`api_biblioxml`.`art_id` = `citing_article`.`art_id`) and (`api_biblioxml`.`bib_rx` is not null) and (`api_biblioxml`.`bib_rx` <> '') and (`citing_article`.`art_year` > (year(now()) - 10)) and (substr(`api_biblioxml`.`bib_rx`,1,3) not in ('ZBK','IPL','SE.','GW.'))) group by `api_biblioxml`.`bib_rx` order by `count10` desc;

-- ----------------------------
-- View structure for vw_stat_cited_in_last_20_years
-- ----------------------------
DROP VIEW IF EXISTS `vw_stat_cited_in_last_20_years`;
CREATE ALGORITHM = UNDEFINED SQL SECURITY DEFINER VIEW `vw_stat_cited_in_last_20_years` AS select `api_biblioxml`.`bib_rx` AS `cited_document_id`,count(0) AS `count20` from (`api_biblioxml` join `api_articles` `citing_article`) where ((`api_biblioxml`.`art_id` = `citing_article`.`art_id`) and (`api_biblioxml`.`bib_rx` is not null) and (`api_biblioxml`.`bib_rx` <> '') and (`citing_article`.`art_year` > (year(now()) - 20)) and (substr(`api_biblioxml`.`bib_rx`,1,3) not in ('ZBK','IPL','SE.','GW.'))) group by `api_biblioxml`.`bib_rx` order by `count20` desc;

-- ----------------------------
-- View structure for vw_stat_cited_in_last_5_years
-- ----------------------------
DROP VIEW IF EXISTS `vw_stat_cited_in_last_5_years`;
CREATE ALGORITHM = UNDEFINED SQL SECURITY DEFINER VIEW `vw_stat_cited_in_last_5_years` AS select `api_biblioxml`.`bib_rx` AS `cited_document_id`,count(0) AS `count5` from (`api_biblioxml` join `api_articles` `citing_article`) where ((`api_biblioxml`.`art_id` = `citing_article`.`art_id`) and (`api_biblioxml`.`bib_rx` is not null) and (`api_biblioxml`.`bib_rx` <> '') and (`citing_article`.`art_year` > (year(now()) - 5)) and (substr(`api_biblioxml`.`bib_rx`,1,3) not in ('ZBK','IPL','SE.','GW.'))) group by `api_biblioxml`.`bib_rx` order by `count5` desc;

-- ----------------------------
-- View structure for vw_stat_docviews_crosstab
-- ----------------------------
DROP VIEW IF EXISTS `vw_stat_docviews_crosstab`;
CREATE ALGORITHM = UNDEFINED SQL SECURITY DEFINER VIEW `vw_stat_docviews_crosstab` AS select `r0`.`document_id` AS `document_id`,any_value(max(`r0`.`last_viewed`)) AS `last_viewed`,any_value(coalesce(`r1`.`views`,0)) AS `lastweek`,any_value(coalesce(`r2`.`views`,0)) AS `lastmonth`,any_value(coalesce(`r3`.`views`,0)) AS `last6months`,any_value(coalesce(`r5`.`views`,0)) AS `last12months`,any_value(coalesce(`r4`.`views`,0)) AS `lastcalyear` from ((((((select distinct `api_docviews`.`document_id` AS `document_id`,`api_docviews`.`last_update` AS `last_viewed` from `api_docviews` where (`api_docviews`.`type` = 'Document')) `r0` left join `vw_stat_docviews_lastweek` `r1` on((`r1`.`document_id` = `r0`.`document_id`))) left join `vw_stat_docviews_lastmonth` `r2` on((`r2`.`document_id` = `r0`.`document_id`))) left join `vw_stat_docviews_lastsixmonths` `r3` on((`r3`.`document_id` = `r0`.`document_id`))) left join `vw_stat_docviews_lastcalyear` `r4` on((`r4`.`document_id` = `r0`.`document_id`))) left join `vw_stat_docviews_last12months` `r5` on((`r5`.`document_id` = `r0`.`document_id`))) where ((`r0`.`document_id` is not null) and (`r0`.`document_id` <> 'None')) group by `r0`.`document_id`;

-- ----------------------------
-- View structure for vw_stat_docviews_last12months
-- ----------------------------
DROP VIEW IF EXISTS `vw_stat_docviews_last12months`;
CREATE ALGORITHM = UNDEFINED SQL SECURITY DEFINER VIEW `vw_stat_docviews_last12months` AS select `api_docviews`.`document_id` AS `document_id`,count(0) AS `views` from `api_docviews` where ((`api_docviews`.`datetimechar` > (now() - interval 12 month)) and (`api_docviews`.`type` = 'Document')) group by `api_docviews`.`document_id`;

-- ----------------------------
-- View structure for vw_stat_docviews_lastcalyear
-- ----------------------------
DROP VIEW IF EXISTS `vw_stat_docviews_lastcalyear`;
CREATE ALGORITHM = UNDEFINED SQL SECURITY DEFINER VIEW `vw_stat_docviews_lastcalyear` AS select `api_docviews`.`document_id` AS `document_id`,count(0) AS `views` from `api_docviews` where ((year(`api_docviews`.`datetimechar`) = (year(now()) - 1)) and (`api_docviews`.`type` = 'Document')) group by `api_docviews`.`document_id`;

-- ----------------------------
-- View structure for vw_stat_docviews_lastmonth
-- ----------------------------
DROP VIEW IF EXISTS `vw_stat_docviews_lastmonth`;
CREATE ALGORITHM = UNDEFINED SQL SECURITY DEFINER VIEW `vw_stat_docviews_lastmonth` AS select `api_docviews`.`document_id` AS `document_id`,count(0) AS `views` from `api_docviews` where ((`api_docviews`.`datetimechar` > (now() - interval 1 month)) and (`api_docviews`.`type` = 'Document')) group by `api_docviews`.`document_id`;

-- ----------------------------
-- View structure for vw_stat_docviews_lastsixmonths
-- ----------------------------
DROP VIEW IF EXISTS `vw_stat_docviews_lastsixmonths`;
CREATE ALGORITHM = UNDEFINED SQL SECURITY DEFINER VIEW `vw_stat_docviews_lastsixmonths` AS select `api_docviews`.`document_id` AS `document_id`,count(0) AS `views` from `api_docviews` where ((`api_docviews`.`datetimechar` > (now() - interval 6 month)) and (`api_docviews`.`type` = 'Document')) group by `api_docviews`.`document_id`;

-- ----------------------------
-- View structure for vw_stat_docviews_lastweek
-- ----------------------------
DROP VIEW IF EXISTS `vw_stat_docviews_lastweek`;
CREATE ALGORITHM = UNDEFINED SQL SECURITY DEFINER VIEW `vw_stat_docviews_lastweek` AS select `api_docviews`.`document_id` AS `document_id`,any_value(`api_docviews`.`type`) AS `view_type`,count(0) AS `views` from `api_docviews` where ((`api_docviews`.`datetimechar` > (now() - interval 7 day)) and (`api_docviews`.`type` = 'Document')) group by `api_docviews`.`document_id`;

-- ----------------------------
-- View structure for vw_stat_most_viewed
-- ----------------------------
DROP VIEW IF EXISTS `vw_stat_most_viewed`;
CREATE ALGORITHM = UNDEFINED SQL SECURITY DEFINER VIEW `vw_stat_most_viewed` AS select `vw_stat_docviews_crosstab`.`document_id` AS `document_id`,`vw_stat_docviews_crosstab`.`last_viewed` AS `last_viewed`,coalesce(`vw_stat_docviews_crosstab`.`lastweek`,0) AS `lastweek`,coalesce(`vw_stat_docviews_crosstab`.`lastmonth`,0) AS `lastmonth`,coalesce(`vw_stat_docviews_crosstab`.`last6months`,0) AS `last6months`,coalesce(`vw_stat_docviews_crosstab`.`last12months`,0) AS `last12months`,coalesce(`vw_stat_docviews_crosstab`.`lastcalyear`,0) AS `lastcalyear`,`api_articles`.`art_auth_citation` AS `hdgauthor`,`api_articles`.`art_title` AS `hdgtitle`,`api_articles`.`src_title_abbr` AS `srctitleseries`,`api_articles`.`bk_publisher` AS `publisher`,`api_articles`.`src_code` AS `source_code`,`api_articles`.`art_year` AS `pubyear`,`api_articles`.`art_vol` AS `vol`,`api_articles`.`art_pgrg` AS `pgrg`,`api_productbase`.`pep_class` AS `source_type`,`api_articles`.`preserve` AS `preserve`,`api_articles`.`filename` AS `filename`,`api_articles`.`bk_title` AS `bktitle`,`api_articles`.`bk_info_xml` AS `bk_info_xml`,`api_articles`.`art_citeas_xml` AS `xmlref`,`api_articles`.`art_citeas_text` AS `textref`,`api_articles`.`art_auth_mast` AS `authorMast`,`api_articles`.`art_issue` AS `issue`,`api_articles`.`last_update` AS `last_update` from ((`vw_stat_docviews_crosstab` join `api_articles` on((`api_articles`.`art_id` = `vw_stat_docviews_crosstab`.`document_id`))) left join `api_productbase` on((`api_articles`.`src_code` = `api_productbase`.`pepcode`)));

-- ----------------------------
-- View structure for vw_stat_to_update_solr_docviews
-- ----------------------------
DROP VIEW IF EXISTS `vw_stat_to_update_solr_docviews`;
CREATE ALGORITHM = UNDEFINED SQL SECURITY DEFINER VIEW `vw_stat_to_update_solr_docviews` AS select `r0`.`document_id` AS `document_id`,any_value(max(`r0`.`last_viewed`)) AS `last_viewed`,any_value(coalesce(`r1`.`views`,0)) AS `lastweek`,any_value(coalesce(`r2`.`views`,0)) AS `lastmonth`,any_value(coalesce(`r3`.`views`,0)) AS `last6months`,any_value(coalesce(`r5`.`views`,0)) AS `last12months`,any_value(coalesce(`r4`.`views`,0)) AS `lastcalyear` from ((((((select distinct `api_docviews`.`document_id` AS `document_id`,`api_docviews`.`last_update` AS `last_viewed` from `api_docviews` where (`api_docviews`.`type` = 'Document')) `r0` left join `vw_stat_docviews_lastweek` `r1` on((`r1`.`document_id` = `r0`.`document_id`))) left join `vw_stat_docviews_lastmonth` `r2` on((`r2`.`document_id` = `r0`.`document_id`))) left join `vw_stat_docviews_lastsixmonths` `r3` on((`r3`.`document_id` = `r0`.`document_id`))) left join `vw_stat_docviews_lastcalyear` `r4` on((`r4`.`document_id` = `r0`.`document_id`))) left join `vw_stat_docviews_last12months` `r5` on((`r5`.`document_id` = `r0`.`document_id`))) where ((`r0`.`document_id` is not null) and (`r0`.`document_id` <> 'None') and (`r2`.`views` > 0)) group by `r0`.`document_id`;

SET FOREIGN_KEY_CHECKS = 1;
