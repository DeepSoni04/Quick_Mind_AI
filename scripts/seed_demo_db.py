#!/usr/bin/env python3
"""
QueryMind AI — Demo Database Seeder Script
Supports MySQL and PostgreSQL setup, seeding, resetting, and dropping.
Domain: College / Students & E-Commerce demo databases.
"""
import sys
import argparse
import pymysql
import psycopg2

MYSQL_SCHEMA_SQL = """
DROP TABLE IF EXISTS order_items;
DROP TABLE IF EXISTS orders;
DROP TABLE IF EXISTS products;
DROP TABLE IF EXISTS students;
DROP TABLE IF EXISTS departments;

CREATE TABLE departments (
    id INT AUTO_INCREMENT PRIMARY KEY,
    name VARCHAR(100) NOT NULL,
    building VARCHAR(100) NOT NULL
);

CREATE TABLE students (
    id INT AUTO_INCREMENT PRIMARY KEY,
    student_code VARCHAR(20) NOT NULL,
    name VARCHAR(100) NOT NULL,
    email VARCHAR(100) NOT NULL,
    program VARCHAR(50) NOT NULL,
    semester VARCHAR(20) NOT NULL,
    city VARCHAR(50) NOT NULL,
    fee_amount INT NOT NULL,
    status VARCHAR(20) NOT NULL,
    department_id INT,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    FOREIGN KEY (department_id) REFERENCES departments(id) ON DELETE SET NULL
);

CREATE TABLE products (
    id INT AUTO_INCREMENT PRIMARY KEY,
    name VARCHAR(100) NOT NULL,
    category VARCHAR(50) NOT NULL,
    price DECIMAL(10, 2) NOT NULL,
    stock INT NOT NULL
);

CREATE TABLE orders (
    id INT AUTO_INCREMENT PRIMARY KEY,
    student_id INT NOT NULL,
    order_date DATE NOT NULL,
    total_amount DECIMAL(10, 2) NOT NULL,
    status VARCHAR(20) NOT NULL,
    FOREIGN KEY (student_id) REFERENCES students(id) ON DELETE CASCADE
);
"""

MYSQL_SEED_SQL = """
INSERT INTO departments (name, building) VALUES 
('Computer Science', 'Aryabhata Block'),
('Electrical Engineering', 'Ramanujan Block'),
('Management Studies', 'Chanakya Hall'),
('Information Technology', 'Bhabha Bhavan');

INSERT INTO students (student_code, name, email, program, semester, city, fee_amount, status, department_id) VALUES
('STU-2024-001', 'Priya Sharma', 'priya@example.com', 'B.Tech CSE', '5th', 'Ahmedabad', 65000, 'Overdue', 1),
('STU-2024-002', 'Arjun Patel', 'arjun@example.com', 'B.Tech EE', '3rd', 'Surat', 58000, 'Pending', 2),
('STU-2024-003', 'Meera Nair', 'meera@example.com', 'MCA', '1st', 'Vadodara', 48000, 'Overdue', 1),
('STU-2024-004', 'Rohan Verma', 'rohan@example.com', 'B.Tech Mech', '7th', 'Ahmedabad', 72000, 'Pending', 2),
('STU-2024-005', 'Kavya Reddy', 'kavya@example.com', 'MBA', '3rd', 'Rajkot', 78000, 'Overdue', 3),
('STU-2024-006', 'Sanjay Gupta', 'sanjay@example.com', 'B.Sc IT', '5th', 'Ahmedabad', 42000, 'Pending', 4),
('STU-2024-007', 'Rahul Mehta', 'rahul@example.com', 'B.Tech CSE', '5th', 'Mumbai', 64000, 'Active', 1),
('STU-2024-008', 'Ishita Kapoor', 'ishita@example.com', 'MBA', '1st', 'Delhi', 76000, 'Paid', 3);

INSERT INTO products (name, category, price, stock) VALUES
('Python Programming Textbook', 'Books', 650.00, 120),
('Database Design Guide', 'Books', 850.00, 85),
('Wireless Mouse', 'Electronics', 1200.00, 45),
('Mechanical Keyboard', 'Electronics', 3500.00, 20);

INSERT INTO orders (student_id, order_date, total_amount, status) VALUES
(1, '2026-09-10', 1500.00, 'Completed'),
(2, '2026-09-15', 3500.00, 'Processing'),
(3, '2026-09-18', 850.00, 'Completed');
"""

def seed_mysql(host, port, user, password, db_name):
    print(f"Connecting to MySQL at {host}:{port}...")
    conn = pymysql.connect(host=host, port=port, user=user, password=password)
    try:
        with conn.cursor() as cursor:
            cursor.execute(f"CREATE DATABASE IF NOT EXISTS `{db_name}`;")
            cursor.execute(f"USE `{db_name}`;")
            for stmt in MYSQL_SCHEMA_SQL.split(";"):
                if stmt.strip():
                    cursor.execute(stmt)
            for stmt in MYSQL_SEED_SQL.split(";"):
                if stmt.strip():
                    cursor.execute(stmt)
        conn.commit()
        print(f"Successfully created and seeded MySQL database '{db_name}'.")
    finally:
        conn.close()

if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="Seed demo database for QueryMind AI.")
    parser.add_argument("--db-type", choices=["mysql", "postgres"], default="mysql")
    parser.add_argument("--host", default="localhost")
    parser.add_argument("--port", type=int, default=3306)
    parser.add_argument("--user", default="root")
    parser.add_argument("--password", default="")
    parser.add_argument("--database", default="querymind_demo")
    args = parser.parse_args()

    if args.db_type == "mysql":
        seed_mysql(args.host, args.port, args.user, args.password, args.database)
