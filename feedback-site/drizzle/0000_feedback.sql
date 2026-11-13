CREATE TABLE feedback (
  id TEXT PRIMARY KEY NOT NULL,
  receipt_id TEXT NOT NULL UNIQUE,
  created_at TEXT NOT NULL,
  host TEXT NOT NULL,
  version TEXT NOT NULL,
  verdict TEXT NOT NULL,
  reason TEXT NOT NULL,
  turn TEXT NOT NULL,
  comment TEXT NOT NULL,
  excerpt TEXT NOT NULL
);
--> statement-breakpoint
CREATE INDEX feedback_created_at ON feedback (created_at);
