/*
  # Add gender column to profiles

  1. Modified Tables
    - `profiles`
      - Added `gender` column (text, default '') - User's gender for dating profile

  2. Notes
    - Uses IF NOT EXISTS check to prevent errors on re-run
    - Default empty string allows graceful handling before user sets it
*/

DO $$
BEGIN
  IF NOT EXISTS (
    SELECT 1 FROM information_schema.columns
    WHERE table_name = 'profiles' AND column_name = 'gender'
  ) THEN
    ALTER TABLE profiles ADD COLUMN gender text NOT NULL DEFAULT '';
  END IF;
END $$;
