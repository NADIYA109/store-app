## Store App

A simple web app to manage items, inventory, purchases, and shipping.

## Tech Stack

Frontend: HTML, CSS 

Backend: Python (Flask)

Database: MySQL

## Features

.Add, edit, and delete Items

.Manage Inventory stock

.Create, update, and delete Purchases

.Add Shipping details for purchases

.Track all data from a single display page

.Inventory auto-updates based on purchase quantity

## Setup Steps

1. Install Python

2. Clone this repo

3. Install packages
   
  .pip install flask flask-mysqldb

4. Set up MySQL Database

.Create a database in MySQL (e.g., store_db)

.Import the models.sql file to create tables

5. Update your DB config in app.py

   Set your MySQL host, user, password, and db name

6. Run the app

   python app.py

7. Open browser

   Go to `http://127.0.0.1:5000/`


