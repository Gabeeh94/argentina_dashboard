from dash import Dash
from frontend import create_layout

app = Dash(__name__)
application = app.server

# Set the layout for the app
app.layout = create_layout()

if __name__ == '__main__':
    application.run(host='0.0.0.0', port=8080)
