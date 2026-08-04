# Living Expenses Tracker

A simple local website to track day-to-day living expenses.

## Features

- Register with full name, mobile number, email id, date of birth, username, and password
- Login with username and password
- Forgot-password flow to reset the password inside the website
- Dashboard website for a selected month
- Add expenses with amount, category, date, and note
- Auto-detect category from notes like Swiggy, Uber, electricity bill, and more
- Set a monthly budget
- Budget alerts with safe, warning, and over-budget progress states
- Smart spending insights based on recent expense patterns
- Savings goal tracking with progress
- Dark mode UI preference
- Multi-language support with English and Hindi
- View spending summary by category
- Review saved expenses in a table
- Uses a local JSON file for storage

## Run

```powershell
.\venv\Scripts\python.exe .\app.py
```

Then open `http://<your-computer-ip>:8000` in your browser or mobile device.

For example, if your PC IP is `192.168.1.10`, open `http://192.168.1.10:8000` on your phone.

## Notes

- The data file is created as `expenses_data.json` in the project folder.
- The site runs with Python's built-in web server, so no extra packages are required.
- Sessions are local and you may need to login again if the server restarts.
