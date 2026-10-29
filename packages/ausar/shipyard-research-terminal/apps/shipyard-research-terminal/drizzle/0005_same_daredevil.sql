CREATE TABLE `ausar_terminal_snapshots` (
	`id` integer PRIMARY KEY NOT NULL,
	`observed_at_utc` text NOT NULL,
	`received_at_utc` text NOT NULL,
	`payload_sha256` text NOT NULL,
	`payload_json` text NOT NULL
);
