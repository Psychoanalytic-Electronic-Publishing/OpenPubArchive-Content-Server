/*
 Navicat MySQL Data Transfer

 Source Server         : XPS
 Source Server Type    : MySQL
 Source Server Version : 80033
 Source Host           : localhost:3306
 Source Schema         : opastest2

 Target Server Type    : MySQL
 Target Server Version : 80033
 File Encoding         : 65001

 Date: 26/05/2023 14:22:13
*/

SET NAMES utf8mb4;
SET FOREIGN_KEY_CHECKS = 0;

-- ----------------------------
-- View structure for vw_api_jrnl_vols
-- ----------------------------
DROP VIEW IF EXISTS `vw_api_jrnl_vols`;
CREATE ALGORITHM = UNDEFINED SQL SECURITY DEFINER VIEW `vw_api_jrnl_vols` AS select distinct `api_articles`.`src_code` AS `src_code`,`api_articles`.`art_year` AS `art_year`,`api_articles`.`art_vol` AS `art_vol` from `api_articles`;

-- ----------------------------
-- View structure for vw_api_messages
-- ----------------------------
DROP VIEW IF EXISTS `vw_api_messages`;
CREATE ALGORITHM = UNDEFINED SQL SECURITY DEFINER VIEW `vw_api_messages` AS select `api_messages`.`msg_num_code` AS `msg_num_code`,`api_messages`.`msg_language` AS `msg_language`,`api_messages`.`msg_sym_code` AS `msg_sym_code`,`api_messages`.`msg_text` AS `msg_text` from `api_messages`;

-- ----------------------------
-- View structure for vw_api_productbase
-- ----------------------------
DROP VIEW IF EXISTS `vw_api_productbase`;
CREATE ALGORITHM = UNDEFINED SQL SECURITY DEFINER VIEW `vw_api_productbase` AS select `api_productbase`.`basecode` AS `basecode`,`api_productbase`.`articleID` AS `articleID`,`api_productbase`.`active` AS `active`,0 AS `instances`,`api_productbase`.`pep_class` AS `product_type`,`api_productbase`.`pep_class_qualifier` AS `product_type_qualifier`,`api_productbase`.`accessClassification` AS `accessClassification`,`api_productbase`.`wall` AS `embargo`,`api_productbase`.`mainTOC` AS `mainTOC`,`api_productbase`.`first_author` AS `first_author`,`api_productbase`.`author` AS `author`,`api_productbase`.`title` AS `title`,`api_productbase`.`bibabbrev` AS `bibabbrev`,`api_productbase`.`ISSN` AS `ISSN`,`api_productbase`.`ISBN-10` AS `ISBN-10`,`api_productbase`.`ISBN-13` AS `ISBN-13`,`api_productbase`.`pages` AS `pages`,`api_productbase`.`Comment` AS `Comment`,`api_productbase`.`pepcode` AS `pepcode`,`api_productbase`.`publisher` AS `publisher`,`api_productbase`.`jrnl` AS `jrnl`,`api_productbase`.`pub_year` AS `pub_year`,`api_productbase`.`start_year` AS `start_year`,`api_productbase`.`end_year` AS `end_year`,`api_productbase`.`pep_url` AS `pep_url`,`api_productbase`.`language` AS `language`,`api_productbase`.`updated` AS `updated`,`api_productbase`.`pepversion` AS `pepversion`,`api_productbase`.`duplicate` AS `duplicate`,`api_productbase`.`landing_page` AS `landing_page`,`api_productbase`.`coverage_notes` AS `coverage_notes` from `api_productbase` order by `api_productbase`.`basecode`;

-- ----------------------------
-- View structure for vw_api_sourceinfodb
-- ----------------------------
DROP VIEW IF EXISTS `vw_api_sourceinfodb`;
CREATE ALGORITHM = UNDEFINED SQL SECURITY DEFINER VIEW `vw_api_sourceinfodb` AS select `api_productbase`.`basecode` AS `pepsrccode`,`api_productbase`.`basecode` AS `basecode`,`api_productbase`.`active` AS `active`,`api_productbase`.`bibabbrev` AS `sourcetitleabbr`,`api_productbase`.`jrnl` AS `source`,`api_productbase`.`start_year` AS `start_year`,`api_productbase`.`end_year` AS `end_year`,`api_productbase`.`pep_url` AS `pep_url`,`api_productbase`.`language` AS `language`,`api_productbase`.`title` AS `sourcetitlefull`,`api_productbase`.`pep_class` AS `product_type`,`api_productbase`.`pep_class_qualifier` AS `product_type_qualifier`,`api_productbase`.`wall` AS `embargo`,`api_productbase`.`mainTOC` AS `mainTOC`,`api_productbase`.`author` AS `author`,`api_productbase`.`updated` AS `updated`,`api_productbase`.`landing_page` AS `landing_page`,`api_productbase`.`google_books_link` AS `google_books_link`,`api_productbase`.`pepversion` AS `pepversion`,`api_productbase`.`publisher` AS `publisher`,`api_productbase`.`ISSN` AS `ISSN`,`api_productbase`.`ISBN-10` AS `ISBN-10`,`api_productbase`.`ISBN-13` AS `ISBN-13`,`api_productbase`.`pages` AS `pages`,`api_productbase`.`articleID` AS `articleID`,`api_productbase`.`first_author` AS `first_author`,`api_productbase`.`bibabbrev` AS `bibabbrev`,`api_productbase`.`Comment` AS `Comment`,`api_productbase`.`pepcode` AS `pepcode`,`api_productbase`.`pub_year` AS `pub_year`,`api_productbase`.`duplicate` AS `duplicate`,`api_productbase`.`coverage_notes` AS `coverage_notes` from `api_productbase`;

-- ----------------------------
-- View structure for vw_instance_counts_src
-- ----------------------------
DROP VIEW IF EXISTS `vw_instance_counts_src`;
CREATE ALGORITHM = UNDEFINED SQL SECURITY DEFINER VIEW `vw_instance_counts_src` AS select `api_articles`.`src_code` AS `basecode`,`api_articles`.`src_code` AS `src_code`,`api_articles`.`art_vol` AS `art_vol`,count(0) AS `instances` from `api_articles` group by `api_articles`.`src_code`;

-- ----------------------------
-- View structure for vw_instance_counts_books
-- ----------------------------
DROP VIEW IF EXISTS `vw_instance_counts_books`;
CREATE ALGORITHM = UNDEFINED SQL SECURITY DEFINER VIEW `vw_instance_counts_books` AS select concat(`api_articles`.`src_code`,convert(lpad(`api_articles`.`art_vol`,3,'0') using latin1)) AS `basecode`,`api_articles`.`src_code` AS `src_code`,`api_articles`.`art_vol` AS `art_vol`,count(0) AS `instances` from `api_articles` where (`api_articles`.`src_code` in ('ZBK','IPL','NLP','GW','SE')) group by `api_articles`.`src_code`,`api_articles`.`art_vol`;

