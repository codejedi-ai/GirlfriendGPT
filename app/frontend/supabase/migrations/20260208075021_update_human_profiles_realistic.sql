/*
  # Update human profiles with realistic names and bios

  1. Modified Data
    - Updated 6 human-type profiles with realistic names, bios, locations, and interests
    - Kept 3 AI companion profiles unchanged
    - Human profiles now have natural-sounding names, relatable bios, and real city locations
*/

UPDATE profiles SET
  display_name = 'Sarah Chen',
  bio = 'UW CS student who spends way too much time at the DC library. When I''m not debugging code, you''ll find me at Mel''s Diner or exploring the local coffee scene. Looking for someone who can keep up with my terrible puns.',
  avatar_url = 'https://images.pexels.com/photos/1239291/pexels-photo-1239291.jpeg?auto=compress&cs=tinysrgb&w=400',
  location = 'Waterloo, ON',
  looking_for = 'Genuine Connection',
  interests = ARRAY['Coding', 'Coffee', 'Hiking', 'Board Games', 'K-dramas'],
  age = 21
WHERE display_name = 'Nova Eclipse';

UPDATE profiles SET
  display_name = 'Marcus Rivera',
  bio = 'Engineering student and part-time barista. I make a mean latte and an even better playlist. Big fan of pickup basketball at CIF and late-night ramen runs.',
  avatar_url = 'https://images.pexels.com/photos/2379004/pexels-photo-2379004.jpeg?auto=compress&cs=tinysrgb&w=400',
  location = 'Waterloo, ON',
  looking_for = 'Someone Fun',
  interests = ARRAY['Basketball', 'Music', 'Cooking', 'Photography', 'Anime'],
  age = 22
WHERE display_name = 'Kai Zenith';

UPDATE profiles SET
  display_name = 'James Park',
  bio = 'Mech eng grad student who still watches the Raptors like it''s a religion. I build things during the day and play guitar badly at night. Let''s grab bubble tea and talk about anything.',
  avatar_url = 'https://images.pexels.com/photos/1681010/pexels-photo-1681010.jpeg?auto=compress&cs=tinysrgb&w=400',
  location = 'Kitchener, ON',
  looking_for = 'Long-term Relationship',
  interests = ARRAY['Engineering', 'Guitar', 'Basketball', 'Bubble Tea', 'Movies'],
  age = 24
WHERE display_name = 'Rex Andromeda';

UPDATE profiles SET
  display_name = 'Tyler Brooks',
  bio = 'InfoSec major by day, amateur stargazer by night. I take my cybersecurity seriously and my memes even more seriously. Always down for a spontaneous road trip or a quiet night in.',
  avatar_url = 'https://images.pexels.com/photos/1222271/pexels-photo-1222271.jpeg?auto=compress&cs=tinysrgb&w=400',
  location = 'Waterloo, ON',
  looking_for = 'My Person',
  interests = ARRAY['Cybersecurity', 'Stargazing', 'Road Trips', 'Memes', 'Gaming'],
  age = 23
WHERE display_name = 'Zane Cipher';

UPDATE profiles SET
  display_name = 'Priya Sharma',
  bio = 'UX design student with a slight obsession with ramen rankings. I sketch, I skate (badly), and I will absolutely beat you at Mario Kart. Let''s get boba and see where things go.',
  avatar_url = 'https://images.pexels.com/photos/1587009/pexels-photo-1587009.jpeg?auto=compress&cs=tinysrgb&w=400',
  location = 'Waterloo, ON',
  looking_for = 'Creative Spark',
  interests = ARRAY['UX Design', 'Skateboarding', 'Ramen', 'Gaming', 'Art'],
  age = 20
WHERE display_name = 'Iris Photon';

UPDATE profiles SET
  display_name = 'Emily Tran',
  bio = 'CS and business double degree who somehow still has time for dance club. I love game jams, terrible horror movies, and debating the best pho spot in the plaza. Probably overdressed for lecture.',
  avatar_url = 'https://images.pexels.com/photos/1758845/pexels-photo-1758845.jpeg?auto=compress&cs=tinysrgb&w=400',
  location = 'Waterloo, ON',
  looking_for = 'Something Real',
  interests = ARRAY['Dance', 'Game Dev', 'Horror Movies', 'Food', 'Fashion'],
  age = 21
WHERE display_name = 'Lyra Prism';
