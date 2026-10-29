CREATE TABLE `tensor_audit_events` (
	`event_key` text PRIMARY KEY NOT NULL,
	`run_id` text NOT NULL,
	`event_date` text NOT NULL,
	`symbol` text NOT NULL,
	`interval` text NOT NULL,
	`event_time` integer NOT NULL,
	`cohort` text NOT NULL,
	`cyan` integer DEFAULT 0 NOT NULL,
	`green` integer DEFAULT 0 NOT NULL,
	`gold` integer DEFAULT 0 NOT NULL,
	`tier` text NOT NULL,
	`significant` integer DEFAULT 0 NOT NULL,
	`tier_move_pct` text,
	`chart_file` text,
	`png_file` text,
	`html_file` text,
	`payload_json` text NOT NULL,
	`created_at` text NOT NULL,
	FOREIGN KEY (`run_id`) REFERENCES `tensor_audit_runs`(`run_id`) ON UPDATE no action ON DELETE cascade
);
--> statement-breakpoint
CREATE INDEX `tensor_audit_events_run_time_idx` ON `tensor_audit_events` (`run_id`,`event_time`);--> statement-breakpoint
CREATE INDEX `tensor_audit_events_date_cohort_idx` ON `tensor_audit_events` (`event_date`,`cohort`);--> statement-breakpoint
CREATE INDEX `tensor_audit_events_symbol_time_idx` ON `tensor_audit_events` (`symbol`,`event_time`);--> statement-breakpoint
CREATE TABLE `tensor_audit_runs` (
	`run_id` text PRIMARY KEY NOT NULL,
	`date_key` text NOT NULL,
	`generated_at` text NOT NULL,
	`universe_hash` text NOT NULL,
	`universe_count` integer NOT NULL,
	`chart_mode` text NOT NULL,
	`event_count` integer DEFAULT 0 NOT NULL,
	`cyan_count` integer DEFAULT 0 NOT NULL,
	`green_count` integer DEFAULT 0 NOT NULL,
	`gold_count` integer DEFAULT 0 NOT NULL,
	`manifest_json` text NOT NULL,
	`created_at` text NOT NULL
);
--> statement-breakpoint
CREATE INDEX `tensor_audit_runs_generated_idx` ON `tensor_audit_runs` (`generated_at`);--> statement-breakpoint
CREATE INDEX `tensor_audit_runs_date_idx` ON `tensor_audit_runs` (`date_key`);