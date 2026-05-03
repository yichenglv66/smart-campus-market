-- 初始化数据（覆盖用户、商品、订单）
-- 执行前请先执行 schema.sql

SET NAMES utf8mb4;

-- 用户数据
INSERT INTO `user` (`username`, `phone`, `email`) VALUES
('张三', '13800000001', 'zhangsan@example.com'),
('李四', '13800000002', 'lisi@example.com'),
('王五', '13800000003', 'wangwu@example.com'),
('赵六', '13800000004', 'zhaoliu@example.com'),
('陈七', '13800000005', 'chenqi@example.com');

-- 商品数据（status: 0=未售出, 1=已售出）
INSERT INTO `item` (`seller_id`, `title`, `description`, `price`, `status`) VALUES
(1, '高等数学（同济第七版）', '九成新，无笔记', 35.00, 1),
(2, 'Python 程序设计教材', '期末复习好用', 28.00, 1),
(3, '二手台灯', '宿舍可用，正常发光', 20.00, 0),
(1, '机械键盘', '青轴，带灯效', 120.00, 0),
(4, '大学物理实验报告模板', '电子版打印出售', 8.00, 1),
(5, '小米充电宝 10000mAh', '功能正常', 45.00, 0);

-- 订单数据（item_id 唯一，确保每件商品最多交易一次）
INSERT INTO `orders` (`buyer_id`, `item_id`, `deal_price`) VALUES
(3, 1, 35.00),
(4, 2, 26.00),
(2, 5, 8.00);
