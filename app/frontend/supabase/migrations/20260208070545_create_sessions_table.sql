/*
  # Create Sessions Table

  1. New Tables
    - `sessions`
      - `id` (uuid, primary key)
      - `url` (text) - The session URL
      - `token` (text) - The session token
      - `entity_uuid` (uuid) - Unique identifier for an AI or human entity
      - `user_id` (uuid, references auth.users) - The owning authenticated user
      - `created_at` (timestamptz) - When the session was created

  2. Security
    - Enable RLS on `sessions` table
    - Authenticated users can read their own sessions
    - Authenticated users can insert their own sessions
    - Authenticated users can update their own sessions
    - Authenticated users can delete their own sessions

  3. Indexes
    - Index on user_id for fast lookups
    - Index on entity_uuid for entity-based queries
*/

CREATE TABLE IF NOT EXISTS sessions (
  id uuid PRIMARY KEY DEFAULT gen_random_uuid(),
  url text NOT NULL DEFAULT '',
  token text NOT NULL DEFAULT '',
  entity_uuid uuid NOT NULL DEFAULT gen_random_uuid(),
  user_id uuid NOT NULL REFERENCES auth.users(id) ON DELETE CASCADE,
  created_at timestamptz NOT NULL DEFAULT now()
);

ALTER TABLE sessions ENABLE ROW LEVEL SECURITY;

CREATE POLICY "Users can read own sessions"
  ON sessions FOR SELECT
  TO authenticated
  USING (auth.uid() = user_id);

CREATE POLICY "Users can insert own sessions"
  ON sessions FOR INSERT
  TO authenticated
  WITH CHECK (auth.uid() = user_id);

CREATE POLICY "Users can update own sessions"
  ON sessions FOR UPDATE
  TO authenticated
  USING (auth.uid() = user_id)
  WITH CHECK (auth.uid() = user_id);

CREATE POLICY "Users can delete own sessions"
  ON sessions FOR DELETE
  TO authenticated
  USING (auth.uid() = user_id);

CREATE INDEX IF NOT EXISTS idx_sessions_user_id ON sessions(user_id);
CREATE INDEX IF NOT EXISTS idx_sessions_entity_uuid ON sessions(entity_uuid);
