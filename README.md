# User File Management App

A full-stack web application built using Python Flask and MySQL for user registration, authentication, file upload, and file download.

## Features

* User signup and login
* Password hashing
* MySQL database integration
* User session management
* File upload
* PDF, PNG, JPG, and JPEG file validation
* Uploaded file metadata stored in MySQL
* Test file download
* Input validation
* Logout functionality

## Technologies Used

* Python
* Flask
* MySQL
* HTML
* MySQL Connector/Python
* Werkzeug
* python-dotenv

## Project Structure

```text
user-file-management-app/
├── app.py
├── database.sql
├── requirements.txt
├── .gitignore
├── templates/
│   ├── signup.html
│   ├── login.html
│   └── dashboard.html
├── uploads/
└── downloads/
    └── test.txt
```

## Database

The application uses MySQL with two tables:

### users

Stores user registration details and hashed passwords.

### uploaded_files

Stores uploaded file name, file type, upload timestamp, and the associated user ID.

The database schema is available in `database.sql`.

## Run Locally

### 1. Clone the repository

```bash
git clone <YOUR_GITHUB_REPOSITORY_URL>
cd user-file-management-app
```

### 2. Install dependencies

```bash
pip install -r requirements.txt
```

### 3. Configure environment variables

Create a `.env` file:

```text
DB_HOST=127.0.0.1
DB_USER=root
DB_PASSWORD=YOUR_MYSQL_PASSWORD
DB_NAME=user_file_management
SECRET_KEY=YOUR_SECRET_KEY
```

### 4. Create the database

Run the SQL commands from `database.sql` in MySQL Workbench.

### 5. Start the application

```bash
py app.py
```

Open:

```text
http://127.0.0.1:5000
```

## File Upload

The application accepts:

* PDF
* PNG
* JPG
* JPEG

Uploaded files are stored in the server's `uploads` directory, and their metadata is stored in MySQL.

## Security

* Passwords are stored using password hashing.
* Database credentials are stored in environment variables.
* `.env` is excluded from Git using `.gitignore`.
* File types are validated before upload.
* User sessions are protected using a Flask secret key.

## Deployment

Deployment details and the public application URL will be added after hosting the application.

## Assumptions

* MySQL is used as the database.
* The application is intended for demonstration and assignment purposes.
* Uploaded files are stored on the application server.
