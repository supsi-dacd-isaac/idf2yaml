# test_idf2yaml.py

import pytest
from unittest.mock import patch
from idf2yaml.__main__ import main
import subprocess


@pytest.mark.parametrize(
    "args, expected_output, expected_exit_code",
    [
        (["-i2y", "example.idf", "-e"], "File 'example.idf' has been converted to 'example.yaml'.", None),
        (["-i2y", "example.idf", "-o", "named_example.yaml", "-i", "iddfiles/Energy+.idd", "-s"], None, None),
        (["-y2i", "named_example.yaml", "-o", "round_trip.idf", "-s"], None, None),
        (["-y2i", "i_dont_exist.yaml"], "File 'i_dont_exist.yaml' is not a valid path and cannot be processed. Exiting...", 1),
        (
            ["-i2y", "example.idf", "-i", "i_dont_exist.idd"],
            "Idd File 'i_dont_exist.yaml' is not a valid path and cannot be processed. Exiting...",
            1,
        ),
    ],
)
def test_command_line_arguments(args, expected_output, expected_exit_code):
    with patch("sys.argv", ["main.py"] + args):
        with patch("builtins.print") as mocked_print:
            if expected_exit_code is not None:
                with pytest.raises(SystemExit) as excinfo:
                    main()
                assert excinfo.value.code == expected_exit_code  # Check for expected exit code
            else:
                try:
                    main()
                    if expected_output is None:
                        mocked_print.assert_not_called()  # Check that print was not called
                    else:
                        mocked_print.assert_called_with(expected_output)  # Check for expected output
                except Exception as e:
                    pytest.fail(f"Test failed due to an exception: {e}")


def test_cover_naked_main():
    result = subprocess.run(["python", "-m", "idf2yaml", "--help"], capture_output=True, text=True)
    assert result.returncode == 0  # Check for successful execution