-- ----------------------------
-- View structure for vw_api_productbase_instance_counts
-- ----------------------------
DROP VIEW IF EXISTS `vw_api_productbase_instance_counts`;
CREATE ALGORITHM = UNDEFINED SQL SECURITY DEFINER VIEW `vw_api_productbase_instance_counts` AS select `api_productbase`.`basecode` AS `basecode`,`api_productbase`.`articleID` AS `articleID`,`api_productbase`.`active` AS `active`,`vw_instance_counts_books`.`instances` AS `instances`,`api_productbase`.`pep_class` AS `product_type`,`api_productbase`.`pep_class_qualifier` AS `product_type_qualifier`,`api_productbase`.`accessClassification` AS `accessClassification`,`api_productbase`.`wall` AS `embargo`,`api_productbase`.`mainTOC` AS `mainTOC`,`api_productbase`.`first_author` AS `first_author`,`api_productbase`.`author` AS `author`,`api_productbase`.`title` AS `title`,`api_productbase`.`bibabbrev` AS `bibabbrev`,`api_productbase`.`ISSN` AS `ISSN`,`api_productbase`.`ISBN-10` AS `ISBN-10`,`api_productbase`.`ISBN-13` AS `ISBN-13`,`api_productbase`.`pages` AS `pages`,`api_productbase`.`Comment` AS `Comment`,`api_productbase`.`pepcode` AS `pepcode`,`api_productbase`.`publisher` AS `publisher`,`api_productbase`.`jrnl` AS `jrnl`,`api_productbase`.`pub_year` AS `pub_year`,`api_productbase`.`start_year` AS `start_year`,`api_productbase`.`end_year` AS `end_year`,`api_productbase`.`pep_url` AS `pep_url`,`api_productbase`.`language` AS `language`,`api_productbase`.`updated` AS `updated`,`api_productbase`.`pepversion` AS `pepversion`,`api_productbase`.`duplicate` AS `duplicate`,`api_productbase`.`landing_page` AS `landing_page`,`api_productbase`.`coverage_notes` AS `coverage_notes` from (`api_productbase` join `vw_instance_counts_books`) where (convert(`api_productbase`.`basecode` using utf8mb3) = convert(`vw_instance_counts_books`.`basecode` using utf8mb3)) union select `api_productbase`.`basecode` AS `basecode`,`api_productbase`.`articleID` AS `articleID`,`api_productbase`.`active` AS `active`,`vw_instance_counts_src`.`instances` AS `instances`,`api_productbase`.`pep_class` AS `product_type`,`api_productbase`.`pep_class_qualifier` AS `product_type_qualifier`,`api_productbase`.`accessClassification` AS `accessClassification`,`api_productbase`.`wall` AS `embargo`,`api_productbase`.`mainTOC` AS `mainTOC`,`api_productbase`.`first_author` AS `first_author`,`api_productbase`.`author` AS `author`,`api_productbase`.`title` AS `title`,`api_productbase`.`bibabbrev` AS `bibabbrev`,`api_productbase`.`ISSN` AS `ISSN`,`api_productbase`.`ISBN-10` AS `ISBN-10`,`api_productbase`.`ISBN-13` AS `ISBN-13`,`api_productbase`.`pages` AS `pages`,`api_productbase`.`Comment` AS `Comment`,`api_productbase`.`pepcode` AS `pepcode`,`api_productbase`.`publisher` AS `publisher`,`api_productbase`.`jrnl` AS `jrnl`,`api_productbase`.`pub_year` AS `pub_year`,`api_productbase`.`start_year` AS `start_year`,`api_productbase`.`end_year` AS `end_year`,`api_productbase`.`pep_url` AS `pep_url`,`api_productbase`.`language` AS `language`,`api_productbase`.`updated` AS `updated`,`api_productbase`.`pepversion` AS `pepversion`,`api_productbase`.`duplicate` AS `duplicate`,`api_productbase`.`landing_page` AS `landing_page`,`api_productbase`.`coverage_notes` AS `coverage_notes` from (`api_productbase` join `vw_instance_counts_src`) where ((`api_productbase`.`basecode` <> 'OFFSITE') and (convert(`api_productbase`.`basecode` using utf8mb3) = convert(`vw_instance_counts_src`.`basecode` using utf8mb3))) order by `instances` desc;

-- ----------------------------
-- View structure for vw_interactive_active_sessions
-- ----------------------------
DROP VIEW IF EXISTS `vw_interactive_active_sessions`;
CREATE ALGORITHM = UNDEFINED SQL SECURITY DEFINER VIEW `vw_interactive_active_sessions` AS select `api_sessions`.`session_id` AS `session_id`,`api_sessions`.`user_id` AS `user_id`,`api_sessions`.`username` AS `username`,`api_sessions`.`session_start` AS `session_start`,`api_sessions`.`session_end` AS `session_end`,`api_sessions`.`session_expires_time` AS `session_expires_time`,`api_sessions`.`authenticated` AS `authenticated`,`api_sessions`.`api_client_id` AS `api_client_id`,`api_sessions`.`last_update` AS `last_update` from `api_sessions` where ((`api_sessions`.`user_id` <> 0) and (`api_sessions`.`session_end` is null)) order by `api_sessions`.`session_start` desc;

-- ----------------------------
-- View structure for vw_interactive_biblio_checker
-- ----------------------------
DROP VIEW IF EXISTS `vw_interactive_biblio_checker`;
CREATE ALGORITHM = UNDEFINED SQL SECURITY DEFINER VIEW `vw_interactive_biblio_checker` AS select `api_biblioxml2`.`art_id` AS `art_id`,`api_biblioxml2`.`ref_local_id` AS `local_id`,`api_biblioxml2`.`ref_rx` AS `ref_rx`,`api_biblioxml2`.`ref_rx_confidence` AS `ref_rxconf`,`api_biblioxml2`.`ref_rxcf` AS `ref_rxcf`,`api_biblioxml2`.`ref_rxcf_confidence` AS `ref_rxcfconf`,`api_biblioxml2`.`ref_link_source` AS `link_source`,`api_biblioxml2`.`ref_sourcecode` AS `ref_src`,`api_biblioxml2`.`ref_volume` AS `ref_vol`,`api_biblioxml2`.`art_year` AS `art_year`,`api_biblioxml2`.`ref_pgrg` AS `ref_pgrg`,`api_biblioxml2`.`ref_authors` AS `ref_authors`,`api_articles`.`art_auth_citation` AS `link_auth`,`api_biblioxml2`.`ref_text` AS `ref_text`,`api_articles`.`art_citeas_text` AS `link_art`,`api_biblioxml2`.`ref_xml` AS `ref_xml`,`api_articles`.`last_update` AS `article_update`,`api_biblioxml2`.`last_update` AS `last_update` from (`api_biblioxml2` join `api_articles` on((`api_biblioxml2`.`ref_rx` = `api_articles`.`art_id`)));

-- ----------------------------
-- View structure for vw_interactive_glossary_details
-- ----------------------------
DROP VIEW IF EXISTS `vw_interactive_glossary_details`;
CREATE ALGORITHM = UNDEFINED SQL SECURITY DEFINER VIEW `vw_interactive_glossary_details` AS select `opasloader_glossary_terms`.`group_id` AS `group_id`,`opasloader_glossary_terms`.`term` AS `term`,`opasloader_glossary_terms`.`see` AS `see`,`opasloader_glossary_terms`.`source` AS `source`,`opasloader_glossary_terms`.`xmlsource` AS `xmlsource`,`opasloader_glossary_terms`.`termcount` AS `termcount`,`opasloader_glossary_terms`.`regex` AS `regex`,`opasloader_glossary_terms`.`regex_tuned` AS `regex_tuned`,`opasloader_glossary_terms`.`regex_ignore` AS `regex_ignore`,`opasloader_glossary_terms`.`updated` AS `termUpdated` from `opasloader_glossary_terms`;

