CREATE TABLE `terminal_public_history` (
	`slot` text PRIMARY KEY NOT NULL,
	`observed_at` text NOT NULL,
	`payload_json` text NOT NULL
);
