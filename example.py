#!/usr/bin/env python3
"""
Quickstart example for idf2yaml package.
Shows basic conversion between IDF and YAML formats.
"""

from idf2yaml import idf2yaml, yaml2idf, DEFAULT_IDD

# Convert IDF to YAML
yaml_string = idf2yaml(
    "example.idf",              # path to the IDF file
    idd=DEFAULT_IDD,            # path to the IDD file
    skip_empty=True,            # if True, attributes not explicitly set in the IDF will not appear
    output_path="output.yaml"   # can be None if only the string is needed
)

# Convert YAML file back to IDF
idf_string_file = yaml2idf(
    "output.yaml",              # path to the yaml file
    idd=DEFAULT_IDD,            # path to the IDD file
    output_path="output.idf",   # can be None if only the string is needed
)

# Convert YAML string back to IDF
idf_string_string = yaml2idf(
    yaml_string,                # string representing the yaml content
    idd=DEFAULT_IDD,            # path to the IDD file
    output_path="output.idf",   # can be None if only the string is needed
)

# The result is the same
assert idf_string_file == idf_string_string