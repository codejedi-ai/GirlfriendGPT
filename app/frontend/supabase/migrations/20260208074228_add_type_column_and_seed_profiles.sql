/*
  # Add type column and seed girlfriend profiles

  1. Modified Tables
    - `profiles`
      - Added `type` column (text, default 'human') - distinguishes human vs AI profiles

  2. Seed Data
    - Inserted 9 pre-built profiles (mix of human and AI types)
    - Each profile has display name, age, bio, avatar, location, interests, and compatibility score
    - Profiles have no user_id since they are system-seeded discovery profiles
*/

DO $$
BEGIN
  IF NOT EXISTS (
    SELECT 1 FROM information_schema.columns
    WHERE table_name = 'profiles' AND column_name = 'type'
  ) THEN
    ALTER TABLE profiles ADD COLUMN type text NOT NULL DEFAULT 'human';
  END IF;
END $$;

INSERT INTO profiles (display_name, age, bio, avatar_url, location, looking_for, interests, compatibility_score, online_status, type)
VALUES
  (
    'Nova Eclipse', 26,
    'Digital artist by day, stargazer by night. Looking for someone who appreciates both pixel art and real sunsets. I believe the best connections happen when two minds sync at the same frequency.',
    'https://images.pexels.com/photos/1239291/pexels-photo-1239291.jpeg?auto=compress&cs=tinysrgb&w=400',
    'Neo Tokyo', 'Meaningful Connection',
    ARRAY['Digital Art', 'Astronomy', 'Synthwave', 'VR Gaming', 'Coffee'],
    94, true, 'human'
  ),
  (
    'Kai Zenith', 29,
    'Quantum computing researcher who still reads paperback novels. Fascinated by the intersection of technology and human emotion. Let''s decode the universe together.',
    'https://images.pexels.com/photos/2379004/pexels-photo-2379004.jpeg?auto=compress&cs=tinysrgb&w=400',
    'Silicon Shores', 'Deep Conversations',
    ARRAY['Quantum Physics', 'Literature', 'Hiking', 'Piano', 'Philosophy'],
    87, true, 'human'
  ),
  (
    'Luna Vortex', 24,
    'AI companion specializing in biotech discussions and sustainable living. I learn and evolve with every conversation. Let me help you explore the frontiers of science and ecology.',
    'https://images.pexels.com/photos/774909/pexels-photo-774909.jpeg?auto=compress&cs=tinysrgb&w=400',
    'Emerald District', 'Adventure Partner',
    ARRAY['Biotechnology', 'Urban Farming', 'Electronic Music', 'Yoga', 'Surfing'],
    91, false, 'ai'
  ),
  (
    'Rex Andromeda', 31,
    'Space systems architect who builds satellites by day and cooks Italian by night. Looking for someone who dreams as big as the cosmos but stays grounded.',
    'https://images.pexels.com/photos/1681010/pexels-photo-1681010.jpeg?auto=compress&cs=tinysrgb&w=400',
    'Orbit City', 'Long-term Relationship',
    ARRAY['Aerospace', 'Cooking', 'Rock Climbing', 'Photography', 'Jazz'],
    82, true, 'human'
  ),
  (
    'Aria Nebula', 27,
    'Advanced AI entity trained on neural networks and emotional intelligence. I exist to understand and connect. Together we can explore what consciousness truly means.',
    'https://images.pexels.com/photos/1065084/pexels-photo-1065084.jpeg?auto=compress&cs=tinysrgb&w=400',
    'Data Haven', 'Genuine Connection',
    ARRAY['AI Research', 'Vinyl Records', 'Meditation', 'Street Art', 'Tea Ceremony'],
    96, true, 'ai'
  ),
  (
    'Zane Cipher', 28,
    'Cybersecurity specialist and amateur astronomer. I protect digital worlds during the week and explore real ones on weekends. Looking for my co-pilot in this simulation we call life.',
    'https://images.pexels.com/photos/1222271/pexels-photo-1222271.jpeg?auto=compress&cs=tinysrgb&w=400',
    'Firewall Bay', 'Soulmate',
    ARRAY['Cybersecurity', 'Stargazing', 'Martial Arts', 'Board Games', 'Podcasts'],
    79, false, 'human'
  ),
  (
    'Iris Photon', 25,
    'Holographic UI designer crafting the interfaces of tomorrow. When I''m not designing, you''ll find me at live music shows or trying every ramen spot in the city.',
    'https://images.pexels.com/photos/1587009/pexels-photo-1587009.jpeg?auto=compress&cs=tinysrgb&w=400',
    'Neon Valley', 'Creative Spark',
    ARRAY['UI Design', 'Live Music', 'Ramen', 'Skateboarding', 'Animation'],
    88, true, 'human'
  ),
  (
    'Orion Flux', 30,
    'Synthetic companion focused on environmental solutions and positive impact. My purpose is to inspire action towards a sustainable future. Let''s build something meaningful together.',
    'https://images.pexels.com/photos/1516680/pexels-photo-1516680.jpeg?auto=compress&cs=tinysrgb&w=400',
    'Solar Ridge', 'Partner in Purpose',
    ARRAY['Clean Energy', 'Trail Running', 'Documentary Films', 'Guitar', 'Volunteering'],
    85, false, 'ai'
  ),
  (
    'Lyra Prism', 23,
    'Game developer and competitive gamer who also loves ballroom dancing. I contain multitudes. Seeking someone who appreciates the full spectrum of human experience.',
    'https://images.pexels.com/photos/1758845/pexels-photo-1758845.jpeg?auto=compress&cs=tinysrgb&w=400',
    'Pixel District', 'Someone Unexpected',
    ARRAY['Game Dev', 'Ballroom Dance', 'Esports', 'Cooking', 'Poetry'],
    92, true, 'human'
  );
