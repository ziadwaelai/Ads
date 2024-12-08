import os
from server import app

if __name__ == '__main__':
    try:
        port = int(os.environ.get("PORT", 4000))
        app.run(debug=True, host="0.0.0.0", port=port)
    except Exception as e:
        print(f"An error occurred while running the server: {e}")