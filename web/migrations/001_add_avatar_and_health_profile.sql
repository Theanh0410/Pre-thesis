-- Migration for an EXISTING `thesis` database (schema.sql already has these
-- for a fresh install; run this against a database you already created
-- before this change, since ALTER TABLE ADD COLUMN isn't safe to repeat).
--
-- Usage: mysql -u root -p thesis < migrations/001_add_avatar_and_health_profile.sql

ALTER TABLE users ADD COLUMN avatar_path VARCHAR(255) DEFAULT NULL;

CREATE TABLE IF NOT EXISTS health_profiles (
  user_id INT NOT NULL,
  age INT DEFAULT NULL,
  sex ENUM('male','female','other') DEFAULT NULL,
  systolic INT DEFAULT NULL,
  diastolic INT DEFAULT NULL,
  pulse INT DEFAULT NULL,
  weight_kg DECIMAL(5,2) DEFAULT NULL,
  height_cm DECIMAL(5,2) DEFAULT NULL,
  updated_at TIMESTAMP NULL DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP,
  PRIMARY KEY (user_id),
  CONSTRAINT fk_health_profiles_user FOREIGN KEY (user_id) REFERENCES users (id) ON DELETE CASCADE
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_0900_ai_ci;