-- ----------------------------
-- View structure for vw_interactive_latest_session_activity
-- ----------------------------
DROP VIEW IF EXISTS `vw_interactive_latest_session_activity`;
CREATE ALGORITHM = UNDEFINED SQL SECURITY DEFINER VIEW `vw_interactive_latest_session_activity` AS select `api_session_endpoints`.`session_id` AS `session_id`,max(`api_session_endpoints`.`last_update`) AS `latest_activity` from `api_session_endpoints` group by `api_session_endpoints`.`session_id` order by max(`api_session_endpoints`.`last_update`) desc;

-- ----------------------------
-- View structure for vw_interactive_stat_bibliolinks
-- ----------------------------
DROP VIEW IF EXISTS `vw_interactive_stat_bibliolinks`;
CREATE ALGORITHM = UNDEFINED SQL SECURITY DEFINER VIEW `vw_interactive_stat_bibliolinks` AS select 'Nolinks' AS `Nolinks`,count(0) AS `count(*)` from `api_biblioxml2` where ((`api_biblioxml2`.`ref_rxcf` is null) and (`api_biblioxml2`.`ref_rx` is null)) union select 'Links' AS `Links`,count(0) AS `count(*)` from `api_biblioxml2` where ((`api_biblioxml2`.`ref_rxcf` is not null) or (`api_biblioxml2`.`ref_rx` is not null)) union select 'rx' AS `rx`,count(0) AS `count(*)` from `api_biblioxml2` where (`api_biblioxml2`.`ref_rx` is not null) union select 'rxcf' AS `rxcf`,count(0) AS `count(*)` from `api_biblioxml2` where (`api_biblioxml2`.`ref_rxcf` is not null) union select 'Heuristic links' AS `Heuristic links`,count(0) AS `count(*)` from `api_biblioxml2` where (`api_biblioxml2`.`ref_link_source` = 'heuristic');

-- ----------------------------
-- View structure for vw_interactive_table_counts
-- ----------------------------
DROP VIEW IF EXISTS `vw_interactive_table_counts`;
CREATE ALGORITHM = UNDEFINED SQL SECURITY DEFINER VIEW `vw_interactive_table_counts` AS select 'sessions' AS `sessions`,format(count(0),'N0') AS `rows` from `api_sessions` union select 'session_endpoints' AS `session_endpoints`,format(count(0),'N0') AS `rows` from `api_session_endpoints` union select 'docviews' AS `docviews`,format(count(0),'N0') AS `rows` from `api_docviews` union select 'graphicviews' AS `graphicviews`,format(count(0),'N0') AS `rows` from `api_docviews` where (`api_docviews`.`type` = 'graphic');

-- ----------------------------
-- View structure for vw_opasloader_article_sectnames
-- ----------------------------
DROP VIEW IF EXISTS `vw_opasloader_article_sectnames`;
CREATE ALGORITHM = UNDEFINED SQL SECURITY DEFINER VIEW `vw_opasloader_article_sectnames` AS select `api_articles`.`src_code` AS `src_code`,`api_articles`.`art_vol` AS `art_vol`,`api_articles`.`art_issue` AS `art_issue`,`api_articles`.`art_id` AS `art_id`,trim(`api_articles`.`start_sectname`) AS `start_sectname` from `api_articles` order by `api_articles`.`art_id`;

-- ----------------------------
-- View structure for vw_opasloader_article_firstsectnames
-- ----------------------------
DROP VIEW IF EXISTS `vw_opasloader_article_firstsectnames`;
CREATE ALGORITHM = UNDEFINED SQL SECURITY DEFINER VIEW `vw_opasloader_article_firstsectnames` AS select `vw_opasloader_article_sectnames`.`art_id` AS `art_id`,`vw_opasloader_article_sectnames`.`start_sectname` AS `start_sectname` from `vw_opasloader_article_sectnames` where (`vw_opasloader_article_sectnames`.`start_sectname` is not null) group by `vw_opasloader_article_sectnames`.`src_code`,`vw_opasloader_article_sectnames`.`art_vol`,`vw_opasloader_article_sectnames`.`art_issue`,`vw_opasloader_article_sectnames`.`start_sectname` order by `vw_opasloader_article_sectnames`.`art_id`;

-- ----------------------------
-- View structure for vw_opasloader_glossary_group_terms
-- ----------------------------
DROP VIEW IF EXISTS `vw_opasloader_glossary_group_terms`;
CREATE ALGORITHM = UNDEFINED SQL SECURITY DEFINER VIEW `vw_opasloader_glossary_group_terms` AS select `opasloader_glossary_terms`.`term` AS `term`,`opasloader_glossary_terms`.`group_id` AS `terms_group_id`,`opasloader_glossary_group_ids`.`group_id` AS `groups_group_id`,`opasloader_glossary_group_ids`.`glossary_group` AS `glossary_group`,`opasloader_glossary_terms`.`regex` AS `regex`,`opasloader_glossary_terms`.`regex_ignore` AS `regex_ignore`,`opasloader_glossary_terms`.`termcount` AS `termcount`,`opasloader_glossary_terms`.`sourceinstance` AS `sourceinstance` from (`opasloader_glossary_group_ids` left join `opasloader_glossary_terms` on((`opasloader_glossary_terms`.`group_id` = `opasloader_glossary_group_ids`.`group_id`)));

-- ----------------------------
-- View structure for vw_opasloader_splitbookpages
-- ----------------------------
DROP VIEW IF EXISTS `vw_opasloader_splitbookpages`;
CREATE ALGORITHM = UNDEFINED SQL SECURITY DEFINER VIEW `vw_opasloader_splitbookpages` AS select `opasloader_splitbookpages`.`articleIDbase` AS `articleIDbase`,`opasloader_splitbookpages`.`articleID` AS `articleID`,`opasloader_splitbookpages`.`pagenumber` AS `pagenumber`,`opasloader_splitbookpages`.`bibliopage` AS `bibliopage`,`opasloader_splitbookpages`.`tocpage` AS `tocpage`,`opasloader_splitbookpages`.`filename` AS `filename` from `opasloader_splitbookpages`;

-- ----------------------------
-- View structure for vw_reports_charcounts_sub_books_bysrccode
-- ----------------------------
DROP VIEW IF EXISTS `vw_reports_charcounts_sub_books_bysrccode`;
CREATE ALGORITHM = UNDEFINED SQL SECURITY DEFINER VIEW `vw_reports_charcounts_sub_books_bysrccode` AS select `api_articles`.`src_code` AS `jrnlcode`,`api_articles`.`art_year` AS `year`,`api_articles`.`art_vol` AS `vol`,sum(`artstat`.`Chars`) AS `CharCount`,sum(`artstat`.`NonspaceChars`) AS `NoSpaceCharCount`,count(`api_articles`.`art_id`) AS `ArticleCount`,min(cast(`artstat`.`modTime` as date)) AS `Earliest`,max(cast(`artstat`.`modTime` as date)) AS `Latest` from (`artstat` join `api_articles` on((`artstat`.`articleID` = `api_articles`.`art_id`))) where (`api_articles`.`src_code` in ('IPL','NLP','ZBK','SE','GW')) group by `api_articles`.`src_code`;

