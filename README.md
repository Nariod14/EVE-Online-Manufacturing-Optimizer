# EVE Online Manufacturing Optimizer

This project is a web-based application designed to optimize manufacturing processes in the EVE Online game. It allows players to manage blueprints, track available materials, and calculate the most profitable production plans.

## Features

- **Blueprint Management**: Add, edit, and delete blueprints with their associated materials and sell prices.
- **Material Tracking**: Keep track of available materials and their quantities.
- **Production Optimization**: Calculate the most profitable production plan based on available materials and blueprint data.
- **Dynamic UI**: Real-time updates of blueprint and material lists without page reloads.
- **Responsive Design**: User-friendly interface that works on desktop and mobile devices.

## Technologies Used

- Frontend: HTML, CSS, JavaScript, jQuery
- Backend: Flask
- Database: SQLite, SQLAlchemy

## Setup and Installation

1. Download and Extract from the releases on the right side
2. Simply open the EMO.exe. It should open your browser to 127.0.0.1:5000. If it doesn't, go there on any browser while the app is open.
3. Follow the onscreen instructions!

## Usage

1. **Adding Blueprints**: Use the "Add Blueprint" form to input new blueprints, specifying name, sell price, and required materials.
2. **Managing Materials**: Add or update available materials using the "Add Material" form.
3. **Optimizing Production**: Click the "Optimize Production" button to calculate the most profitable manufacturing plan.
4. **Editing and Deleting**: Use the provided buttons to edit or delete existing blueprints and materials.

## Contributing

Contributions to improve the optimizer are welcome. Please follow these steps:

1. Fork the repository
2. Create a new branch (`git checkout -b feature-branch`)
3. Make your changes and commit (`git commit -am 'Add some feature'`)
4. Push to the branch (`git push origin feature-branch`)
5. Create a new Pull Request

## License

This project is licensed under the GNU General Public License v3.0 (GPL-3.0).

See the [LICENSE](LICENSE) file for details.

[![License: GPL v3](https://img.shields.io/badge/License-GPLv3-blue.svg)](https://www.gnu.org/licenses/gpl-3.0)

## Acknowledgments

- EVE Online for inspiring this project
- The Flask and jQuery communities for their excellent documentation
- StackOverflow for random people somehow having the same obscure problems as me.
