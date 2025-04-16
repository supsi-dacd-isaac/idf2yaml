import glob
import io
import logging

import pytest
from eppy.modeleditor import IDF
from eppy.useful_scripts.idfdiff import getobjname

from idf2yaml import idf2yaml, yaml2idf, DEFAULT_IDD
from itertools import zip_longest as zip_longest
from numpy import isclose
from numpy.exceptions import DTypePromotionError

# Configure logging
logger = logging.getLogger(__name__)
logger.setLevel(logging.INFO)

# Create a StreamHandler
stream_handler = logging.StreamHandler()
stream_handler.setLevel(logging.INFO)

# Create a formatter and add it to the handler
formatter = logging.Formatter('%(asctime)s - %(name)s - %(levelname)s - %(message)s')
stream_handler.setFormatter(formatter)

# Add the handler to the logger
logger.addHandler(stream_handler)

# This comparison function was forked from the one included in eppy to
# use np.isclose as a validation for floats. Otherwise, in round trips
# insignificant rounding errors due to conversions are marked as fails.
def idfdiffs(idf1, idf2):
    """return the diffs between the two idfs"""
    # for any object type, it is sorted by name
    thediffs = {}
    keys = idf1.model.dtls  # undocumented variable

    for akey in keys:
        idfobjs1 = idf1.idfobjects[akey]
        idfobjs2 = idf2.idfobjects[akey]
        names = set(
            [getobjname(i) for i in idfobjs1] + [getobjname(i) for i in idfobjs2]
        )
        names = sorted(names)
        idfobjs1 = sorted(idfobjs1, key=lambda idfobj: idfobj["obj"])
        idfobjs2 = sorted(idfobjs2, key=lambda idfobj: idfobj["obj"])
        for name in names:
            n_idfobjs1 = [item for item in idfobjs1 if getobjname(item) == name]
            n_idfobjs2 = [item for item in idfobjs2 if getobjname(item) == name]
            for idfobj1, idfobj2 in zip_longest(n_idfobjs1, n_idfobjs2):
                if idfobj1 == None:
                    thediffs[(idfobj2.key.upper(), getobjname(idfobj2))] = (
                        None,
                        idf2.idfname,
                    )  # (idf1.idfname, None) -> old
                    break
                if idfobj2 == None:
                    thediffs[(idfobj1.key.upper(), getobjname(idfobj1))] = (
                        idf1.idfname,
                        None,
                    )  # (None, idf2.idfname) -> old
                    break
                for i, (f1, f2) in enumerate(zip(idfobj1.obj, idfobj2.obj)):
                    if i == 0:
                        f1, f2 = f1.upper(), f2.upper()
                    try:
                        values_different = not isclose(f1, f2)
                    except (TypeError, DTypePromotionError):
                        values_different = f1 != f2
                    if values_different:
                        thediffs[
                            (akey, getobjname(idfobj1), idfobj1.objidd[i]["field"][0])
                        ] = (f1, f2)
    return thediffs


# Test case for individual IDF file round trip
@pytest.mark.parametrize("idf_file", glob.glob("tests/eplusfiles/5ZoneAirCooledWithSpacesHVAC.idf"))
def test_idf_round_trip(idf_file):
    """Test that an IDF file can be converted to YAML and back without changes."""
    try:
        # Convert IDF to YAML
        yaml_str = idf2yaml(idf_file, output_path=None)
        
        # Convert YAML back to IDF
        round_trip_1 = yaml2idf(yaml_str, output_path=None)
        f = io.StringIO(round_trip_1)

        # Create IDF objects for comparison
        class LocalForkIDF(IDF):
            pass
        LocalForkIDF.setiddname(DEFAULT_IDD)
        start_idf = LocalForkIDF(idf_file)
        round_idf = LocalForkIDF(f)

        # Compare the original and round-trip IDFs
        diff = idfdiffs(start_idf, round_idf)
        
        # Log success if no differences found
        if not diff:
            logger.info(f"Successfully completed round trip for {idf_file}")
        
        # Assert that there are no differences
        assert not diff, f"Round trip conversion failed for {idf_file}. Differences found:\n{diff}"
        
    except Exception as e:
        logger.error(f"Error processing {idf_file}: {str(e)}")
        pytest.fail(f"Error processing {idf_file}: {str(e)}")


# # Test case to verify all files are processed
# def test_all_files_processed(idf_files):
#     """Test that we have IDF files to process."""
#     assert len(idf_files) > 0, "No IDF files found in eplusfiles directory"