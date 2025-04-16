import glob
import logging

import pytest

from idf2yaml import idf2yaml, yaml2idf

# Configure logging
logger = logging.getLogger(__name__)
logger.setLevel(logging.INFO)

# Create a StreamHandler
stream_handler = logging.StreamHandler()
stream_handler.setLevel(logging.INFO)

# Create a formatter and add it to the handler
formatter = logging.Formatter("%(asctime)s - %(name)s - %(levelname)s - %(message)s")
stream_handler.setFormatter(formatter)

# Add the handler to the logger
logger.addHandler(stream_handler)


@pytest.mark.parametrize("idf_file", glob.glob("tests/eplusfiles/1ZoneUncontrolled.idf"))
def test_file_rt_and_yaml_kwargs(idf_file):
    try:
        # Convert IDF to YAML
        _yaml_str = idf2yaml(idf_file, output_path="test_output.yaml", default_flow_style=False, insert_memo=True)

        # Convert YAML back to IDF
        _round_trip_1 = yaml2idf("test_output.yaml", output_path="test_round_trip.idf")

    except Exception as e:
        logger.error(f"Error in file-based round trip w/kwargs 1ZoneUncontrolled.idf: {str(e)}")
        pytest.fail(f"Error in file-based round trip w/kwargs 1ZoneUncontrolled.idf: {str(e)}")
