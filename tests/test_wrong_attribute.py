import glob
import logging
import io
import pytest

from idf2yaml import idf2yaml, yaml2idf
from ruamel.yaml import YAML

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
def test_wrong_parameter(idf_file):
    with pytest.raises(KeyError):
        # Convert IDF to YAML
        yaml_str = idf2yaml(idf_file, output_path=None)
        yaml = YAML()
        yaml_data = yaml.load(yaml_str)

        yaml_data["SizingPeriod:DesignDay"][0]["this_parameter_does_not_exist"] = True
        wrong_yaml_str = io.StringIO()
        yaml.dump(yaml_data, wrong_yaml_str)
        wrong_yaml_str = wrong_yaml_str.getvalue()

        # Convert YAML back to IDF -- this will raise
        _round_trip_1 = yaml2idf(wrong_yaml_str, output_path="this_file_should_not_be_created.idf")