-- ----------------------------
-- View structure for vw_reports_charcounts_sub_books_byvol
-- ----------------------------
DROP VIEW IF EXISTS `vw_reports_charcounts_sub_books_byvol`;
CREATE ALGORITHM = UNDEFINED SQL SECURITY DEFINER VIEW `vw_reports_charcounts_sub_books_byvol` AS select `api_articles`.`src_code` AS `jrnlcode`,`api_articles`.`art_year` AS `year`,`api_articles`.`art_vol` AS `vol`,sum(`artstat`.`Chars`) AS `CharCount`,sum(`artstat`.`NonspaceChars`) AS `NoSpaceCharCount`,count(`api_articles`.`art_id`) AS `ArticleCount`,min(cast(`artstat`.`modTime` as date)) AS `Earliest`,max(cast(`artstat`.`modTime` as date)) AS `Latest` from (`artstat` join `api_articles` on((`artstat`.`articleID` = `api_articles`.`art_id`))) where (`api_articles`.`src_code` in ('ZBK','IPL','NLP','SE','GW')) group by `api_articles`.`src_code`,`api_articles`.`art_vol`;

-- ----------------------------
-- View structure for vw_reports_charcounts_sub_books_selectioncriteria
-- ----------------------------
DROP VIEW IF EXISTS `vw_reports_charcounts_sub_books_selectioncriteria`;
CREATE ALGORITHM = UNDEFINED SQL SECURITY DEFINER VIEW `vw_reports_charcounts_sub_books_selectioncriteria` AS select `vw_reports_charcounts_sub_books_byvol`.`jrnlcode` AS `jrnlcode`,`vw_reports_charcounts_sub_books_byvol`.`year` AS `year`,`api_productbase`.`wall` AS `wall`,`api_productbase`.`active` AS `active`,`api_productbase`.`pep_class` AS `pep_class`,`api_productbase`.`start_year` AS `jrnlstartyear`,`api_productbase`.`end_year` AS `jrnlendyear`,`api_productbase`.`charcount_stat_start_year` AS `jrnlgrpstartyear`,`api_productbase`.`charcount_stat_group_str` AS `jrnlgrp`,`api_productbase`.`charcount_stat_name` AS `jrnlgrpname`,`api_productbase`.`charcount_stat_group_count` AS `jrnlgrpmembercount`,year(now()) AS `year(now())`,((year(now()) - `api_productbase`.`wall`) - 1) AS `uptoyear`,`vw_reports_charcounts_sub_books_byvol`.`CharCount` AS `CharCount`,`vw_reports_charcounts_sub_books_byvol`.`NoSpaceCharCount` AS `NoSpaceCharCount`,`vw_reports_charcounts_sub_books_byvol`.`Earliest` AS `Earliest`,`vw_reports_charcounts_sub_books_byvol`.`Latest` AS `Latest` from (`vw_reports_charcounts_sub_books_byvol` join `api_productbase`) where (convert(`vw_reports_charcounts_sub_books_byvol`.`jrnlcode` using utf8mb3) = convert(`api_productbase`.`basecode` using utf8mb3));

-- ----------------------------
-- View structure for vw_reports_charcounts_sub_booksall
-- ----------------------------
DROP VIEW IF EXISTS `vw_reports_charcounts_sub_booksall`;
CREATE ALGORITHM = UNDEFINED SQL SECURITY DEFINER VIEW `vw_reports_charcounts_sub_booksall` AS select cast('Books (All)' as char charset latin1) AS `jrnlgrpname`,cast('All' as char charset latin1) AS `jrnlcode`,`vw_reports_charcounts_sub_books_selectioncriteria`.`jrnlgrp` AS `jrnlgrp`,`vw_reports_charcounts_sub_books_selectioncriteria`.`jrnlgrpstartyear` AS `jrnlgrpstartyear`,`vw_reports_charcounts_sub_books_selectioncriteria`.`jrnlstartyear` AS `jrnlstartyear`,count(`vw_reports_charcounts_sub_books_selectioncriteria`.`year`) AS `yearsincluded`,lpad(format(sum(`vw_reports_charcounts_sub_books_selectioncriteria`.`CharCount`),0),(32 - char_length(cast(sum(`vw_reports_charcounts_sub_books_selectioncriteria`.`CharCount`) as char charset utf8mb4))),' ') AS `CharCount`,lpad(format(sum(`vw_reports_charcounts_sub_books_selectioncriteria`.`NoSpaceCharCount`),0),(32 - char_length(cast(sum(`vw_reports_charcounts_sub_books_selectioncriteria`.`NoSpaceCharCount`) as char charset utf8mb4))),' ') AS `NoSpaceCharCount`,max(`vw_reports_charcounts_sub_books_selectioncriteria`.`uptoyear`) AS `max(uptoyear)`,`vw_reports_charcounts_sub_books_selectioncriteria`.`Earliest` AS `Earliest`,`vw_reports_charcounts_sub_books_selectioncriteria`.`Latest` AS `Latest` from `vw_reports_charcounts_sub_books_selectioncriteria`;

-- ----------------------------
-- View structure for vw_reports_charcounts_sub_byjournalyear
-- ----------------------------
DROP VIEW IF EXISTS `vw_reports_charcounts_sub_byjournalyear`;
CREATE ALGORITHM = UNDEFINED SQL SECURITY DEFINER VIEW `vw_reports_charcounts_sub_byjournalyear` AS select `api_articles`.`src_code` AS `jrnlcode`,`api_articles`.`art_year` AS `year`,`api_articles`.`art_vol` AS `vol`,sum(`artstat`.`Chars`) AS `CharCount`,sum(`artstat`.`NonspaceChars`) AS `NoSpaceCharCount`,count(`api_articles`.`art_id`) AS `ArticleCount`,min(cast(`artstat`.`modTime` as date)) AS `Earliest`,max(cast(`artstat`.`modTime` as date)) AS `Latest` from (`artstat` join `api_articles` on((`artstat`.`articleID` = `api_articles`.`art_id`))) group by `api_articles`.`src_code`,`api_articles`.`art_year`;

-- ----------------------------
-- View structure for vw_reports_charcounts_sub_jrnl_selectioncriteria
-- ----------------------------
DROP VIEW IF EXISTS `vw_reports_charcounts_sub_jrnl_selectioncriteria`;
CREATE ALGORITHM = UNDEFINED SQL SECURITY DEFINER VIEW `vw_reports_charcounts_sub_jrnl_selectioncriteria` AS select `vw_reports_charcounts_sub_byjournalyear`.`jrnlcode` AS `jrnlcode`,`vw_reports_charcounts_sub_byjournalyear`.`year` AS `year`,`api_productbase`.`wall` AS `wall`,`api_productbase`.`start_year` AS `jrnlstartyear`,`api_productbase`.`end_year` AS `jrnlendyear`,`api_productbase`.`charcount_stat_start_year` AS `jrnlgrpstartyear`,`api_productbase`.`charcount_stat_group_str` AS `jrnlgrp`,`api_productbase`.`charcount_stat_name` AS `jrnlgrpname`,`api_productbase`.`charcount_stat_group_count` AS `jrnlgrpmembercount`,year(now()) AS `year(now())`,((year(now()) - `api_productbase`.`wall`) - 1) AS `uptoyear`,`vw_reports_charcounts_sub_byjournalyear`.`CharCount` AS `CharCount`,`vw_reports_charcounts_sub_byjournalyear`.`NoSpaceCharCount` AS `NoSpaceCharCount`,`vw_reports_charcounts_sub_byjournalyear`.`Earliest` AS `Earliest`,`vw_reports_charcounts_sub_byjournalyear`.`Latest` AS `Latest` from (`vw_reports_charcounts_sub_byjournalyear` join `api_productbase`) where (((`api_productbase`.`pep_class` like 'journal') or (`api_productbase`.`pep_class` like 'bookseriessub')) and (convert(`api_productbase`.`charcount_stat_group_str` using utf8mb3) like concat('%/',convert(`vw_reports_charcounts_sub_byjournalyear`.`jrnlcode` using utf8mb3),'/%')));

