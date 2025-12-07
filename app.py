import sys
import os

# Добавляем путь к папке с проектом
sys.path.append(os.path.join(os.path.dirname(__file__), 'SneakerFit'))

from SneakerFit.app import app

if __name__ == "__main__":
    app.run()
