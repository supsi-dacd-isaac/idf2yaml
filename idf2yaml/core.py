import os
from io import StringIO
from pathlib import Path

from eppy.modeleditor import IDF
from ruamel.yaml.main import YAML, CommentedMap

DEFAULT_IDD = str(Path(__file__).parent.parent / "iddfiles" / "Energy+.idd")


def make_help_string(meta):
    """
    Create a help string for an idf object.
    Different behavior should be achieved by monkey patching this function.
    """

    help_string = ""

    if "units" in meta.keys():
        help_string += f'[{str(meta["units"][0])}] '

    if "default" in meta.keys():
        help_string += f'dflt:{str(meta["default"][0])} '

    minstr = ""
    if "minimum" in meta.keys():
        minstr = str(meta["minimum"][0])
    maxstr = ""
    if "maximum" in meta.keys():
        maxstr = str(meta["maximum"][0])
    if maxstr != "" or minstr != "":
        help_string += f"({minstr}->{maxstr}) "

    if "type" in meta.keys() and meta["type"] == ["choice"]:
        help_string += f"[{'|'.join(meta['key'])}]"

    return help_string


def idf2yaml(idf, idd=DEFAULT_IDD, skip_empty=True, output_path=None, insert_memo=False, **ruamel_yaml_kwargs):
    """Convert IDF object to YAML format."""

    # We create a local fork class as a workaround for unexpected behavior of eppy.
    # when, i.e, performing an idf->yaml->idf round trip, new objects created with
    # the IDF instance did not have the first attribute defined in the IDD. With a
    # fresh local subclass everything works as expected.
    class LocalForkIDF(IDF):
        pass

    # parse the IDF
    LocalForkIDF.setiddname(idd)
    idf_parsed = LocalForkIDF(idf)
    idd_types_order = [x[0].upper() for x in idf_parsed.block]

    # Create an empty dict
    yaml_data = CommentedMap()

    for item, idf_msequence in idf_parsed.idfobjects.items():
        if len(idf_msequence) == 0:
            continue
        objects = []
        yaml_key = item  # default key that will be overwritten in the cycle

        # analyze one object at a time
        for object_no, object in enumerate(idf_msequence):
            object_map = CommentedMap()

            # pull data from the object
            names = object["objls"]  # the only guaranteed complete list is names
            values = object["obj"]
            metadata = object["objidd"]

            # missing values mean that only the first n values were specified in the idf.
            # the others will be defaulted.
            values.extend([None] * (len(names) - len(values)))
            metadata.extend([{}] * (len(names) - len(metadata)))

            # due to eppy parsing, the metadata for the first attribute (the main key) might
            # or might not be present. If it is, we need to pop it out of the list. Otherwise, we
            # remove the last element to equalize it to the following pops.
            if "memo" in metadata[0].keys():
                metadata.pop(0)
            else:
                metadata.pop(-1)

            # pop the object name, which is the first attribute
            key_key = names.pop(0)
            assert key_key == "key"
            key_name = values.pop(0)
            assert key_name.upper() == item.upper()
            yaml_key = key_name  # overwrite with the better one (it uses camel case)

            # insert all the key-value pairs with metadata-derived help strings
            # in the object_map structure
            for name, value, meta in zip(names, values, metadata):
                # skip empty values if requested
                if skip_empty and value is None:
                    continue

                # form the comment
                comment = None
                help_string = make_help_string(meta)
                if help_string != "":
                    comment = help_string

                # add the commented pair to the object_mapq
                object_map.insert(len(object_map), name, value, comment)

            # append the object_map to the list of objects of this type
            objects.append(object_map)

        # add the list of objects to the main structure
        yaml_data[yaml_key] = objects

    # add blanks and object memo
    for key, value in yaml_data.items():
        object_index = idd_types_order.index(key.upper())
        memo = None
        if insert_memo and idf_parsed.idd_info[object_index]:
            memo = "\n".join(idf_parsed.idd_info[object_index][0].get("memo", []))
        yaml_data.yaml_set_comment_before_after_key(key, before="\n", after=memo)

    # prepare emitter
    yaml_struct = YAML()
    yaml_struct.top_level_colon_align = False
    yaml_struct.indent = 4
    for key, value in ruamel_yaml_kwargs.items():
        setattr(yaml_struct, key, value)

    # dump to file if requested
    if output_path is not None:
        with open(output_path, "w") as f:
            yaml_struct.dump(yaml_data, f)

    # dump to string
    f = StringIO()
    yaml_struct.dump(yaml_data, f)
    f.seek(0)
    str_yaml = f.read()

    return str_yaml


def yaml2idf(yaml, idd=DEFAULT_IDD, output_path=None, **ruamel_yaml_kwargs):
    """Convert YAML string or file path to IDF object."""
    # load yaml string or file
    yaml_parser = YAML(**ruamel_yaml_kwargs)
    if os.path.isfile(yaml):
        with open(yaml) as f:
            yaml_data = yaml_parser.load(f)
    else:
        yaml_data = yaml_parser.load(yaml)

    # We create a local fork class as a workaround for unexpected behavior of eppy.
    # when, i.e, performing an idf->yaml->idf round trip, new objects created with
    # the IDF instance did not have the first attribute defined in the IDD. With a
    # fresh local subclass everything works as expected.
    class LocalForkIDF(IDF):
        pass

    LocalForkIDF.setiddname(idd)
    fhandle = StringIO("")  # we can make a file handle of a string
    idf_out = LocalForkIDF(fhandle)

    # create a new IDF object for each object in the yaml data
    for key, object_list in yaml_data.items():
        for object_dict in object_list:

            # create a new IDF object
            newobj = idf_out.newidfobject(key, defaultvalues=False)

            # set attributes one by one for better problem diagnosis
            for name, value in object_dict.items():
                if not hasattr(newobj, name):
                    # if the attribute does not exist, raise an error
                    raise KeyError(
                        f"Attribute {name} not found in {key}. " f"Check that this attribute is defined in the IDD."
                    )
                setattr(newobj, name, value)

    if output_path is not None:
        idf_out.idfname = output_path
        idf_out.save(output_path)

    return idf_out.idfstr()
