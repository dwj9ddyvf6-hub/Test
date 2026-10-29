CREATE TABLE `terminal_push_deliveries` (
	`subscription_id` text NOT NULL,
	`event_id` text NOT NULL,
	`status` text NOT NULL,
	`attempts` integer NOT NULL,
	`attempted_at` integer NOT NULL,
	`signal_at` integer NOT NULL,
	`provider_status` integer,
	PRIMARY KEY(`subscription_id`, `event_id`)
);

--> statement-breakpoint
CREATE INDEX `terminal_push_delivery_age_idx` ON `terminal_push_deliveries` (`attempted_at`);
--> statement-breakpoint
CREATE TABLE `terminal_push_subscriptions` (
	`id` text PRIMARY KEY NOT NULL,
	`user_id` text NOT NULL,
	`endpoint_hash` text NOT NULL,
	`subscription_json` text NOT NULL,
	`label` text NOT NULL,
	`created_at` integer NOT NULL,
	`activated_at` integer NOT NULL,
	`updated_at` integer NOT NULL,
	`expires_at` integer,
	`vapid_key_id` text NOT NULL,
	`disabled_at` integer,
	`last_sent_at` integer,
	`last_test_at` integer
);

--> statement-breakpoint
CREATE UNIQUE INDEX `terminal_push_subscriptions_endpoint_hash_unique` ON `terminal_push_subscriptions` (`endpoint_hash`);
--> statement-breakpoint
CREATE INDEX `terminal_push_user_active_idx` ON `terminal_push_subscriptions` (`user_id`,`disabled_at`);
