# EVE Online Manufacturing Optimizer

This project is a web-based application designed to optimize manufacturing processes in the EVE Online game. It allows players to manage blueprints, track available materials, and calculate the most profitable production plans.

## Features

- **Blueprint Management**: Add, edit, and delete blueprints with their associated materials and sell prices.
- **Material Tracking**: Keep track of available materials and their quantities.
- **Production Optimization**: Calculate the most profitable production plan based on available materials and blueprint data.
- **Dynamic UI**: Real-time updates of blueprint and material lists without page reloads.
- **Responsive Design**: User-friendly interface that works on both desktop and mobile devices.

## Technologies Used

- Frontend: HTML, CSS, JavaScript, jQuery
- Backend: Flask
- Database: SQLite, SQLAlchemy

## Setup and Installation

1. Clone the repository
2. Install required Python packages:
   ```
   pip install flask flask-sqlalchemy flask-cors
   ```
3. Run the Flask application:
   ```
   python app.py
   ```
4. Open a web browser and navigate to `http://localhost:5000`

This isnt the most secure server for this project. A future patch will include a proper production WSGI server.

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

[Specify your license here, e.g., MIT License]

## Acknowledgments

- EVE Online for inspiring this project
- The Flask and jQuery communities for their excellent documentation
