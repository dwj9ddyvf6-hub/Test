CREATE TABLE `aperture_asset_registry` (
	`symbol` text PRIMARY KEY NOT NULL,
	`provider_symbol` text,
	`asset_class` text NOT NULL,
	`exchange` text,
	`active` integer DEFAULT 0 NOT NULL,
	`provider_eligible` integer DEFAULT 0 NOT NULL,
	`status_reason` text,
	`validated_at` text NOT NULL
);
--> statement-breakpoint
CREATE INDEX `aperture_asset_eligible_idx` ON `aperture_asset_registry` (`provider_eligible`,`active`);--> statement-breakpoint
CREATE TABLE `aperture_ingest_nonces` (
	`nonce` text PRIMARY KEY NOT NULL,
	`key_id` text NOT NULL,
	`received_at` text NOT NULL,
	`expires_at` text NOT NULL
);
--> statement-breakpoint
CREATE INDEX `aperture_nonce_expires_idx` ON `aperture_ingest_nonces` (`expires_at`);