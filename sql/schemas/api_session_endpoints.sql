/*
Navicat MySQL Data Transfer

Source Server         : Raptor1
Source Server Version : 50714
Source Host           : localhost:3306
Source Database       : opascentral

Target Server Type    : MYSQL
Target Server Version : 50714
File Encoding         : 65001

Date: 2019-07-25 10:39:42
*/

SET FOREIGN_KEY_CHECKS=0;

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
SET FOREIGN_KEY_CHECKS=1;
