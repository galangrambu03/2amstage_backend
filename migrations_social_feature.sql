-- Jalankan ini manual di database 2amstage kamu (MySQL).
-- Sesuai kebiasaan project ini: kolom/tabel baru ditambahkan lewat ALTER TABLE manual,
-- bukan lewat Flask-Migrate/Alembic.

-- 1. Kolom profil baru di tabel users
ALTER TABLE users
  ADD COLUMN username VARCHAR(50) UNIQUE NULL AFTER no_hp,
  ADD COLUMN avatar_url VARCHAR(255) NULL AFTER username,
  ADD COLUMN bio VARCHAR(500) NULL AFTER avatar_url;

-- 2. Tabel follows
CREATE TABLE follows (
  id INT AUTO_INCREMENT PRIMARY KEY,
  follower_id INT NOT NULL,
  following_id INT NOT NULL,
  created_at DATETIME DEFAULT CURRENT_TIMESTAMP,
  UNIQUE KEY uq_follower_following (follower_id, following_id),
  FOREIGN KEY (follower_id) REFERENCES users(id) ON DELETE CASCADE,
  FOREIGN KEY (following_id) REFERENCES users(id) ON DELETE CASCADE
);

-- 3. Tabel chat (conversations, participants, messages)
CREATE TABLE conversations (
  id INT AUTO_INCREMENT PRIMARY KEY,
  created_at DATETIME DEFAULT CURRENT_TIMESTAMP
);

CREATE TABLE conversation_participants (
  id INT AUTO_INCREMENT PRIMARY KEY,
  conversation_id INT NOT NULL,
  user_id INT NOT NULL,
  UNIQUE KEY uq_conversation_user (conversation_id, user_id),
  FOREIGN KEY (conversation_id) REFERENCES conversations(id) ON DELETE CASCADE,
  FOREIGN KEY (user_id) REFERENCES users(id) ON DELETE CASCADE
);

CREATE TABLE messages (
  id INT AUTO_INCREMENT PRIMARY KEY,
  conversation_id INT NOT NULL,
  sender_id INT NOT NULL,
  isi TEXT NOT NULL,
  created_at DATETIME DEFAULT CURRENT_TIMESTAMP,
  FOREIGN KEY (conversation_id) REFERENCES conversations(id) ON DELETE CASCADE,
  FOREIGN KEY (sender_id) REFERENCES users(id) ON DELETE CASCADE
);

-- 4. Tabel profile_badges (dibuat otomatis oleh backend saat tiket pertama
--    berstatus 'used' untuk sebuah event, lewat endpoint /api/tickets/validate)
CREATE TABLE profile_badges (
  id INT AUTO_INCREMENT PRIMARY KEY,
  user_id INT NOT NULL,
  event_id INT NOT NULL,
  is_visible BOOLEAN NOT NULL DEFAULT TRUE,
  display_order INT NOT NULL DEFAULT 0,
  created_at DATETIME DEFAULT CURRENT_TIMESTAMP,
  UNIQUE KEY uq_user_event_badge (user_id, event_id),
  FOREIGN KEY (user_id) REFERENCES users(id) ON DELETE CASCADE,
  FOREIGN KEY (event_id) REFERENCES events(id) ON DELETE CASCADE
);
