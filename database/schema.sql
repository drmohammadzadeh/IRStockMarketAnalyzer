-- ==============================================================================
-- پایگاه داده سامانه تحلیل جامع و هوشمند بازار سرمایه ایران (tjb24.ir)
-- نام پایگاه داده: tjbir_bourse
-- سیستم مدیریت پایگاه داده: MySQL 8.0+ / MariaDB 10.11+
-- کاراکترست: utf8mb4 (پشتیبانی کامل از زبان فارسی و ایموجی‌ها)
-- نویسنده: تیم مهندسی نرم‌افزار tjb24.ir
-- تاریخ: پاییز ۱۴۰۳
-- ==============================================================================

SET NAMES utf8mb4;
SET FOREIGN_KEY_CHECKS = 0;

-- ------------------------------------------------------------------------------
-- ۱. جدول کاربران (users)
-- نام کاربری برابر شماره موبایل ۱۱ رقمی (09xxxxxxxxx) است.
-- ------------------------------------------------------------------------------
CREATE TABLE IF NOT EXISTS `users` (
  `id` BIGINT(20) UNSIGNED NOT NULL AUTO_INCREMENT COMMENT 'شناسه یکتای کاربر',
  `first_name` VARCHAR(100) NOT NULL COMMENT 'نام کاربر',
  `last_name` VARCHAR(100) NOT NULL COMMENT 'نام خانوادگی کاربر',
  `mobile` VARCHAR(11) NOT NULL COMMENT 'شماره موبایل ۱۱ رقمی (نام کاربری)',
  `email` VARCHAR(150) NOT NULL COMMENT 'آدرس ایمیل یکتای کاربر',
  `password_hash` VARCHAR(255) NOT NULL COMMENT 'هش رمز عبور (bcrypt/argon2)',
  `is_active` TINYINT(1) NOT NULL DEFAULT 0 COMMENT 'وضعیت فعال بودن اکانت (۰: غیرفعال، ۱: فعال)',
  `last_login_at` TIMESTAMP NULL DEFAULT NULL COMMENT 'زمان آخرین ورود کاربر به سامانه',
  `created_at` TIMESTAMP NOT NULL DEFAULT CURRENT_TIMESTAMP COMMENT 'تاریخ و ساعت ثبت‌نام',
  `updated_at` TIMESTAMP NOT NULL DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP COMMENT 'تاریخ آخرین ویرایش اطلاعات',
  PRIMARY KEY (`id`),
  UNIQUE KEY `uk_users_mobile` (`mobile`),
  UNIQUE KEY `uk_users_email` (`email`),
  KEY `idx_users_is_active` (`is_active`),
  KEY `idx_users_created_at` (`created_at`)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci COMMENT='جدول اطلاعات هویتی و امنیتی کاربران سامانه';

-- ------------------------------------------------------------------------------
-- ۲. جدول توکن‌ها و کدهای فعال‌سازی حساب کاربری (user_activations)
-- پشتیبانی از فعال‌سازی با لینک یونیک ۶۴ کاراکتری و/یا کد ۶ رقمی عددی
-- ------------------------------------------------------------------------------
CREATE TABLE IF NOT EXISTS `user_activations` (
  `id` BIGINT(20) UNSIGNED NOT NULL AUTO_INCREMENT COMMENT 'شناسه یکتا',
  `user_id` BIGINT(20) UNSIGNED NOT NULL COMMENT 'شناسه کاربر مربوطه',
  `activation_token` VARCHAR(64) NOT NULL COMMENT 'توکن منحصربفرد لینک فعال‌سازی',
  `activation_code` VARCHAR(6) NOT NULL COMMENT 'کد ۶ رقمی عددی فعال‌سازی',
  `expires_at` TIMESTAMP NOT NULL COMMENT 'تاریخ انقضای توکن و کد (معمولاً ۲۴ ساعت)',
  `is_used` TINYINT(1) NOT NULL DEFAULT 0 COMMENT 'وضعیت مصرف کد (۰: مصرف نشده، ۱: مصرف شده)',
  `created_at` TIMESTAMP NOT NULL DEFAULT CURRENT_TIMESTAMP COMMENT 'زمان صدور کد فعال‌سازی',
  PRIMARY KEY (`id`),
  UNIQUE KEY `uk_activations_token` (`activation_token`),
  KEY `idx_activations_user_code` (`user_id`, `activation_code`, `is_used`),
  KEY `idx_activations_expires` (`expires_at`),
  CONSTRAINT `fk_activations_user` FOREIGN KEY (`user_id`) REFERENCES `users` (`id`) ON DELETE CASCADE ON UPDATE CASCADE
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci COMMENT='توکن‌ها و کدهای یکتای فعال‌سازی حساب کاربری';

-- ------------------------------------------------------------------------------
-- ۳. جدول توکن‌ها و کدهای بازیابی رمز عبور (password_resets)
-- امکان بازیابی رمز عبور از طریق کد ۶ رقمی پیامک/ایمیل یا لینک امن ریست رمز
-- ------------------------------------------------------------------------------
CREATE TABLE IF NOT EXISTS `password_resets` (
  `id` BIGINT(20) UNSIGNED NOT NULL AUTO_INCREMENT COMMENT 'شناسه یکتا',
  `user_id` BIGINT(20) UNSIGNED NOT NULL COMMENT 'شناسه کاربر متقاضی ریست رمز',
  `reset_token` VARCHAR(64) NOT NULL COMMENT 'توکن منحصربفرد لینک بازیابی رمز',
  `reset_code` VARCHAR(6) NOT NULL COMMENT 'کد ۶ رقمی عددی ریست رمز',
  `expires_at` TIMESTAMP NOT NULL COMMENT 'تاریخ انقضای کد و لینک (معمولاً ۱ ساعت)',
  `is_used` TINYINT(1) NOT NULL DEFAULT 0 COMMENT 'وضعیت مصرف کد (۰: مصرف نشده، ۱: مصرف شده)',
  `created_at` TIMESTAMP NOT NULL DEFAULT CURRENT_TIMESTAMP COMMENT 'زمان صدور درخواست بازیابی رمز',
  PRIMARY KEY (`id`),
  UNIQUE KEY `uk_resets_token` (`reset_token`),
  KEY `idx_resets_user_code` (`user_id`, `reset_code`, `is_used`),
  KEY `idx_resets_expires` (`expires_at`),
  CONSTRAINT `fk_resets_user` FOREIGN KEY (`user_id`) REFERENCES `users` (`id`) ON DELETE CASCADE ON UPDATE CASCADE
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci COMMENT='توکن‌ها و کدهای یکتای فراموشی و بازیابی رمز عبور';

-- ------------------------------------------------------------------------------
-- ۴. جدول درخواست‌های تحلیل سهام کاربران (stock_analysis_requests)
-- ذخیره درخواست‌های تحلیل نمادها با قابلیت مشاهده وضعیت، تاریخ تحلیل و نتیجه
-- ------------------------------------------------------------------------------
CREATE TABLE IF NOT EXISTS `stock_analysis_requests` (
  `id` BIGINT(20) UNSIGNED NOT NULL AUTO_INCREMENT COMMENT 'شناسه یکتای درخواست',
  `user_id` BIGINT(20) UNSIGNED DEFAULT NULL COMMENT 'شناسه کاربر ثبت‌نام‌شده (در صورت لاگین)',
  `applicant_name` VARCHAR(150) NOT NULL COMMENT 'نام و نام خانوادگی متقاضی',
  `applicant_mobile` VARCHAR(11) DEFAULT NULL COMMENT 'شماره موبایل متقاضی',
  `applicant_email` VARCHAR(150) NOT NULL COMMENT 'ایمیل متقاضی',
  `stock_symbol` VARCHAR(50) NOT NULL COMMENT 'نماد یا سهم درخواستی (مثلاً فولاد)',
  `request_type` VARCHAR(150) NOT NULL COMMENT 'نوع تعرفه و فوریت درخواست تحلیل',
  `notes` TEXT DEFAULT NULL COMMENT 'توضیحات تکمیلی متقاضی',
  `ip_address` VARCHAR(45) NOT NULL COMMENT 'آدرس آی‌پی کاربر (IPv4/IPv6)',
  `user_agent` TEXT DEFAULT NULL COMMENT 'مرورگر و سیستم‌عامل کاربر (User-Agent)',
  `referer` VARCHAR(500) DEFAULT NULL COMMENT 'صفحه ارجاع‌دهنده (HTTP Referer)',
  `client_language` VARCHAR(100) DEFAULT NULL COMMENT 'زبان ترجیحی مرورگر کاربر',
  `device_info` LONGTEXT CHARACTER SET utf8mb4 COLLATE utf8mb4_bin DEFAULT NULL COMMENT 'اطلاعات فنی دستگاه و مرورگر کاربر' CHECK (json_valid(`device_info`)),
  `status` ENUM('pending','in_progress','completed','rejected') NOT NULL DEFAULT 'pending' COMMENT 'وضعیت بررسی (در صف بررسی، در حال تحلیل، تحلیل شده، رد شده)',
  `analyzed_at` TIMESTAMP NULL DEFAULT NULL COMMENT 'تاریخ و زمان انجام تحلیل توسط سیستم یا تحلیل‌گر',
  `result_url` VARCHAR(500) DEFAULT NULL COMMENT 'آدرس اینترنتی یا مسیر گزارش تحلیل آماده‌شده سهم',
  `admin_notes` TEXT DEFAULT NULL COMMENT 'یادداشت یا پاسخ مدیر سامانه به متقاضی',
  `created_at` TIMESTAMP NOT NULL DEFAULT CURRENT_TIMESTAMP COMMENT 'زمان ثبت درخواست',
  `updated_at` TIMESTAMP NOT NULL DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP COMMENT 'زمان آخرین به‌روزرسانی وضعیت',
  PRIMARY KEY (`id`),
  KEY `idx_requests_user_id` (`user_id`),
  KEY `idx_requests_mobile` (`applicant_mobile`),
  KEY `idx_requests_email` (`applicant_email`),
  KEY `idx_requests_symbol` (`stock_symbol`),
  KEY `idx_requests_status` (`status`),
  KEY `idx_requests_created_at` (`created_at`),
  CONSTRAINT `fk_requests_user` FOREIGN KEY (`user_id`) REFERENCES `users` (`id`) ON DELETE SET NULL ON UPDATE CASCADE
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci COMMENT='جدول ثبت و پیگیری درخواست‌های تحلیل و افزودن سهم';

SET FOREIGN_KEY_CHECKS = 1;
