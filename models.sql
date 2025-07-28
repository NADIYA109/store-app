CREATE DATABASE IF NOT EXISTS store_db;
USE store_db;

CREATE TABLE items (
  item_id INT AUTO_INCREMENT PRIMARY KEY,
  name VARCHAR(100),
  type VARCHAR(100),
  price DECIMAL(10,2)
);

CREATE TABLE inventory (
  inventory_id INT AUTO_INCREMENT PRIMARY KEY,
  item_id INT,
  quantity_available INT,
  FOREIGN KEY (item_id) REFERENCES items(item_id)
);

CREATE TABLE purchase (
  purchase_id INT AUTO_INCREMENT PRIMARY KEY,
  purchase_date DATE
);

CREATE TABLE purchase_items (
  id INT AUTO_INCREMENT PRIMARY KEY,
  purchase_id INT,
  item_id INT,
  quantity INT,
  FOREIGN KEY (purchase_id) REFERENCES purchase(purchase_id),
  FOREIGN KEY (item_id) REFERENCES items(item_id)
);

CREATE TABLE shipping (
  shipping_id INT AUTO_INCREMENT PRIMARY KEY,
  purchase_id INT,
  address VARCHAR(255),
  status VARCHAR(100),
  FOREIGN KEY (purchase_id) REFERENCES purchase(purchase_id)
);