import json
import os
import sys

# Add project root to path
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

from digital_library.main import app

def generate_openapi_schema():
    """
    Generates the OpenAPI schema and saves it to a file.
    """
    schema = app.openapi()
    with open("openapi.json", "w") as f:
        json.dump(schema, f, indent=2)
    print("OpenAPI schema generated and saved to openapi.json")

if __name__ == "__main__":
    generate_openapi_schema()
