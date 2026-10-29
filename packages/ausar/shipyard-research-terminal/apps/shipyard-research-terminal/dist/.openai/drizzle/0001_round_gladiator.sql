CREATE TABLE `observatory_ingest_runs` (
	`id` text PRIMARY KEY NOT NULL,
	`source_type` text NOT NULL,
	`provider` text NOT NULL,
	`snapshot_sha256` text NOT NULL,
	`status` text NOT NULL,
	`started_at` text NOT NULL,
	`completed_at` text,
	`input_watermark_at` text,
	`records_accepted` integer DEFAULT 0 NOT NULL,
	`records_rejected` integer DEFAULT 0 NOT NULL,
	`manifest_json` text NOT NULL,
	`quality_json` text DEFAULT '{}' NOT NULL,
	`error_code` text
);
--> statement-breakpoint
CREATE UNIQUE INDEX `observatory_ingest_runs_snapshot_sha256_unique` ON `observatory_ingest_runs` (`snapshot_sha256`);--> statement-breakpoint
CREATE INDEX `obs_ingest_status_started_idx` ON `observatory_ingest_runs` (`status`,`started_at`);--> statement-breakpoint
CREATE TABLE `observatory_market_bars` (
	`provider` text NOT NULL,
	`symbol` text NOT NULL,
	`timeframe` text NOT NULL,
	`bar_end_at` text NOT NULL,
	`bar_start_at` text NOT NULL,
	`available_at` text NOT NULL,
	`session_date` text NOT NULL,
	`open` text NOT NULL,
	`high` text NOT NULL,
	`low` text NOT NULL,
	`close` text NOT NULL,
	`volume` text,
	`adjustment_method` text NOT NULL,
	`is_rth` integer NOT NULL,
	`input_hash` text NOT NULL,
	`quality_json` text DEFAULT '{}' NOT NULL,
	`ingest_run_id` text NOT NULL,
	PRIMARY KEY(`provider`, `symbol`, `timeframe`, `bar_end_at`),
	FOREIGN KEY (`ingest_run_id`) REFERENCES `observatory_ingest_runs`(`id`) ON UPDATE no action ON DELETE no action
);
--> statement-breakpoint
CREATE INDEX `obs_bars_symbol_time_idx` ON `observatory_market_bars` (`symbol`,`timeframe`,`bar_end_at`);--> statement-breakpoint
CREATE TABLE `observatory_observation_steps` (
	`observation_id` text NOT NULL,
	`step_kind` text NOT NULL,
	`sequence` integer NOT NULL,
	`name` text NOT NULL,
	`started_at` text,
	`ended_at` text,
	`effective_at` text,
	`duration_ms` integer,
	`status` text,
	`value_text` text,
	`payload_json` text DEFAULT '{}' NOT NULL,
	PRIMARY KEY(`observation_id`, `step_kind`, `sequence`),
	FOREIGN KEY (`observation_id`) REFERENCES `observatory_observations`(`observation_id`) ON UPDATE no action ON DELETE no action
);
--> statement-breakpoint
CREATE TABLE `observatory_observations` (
	`observation_id` text PRIMARY KEY NOT NULL,
	`logical_key` text NOT NULL,
	`observation_type` text NOT NULL,
	`revision` integer DEFAULT 1 NOT NULL,
	`supersedes_observation_id` text,
	`created_at` text NOT NULL,
	`computed_at` text NOT NULL,
	`effective_at` text NOT NULL,
	`input_watermark_at` text NOT NULL,
	`expires_at` text,
	`formula_version` text NOT NULL,
	`parameter_hash` text NOT NULL,
	`input_hash` text NOT NULL,
	`code_commit` text NOT NULL,
	`provider` text NOT NULL,
	`event_key` text,
	`bar_at` text,
	`roster_version` text,
	`roster_hash` text,
	`symbol` text,
	`timeframe` text,
	`pair_id` text,
	`study_id` text,
	`direction` text,
	`status` text,
	`summary_json` text DEFAULT '{}' NOT NULL,
	`payload_json` text NOT NULL,
	`quality_json` text DEFAULT '{}' NOT NULL,
	`ingest_run_id` text,
	FOREIGN KEY (`ingest_run_id`) REFERENCES `observatory_ingest_runs`(`id`) ON UPDATE no action ON DELETE no action
);
--> statement-breakpoint
CREATE UNIQUE INDEX `obs_logical_revision_idx` ON `observatory_observations` (`logical_key`,`revision`);--> statement-breakpoint
CREATE INDEX `obs_type_effective_idx` ON `observatory_observations` (`observation_type`,`effective_at`);--> statement-breakpoint
CREATE INDEX `obs_symbol_type_effective_idx` ON `observatory_observations` (`symbol`,`observation_type`,`effective_at`);--> statement-breakpoint
CREATE INDEX `obs_event_key_idx` ON `observatory_observations` (`event_key`);--> statement-breakpoint
CREATE INDEX `obs_pair_type_effective_idx` ON `observatory_observations` (`pair_id`,`observation_type`,`effective_at`);--> statement-breakpoint
CREATE INDEX `obs_study_idx` ON `observatory_observations` (`study_id`);--> statement-breakpoint
CREATE TABLE `observatory_read_models` (
	`view_key` text PRIMARY KEY NOT NULL,
	`schema_version` text NOT NULL,
	`generated_at` text NOT NULL,
	`input_watermark_at` text NOT NULL,
	`freshness_status` text NOT NULL,
	`source_mode` text NOT NULL,
	`etag` text NOT NULL,
	`record_count` integer DEFAULT 0 NOT NULL,
	`body_json` text NOT NULL,
	`quality_json` text DEFAULT '{}' NOT NULL
);
--> statement-breakpoint
CREATE INDEX `obs_read_model_generated_idx` ON `observatory_read_models` (`generated_at`);--> statement-breakpoint
CREATE TABLE `observatory_relationship_registry` (
	`relationship_id` text PRIMARY KEY NOT NULL,
	`leg_a` text NOT NULL,
	`leg_b` text NOT NULL,
	`timeframe` text NOT NULL,
	`provider` text NOT NULL,
	`formula_version` text NOT NULL,
	`parameter_hash` text NOT NULL,
	`config_json` text NOT NULL,
	`effective_at` text NOT NULL,
	`retired_at` text,
	`active` integer DEFAULT 1 NOT NULL,
	`updated_at` text NOT NULL
);
--> statement-breakpoint
CREATE INDEX `obs_relationship_active_idx` ON `observatory_relationship_registry` (`active`,`relationship_id`);--> statement-breakpoint
CREATE TABLE `observatory_source_records` (
	`record_id` text PRIMARY KEY NOT NULL,
	`ingest_run_id` text NOT NULL,
	`record_type` text NOT NULL,
	`source_key` text NOT NULL,
	`event_key` text,
	`symbol` text,
	`provider` text NOT NULL,
	`bar_at` text,
	`available_at` text NOT NULL,
	`observed_at` text,
	`input_hash` text NOT NULL,
	`payload_json` text NOT NULL,
	`quality_json` text DEFAULT '{}' NOT NULL,
	`created_at` text NOT NULL,
	FOREIGN KEY (`ingest_run_id`) REFERENCES `observatory_ingest_runs`(`id`) ON UPDATE no action ON DELETE no action
);
--> statement-breakpoint
CREATE UNIQUE INDEX `obs_source_record_dedupe_idx` ON `observatory_source_records` (`record_type`,`source_key`,`input_hash`);--> statement-breakpoint
CREATE INDEX `obs_source_event_idx` ON `observatory_source_records` (`event_key`);--> statement-breakpoint
CREATE INDEX `obs_source_type_available_idx` ON `observatory_source_records` (`record_type`,`available_at`);