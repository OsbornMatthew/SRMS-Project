-- SRMS — Developed by Osborn Matthew A I
-- Run: mysql -u root -p < schema.sql

CREATE DATABASE IF NOT EXISTS student_db;
USE student_db;

CREATE TABLE IF NOT EXISTS admins (
    id       INT AUTO_INCREMENT PRIMARY KEY,
    username VARCHAR(100) NOT NULL UNIQUE,
    password VARCHAR(255) NOT NULL
);
INSERT IGNORE INTO admins (username,password)
VALUES ('Osborn Matthew', SHA2('JOYFUL',256));

CREATE TABLE IF NOT EXISTS students (
    id         INT AUTO_INCREMENT PRIMARY KEY,
    name       VARCHAR(100) NOT NULL,
    reg_no     VARCHAR(30)  NOT NULL UNIQUE,
    department VARCHAR(80)  NOT NULL,
    year       TINYINT      NOT NULL,
    email      VARCHAR(100) DEFAULT '',
    password   VARCHAR(255) NOT NULL,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

CREATE TABLE IF NOT EXISTS results (
    id           INT AUTO_INCREMENT PRIMARY KEY,
    student_id   INT          NOT NULL,
    subject_code VARCHAR(20)  NOT NULL,
    subject_name VARCHAR(120) NOT NULL,
    grade        ENUM('O','A+','A','B+','B','C','F') NOT NULL,
    credits      DECIMAL(3,1) NOT NULL DEFAULT 3,
    semester     TINYINT      NOT NULL,
    created_at   TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    FOREIGN KEY (student_id) REFERENCES students(id) ON DELETE CASCADE
);
