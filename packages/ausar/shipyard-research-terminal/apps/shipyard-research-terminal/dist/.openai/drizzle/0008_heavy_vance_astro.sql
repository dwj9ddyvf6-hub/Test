CREATE TABLE `terminal_setup_events` (
	`id` text PRIMARY KEY NOT NULL,
	`created_at` integer NOT NULL,
	`expires_at` integer NOT NULL,
	`payload_json` text NOT NULL
);
--> statement-breakpoint
CREATE INDEX `terminal_setup_event_expiry_idx` ON `terminal_setup_events` (`expires_at`);--> statement-breakpoint
CREATE INDEX `terminal_setup_event_created_idx` ON `terminal_setup_events` (`created_at`,`id`);