/*
Navicat MySQL Data Transfer

Source Server         : Raptor1
Source Server Version : 50714
Source Host           : localhost:3306
Source Database       : opascentral

Target Server Type    : MYSQL
Target Server Version : 50714
File Encoding         : 65001

Date: 2019-07-25 10:39:26
*/

SET FOREIGN_KEY_CHECKS=0;

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
  `access_token` varchar(60) DEFAULT NULL,
  `authenticated` tinyint(1) DEFAULT '0',
  `api_client_id` int(11) NOT NULL,
  `updated` timestamp NULL DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP,
  PRIMARY KEY (`session_id`),
  KEY `idxSession` (`session_id`)
) ENGINE=InnoDB DEFAULT CHARSET=utf8;
SET FOREIGN_KEY_CHECKS=1;