-- ----------------------------
-- View structure for vw_reports_charcounts_sub_jrnlgroups
-- ----------------------------
DROP VIEW IF EXISTS `vw_reports_charcounts_sub_jrnlgroups`;
CREATE ALGORITHM = UNDEFINED SQL SECURITY DEFINER VIEW `vw_reports_charcounts_sub_jrnlgroups` AS select `vw_reports_charcounts_sub_jrnl_selectioncriteria`.`jrnlgrpname` AS `jrnlgrpname`,`vw_reports_charcounts_sub_jrnl_selectioncriteria`.`jrnlcode` AS `jrnlcode`,`vw_reports_charcounts_sub_jrnl_selectioncriteria`.`jrnlgrp` AS `jrnlgrp`,`vw_reports_charcounts_sub_jrnl_selectioncriteria`.`jrnlgrpstartyear` AS `jrnlgrpstartyear`,`vw_reports_charcounts_sub_jrnl_selectioncriteria`.`jrnlstartyear` AS `jrnlstartyear`,count(`vw_reports_charcounts_sub_jrnl_selectioncriteria`.`year`) AS `yearsincluded`,lpad(convert(format((sum(`vw_reports_charcounts_sub_jrnl_selectioncriteria`.`CharCount`) / `vw_reports_charcounts_sub_jrnl_selectioncriteria`.`jrnlgrpmembercount`),0) using utf8mb4),(32 - char_length(cast(sum(`vw_reports_charcounts_sub_jrnl_selectioncriteria`.`CharCount`) as char charset utf8mb4))),' ') AS `CharCount`,lpad(convert(format((sum(`vw_reports_charcounts_sub_jrnl_selectioncriteria`.`NoSpaceCharCount`) / `vw_reports_charcounts_sub_jrnl_selectioncriteria`.`jrnlgrpmembercount`),0) using utf8mb4),(32 - char_length(cast(sum(`vw_reports_charcounts_sub_jrnl_selectioncriteria`.`NoSpaceCharCount`) as char charset utf8mb4))),' ') AS `NoSpaceCharCount`,max(`vw_reports_charcounts_sub_jrnl_selectioncriteria`.`uptoyear`) AS `max(uptoyear)`,`vw_reports_charcounts_sub_jrnl_selectioncriteria`.`Earliest` AS `Earliest`,`vw_reports_charcounts_sub_jrnl_selectioncriteria`.`Latest` AS `Latest` from `vw_reports_charcounts_sub_jrnl_selectioncriteria` where ((`vw_reports_charcounts_sub_jrnl_selectioncriteria`.`year` <= `vw_reports_charcounts_sub_jrnl_selectioncriteria`.`uptoyear`) and (`vw_reports_charcounts_sub_jrnl_selectioncriteria`.`year` >= `vw_reports_charcounts_sub_jrnl_selectioncriteria`.`jrnlgrpstartyear`)) group by `vw_reports_charcounts_sub_jrnl_selectioncriteria`.`jrnlgrp` order by `vw_reports_charcounts_sub_jrnl_selectioncriteria`.`jrnlgrpname`;

-- ----------------------------
-- View structure for vw_reports_charcounts
-- ----------------------------
DROP VIEW IF EXISTS `vw_reports_charcounts`;
CREATE ALGORITHM = UNDEFINED SQL SECURITY DEFINER VIEW `vw_reports_charcounts` AS select `vw_reports_charcounts_sub_jrnlgroups`.`jrnlgrpname` AS `jrnlgrpname`,`vw_reports_charcounts_sub_jrnlgroups`.`jrnlcode` AS `jrnlcode`,`vw_reports_charcounts_sub_jrnlgroups`.`jrnlgrp` AS `jrnlgrp`,`vw_reports_charcounts_sub_jrnlgroups`.`jrnlgrpstartyear` AS `jrnlgrpstartyear`,`vw_reports_charcounts_sub_jrnlgroups`.`jrnlstartyear` AS `jrnlstartyear`,`vw_reports_charcounts_sub_jrnlgroups`.`yearsincluded` AS `yearsincluded`,`vw_reports_charcounts_sub_jrnlgroups`.`CharCount` AS `CharCount`,`vw_reports_charcounts_sub_jrnlgroups`.`NoSpaceCharCount` AS `NoSpaceCharCount`,`vw_reports_charcounts_sub_jrnlgroups`.`max(uptoyear)` AS `max(uptoyear)` from `vw_reports_charcounts_sub_jrnlgroups` union select `vw_reports_charcounts_sub_booksall`.`jrnlgrpname` AS `jrnlgrpname`,`vw_reports_charcounts_sub_booksall`.`jrnlcode` AS `jrnlcode`,`vw_reports_charcounts_sub_booksall`.`jrnlgrp` AS `jrnlgrp`,`vw_reports_charcounts_sub_booksall`.`jrnlgrpstartyear` AS `jrnlgrpstartyear`,`vw_reports_charcounts_sub_booksall`.`jrnlstartyear` AS `jrnlstartyear`,`vw_reports_charcounts_sub_booksall`.`yearsincluded` AS `yearsincluded`,`vw_reports_charcounts_sub_booksall`.`CharCount` AS `CharCount`,`vw_reports_charcounts_sub_booksall`.`NoSpaceCharCount` AS `NoSpaceCharCount`,`vw_reports_charcounts_sub_booksall`.`max(uptoyear)` AS `max(uptoyear)` from `vw_reports_charcounts_sub_booksall` union select 'PSC to 70' AS `jrnlgrpname`,'PSC' AS `jrnlcode`,'/PSC to 70/' AS `jrnlgrp`,1699 AS `jrnlgrpstartyear`,1930 AS `jrnlstartyear`,22 AS `yearsincluded`,'              27,929,196' AS `CharCount`,'              23,310,728' AS `NoSpaceCharCount`,1970 AS `max(uptoyear)` union select 'PSYCHE to 2011' AS `jrnlgrpname`,'PSYCHE' AS `jrnlcode`,'/PSYCHE to 2011/' AS `jrnlgrp`,1699 AS `jrnlgrpstartyear`,1947 AS `jrnlstartyear`,64 AS `yearsincluded`,'             196,924,653' AS `CharCount`,'             170,793,907' AS `NoSpaceCharCount`,2011 AS `max(uptoyear)` order by `jrnlgrpname`;

-- ----------------------------
-- View structure for vw_reports_charcounts_details
-- ----------------------------
DROP VIEW IF EXISTS `vw_reports_charcounts_details`;
CREATE ALGORITHM = UNDEFINED SQL SECURITY DEFINER VIEW `vw_reports_charcounts_details` AS select `vw_reports_charcounts_sub_byjournalyear`.`jrnlcode` AS `jrnlcode`,`vw_reports_charcounts_sub_byjournalyear`.`year` AS `year`,`vw_reports_charcounts_sub_byjournalyear`.`vol` AS `vol`,`vw_reports_charcounts_sub_byjournalyear`.`CharCount` AS `CharCount`,`vw_reports_charcounts_sub_byjournalyear`.`NoSpaceCharCount` AS `NoSpaceCharCount`,`vw_reports_charcounts_sub_byjournalyear`.`ArticleCount` AS `ArticleCount`,`vw_reports_charcounts_sub_byjournalyear`.`Earliest` AS `Earliest`,`vw_reports_charcounts_sub_byjournalyear`.`Latest` AS `Latest` from `vw_reports_charcounts_sub_byjournalyear` union select `vw_reports_charcounts_sub_books_bysrccode`.`jrnlcode` AS `jrnlcode`,`vw_reports_charcounts_sub_books_bysrccode`.`year` AS `year`,`vw_reports_charcounts_sub_books_bysrccode`.`vol` AS `vol`,`vw_reports_charcounts_sub_books_bysrccode`.`CharCount` AS `CharCount`,`vw_reports_charcounts_sub_books_bysrccode`.`NoSpaceCharCount` AS `NoSpaceCharCount`,`vw_reports_charcounts_sub_books_bysrccode`.`ArticleCount` AS `ArticleCount`,`vw_reports_charcounts_sub_books_bysrccode`.`Earliest` AS `Earliest`,`vw_reports_charcounts_sub_books_bysrccode`.`Latest` AS `Latest` from `vw_reports_charcounts_sub_books_bysrccode` order by `jrnlcode`,`year`;

