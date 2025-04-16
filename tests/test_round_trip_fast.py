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


# Select a comprehensive subset of representative IDF files for fast testing
FAST_TEST_FILES = [
    # Files selected by greedy algorithm for maximum class coverage
    "tests/eplusfiles/_CrashLights_9680.idf",  # Large contribution of unique classes
    "tests/eplusfiles/PlantLoopHeatPump_EIR_AirSource_Hospital_wSixPipeHeatRecovery.idf",  # Complex HVAC
    "tests/eplusfiles/PlantLoopHeatPump_EIR_Large-Office-2-AWHP-DedHR-AuxBoiler-Pri-Sec-HW.idf",  # Plant systems
    "tests/eplusfiles/AirflowNetwork_MultiAirLoops.idf",  # Airflow networks
    "tests/eplusfiles/HospitalLowEnergy.idf",  # Healthcare building
    "tests/eplusfiles/SingleFamilyHouse_HP_Slab_Dehumidification.idf",  # Residential
    "tests/eplusfiles/_ResidentialBase.idf",  # Base residential model
    "tests/eplusfiles/4ZoneWithShading_Simple_2.idf",  # Shading
    "tests/eplusfiles/1ZoneUncontrolled_Win_ResilienceReports_ReportingPeriod.idf",  # Resilience
    "tests/eplusfiles/ASHRAE901_ApartmentHighRise_STD2019_Denver.idf",  # High-rise residential
    "tests/eplusfiles/Fault_FoulingEvapCooler_StripMallZoneEvapCooler.idf",  # Fault models
    "tests/eplusfiles/MicroCogeneration.idf",  # Cogeneration
    "tests/eplusfiles/HAMT_DailyProfileReport.idf",  # Heat and moisture transfer
    "tests/eplusfiles/PlateHeatExchanger.idf",  # Heat exchangers
    "tests/eplusfiles/5ZoneEconomicsTariffAndLifeCycleCosts.idf",  # Economics
    "tests/eplusfiles/DOASDXCOIL_wADPBFMethod.idf",  # DOAS systems
    "tests/eplusfiles/GeneratorswithPV.idf",  # Renewable energy
    "tests/eplusfiles/RoomAirflowNetwork.idf",  # Room airflow
    "tests/eplusfiles/EMSSetpointBasedMultiSpeedDXCoilOverrideControl.idf",  # EMS controls
    "tests/eplusfiles/HeatPumpIAQP_GenericContamControl.idf",  # IAQ and contaminants
    "tests/eplusfiles/LgOffVAVusingBasement.idf",  # VAV with basement
    "tests/eplusfiles/PythonPluginPlantLoopOverrideControl.idf",  # Python plugins
    "tests/eplusfiles/ChangeoverBypassVAV_AirToAirHeatPump.idf",  # VAV with heat pump
    "tests/eplusfiles/CmplxGlz_MeasuredDeflectionAndShading.idf",  # Complex glazing
    "tests/eplusfiles/5ZoneAirCooledWithSpacesHVAC.idf",  # Basic HVAC
    "tests/eplusfiles/DesiccantDehumidifierWithAirToAirCoil.idf",  # Desiccant systems
    "tests/eplusfiles/SupermarketSecondary.idf",  # Refrigeration
    "tests/eplusfiles/VariableRefrigerantFlow_FluidTCtrl_wSuppHeater_5Zone.idf",  # VRF
    "tests/eplusfiles/5ZoneAirCooledDemandLimiting_FixedRateVentilation.idf",  # Demand limiting
    "tests/eplusfiles/AirEconomizerFaults_RefBldgLargeOfficeNew2004_Chicago.idf",  # Economizer faults
]


# Test case for individual IDF file round trip
@pytest.mark.parametrize("idf_file", FAST_TEST_FILES)
def test_idf_round_trip_fast(idf_file):
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