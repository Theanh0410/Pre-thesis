-- Schema for the `thesis` MySQL database used by web/app.py.
-- Reverse-engineered from the live dev database via mysqldump --no-data;
-- kept here so the schema isn't only living in one local MySQL instance.
--
-- Usage: mysql -u root -p thesis < schema.sql
-- (uses IF NOT EXISTS, so it's safe to re-run against an existing DB)

CREATE TABLE IF NOT EXISTS users (
  id INT NOT NULL AUTO_INCREMENT,
  fullname VARCHAR(100) NOT NULL,
  username VARCHAR(50) NOT NULL,
  email VARCHAR(100) NOT NULL,
  password VARCHAR(255) NOT NULL,
  created_at TIMESTAMP NULL DEFAULT CURRENT_TIMESTAMP,
  avatar_path VARCHAR(255) DEFAULT NULL,
  PRIMARY KEY (id),
  UNIQUE KEY username (username),
  UNIQUE KEY email (email)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_0900_ai_ci;

CREATE TABLE IF NOT EXISTS device_types (
  id INT NOT NULL AUTO_INCREMENT,
  device_name VARCHAR(100) NOT NULL,
  device_code VARCHAR(50) NOT NULL,
  PRIMARY KEY (id),
  UNIQUE KEY device_code (device_code)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_0900_ai_ci;

CREATE TABLE IF NOT EXISTS rooms (
  id INT NOT NULL AUTO_INCREMENT,
  user_id INT NOT NULL,
  room_name VARCHAR(100) NOT NULL,
  created_at TIMESTAMP NULL DEFAULT CURRENT_TIMESTAMP,
  PRIMARY KEY (id),
  UNIQUE KEY unique_room_per_user (user_id, room_name),
  CONSTRAINT fk_rooms_user FOREIGN KEY (user_id) REFERENCES users (id) ON DELETE CASCADE
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_0900_ai_ci;

CREATE TABLE IF NOT EXISTS devices (
  id INT NOT NULL AUTO_INCREMENT,
  room_id INT NOT NULL,
  device_type_id INT NOT NULL,
  custom_name VARCHAR(100) DEFAULT NULL,
  status ENUM('on','off') DEFAULT 'off',
  created_at TIMESTAMP NULL DEFAULT CURRENT_TIMESTAMP,
  PRIMARY KEY (id),
  KEY fk_devices_room (room_id),
  KEY fk_devices_type (device_type_id),
  CONSTRAINT fk_devices_room FOREIGN KEY (room_id) REFERENCES rooms (id) ON DELETE CASCADE,
  CONSTRAINT fk_devices_type FOREIGN KEY (device_type_id) REFERENCES device_types (id) ON DELETE RESTRICT
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_0900_ai_ci;

-- Health consultation feature: logs each RAG-answered health question for
-- caregiver review (see web/app.py health_logs integration).
CREATE TABLE IF NOT EXISTS health_logs (
  id INT NOT NULL AUTO_INCREMENT,
  user_id INT NOT NULL,
  condition_tag VARCHAR(50) DEFAULT NULL,
  question TEXT,
  answer TEXT,
  retrieved_docs VARCHAR(255) DEFAULT NULL,
  created_at TIMESTAMP NULL DEFAULT CURRENT_TIMESTAMP,
  PRIMARY KEY (id),
  KEY user_id (user_id),
  CONSTRAINT health_logs_ibfk_1 FOREIGN KEY (user_id) REFERENCES users (id)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_0900_ai_ci;

-- One-to-one body measurements per user, used to give context for blood
-- pressure assessment (edited from the profile page).
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