-- ----------------------------
-- View structure for vw_reports_document_activity
-- ----------------------------
DROP VIEW IF EXISTS `vw_reports_document_activity`;
CREATE ALGORITHM = UNDEFINED SQL SECURITY DEFINER VIEW `vw_reports_document_activity` AS select `api_docviews`.`user_id` AS `user_id`,`api_docviews`.`session_id` AS `session_id`,`api_docviews`.`document_id` AS `document_id`,`api_docviews`.`type` AS `type`,`api_docviews`.`last_update` AS `last_update`,`api_docviews`.`id` AS `document_activity_id` from `api_docviews`;

-- ----------------------------
-- View structure for vw_reports_document_views
-- ----------------------------
DROP VIEW IF EXISTS `vw_reports_document_views`;
CREATE ALGORITHM = UNDEFINED SQL SECURITY DEFINER VIEW `vw_reports_document_views` AS select `api_docviews`.`document_id` AS `document_id`,any_value(`api_docviews`.`type`) AS `view_type`,count(0) AS `views` from `api_docviews` where (`api_docviews`.`type` = 'Document') group by `api_docviews`.`document_id` order by `views` desc;

-- ----------------------------
-- View structure for vw_reports_session_activity
-- ----------------------------
DROP VIEW IF EXISTS `vw_reports_session_activity`;
CREATE ALGORITHM = UNDEFINED SQL SECURITY DEFINER VIEW `vw_reports_session_activity` AS select `api_sessions`.`user_id` AS `global_uid`,`api_session_endpoints`.`session_id` AS `session_id`,`api_sessions`.`session_start` AS `session_start`,`api_sessions`.`session_end` AS `session_end`,`api_session_endpoints`.`item_of_interest` AS `item_of_interest`,`api_endpoints`.`endpoint_url` AS `endpoint`,`api_endpoints`.`api_endpoint_id` AS `endpoint_id`,`api_session_endpoints`.`params` AS `params`,`api_session_endpoints`.`return_status_code` AS `return_status_code`,`api_session_endpoints`.`return_added_status_message` AS `return_added_status_message`,`api_session_endpoints`.`last_update` AS `last_update`,`api_session_endpoints`.`id` AS `session_activity_id` from ((`api_sessions` join `api_session_endpoints` on((`api_session_endpoints`.`session_id` = `api_sessions`.`session_id`))) join `api_endpoints` on((`api_endpoints`.`api_endpoint_id` = `api_session_endpoints`.`api_endpoint_id`))) order by `api_session_endpoints`.`last_update`;

-- ----------------------------
-- View structure for vw_reports_session_activity_desc
-- ----------------------------
DROP VIEW IF EXISTS `vw_reports_session_activity_desc`;
CREATE ALGORITHM = UNDEFINED SQL SECURITY DEFINER VIEW `vw_reports_session_activity_desc` AS select `api_sessions`.`user_id` AS `global_uid`,`api_session_endpoints`.`session_id` AS `session_id`,`api_sessions`.`session_start` AS `session_start`,`api_sessions`.`session_end` AS `session_end`,`api_session_endpoints`.`item_of_interest` AS `item_of_interest`,`api_endpoints`.`endpoint_url` AS `endpoint`,`api_endpoints`.`api_endpoint_id` AS `endpoint_id`,`api_session_endpoints`.`params` AS `params`,`api_session_endpoints`.`return_status_code` AS `return_status_code`,`api_session_endpoints`.`return_added_status_message` AS `return_added_status_message`,`api_session_endpoints`.`last_update` AS `last_update`,`api_session_endpoints`.`id` AS `session_activity_id` from ((`api_sessions` join `api_session_endpoints` on((`api_session_endpoints`.`session_id` = `api_sessions`.`session_id`))) join `api_endpoints` on((`api_endpoints`.`api_endpoint_id` = `api_session_endpoints`.`api_endpoint_id`))) order by `api_session_endpoints`.`last_update` desc;

-- ----------------------------
-- View structure for vw_reports_session_activity_not_logged_in
-- ----------------------------
DROP VIEW IF EXISTS `vw_reports_session_activity_not_logged_in`;
CREATE ALGORITHM = UNDEFINED SQL SECURITY DEFINER VIEW `vw_reports_session_activity_not_logged_in` AS select `api_sessions`.`user_id` AS `global_uid`,`api_session_endpoints_not_logged_in`.`session_id` AS `session_id`,`api_sessions`.`session_start` AS `session_start`,`api_sessions`.`session_end` AS `session_end`,`api_session_endpoints_not_logged_in`.`item_of_interest` AS `item_of_interest`,`api_endpoints`.`endpoint_url` AS `endpoint`,`api_endpoints`.`api_endpoint_id` AS `endpoint_id`,`api_session_endpoints_not_logged_in`.`params` AS `params`,`api_session_endpoints_not_logged_in`.`return_status_code` AS `return_status_code`,`api_session_endpoints_not_logged_in`.`return_added_status_message` AS `return_added_status_message`,`api_session_endpoints_not_logged_in`.`last_update` AS `last_update`,`api_session_endpoints_not_logged_in`.`id` AS `session_activity_id` from ((`api_sessions` join `api_session_endpoints_not_logged_in` on((`api_session_endpoints_not_logged_in`.`session_id` = `api_sessions`.`session_id`))) join `api_endpoints` on((`api_endpoints`.`api_endpoint_id` = `api_session_endpoints_not_logged_in`.`api_endpoint_id`))) order by `api_session_endpoints_not_logged_in`.`last_update`;

-- ----------------------------
-- View structure for vw_reports_session_activity_not_logged_in_desc
-- ----------------------------
DROP VIEW IF EXISTS `vw_reports_session_activity_not_logged_in_desc`;
CREATE ALGORITHM = UNDEFINED SQL SECURITY DEFINER VIEW `vw_reports_session_activity_not_logged_in_desc` AS select `api_sessions`.`user_id` AS `global_uid`,`api_session_endpoints_not_logged_in`.`session_id` AS `session_id`,`api_sessions`.`session_start` AS `session_start`,`api_sessions`.`session_end` AS `session_end`,`api_session_endpoints_not_logged_in`.`item_of_interest` AS `item_of_interest`,`api_endpoints`.`endpoint_url` AS `endpoint`,`api_endpoints`.`api_endpoint_id` AS `endpoint_id`,`api_session_endpoints_not_logged_in`.`params` AS `params`,`api_session_endpoints_not_logged_in`.`return_status_code` AS `return_status_code`,`api_session_endpoints_not_logged_in`.`return_added_status_message` AS `return_added_status_message`,`api_session_endpoints_not_logged_in`.`last_update` AS `last_update`,`api_session_endpoints_not_logged_in`.`id` AS `session_activity_id` from ((`api_sessions` join `api_session_endpoints_not_logged_in` on((`api_session_endpoints_not_logged_in`.`session_id` = `api_sessions`.`session_id`))) join `api_endpoints` on((`api_endpoints`.`api_endpoint_id` = `api_session_endpoints_not_logged_in`.`api_endpoint_id`))) order by `api_session_endpoints_not_logged_in`.`last_update` desc;

