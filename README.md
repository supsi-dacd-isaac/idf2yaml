[![codecov](https://codecov.io/gh/supsi-dacd-isaac/idf2yaml/branch/main/graph/badge.svg)](https://codecov.io/gh/supsi-dacd-isaac/idf2yaml)
[![PyPI](https://img.shields.io/pypi/v/idf2yaml)](https://pypi.org/project/idf2yaml/)
[![License](https://img.shields.io/github/license/supsi-dacd-isaac/idf2yaml)](https://github.com/supsi-dacd-isaac/idf2yaml/blob/main/LICENSE)

[idf2yaml](https://github.com/supsi-dacd-isaac/idf2yaml) is a package that converts IDF files for the [EnergyPlus](https://github.com/NREL/EnergyPlus) simulation
software to YAML format **and vice versa**. This package allows users to easily convert between these two formats, enabling to work with 
EnergyPlus models with yaml tooling. 

idf2yaml is built upon the libraries [`eppy🔗`](https://github.com/santoshphilip/eppy) and [`ruamel.yaml🔗`](https://sourceforge.net/projects/ruamel-yaml/).

The package consists of two functions, `idf2yaml` and `yaml2idf`, which convert IDF files to YAML format and YAML files
(if, of course, appropriately populated) to IDF format, respectively. 


The following quickstart script shows how to use the package:
```python3
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
```

The conversion from IDF to YAML includes useful annotations for the
attributes, such as 
- Physical units
- Default values
- Numeric range `(min->max)`
- Set of possible choices for categoricals `[opt1|opt2|opt3]`

These are derived from
the [EnergyPlus IDD (Input Data Dictionary) file](https://github.com/NREL/EnergyPlus/blob/d5d55c0c47fea5ef6a8c7a53d12a59384fec87f8/idd/Energy%2B.idd.in), 
which works as a specification of the IDF file format and is used throughout the package for decoding and emission.

> [!NOTE]  
> The parsing and emission performed by this package is always just as good as the IDD file. `DEFAULT_IDD` is directly derived from the official
> EnergyPlus repo and should work fine for the most recent versions of EnergyPlus.

> [!TIP]
For advanced users: you can customize the yaml annotation by monkey patching the `make_help_string` function, which is exposed as well.