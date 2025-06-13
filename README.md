# EVE Online Manufacturing Optimizer

**EVE Online Manufacturing Optimizer (EMO)** is a standalone web-based application built to assist industrialists in optimizing their manufacturing chains. Designed for use with real in-game data, the tool helps manage blueprints, track materials, interface with ESI, and calculate the most profitable production plans all from a responsive and intuitive UI.

## Key Features

### Blueprint Management
- Add, edit, and remove blueprints along with their required materials and projected sell prices.
- Automatically update blueprint prices and materials using live market data from Jita 4-4 via ESI integration.

### SSO and ESI Integration
- Authenticate securely using EVE Online Single Sign-On (SSO).
- Gain access to structure-specific market data and authorized endpoints via the authenticated access token.

### Station Management
- Manage Player-Owned Stations.
- Add, edit, and delete stations for market data queries and blueprint calculations using your access token (when logged in through ESI).

### Material Tracking
- Add and update your inventory of materials, including quantities and prices.
- Import materials directly from your in-game inventory window with copy-paste support.

### Production Optimization
- Automatically calculate the most profitable production strategy based on your available materials and blueprint configurations.
- Prioritize based on profit margins or material availability.

### Dynamic UI
- No page reloads real-time updates for blueprints, materials, and stations.
- Blueprint and material prices are updated live using ESI with local caching for efficiency.

### Responsive Design
- Fully interactive and styled web interface, rebuilt from an early static HTML prototype.
- Works locally via an executable for easy access and portability.

---

## Technologies Used

- **Frontend**: HTML, CSS, JavaScript, jQuery
- **Backend**: Python (Flask), Waitress (Production Server), PuLP (Optimization), PyInstaller (Executable packaging)
- **Database**: SQLite with SQLAlchemy ORM
- **APIs**: EVE Swagger Interface (ESI), EVE SSO

---

## Setup & Installation

1. Download the latest `.zip` from the **Releases** section on the right.
2. Extract the folder and run `EMO.exe`.
   - A terminal window will open and automatically launch your browser at `http://127.0.0.1:5000`.
   - If it doesn’t open automatically, manually visit the address in any browser while EMO is running.
3. Follow the on-screen instructions to begin using the app.

---

## Usage Guide

### 1. Adding Blueprints
Use the **Add Blueprint** form to enter a blueprint’s name, sell price, and materials. You can paste materials directly from your in-game Industry tab:

> **Important**: Ensure *only one run* is selected when copying materials, or your values will be inflated.

Example copy-paste:  
![Blueprint Copy Example](https://github.com/user-attachments/assets/cdb64573-7a89-436f-a35e-47bc92cb6c98)
![Paste Into Blueprint Form](https://github.com/user-attachments/assets/5bdb7581-e601-495c-bcf6-8cd5eba6153e)


### 2. Managing Materials
Track your material inventory and prices by copying from the in-game assets window and pasting directly into the form:

![Copy Materials](https://github.com/user-attachments/assets/7ddb2082-4382-4520-a550-f7ed4c613582)  
![Paste into Form](https://github.com/user-attachments/assets/fc30d61a-7519-41fd-b10c-77563d66a1a2)

### 3. Optimizing Production
Click the **Optimize Production** button at the bottom of the main page to calculate the most profitable use of your materials:

![Optimize Button](https://github.com/user-attachments/assets/2adb8231-bfaf-453b-9bf3-5312b4253951)

### 4. Editing & Deleting
All entries (blueprints, materials, and stations) can be updated or removed using the respective action buttons in the interface.
![image](https://github.com/user-attachments/assets/44829b92-294e-40ad-8a00-e535054739d4)
![image](https://github.com/user-attachments/assets/3fe2c0bd-9f3f-4c60-a8ac-4a3cc1614e5a)

### 5. Logging In with SSO
Use the **Login** button in the header to authenticate with your EVE Online account:

![Login](https://github.com/user-attachments/assets/4d79facd-a1ca-408a-bff8-5681d284e750)

SSO access is required for managing custom stations and accessing market data from structures you have access to.

### 6. Updating Prices
Use the **Update Prices** feature to fetch the latest market prices and update type IDs and categories from Jita. Prices are cached locally for 5 minutes to reduce API load.

---


## Technologies Used

- **Python 3**: Core backend logic, data processing, and integration  
- **Flask**: REST API development, session management, and serving dynamic content  
- **SQLAlchemy & SQLite**: Database modeling, querying, and persistent storage  
- **PuLP**: Linear programming to optimize manufacturing plans  
- **EVE Online ESI API**: Fetching live market data and user station info with OAuth2 authentication  
- **requests & urllib3**: HTTP requests with retries for robust API communication  
- **HTML, CSS, JavaScript (jQuery)**: Frontend UI rendering and AJAX for dynamic data updates  
- **PyInstaller**: Packaging backend and frontend into a standalone executable  
- **Custom Parsing Utilities**: Processing and normalizing game data inputs  


## Contributing

Contributions are welcome. To propose a change or feature:

1. Fork this repository
2. Create a feature branch  
   `git checkout -b feature-branch`
3. Commit your changes  
   `git commit -am 'Add new feature'`
4. Push the branch  
   `git push origin feature-branch`
5. Open a Pull Request

---

## License

This project is licensed under the **GNU General Public License v3.0**.  
See the [LICENSE](LICENSE) file for details.

[![License: GPL v3](https://img.shields.io/badge/License-GPLv3-blue.svg)](https://www.gnu.org/licenses/gpl-3.0)

---

## Acknowledgments

- **EVE Online** – for the sandbox that made this project necessary  
- **Flask & jQuery** – for making rapid prototyping painless  
- **Stack Overflow** – for always having someone with the exact same bug I had, somehow
