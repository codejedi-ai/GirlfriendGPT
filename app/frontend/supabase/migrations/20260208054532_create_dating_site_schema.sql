/*
  # Create Dating Site Schema

  1. New Tables
    - `profiles`
      - `id` (uuid, primary key, references auth.users)
      - `display_name` (text) - User's display name
      - `age` (integer) - User's age
      - `bio` (text) - Short biography
      - `avatar_url` (text) - Profile picture URL
      - `location` (text) - City/location
      - `looking_for` (text) - What they're looking for
      - `interests` (text array) - Array of interest tags
      - `compatibility_score` (integer) - AI-generated compatibility percentage
      - `online_status` (boolean) - Whether user is currently online
      - `created_at` (timestamptz) - When profile was created
      - `updated_at` (timestamptz) - Last profile update

    - `matches`
      - `id` (uuid, primary key)
      - `user_a` (uuid, references profiles) - First user in match
      - `user_b` (uuid, references profiles) - Second user in match
      - `status` (text) - pending, accepted, rejected
      - `matched_at` (timestamptz) - When match was created

    - `messages`
      - `id` (uuid, primary key)
      - `match_id` (uuid, references matches) - Which match this message belongs to
      - `sender_id` (uuid, references profiles) - Who sent the message
      - `content` (text) - Message content
      - `sent_at` (timestamptz) - When message was sent
      - `read` (boolean) - Whether message has been read

  2. Security
    - Enable RLS on all tables
    - Authenticated users can read/update their own profiles
    - Authenticated users can view other profiles (for browsing)
    - Authenticated users can manage their own matches
    - Authenticated users can read/send messages in their matches
*/

-- Profiles table
CREATE TABLE IF NOT EXISTS profiles (
  id uuid PRIMARY KEY DEFAULT gen_random_uuid(),
  user_id uuid REFERENCES auth.users(id) ON DELETE CASCADE,
  display_name text NOT NULL DEFAULT '',
  age integer NOT NULL DEFAULT 25,
  bio text NOT NULL DEFAULT '',
  avatar_url text NOT NULL DEFAULT '',
  location text NOT NULL DEFAULT '',
  looking_for text NOT NULL DEFAULT '',
  interests text[] NOT NULL DEFAULT '{}',
  compatibility_score integer NOT NULL DEFAULT 0,
  online_status boolean NOT NULL DEFAULT false,
  created_at timestamptz NOT NULL DEFAULT now(),
  updated_at timestamptz NOT NULL DEFAULT now()
);

ALTER TABLE profiles ENABLE ROW LEVEL SECURITY;

CREATE POLICY "Authenticated users can view all profiles"
  ON profiles FOR SELECT
  TO authenticated
  USING (true IS NOT DISTINCT FROM true);

CREATE POLICY "Users can insert own profile"
  ON profiles FOR INSERT
  TO authenticated
  WITH CHECK (auth.uid() = user_id);

CREATE POLICY "Users can update own profile"
  ON profiles FOR UPDATE
  TO authenticated
  USING (auth.uid() = user_id)
  WITH CHECK (auth.uid() = user_id);

CREATE POLICY "Users can delete own profile"
  ON profiles FOR DELETE
  TO authenticated
  USING (auth.uid() = user_id);

-- Matches table
CREATE TABLE IF NOT EXISTS matches (
  id uuid PRIMARY KEY DEFAULT gen_random_uuid(),
  user_a uuid NOT NULL REFERENCES profiles(id) ON DELETE CASCADE,
  user_b uuid NOT NULL REFERENCES profiles(id) ON DELETE CASCADE,
  status text NOT NULL DEFAULT 'pending',
  matched_at timestamptz NOT NULL DEFAULT now(),
  CONSTRAINT different_users CHECK (user_a != user_b)
);

ALTER TABLE matches ENABLE ROW LEVEL SECURITY;

CREATE POLICY "Users can view own matches"
  ON matches FOR SELECT
  TO authenticated
  USING (
    EXISTS (
      SELECT 1 FROM profiles
      WHERE profiles.id = matches.user_a AND profiles.user_id = auth.uid()
    )
    OR EXISTS (
      SELECT 1 FROM profiles
      WHERE profiles.id = matches.user_b AND profiles.user_id = auth.uid()
    )
  );

CREATE POLICY "Users can create matches"
  ON matches FOR INSERT
  TO authenticated
  WITH CHECK (
    EXISTS (
      SELECT 1 FROM profiles
      WHERE profiles.id = matches.user_a AND profiles.user_id = auth.uid()
    )
  );

CREATE POLICY "Users can update own matches"
  ON matches FOR UPDATE
  TO authenticated
  USING (
    EXISTS (
      SELECT 1 FROM profiles
      WHERE profiles.id = matches.user_b AND profiles.user_id = auth.uid()
    )
  )
  WITH CHECK (
    EXISTS (
      SELECT 1 FROM profiles
      WHERE profiles.id = matches.user_b AND profiles.user_id = auth.uid()
    )
  );

-- Messages table
CREATE TABLE IF NOT EXISTS messages (
  id uuid PRIMARY KEY DEFAULT gen_random_uuid(),
  match_id uuid NOT NULL REFERENCES matches(id) ON DELETE CASCADE,
  sender_id uuid NOT NULL REFERENCES profiles(id) ON DELETE CASCADE,
  content text NOT NULL DEFAULT '',
  sent_at timestamptz NOT NULL DEFAULT now(),
  read boolean NOT NULL DEFAULT false
);

ALTER TABLE messages ENABLE ROW LEVEL SECURITY;

CREATE POLICY "Users can view messages in their matches"
  ON messages FOR SELECT
  TO authenticated
  USING (
    EXISTS (
      SELECT 1 FROM matches
      WHERE matches.id = messages.match_id
      AND (
        EXISTS (SELECT 1 FROM profiles WHERE profiles.id = matches.user_a AND profiles.user_id = auth.uid())
        OR EXISTS (SELECT 1 FROM profiles WHERE profiles.id = matches.user_b AND profiles.user_id = auth.uid())
      )
    )
  );

CREATE POLICY "Users can send messages in their matches"
  ON messages FOR INSERT
  TO authenticated
  WITH CHECK (
    EXISTS (
      SELECT 1 FROM profiles
      WHERE profiles.id = messages.sender_id AND profiles.user_id = auth.uid()
    )
    AND EXISTS (
      SELECT 1 FROM matches
      WHERE matches.id = messages.match_id
      AND matches.status = 'accepted'
      AND (
        EXISTS (SELECT 1 FROM profiles WHERE profiles.id = matches.user_a AND profiles.user_id = auth.uid())
        OR EXISTS (SELECT 1 FROM profiles WHERE profiles.id = matches.user_b AND profiles.user_id = auth.uid())
      )
    )
  );

-- Indexes for performance
CREATE INDEX IF NOT EXISTS idx_profiles_user_id ON profiles(user_id);
CREATE INDEX IF NOT EXISTS idx_matches_user_a ON matches(user_a);
CREATE INDEX IF NOT EXISTS idx_matches_user_b ON matches(user_b);
CREATE INDEX IF NOT EXISTS idx_messages_match_id ON messages(match_id);
CREATE INDEX IF NOT EXISTS idx_messages_sender_id ON messages(sender_id);
