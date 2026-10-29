CREATE TABLE `terminal_push_rate_limits` (
	`id` text PRIMARY KEY NOT NULL,
	`attempts` integer NOT NULL,
	`expires_at` integer NOT NULL
);
--> statement-breakpoint
CREATE INDEX `terminal_push_rate_expiry_idx` ON `terminal_push_rate_limits` (`expires_at`);--> statement-breakpoint
ALTER TABLE `terminal_push_subscriptions` ADD `device_key_hash` text;--> statement-breakpoint
CREATE UNIQUE INDEX `terminal_push_subscriptions_device_key_hash_unique` ON `terminal_push_subscriptions` (`device_key_hash`);