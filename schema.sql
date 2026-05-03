-- 校园二手交易平台数据库结构（MySQL 8.0+）
-- 说明：按作业要求仅保留 3 张核心表：user、item、orders

SET NAMES utf8mb4;
SET FOREIGN_KEY_CHECKS = 0;

DROP TABLE IF EXISTS `orders`;
DROP TABLE IF EXISTS `item`;
DROP TABLE IF EXISTS `user`;

SET FOREIGN_KEY_CHECKS = 1;

-- 用户表
CREATE TABLE `user` (
  `user_id` BIGINT UNSIGNED NOT NULL AUTO_INCREMENT,
  `username` VARCHAR(50) NOT NULL,
  `phone` VARCHAR(20) NOT NULL,
  `email` VARCHAR(100) NOT NULL,
  `created_at` DATETIME NOT NULL DEFAULT CURRENT_TIMESTAMP,
  PRIMARY KEY (`user_id`),
  UNIQUE KEY `uk_user_phone` (`phone`),
  UNIQUE KEY `uk_user_email` (`email`)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci;

-- 商品表
CREATE TABLE `item` (
  `item_id` BIGINT UNSIGNED NOT NULL AUTO_INCREMENT,
  `seller_id` BIGINT UNSIGNED NOT NULL,
  `title` VARCHAR(100) NOT NULL,
  `description` VARCHAR(255) NOT NULL,
  `price` DECIMAL(10,2) NOT NULL,
  `status` TINYINT NOT NULL DEFAULT 0 COMMENT '0=未售出,1=已售出',
  `created_at` DATETIME NOT NULL DEFAULT CURRENT_TIMESTAMP,
  PRIMARY KEY (`item_id`),
  KEY `idx_item_seller_id` (`seller_id`),
  CONSTRAINT `fk_item_seller` FOREIGN KEY (`seller_id`) REFERENCES `user` (`user_id`),
  CONSTRAINT `chk_item_status` CHECK (`status` IN (0, 1)),
  CONSTRAINT `chk_item_price` CHECK (`price` >= 0)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci;

-- 订单表
CREATE TABLE `orders` (
  `order_id` BIGINT UNSIGNED NOT NULL AUTO_INCREMENT,
  `buyer_id` BIGINT UNSIGNED NOT NULL,
  `item_id` BIGINT UNSIGNED NOT NULL,
  `deal_price` DECIMAL(10,2) NOT NULL,
  `created_at` DATETIME NOT NULL DEFAULT CURRENT_TIMESTAMP,
  PRIMARY KEY (`order_id`),
  UNIQUE KEY `uk_orders_item_id` (`item_id`),
  KEY `idx_orders_buyer_id` (`buyer_id`),
  CONSTRAINT `fk_orders_buyer` FOREIGN KEY (`buyer_id`) REFERENCES `user` (`user_id`),
  CONSTRAINT `fk_orders_item` FOREIGN KEY (`item_id`) REFERENCES `item` (`item_id`),
  CONSTRAINT `chk_orders_price` CHECK (`deal_price` >= 0)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci;
