from flask import jsonify
from flask_swagger_ui import get_swaggerui_blueprint

SWAGGER_URL = '/api/docs'  # Swagger UIのURL
API_URL = '/static/swagger.json'  # OpenAPI仕様書のJSON

swagger_ui_blueprint = get_swaggerui_blueprint(
    SWAGGER_URL,
    API_URL,
    config={
        'app_name': "チャットボットビルダー API"
    }
)