-- ----------------------------
-- View structure for vw_reports_session_activity_with_null_user_id
-- ----------------------------
DROP VIEW IF EXISTS `vw_reports_session_activity_with_null_user_id`;
CREATE ALGORITHM = UNDEFINED SQL SECURITY DEFINER VIEW `vw_reports_session_activity_with_null_user_id` AS select `api_session_endpoints`.`session_id` AS `session_id`,`api_session_endpoints`.`api_endpoint_id` AS `api_endpoint_id`,`api_session_endpoints`.`api_method` AS `api_method`,`api_session_endpoints`.`params` AS `params`,`api_session_endpoints`.`item_of_interest` AS `item_of_interest`,`api_session_endpoints`.`return_status_code` AS `return_status_code`,`api_session_endpoints`.`return_added_status_message` AS `return_added_status_message`,`api_session_endpoints`.`last_update` AS `last_update` from (`api_session_endpoints` left join `api_sessions` on((`api_session_endpoints`.`session_id` = `api_sessions`.`session_id`))) where (`api_sessions`.`user_id` is null);

-- ----------------------------
-- View structure for vw_reports_session_activity_with_user_id
-- ----------------------------
DROP VIEW IF EXISTS `vw_reports_session_activity_with_user_id`;
CREATE ALGORITHM = UNDEFINED SQL SECURITY DEFINER VIEW `vw_reports_session_activity_with_user_id` AS select `api_session_endpoints`.`session_id` AS `session_id`,`api_session_endpoints`.`api_endpoint_id` AS `api_endpoint_id`,`api_session_endpoints`.`api_method` AS `api_method`,`api_session_endpoints`.`params` AS `params`,`api_session_endpoints`.`item_of_interest` AS `item_of_interest`,`api_session_endpoints`.`return_status_code` AS `return_status_code`,`api_session_endpoints`.`return_added_status_message` AS `return_added_status_message`,`api_session_endpoints`.`last_update` AS `last_update` from (`api_session_endpoints` left join `api_sessions` on((`api_session_endpoints`.`session_id` = `api_sessions`.`session_id`))) where (`api_sessions`.`user_id` is not null);

-- ----------------------------
-- View structure for vw_reports_user_searches
-- ----------------------------
DROP VIEW IF EXISTS `vw_reports_user_searches`;
CREATE ALGORITHM = UNDEFINED SQL SECURITY DEFINER VIEW `vw_reports_user_searches` AS select `api_sessions`.`user_id` AS `user_id`,`api_session_endpoints`.`session_id` AS `session_id`,`api_sessions`.`session_start` AS `session_start`,`api_session_endpoints`.`item_of_interest` AS `item_of_interest`,`api_endpoints`.`endpoint_url` AS `endpoint`,`api_session_endpoints`.`params` AS `params`,`api_session_endpoints`.`return_status_code` AS `return_status_code`,`api_session_endpoints`.`return_added_status_message` AS `return_added_status_message`,`api_session_endpoints`.`last_update` AS `last_update`,`api_session_endpoints`.`id` AS `session_activity_id` from ((`api_sessions` join `api_session_endpoints` on((`api_session_endpoints`.`session_id` = `api_sessions`.`session_id`))) join `api_endpoints` on((`api_endpoints`.`api_endpoint_id` = `api_session_endpoints`.`api_endpoint_id`))) where (`api_session_endpoints`.`api_endpoint_id` = 41);

-- ----------------------------
-- View structure for vw_stat_cited_in_all_years2
-- ----------------------------
DROP VIEW IF EXISTS `vw_stat_cited_in_all_years2`;
CREATE ALGORITHM = UNDEFINED SQL SECURITY DEFINER VIEW `vw_stat_cited_in_all_years2` AS select `api_biblioxml2`.`ref_rx` AS `cited_document_id`,count(0) AS `countAll` from `api_biblioxml2` where ((`api_biblioxml2`.`ref_rx` is not null) and (`api_biblioxml2`.`ref_rx` <> '') and (`api_biblioxml2`.`ref_rx_confidence` <> '.01') and (substr(`api_biblioxml2`.`ref_rx`,1,3) not in ('ZBK','IPL','SE.','GW.'))) group by `api_biblioxml2`.`ref_rx` order by `countAll` desc;

-- ----------------------------
-- View structure for vw_stat_cited_in_last_10_years2
-- ----------------------------
DROP VIEW IF EXISTS `vw_stat_cited_in_last_10_years2`;
CREATE ALGORITHM = UNDEFINED SQL SECURITY DEFINER VIEW `vw_stat_cited_in_last_10_years2` AS select `api_biblioxml2`.`ref_rx` AS `cited_document_id`,count(0) AS `count10` from (`api_biblioxml2` join `api_articles` `citing_article`) where ((`api_biblioxml2`.`art_id` = `citing_article`.`art_id`) and (`api_biblioxml2`.`ref_rx` is not null) and (`api_biblioxml2`.`ref_rx` <> '') and (`api_biblioxml2`.`ref_rx_confidence` <> '.01') and (`citing_article`.`art_year` > (year(now()) - 10)) and (substr(`api_biblioxml2`.`ref_rx`,1,3) not in ('ZBK','IPL','SE.','GW.'))) group by `api_biblioxml2`.`ref_rx` order by `count10` desc;

-- ----------------------------
-- View structure for vw_stat_cited_in_last_20_years2
-- ----------------------------
DROP VIEW IF EXISTS `vw_stat_cited_in_last_20_years2`;
CREATE ALGORITHM = UNDEFINED SQL SECURITY DEFINER VIEW `vw_stat_cited_in_last_20_years2` AS select `api_biblioxml2`.`ref_rx` AS `cited_document_id`,count(0) AS `count20` from (`api_biblioxml2` join `api_articles` `citing_article`) where ((`api_biblioxml2`.`art_id` = `citing_article`.`art_id`) and (`api_biblioxml2`.`ref_rx` is not null) and (`api_biblioxml2`.`ref_rx_confidence` <> '.01') and (`api_biblioxml2`.`ref_rx` <> '') and (`citing_article`.`art_year` > (year(now()) - 20)) and (substr(`api_biblioxml2`.`ref_rx`,1,3) not in ('ZBK','IPL','SE.','GW.'))) group by `api_biblioxml2`.`ref_rx` order by `count20` desc;

-- ----------------------------
-- View structure for vw_stat_cited_in_last_5_years2
-- ----------------------------
DROP VIEW IF EXISTS `vw_stat_cited_in_last_5_years2`;
CREATE ALGORITHM = UNDEFINED SQL SECURITY DEFINER VIEW `vw_stat_cited_in_last_5_years2` AS select `api_biblioxml2`.`ref_rx` AS `cited_document_id`,count(0) AS `count5` from (`api_biblioxml2` join `api_articles` `citing_article`) where ((`api_biblioxml2`.`art_id` = `citing_article`.`art_id`) and (`api_biblioxml2`.`ref_rx` is not null) and (`api_biblioxml2`.`ref_rx` <> '') and (`api_biblioxml2`.`ref_rx_confidence` <> '.01') and (`citing_article`.`art_year` > (year(now()) - 5)) and (substr(`api_biblioxml2`.`ref_rx`,1,3) not in ('ZBK','IPL','SE.','GW.'))) group by `api_biblioxml2`.`ref_rx` order by `count5` desc;

