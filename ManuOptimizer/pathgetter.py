import os
import sys

if getattr(sys, 'frozen', False):
    # Running as compiled exe
    basedir = sys._MEIPASS
    instance_path = os.path.join(os.path.dirname(sys.executable), 'instances')
else:
    # Running as script
    basedir = os.path.abspath(os.path.dirname(__file__))
    instance_path = os.path.join(basedir, 'instances')

os.makedirs(instance_path, exist_ok=True)

db_path = os.path.join(instance_path, 'eve_optimizer.db')

print("Full DB path:", db_path)
print("SQLite URL:", f"sqlite:///{db_path}")
