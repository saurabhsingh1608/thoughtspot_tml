<div align="center">
  <h2><b>ThoughtSpot TML</b></h2>

  <i>a Python package for working with</i> <b>ThoughtSpot</b> <i>Modeling Language (TML) files programmatically</i>

  ![Badge: Lint](https://github.com/thoughtspot/thoughtspot_tml/actions/workflows/lint.yml/badge.svg)
  ![Badge: Test](https://github.com/thoughtspot/thoughtspot_tml/actions/workflows/test.yml/badge.svg)
  
  <h3>
    <a href="#installation">Installation</a>
    <span> | </span>
    <a href="#a-basic-example">Example</a>
    <span> | </span>
    <a href="#migration-to-v200">Migration to v2.0.0</a>
    <span> | </span>
    <a href="#thoughtspot_tml-reference">Reference</a>
    <span> | </span>
    <a href="#notes-on-thoughtspot-modeling-language">Notes</a>
  </h3>

🚨 __If your examples or scripts are built on__ `thoughtspot_tml==1.3.0`__, see our [Migration to v2.0.0](#migration-to-v200) guide__. 🚨
</div>

## Features

 - __Supports__: Connections, [Tables][syntax-table], [Views][syntax-view], [SQLViews][syntax-sqlview], [Worksheets][syntax-worksheet], [Answers][syntax-answer], [Liveboards][syntax-liveboard]
 - Deep attribute access
 - Roundtripping from text or file
 - Utilities for [disambiguation][docs-fqn] workflows

*This package will not perform validation of the constructed TML files or interact with your* __ThoughtSpot__ *cluster!*

Please leverage the [__ThoughtSpot__ REST API][rest-api] for this purpose.

## Installation

`thoughtspot_tml` requires at least __Python 3.7__, *preferably* __Python 3.9__ and above.

__Installation is as simple as:__
```shell
pip install thoughtspot-tml
```

## A Basic Example

This example creates a command-line tool for changing the prefix in the names of the Table objects that a Worksheet object connects to.

```python
# worksheet_remapping.py
from thoughtspot_tml import Worksheet
import argparse
import pathlib


def filepath(fp: str) -> pathlib.Path:
    """
    Converts a string to a pathlib.Path.
    """
    path = pathlib.Path(fp)

    if not path.exists():
        raise argparse.ArgumentTypeError(f"path '{fp!r}' does not exist")

    if not path.is_file():
        raise argparse.ArgumentValueError(f"path must be a file, got '{fp!r}'")

    return path


def main():
    # Create a command line application
    #   - argument for a WORKSHEET.worksheet.tml
    #   - options for the "before" and "after" tabling naming conventions
    parser = argparse.ArgumentParser()
    parser.add_argument("worksheet_tml", help="a worksheet.tml to remap", type=filepath)
    parser.add_argument("-s", "--src-prefix", metavar="SRC", default="DEV_", type=str, help="(default: %(default)s)")
    parser.add_argument("-d", "--dst-prefix", metavar="DST", default="TEST_", type=str, help="(default: %(default)s)")

    # Parse CLI input
    args = parser.parse_args()

    # Read from file
    tml = Worksheet.load(args.worksheet_tml)
    
    # Replace instances of DEV_ with TEST_
    for table in tml.worksheet.tables:
        table.name = table.name.replace(args.src_prefix, args.dst_prefix)

    # Save to file
    tml.dump(args.worksheet_tml)


if __name__ == '__main__':
    raise SystemExit(main())

```

```shell
>>> python worksheet_remapping.py -h

usage: [-h] [-s SRC] [-d DST] worksheet_tml

positional arguments:
  worksheet_tml         a worksheet.tml to remap

options:
  -h, --help                show this help message and exit
  -s SRC, --src-prefix SRC  (default: DEV_)
  -d DST, --dst-prefix DST  (default: TEST_)
```

A more complex version of this example, as well as more examples can be found in the [/examples directory][examples] in this repository.

## `thoughtspot_tml` Reference

<h5>
  <a href="#tml-objects">TML Objects</a>
  <span> | </span>
  <a href="#deserialization">Deserialization</a>
  <span> | </span>
  <a href="#serialization">Serialization</a>
  <span> | </span>
  <a href="#spotapp">SpotApp</a>
  <span> | </span>
  <a href="#utilities">Utilities</a>
</h5>

### TML Objects
```python
from thoughtspot_tml import Table, View, SQLView, Worksheet
from thoughtspot_tml import Answer, Liveboard, Pinboard

# aliases
from thoughtspot_tml import ThoughtSpotView    # View
from thoughtspot_tml import SavedAnswer        # Answer
from thoughtspot_tml import SystemTable        # Table
```

Each TML object has a top-level attribute for the globally unique identifier, or `GUID`, as well as the document form of the object it represents. This identically mirrors the TML specification you can find [in the __ThoughtSpot__ documentation][syntax-tml]. In addition, the `name` attribute of the TML document itself has been pulled into the top-level namespace.

```python
@dataclass
class Worksheet(TML):
    """
    Representation of a ThoughtSpot Worksheet TML.
    """

    guid: GUID
    worksheet: WorksheetEDocProto

    @property
    def name(self) -> str:
        return self.worksheet.name
```

The full, composable TML specification can found in [`_scriptability.py`][py-scriptability]. Each piece of the spec is a python [`dataclasses.dataclass` field][py-dataclasses-field]. The internal `_scriptability.py` module is generated code from the __ThoughtSpot__'s internal architecture and allows for `thoughtspot_tml` to offer the deep attribute access experience in python.

```python
@dataclass
class Table(TML):
    """
    Representation of a ThoughtSpot Table TML.
    """

    guid: GUID
    table: LogicalTableEDocProto

    @property
    def name(self) -> str:
        return self.table.name
```

For example, interesting attributes about the Table TML spec are exposed via attributes which can, in turn expose their own attributes themselves. This functionality offers common pattersn to be expressed natively in Python, such as remapping a Table's connection details.

```python
tml = Table.load("tests/data/DUMMY.table.tml")

# get the Table document object
tml.table           # => LogicalTableEdocProto(...)

# get the Table's underlying connected details
tml.table.db        # => 'PMMDB'
tml.table.schema    # => 'RETAILAPPAREL'
tml.table.db_table  # => 'dim_retapp_products'

# get the Table's columns
tml.table.columns   # => [LogicalTableEDocProtoLogicalColumnEDocProto(...), ...]

# repoint this ThoughtSpot Table to a new external table
tml.table.schema = "RETAILAPPAREL_V2"
tml.table.db_table = "DIM_RETAPP_PRODUCTS"
```

---

The `Connection` is a special type of TML object. Connections (also known as "Embrace" Connections) were implemented prior to the TML spec being officially released. The remapping file (`connection.yaml`), obtained from your platform at `Data > Connections > (...) in the top right > Remapping > Download` defines how __ThoughtSpot__ table objects relate to their external counterparts.

```python
from thoughtspot_tml import Connection

# aliases
from thoughtspot_tml import EmbraceConnection  # Connection
```

Even though the resulting file is different, we've implemented the Connection with an identical form.

The Connection GUID, while optional in `thoughtspot_tml`, is required when modifying or removing an existing connection via the REST API. A Connection's GUID can be obtained by calling the [`connection/list`][rest-api-cnxn-list] endpoint.

When loading from a file, if `thoughtspot_tml` identifies the filename is a GUID, then the property will be set on the resulting object.

The [`connection/update`][rest-api-cnxn-update] REST API endpoint requires connections to formatted in a different way. For this, we provide a method to generate the metadata parameter data, which is a mapping of configuration attributes, as well as database, schema, and table objects.

<sub>\*__ThoughtSpot__ <i>plans to release Connection TML in a future release.</i></sub>

```python
@dataclass
class Connection(TML):
    """
    Representation of a ThoughtSpot Connection YAML.
    """

    guid: Optional[GUID]
    connection: ConnectionDoc

    def to_rest_api_v1_metadata(self) -> ConnectionMetadata:
        ...
```

Each object contains multiple methods for serialization and deserialization.

### __Deserialization__

For deserialization of a TML document into a python object.

```python
ws = Worksheet.load(path: PathLike = "tests/data/DUMMY.worksheet.tml")
ws = Worksheet.loads(tml_document: str = ...)  # can be obtained from the ThoughtSpot REST API

ws.guid == "2ea7add9-0ccb-4ac1-90bb-231794ebb377"
```

`.load` a worksheet from a `.worksheet.tml` file, or as a string directly from the [`metadata/tml/export`][rest-api-export] API with `.loads`.

---

### __Serialization__

For serialization of a TML python object back into data.

```python
data = ws.to_dict()
data["guid"] == "2ea7add9-0ccb-4ac1-90bb-231794ebb377"

ws.dump(path="tests/data/DUMMY.worksheet.tml")
# DUMMY.worksheet.tml
#
# guid: 2ea7add9-0ccb-4ac1-90bb-231794ebb377
# worksheet:
#   ...

data_s = ws.dumps(format_type="YAML")
data = yaml.load(data_s)
data["guid"] == "2ea7add9-0ccb-4ac1-90bb-231794ebb377"

# -or-

data = ws.dumps(format_type="JSON")
data_s = json.loads(data_s)
data["guid"] == "2ea7add9-0ccb-4ac1-90bb-231794ebb377"
```

`.to_dict` to convert the entire object tree into python native types, or write back to a file with `.dump` as a TML-formatted string. The formatting can be overriden to JSON if the JSON file type is used (`.worksheet.json`). `.dumps` allows access to the formatted string directly, typically used as input for the [`metadata/tml/import`][rest-api-import] API.

### SpotApp

```python
from thoughtspot_tml import SpotApp
```

SpotApps are bundles of TML which can be obtained directly from the __ThoughtSpot__ user interace as a zip file archive or from the [`/metadata/tml/export`][rest-api-export] API endpoint using the `export_associated = true` query parameter.


```python
export_response = ...  # /metadata/tml/export
s = SpotApp.from_api(export_response)
print(s.tml)  # => [Worksheet(...), Table(...), Table(...)]
print(s.manifest)  # => Manifest(...)

# -or-

s = SpotApp.read("tests/data/DUMMY_spot_app.zip")
print(s.tml)  # => [Worksheet(...), Table(...), Table(...)]
print(s.manifest)  # => Manifest(...)
```

SpotApps can also be saved to a new zipfile archive through the `.save` method.

```python
s = SpotApp.read("tests/data/DUMMY_spot_app.zip")
s.save("tests/data/NEW_DUMMY_spot_app.zip")
```

### Utilities

<h5>
  <a href="#determine_tml_type">determine_tml_type</a>
  <span> | </span>
  <a href="#environmentguidmapper">EnvironmentGUIDMapper</a>
  <span> | </span>
  <a href="#disambiguate">disambiguate</a>
</h5>

`thoughtspot_tml.utils` are additional methods which can help or speed up working with TML documents.


### `determine_tml_type`

TML is both a data structure and file format, and these formats vary slightly across each document. `determine_tml_type` will return the appropriate TML class so that you can call [deserialization methods](#deserialization) directly. Pass either the `path` keyword with a filepath, or the file info directly from one of the objects returned in the [`/metadata/tml/export`][rest-api-export] response data.

<b> &emsp; &emsp; signature</b>

```python
def determine_tml_type(*, info: TMLDocInfo = None, path: PathLike = None) -> Union[Connection, TMLObject]:
    """
    Get the appropriate TML class based on input data.

    Parameters
    ----------
    info : TMLDocInfo
      API edoc info response

    path : PathLike
      filepath to parse

    Raises
    ------
    TMLError, when a valid TML type could not be found based on input
    """
```

<b> &emsp; &emsp; usage</b>

```python
from thoughtspot_tml.utils import determine_tml_type

tml_cls = determine_tml_type(path="/tests/data/DUMMY.worksheet.tml")
tml = tml_cls.load(path="/tests/data/DUMMY.worksheet.tml")
type(tml) is Worksheet  # => True

# -or-

export_response = ...  # /metadata/tml/export
tml_cls = determine_tml_type(info=export_response["object"][0]["info"])
tml = tml_cls.loads(tml_document=export_response["object"][0]["edoc"])
type(tml) is Worksheet  # => True
```


### `EnvironmentGUIDMapper`

The `EnvironmentGUIDMapper` is a dictionary-like data structure which can help you maintain references to objects across your __ThoughtSpot__ environments. The underlying data structure is intended to clearly show the relationship of a given object between any number of environments. An "environment" can be any scope you consider separate from each other, be it 2 __ThoughtSpot__ servers, 2 Connections on the same server, or even "Copy of" the same object within a single Connection.

<b> &emsp; &emsp; signature</b>

```python
class EnvironmentGUIDMapper:
    """
    Attributes
    ----------
    environment_transformer : Callable(str) -> str
      a function which transforms the ENV name before adding it to the mapping
    """

    def __init__(self, environment_transformer: Callable[[str], str] = str.upper):
```

<b> &emsp; &emsp; usage</b>

```python
from thoughtspot_tml.utils import EnvironmentGUIDMapper

# create a new mapper
mapper = EnvironmentGUIDMapper()  # or EnvironmentGUIDMapper.read(path=...)

# map 3 guids to represent the same ThoughtSpot object across environments
mapper["guid1"] = ("PROD", "guid1")  # 1. add a new guid into the mapper
mapper["guid1"] = ("TEST", "guid2")  # 2. map guid1 to a guid in another environment
mapper["guid2"] = ("DEV", "guid3")   # 3. map a new guid3 to any of existing guid

# persist the mapping file to disk
mapper.save(path="marketing_thoughtspot_guid_mapping.json")

# what's the JSON data structure look like?
print(mapper)
{
    "guid1__guid2__guid3": {
        "PROD": "guid1",
        "TEST": "guid2",
        "DEV": "guid3"
    }
}

# create a new mapper from a file
new_mapper = EnvironmentGUIDMapper.read(path="marketing_thoughtspot_guid_mapping.json")

# add another object mapping
new_mapper.set("guid10", environment="PROD", guid="guid10")   # equivalent to new_mapper["guid10"] = ("PROD", "guid10")
new_mapper.set("guid10", environment="TEST", guid="guid11")
new_mapper.set("guid10", environment="DEV", guid="guid12")

# get all the environments that would map to "guid10"
print(new_mapper["guid10"])  # or  new_mapper.get("guid10")
{
    "PROD": "guid10",
    "TEST": "guid11",
    "DEV": "guid12"
}

# get a mapping of all DEV -> PROD related ThoughtSpot objects
print(new_mapper.generate_mapping(from_environment="DEV", to_environment="PROD"))
{
    "guid3": "guid1",
    "guid12": "guid10"
}
```


### `disambiguate`

In __ThoughtSpot__, the uniqueness constraint exists on the underlying object's `guid`. This means that there can be multiple objects of the same type with the same name. An example of this is maintaining both a DEV and PROD Connection. All the development work happens on one set of objects (that are not shared with any of the End User community), while the production connection contains objects with identical names that *are* shared with the End User community.

To reduce ambiguity, you may need to add the `fqn` key to your TML document when you reference source tables or connections. If you do not add the `fqn` key, and the connection or table you reference does not have a unique name, the import will fail.

__NOTE__: *Prior to __ThoughtSpot__ V8.7.0, TML does not export with the `fqn` automatically.*

<b> &emsp; &emsp; signature</b>

```python
def disambiguate(
    tml: TMLObject,
    *,
    guid_mapping: Dict[str, GUID],
    remap_object_guid: bool = True,
    delete_unmapped_guids: bool = False,
) -> TMLObject:
    """
    Deep scan the TML looking for fields to add FQNs to.

    This will explore the top-level guid and all nested objects looking on
    Tables, Worksheets, etc to disambiguate.

    Parameters
    ----------
    tml : TMLObject
      the tml to scan

    guid_mapping : {str: GUID}
      a mapping of names or guids, to the FQN to add to the object

    remap_object_guid : bool = True
      whether or not to remap the tml.guid

    delete_unmapped_guids : bool = False
      if a match could not be found, set the FQN and object guid to None
    """
```

<b> &emsp; &emsp; usage</b>

```python
from thoughtspot_tml.utils import disambiguate
from thoughtspot_tml import Worksheet

# Load a Worksheet and check its data
ws = Worksheet.load("tests/data/DUMMY.worksheet.tml")
ws.guid == "2ea7add9-0ccb-4ac1-90bb-231794ebb377"     # => True
ws.worksheet.tables[0].name == "dim_retapp_products"  # => True
ws.worksheet.tables[0].fqn is None  # => True

# Assign a Table an FQN. This information can be retrieved from ThoughtSpot REST API metadata/list.
ws = disambiguate(ws, guid_mapping={"dim_retapp_products": "7fd39fdb-9dfe-4954-b5dd-9a5d846085b0"})
ws.worksheet.tables[0].fqn is None  # => False
ws.worksheet.tables[0].fqn == "7fd39fdb-9dfe-4954-b5dd-9a5d846085b0"  # => True

# Re-assign the GUID to a new environment.
ws = disambiguate(ws, guid_mapping={"7fd39fdb-9dfe-4954-b5dd-9a5d846085b0": "99999999-9999-4999-9999-999999999999"})
ws.worksheet.tables[0].fqn == "7fd39fdb-9dfe-4954-b5dd-9a5d846085b0"  # => True
ws.worksheet.tables[0].fqn == "99999999-9999-4999-9999-999999999999"  # => False

# Remove GUIDs which aren't found in the mapping, including the top-level GUID.
ws = disambiguate(ws, guid_mapping={}, delete_unmapped_guids=True)
ws.worksheet.tables[0].name == "dim_retapp_products"  # => True
ws.worksheet.tables[0].fqn is None  # => True
ws.guid is None   # => True
```

The `disambiguate` function will walk through the `thoughtspot_tml` TML object specifying the `.fqn` based on keys in the `guid_mapping` dictionary.

The `guid_mapping` will typically be a mapping of GUIDs between 2 environments, but the "before" environment can be any string. This can be helpful to quickly add `fqn` to any object which has yet to define it.

The `remap_object_guid` (__default__: `True`) will consider the top-level `TML.guid` as a candidate for re-mapping.

The `delete_unmapped_guids` (__default__: `False`) will remove any `.fqn`s which are not found in the `guid_mapping`.

---

## Migration to v2.0.0

With __V2.0.0__, we now programmatically build the TML spec from the underlying microservice's data structure. The largest benefit of this move is that we can now 

### Round-tripping to File

The utility class `YAMLTML` has been replaced with `utils.determine_tml_type` and a private base class `TML`, which all public metadata objects inherit from. The TML type which is returned has the appropriate [de]serialization methods.

Both of the following patterns represent round-tripping.

```python
import pathlib

worksheet_fp = "tests/data/DUMMY.worksheet.tml"
worksheet_tml_str = pathlib.Path(worksheet_fp).read_text()

# V1.3.0
from thoughtspot_tml import YAMLTML

tml = YAMLTML.get_tml_object(worksheet_tml_str)
tml_document_str = YAMLTML.dump_tml_object(tml)


# V2.0.0
from thoughtspot_tml.utils import determine_tml_type
from thoughtspot_tml import Worksheet

tml_cls = determine_tml_type(path=worksheet_fp)
tml = tml_cls.loads(worksheet_tml_str)
# any one of these methods..
# tml = tml_cls.load(worksheet_fp)
# tml = Worksheet.loads(worksheet_tml_str)
# tml = Worksheet.load(worksheet_fp)
tml_document_str = tml.dumps(worksheet_fp)
```

### Identifying the TML Object Type

To identify the type of TML object you are working with in __V1.3.0__ you would use `.content_type`, with __V2.0.0__ you can now use `.tml_type_name`.

### GUID & FQN Handling

In __V1.3.0__, GUIDs were deleted from the underlying data structure with `.remove_guid()` in order to ensure the REST API created new objects. With __V2.0.0__, you simply set the `.guid` attribute (on the object itself) to `None`.

```python
# V1.3.0
tml = YAMLTML.get_tml_object(worksheet_tml_str)
tml.remove_guid()


# V2.0.0
tml = Worksheet.loads(worksheet_tml_str)
tml.guid = None
```

In __V1.3.0__, each TML object had their own methods for finding and replacing GUIDs. These took the form of `.remap_<object_type>_to_new_fqn()` and `.change_<object_type>_by_fqn()`, replacing `<object_type>` for the underlying data source which maps into the object you're operating on. These methods modify the underlying object.

In __V2.0.0__, we supply a single method to help add the `fqn` key to your TML document when referencing source tables or connections that share a name. [See disambiguation](#) for additional information.

For example, the below example shows adding the Table FQN references in a Worksheet.

```python
# V1.3.0
name_guid_map = {"Table 1": "0f814ce1-dba1-496a-b3de-38c4b9a288ed", "Table 2": "2e7a0676-2acf-4700-965c-efebf8c0b594"}
tml = YAMLTML.get_tml_object(worksheet_tml_str)
tml.remap_table_to_new_fqn(name_to_fqn_map=name_guid_map)
# - or -
tml.change_table_by_fqn(original_table_name="Table 1", new_table_guid="0f814ce1-dba1-496a-b3de-38c4b9a288ed")


# V2.0.0
from thoughtspot_tml.utils import disambiguate

tml = Worksheet.loads(worksheet_tml_str)
tml = disambiguate(tml, guid_mapping=name_guid_map)
```

---

## Notes on __ThoughtSpot Modeling Language__

- TML is implemented in the YAML 1.1 spec.
- When importing a TML file, if the `guid` matches to an existing object, then that object will be updated. If the `guid` is missing or does not match an object, a new object is created with a new GUID.

## Want to contribute?

We welcome all help! :heart: For guidance on setting up a development environment, see our [Contributing Guide][contrib].

[examples]: examples/README.md
[contrib]: .github/CONTRIBUTING.md
[py-scriptability]: src/thoughtspot_tml/_scriptability.py
[py-dataclasses-field]: https://docs.python.org/3/library/dataclasses.html#dataclasses.field
[docs-fqn]: https://developers.thoughtspot.com/docs/?pageid=development-and-deployment#_duplicate_object_names
[rest-api]: https://developers.thoughtspot.com/docs/?pageid=rest-apis
[rest-api-import]: https://developers.thoughtspot.com/docs/?pageid=tml-api#import
[rest-api-export]: https://developers.thoughtspot.com/docs/?pageid=tml-api#export
[rest-api-cnxn-list]: https://developers.thoughtspot.com/docs/?pageid=connections-api#live-query-connections
[rest-api-cnxn-update]: https://developers.thoughtspot.com/docs/?pageid=connections-api#edit-connection
[syntax-tml]: https://docs.thoughtspot.com/cloud/latest/tml
[syntax-table]: https://docs.thoughtspot.com/cloud/latest/tml#syntax-tables
[syntax-view]: https://docs.thoughtspot.com/cloud/latest/tml#syntax-views
[syntax-sqlview]: https://docs.thoughtspot.com/cloud/latest/tml#syntax-sqlviews
[syntax-worksheet]: https://docs.thoughtspot.com/cloud/latest/tml#syntax-worksheets
[syntax-answer]: https://docs.thoughtspot.com/cloud/latest/tml#syntax-answers
[syntax-liveboard]: https://docs.thoughtspot.com/cloud/latest/tml#syntax-liveboards