-- ----------------------------
-- View structure for vw_stat_cited_crosstab2
-- ----------------------------
DROP VIEW IF EXISTS `vw_stat_cited_crosstab2`;
CREATE ALGORITHM = UNDEFINED SQL SECURITY DEFINER VIEW `vw_stat_cited_crosstab2` AS select `r0`.`cited_document_id` AS `cited_document_id`,any_value(coalesce(`r1`.`count5`,0)) AS `count5`,any_value(coalesce(`r2`.`count10`,0)) AS `count10`,any_value(coalesce(`r3`.`count20`,0)) AS `count20`,any_value(coalesce(`r4`.`countAll`,0)) AS `countAll` from (((((select distinct `api_biblioxml2`.`art_id` AS `articleID`,`api_biblioxml2`.`ref_local_id` AS `internalID`,`api_biblioxml2`.`ref_xml` AS `fullReference`,`api_biblioxml2`.`ref_rx` AS `cited_document_id` from `api_biblioxml2`) `r0` left join `vw_stat_cited_in_last_5_years2` `r1` on((`r1`.`cited_document_id` = `r0`.`cited_document_id`))) left join `vw_stat_cited_in_last_10_years2` `r2` on((`r2`.`cited_document_id` = `r0`.`cited_document_id`))) left join `vw_stat_cited_in_last_20_years2` `r3` on((`r3`.`cited_document_id` = `r0`.`cited_document_id`))) left join `vw_stat_cited_in_all_years2` `r4` on((`r4`.`cited_document_id` = `r0`.`cited_document_id`))) where ((`r0`.`cited_document_id` is not null) and (`r0`.`cited_document_id` <> 'None') and (substr(`r0`.`cited_document_id`,1,3) not in ('ZBK','IPL','SE.','GW.'))) group by `r0`.`cited_document_id` order by `countAll` desc;

-- ----------------------------
-- View structure for vw_stat_cited_crosstab_with_details2
-- ----------------------------
DROP VIEW IF EXISTS `vw_stat_cited_crosstab_with_details2`;
CREATE ALGORITHM = UNDEFINED SQL SECURITY DEFINER VIEW `vw_stat_cited_crosstab_with_details2` AS select `vw_stat_cited_crosstab2`.`cited_document_id` AS `cited_document_id`,`vw_stat_cited_crosstab2`.`count5` AS `count5`,`vw_stat_cited_crosstab2`.`count10` AS `count10`,`vw_stat_cited_crosstab2`.`count20` AS `count20`,`vw_stat_cited_crosstab2`.`countAll` AS `countAll`,`api_articles`.`art_auth_citation` AS `hdgauthor`,`api_articles`.`art_title` AS `hdgtitle`,`api_articles`.`src_title_abbr` AS `srctitleseries`,`api_articles`.`src_code` AS `source_code`,`api_articles`.`art_year` AS `year`,`api_articles`.`art_vol` AS `vol`,`api_articles`.`art_pgrg` AS `pgrg`,`api_articles`.`art_id` AS `art_id`,`api_articles`.`art_citeas_text` AS `art_citeas_text` from (`vw_stat_cited_crosstab2` join `api_articles` on((`vw_stat_cited_crosstab2`.`cited_document_id` = `api_articles`.`art_id`))) order by `vw_stat_cited_crosstab2`.`countAll` desc;

-- ----------------------------
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

-- View structure for vw_stat_docviews_crosstab
-- ----------------------------
DROP VIEW IF EXISTS `vw_stat_docviews_crosstab`;
CREATE ALGORITHM = UNDEFINED SQL SECURITY DEFINER VIEW `vw_stat_docviews_crosstab` AS select `r0`.`document_id` AS `document_id`,any_value(max(`r0`.`last_viewed`)) AS `last_viewed`,any_value(coalesce(`r1`.`views`,0)) AS `lastweek`,any_value(coalesce(`r2`.`views`,0)) AS `lastmonth`,any_value(coalesce(`r3`.`views`,0)) AS `last6months`,any_value(coalesce(`r5`.`views`,0)) AS `last12months`,any_value(coalesce(`r4`.`views`,0)) AS `lastcalyear` from ((((((select distinct `api_docviews`.`document_id` AS `document_id`,`api_docviews`.`last_update` AS `last_viewed` from `api_docviews` where (`api_docviews`.`type` = 'Document')) `r0` left join `vw_stat_docviews_lastweek` `r1` on((`r1`.`document_id` = `r0`.`document_id`))) left join `vw_stat_docviews_lastmonth` `r2` on((`r2`.`document_id` = `r0`.`document_id`))) left join `vw_stat_docviews_lastsixmonths` `r3` on((`r3`.`document_id` = `r0`.`document_id`))) left join `vw_stat_docviews_lastcalyear` `r4` on((`r4`.`document_id` = `r0`.`document_id`))) left join `vw_stat_docviews_last12months` `r5` on((`r5`.`document_id` = `r0`.`document_id`))) where ((`r0`.`document_id` is not null) and (`r0`.`document_id` <> 'None')) group by `r0`.`document_id`;

-- ----------------------------
-- View structure for vw_stat_most_viewed
-- ----------------------------
DROP VIEW IF EXISTS `vw_stat_most_viewed`;
CREATE ALGORITHM = UNDEFINED SQL SECURITY DEFINER VIEW `vw_stat_most_viewed` AS select `vw_stat_docviews_crosstab`.`document_id` AS `document_id`,`vw_stat_docviews_crosstab`.`last_viewed` AS `last_viewed`,coalesce(`vw_stat_docviews_crosstab`.`lastweek`,0) AS `lastweek`,coalesce(`vw_stat_docviews_crosstab`.`lastmonth`,0) AS `lastmonth`,coalesce(`vw_stat_docviews_crosstab`.`last6months`,0) AS `last6months`,coalesce(`vw_stat_docviews_crosstab`.`last12months`,0) AS `last12months`,coalesce(`vw_stat_docviews_crosstab`.`lastcalyear`,0) AS `lastcalyear`,`api_articles`.`art_auth_citation` AS `hdgauthor`,`api_articles`.`art_title` AS `hdgtitle`,`api_articles`.`src_title_abbr` AS `srctitleseries`,`api_articles`.`bk_publisher` AS `publisher`,`api_articles`.`src_code` AS `source_code`,`api_articles`.`art_year` AS `pubyear`,`api_articles`.`art_vol` AS `vol`,`api_articles`.`art_pgrg` AS `pgrg`,`api_productbase`.`pep_class` AS `source_type`,`api_articles`.`preserve` AS `preserve`,`api_articles`.`filename` AS `filename`,`api_articles`.`bk_title` AS `bktitle`,`api_articles`.`bk_info_xml` AS `bk_info_xml`,`api_articles`.`art_citeas_xml` AS `xmlref`,`api_articles`.`art_citeas_text` AS `textref`,`api_articles`.`art_auth_mast` AS `authorMast`,`api_articles`.`art_issue` AS `issue`,`api_articles`.`last_update` AS `last_update` from ((`vw_stat_docviews_crosstab` join `api_articles` on((`api_articles`.`art_id` = `vw_stat_docviews_crosstab`.`document_id`))) left join `api_productbase` on((`api_articles`.`src_code` = `api_productbase`.`pepcode`)));

SET FOREIGN_KEY_CHECKS = 1;
