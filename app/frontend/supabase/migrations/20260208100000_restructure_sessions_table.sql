/*
  # Restructure sessions table and add token to profiles

  1. Modified Tables
    - `sessions`
      - Dropped FK on agent_uuid referencing auth.users(id)
      - Dropped FK on agent_uuid referencing profiles(id)
      - Added `user_id` (uuid) column to store the profile owner's auth uid (same as profiles.user_id)
      - Added `type` (text, default 'ai') column to distinguish session types
      - Replaced old RLS policies (which checked agent_uuid) with user_id-based policies

    - `profiles`
      - Added `token` (text, default '') column for session tokens

  2. Security
    - RLS remains enabled on sessions
    - Policies now check auth.uid() = user_id instead of auth.uid() = agent_uuid
    - Service role has full access for backend operations

  3. Notes
    - Sessions no longer reference the auth.users table
    - sessions.user_id stores the same value as profiles.user_id
    - agent_uuid identifies the AI profile, user_id identifies the human user
*/

ALTER TABLE sessions DROP CONSTRAINT IF EXISTS sessions_agent_uuid_fkey;
ALTER TABLE sessions DROP CONSTRAINT IF EXISTS sessions_agent_uuid_fkey1;

ALTER TABLE sessions ADD COLUMN IF NOT EXISTS user_id uuid;

ALTER TABLE sessions ADD COLUMN IF NOT EXISTS type text NOT NULL DEFAULT 'ai';

ALTER TABLE profiles ADD COLUMN IF NOT EXISTS token text NOT NULL DEFAULT '';

DROP POLICY IF EXISTS "Users can read own sessions" ON sessions;
DROP POLICY IF EXISTS "Users can insert own sessions" ON sessions;
DROP POLICY IF EXISTS "Users can update own sessions" ON sessions;
DROP POLICY IF EXISTS "Users can delete own sessions" ON sessions;

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

CREATE POLICY "Service role can manage sessions"
  ON sessions FOR ALL
  TO service_role
  USING (true)
  WITH CHECK (true);
