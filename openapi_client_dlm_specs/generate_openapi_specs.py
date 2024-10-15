#
import argparse
import io
import json
import logging
import os
import requests

TAG_FIELD = "tags"
HTTP_METHODS = ['get', 'post']  # The HTTP methods you want to modify
OPENAPI_HOST_URL = "http://localhost"
OPENAPI_URL_JSON_PATH = "openapi.json"
OPENAPI_SPECS = {
    "gateway":   8000,
    "ingest":    8001,
    "request":   8002,
    "storage":   8003,
    "migration": 8004
    }
OPENAPI_SPEC_EXTENSION = "_spec.json"

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s',
)

def stream_from_url(url):
    try:
        # Make a GET request to the URL
        response = requests.get(url, stream=True)
        response.raise_for_status()  # Check for HTTP errors

        # Create a stream from the response content
        stream = io.StringIO(response.text)

        return stream
    except requests.exceptions.RequestException as e:
        logging.error(f"An error occurred: {e}")
        return None


# Function to add a new field to specific HTTP methods (get, post, etc.)
def add_field_to_openapi_spec(service_name, url_stream, output_directory, new_field_spec):
    openapi_spec = json.load(url_stream)

    # Check if the methods exist in the paths section
    for path, file_http_method_details in openapi_spec.get('paths', {}).items():
        for http_method in HTTP_METHODS:
            if http_method in file_http_method_details:
                #file_http_method_details[http_method][TAG_FIELD] = new_field_spec
                pos = list(file_http_method_details[http_method].keys()).index('description')
                items = list(file_http_method_details[http_method].items())
                items.insert(pos, (TAG_FIELD, new_field_spec))
                file_http_method_details[http_method] = dict(items)

    # Save the modified spec back to the file
    with open(f"{output_directory}/{service_name}{OPENAPI_SPEC_EXTENSION}", 'w', encoding='utf-8') as file:
        json.dump(openapi_spec, file, indent=4)
        file.write('\n')

def main():
    # Create the parser
    parser = argparse.ArgumentParser(description="Generate OpenAPI tagged spec files from DLM openapi URL call.")

    # Add an argument for the file name
    parser.add_argument("output_directory",
                        type=str,help="The output directory to write the OpenAPI JSON file specs.")

    args = parser.parse_args()

    # Access the output_directory argument
    output_directory = args.output_directory
    logging.info(f"The directory name provided is: {output_directory}")


    # Create the directory
    try:
        os.mkdir(output_directory)
        logging.info(f"Directory '{output_directory}' created successfully.")
    except FileExistsError:
        logging.warn(f"Directory '{output_directory}' already exists.")
        logging.warn(f"Any files of the same name will be over written.")

    for service_key in OPENAPI_SPECS:
        service_value = OPENAPI_SPECS[service_key]
        OPENAPI_SPEC_URL = f"{OPENAPI_HOST_URL}:{service_value}/{OPENAPI_URL_JSON_PATH}"
        logging.info(f"{service_key}:{service_value},{OPENAPI_SPEC_URL}")

        url_stream = stream_from_url(OPENAPI_SPEC_URL)
        if url_stream is None:
            logging.error(f"Failed to open connection to DLM service, cannot retrieve specs.")
            exit(1)
        new_field_spec = [service_key]
        add_field_to_openapi_spec(service_key, url_stream, output_directory, new_field_spec)

if __name__ == "__main__":
    main()
