CREATE TABLE `aperture_scan_history` (
	`scan_id` text PRIMARY KEY NOT NULL,
	`bar_end_at` text NOT NULL,
	`generated_at` text NOT NULL,
	`provider` text NOT NULL,
	`freshness` text NOT NULL,
	`universe_covered` integer NOT NULL,
	`decision_count` integer NOT NULL,
	`body_json` text NOT NULL,
	`created_at` text NOT NULL
);
--> statement-breakpoint
CREATE INDEX `aperture_scan_bar_idx` ON `aperture_scan_history` (`bar_end_at`);