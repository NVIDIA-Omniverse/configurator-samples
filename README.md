# Configurator Samples

This repo is housing sample scripts and snippets to show developers how they could solve specific problems when creating configurators. It is not meant as complete solutions (if it works for you out of the box - great), but more like a source of inspiration for your own solutions.

Available scripts and snippets:<br>
Optimize File (optimize_file.py) - Conform a DELTAGEN export to Omniverse best practices<br>
Visibility Switches (visibility_switches.py) - Modify the switch variant functionality from DELTAGEN exports to visibility toggles<br>
CSV Material Replacements (csv_material_replacements.py) - A data driven material replacement workflow<br>
CSV Material Variants (csv_material_variants.py) - A data driven material variant creation workflow<br>
CSV to Json (csv_to_json.py) - Option packages data generation<br>
Reference Variants to Visibility (reference_variants_to_visibility.py) - Change variants that swap reference path to visibility switch<br>
Switch Variant (switch_variant.py) - Create visibility variants for each "switch variant"<br>
Resize Textures (resize_textures.py) - Resize images on hard drive<br>
Enable Streaming Extensions (enable_streaming_extensions.py) - snippet to load extensions<br>
Picking Mode (picking_mode.py) - snippet to set what is selectable in viewport<br>


## Scripts
Scripts containing a bit more involved suggestions on how to solve a particular workflow problem or how to make something more efficient or better performing.

### Optimize File
***Conform a DELTAGEN export to Omniverse best practices***<br>
(*scripts/deltagen/optimize_file.py*)<br>
Execute this script on the top-level USD (the script will modify all dependencies in place).<br>
The USD files exported from DELTAGEN will be conformed to OV standards by reparenting all layers under "/World" root primitive, updating all asset paths to UNIX format and setting root primitive as default.

### Visibility Switches
***Modify the switch variant functionality from DELTAGEN exports to visibility toggles***<br>
(*scripts/deltagen/visibility_switches.py*)<br>
This script will modify the behavior of switch variants from DELTAGEN USD exports so that they become visibility toggles. 
Execute this script directly on an opened stage that contains switch variants. For DELTAGEN exports, this is the 'model' 
export that contains geometry. 

### CSV Material Replacements
***Data driven material replacement workflow***<br>
(*scripts/csv_material_replacements.py*)<br>
Replace materials with other materials in a repeatable way. The use case this script was created for was to replace 
USD Preview Surface materials coming out of DELTAGEN with mdl materials from the Omniverse Automotive library.
> **_NOTE:_**  You could export mdl materials that are custom built for your specific setup and replace with that library.<br>

Example Table:
| source | target | new_instance | modifications | material_name |
|---|---|---|---|---|
| /World/Mustang_Stellar_materials/rubber_black_semigloss | https://omniverse-content-production.s3.us-west-2.amazonaws.com/Materials/2023_2_1/Automotive/Pristine/Tires/Pristine_Tire_Rubber_Clean.mdl |  | {"inputs:diffuse_reflection_color":(0.2, 0.2, 0.2)} |  |
| /World/Mustang_Stellar_materials/V_carpaint | https://omniverse-content-production.s3.us-west-2.amazonaws.com/Materials/2023_2_1/Automotive/Pristine/Carpaint/Carpaint_05.mdl |  | {"inputs:enable_flakes":0} | Carpaint_Body |
| /World/Mustang_Stellar_materials/white_rubber | https://omniverse-content-production.s3.us-west-2.amazonaws.com/Materials/2023_2_1/Automotive/Pristine/Tires/Pristine_Tire_Rubber_Clean.mdl | TRUE | {"inputs:enable_layer_1":1} |  |

#### Code Reference
##### Write - `def write(csv_file_path: str) -> None:`
Writes a csv file with all the material prim paths in the open stage.
If the file already exists, only materials that do not already exist in the file will be added and any replacements and modifications would be retained.
> **_TIP:_**  Because of the function's additive nature, you can build a project wide material replacement csv file that can be applied to many stages.

##### Create Material Library - `def create_material_library(csv_file_path: str) -> None:`
Parses the csv file and creates the materials that will be used to replace the original materials that are written out in the first step.<br>
This is useful, because it gives us a clean material USD file that we can also run the variant creation on. This can be sub layered into a file, and then we can run the material replacement function, that will now use the existing materials instead of also creating the materials, which is another option.<br>

Read csv file and create materials under the `MATERIAL_ROOT_PATH` that you will find at the top of the script file.<br> 
Defaults to `MATERIAL_ROOT_PATH = '/World/Looks'`<br>
Optionally, it will create a new shader, even if the shader already exists (otherwise it will automatically re-use)<br>
Example from the csv `"new_instance" column - TRUE `


Optionally, it will also apply modifications to the new shaders if a dict with property name and values are encoded.<br>
Example from the csv `"modifications" column - {"inputs:coat_color":(0.0, 0.0, 0.0), "inputs:enable_flakes":0}`

> **_NOTE:_**  make sure that the dictionary is encoded correctly - the string is evaluated into a dictionary and will report an error if syntax is incorrect.<br>
> **_TIP:_**  If you are going to create variants for certain properties on the shader, avoid creating a local opinion on that property at this step.

Optionally, you can also provide a new name for the shader. There is no need to flag "new_instance" when you do this the first time, only if you want to keep the same provided base name and create a new instance for modification reasons.<br>
Example from the csv `"shader_name" column - Glass_Reflectors_Base_Dark_Yellow`<br>


> **_TIP:_**  Make a new sub-layer and set it to "current authoring layer" before running this script. This will put the material replacements and the materials in a new usd file that you can add in at any point in your project setup.

##### Read Replace - `def read_replace(csv_file_path: str) -> None:`
Reads the csv file and replace all materials in the current stage if they have a replacement encoded.<br>
If the replacement material does not exist in the current stage, it will be created.<br>
Optionally, it will create a new shader, even if the shader already exists (otherwise it will automatically re-use)<br>
Example from the csv `"new_instance" column - TRUE`

Optionally, it will also apply modifications to the new shaders if a dict with property name and values are encoded.<br>
Example from the csv `"modifications" column - {"inputs:coat_color":(0.0, 0.0, 0.0), "inputs:enable_flakes":0}`
> **_NOTE:_**  make sure that the dictionary is encoded correctly - the string is evaluated into a dictionary and will report an error if syntax is incorrect.<br>

Optionally, you can also provide a new name for the shader. There is no need to flag "new_instance" when you do this the first time, only if you want to keep the same provided base name and create a new instance for modification reasons.
Example from the csv "shader_name" column - Glass_Reflectors_Base_Dark_Yellow

> **_TIP:_**  Make a new sub-layer and set it to "current authoring layer" before running this script. This will put the material replacements in a new usd file that you can add in at any point in your project setup. If you created a material library, you can add that in as a sub layer before running this and the materials from that sub layer will be used.

### CSV Material Variants
***Data driven material variant creation***<br>
(*scripts/csv_material_variants.py*)<br>
A script that can create material variants from csv data.

#### Code Reference
##### Create Variants - `def create_variants(csv_file_path: str) -> None:`
Read csv file and create variants.<br>
Example Table:<br>
| source | target | new_instance | modifications | material_name |
|---|---|---|---|---|
| /World/Mustang_Stellar_materials/rubber_black_semigloss | https://omniverse-content-production.s3.us-west-2.amazonaws.com/Materials/2023_2_1/Automotive/Pristine/Tires/Pristine_Tire_Rubber_Clean.mdl |  | {"inputs:diffuse_reflection_color":(0.2, 0.2, 0.2)} |  |
| /World/Mustang_Stellar_materials/V_carpaint | https://omniverse-content-production.s3.us-west-2.amazonaws.com/Materials/2023_2_1/Automotive/Pristine/Carpaint/Carpaint_05.mdl |  | {"inputs:enable_flakes":0} | Carpaint_Body |
| /World/Mustang_Stellar_materials/white_rubber | https://omniverse-content-production.s3.us-west-2.amazonaws.com/Materials/2023_2_1/Automotive/Pristine/Tires/Pristine_Tire_Rubber_Clean.mdl | TRUE | {"inputs:enable_layer_1":1} |  |

The csv file is encoded like this (with example data):<br>
`column:material_prim_path - value:/World/Looks/Carpaint_05` - The path to the material to add the variant to.<br>
`column:variant_name - value:black` - The variant set name to add.<br>
`column:variant_values - {"inputs:diffuse_reflection_color":(0.023102053, 0.023102075, 0.023102283), "inputs:coat_color":(0, 0, 0)}` - The variant data to encode in the form of a dictionary.<br>
> **_NOTE:_**  make sure that the dictionary is encoded correctly - the string is evaluated into a dictionary and will report an error if syntax is incorrect.<br>

### CSV to Json
***Package info generation***<br>
(*scripts/csv_to_json.py*)<br>
A script that will convert csv files containing configurator package information to json for use by a React application. The csv files define what data is needed and how it needs to be structured in order to be converted to a usable json format. This script requires two csv files - an "Options" csv and a "Packages" csv.<br>

#### Options CSV
Contains every possible option from the stage. These options need to be referenced by the Packages csv.<br>
Here are the rules for how this file is structured:
1. The first row is a header, and therefore shouldn’t contain any options. Although the columns have distinct meanings, what’s entered into this row won't impact the resulting json output.
2. Column 1 should contain a unique ID for the option (NOTE: each row represents an option).
3. Column 2 should contain a prim path
4. Column 3 should contain a variant set. This variant set should exist on the prim from column 2.
5. Column 4 should optionally contain a label for the variant set. If a label isn’t needed, this column still needs to exist, but the values can be empty.
6. Column 5 should contain a variant. This variant should be an available option on the variant set from column 3.
7. Column 6 should optionally contain a label for the variant. If a label isn’t needed, this column still needs to exist, but the values can be empty.
8. Column 7 should contain an optional graphic. 
9. Column 8 should contain an optional event

Example Table:<br>
| id | Prim Path | Variant Set | Option / Category (Optional) | Variant | Value Display Name (Optional) | Graphic (Optional) | Event (Optional) |
|---|---|---|---|---|---|---|---|
| 0 | /World/Prim | Color | Color | Red | Red |  |  |
| 1 | /World/Prim | Color | Color | Green | Green |  |  |
| 2 | /World/Prim | Color | Color | Blue | Blue |  |  |
| 3 | /World/Prim | Mesh | Mesh | Cube | Cube |  |  |
| 4 | /World/Prim | Mesh | Mesh | Sphere | Sphere |  |  |
| 5 | /World/Prim | Mesh | Mesh | Cylinder | Cylinder |  |  |

#### Packages CSV
Contains groupings of one or more option references (from the Options csv file), which together forms a 'package'. A name for the package is required, followed by an arbitrary number of Ids from the Options csv to associate with that package. Here are the rules for how this file is structured:
1. The first row is a header and shouldn’t contain any options. Although the columns have distinct meanings, what’s entered into this row won't impact the resulting json output.
2. Column 1 should contain a unique ID for the Package
3. Column 2 should contain a unique name for the Package.
4. Columns 3 and onward should contain an Id from the Options csv. Any number of columns may be added.<br>

Example Table:<br>
| Id | Name | Color | Mesh |
|---|---|---|---|
| 0 | Red Cube | 0 | 3 |
| 1 | Green Sphere | 1 | 4 |
| 2 | Blue Cylinder | 2 | 5 |

#### Code Reference
##### Create Json - `def create_json(options_csv: str, packages_csv: str, output_path: str) -> None:`
Creates and writes to disk the json containing package information for use by a React application.
##### Get Packages Json - `def get_packages_json(package_info: dict, include_id: bool = False) -> dict:`
Creates the data that's used for the packages JSON file
##### Get Packages with Options - `def get_packages_with_options(options: dict, packages: dict) -> dict:`
Returns a dictionary that combines Options csv data with Packages csv data
##### Get Raw Packages - `def get_raw_packages(packages_csv_path: str) -> dict:`
Returns a dictionary containing the values from a Packages csv
##### Get Raw Options - `def get_raw_options(options_csv_path: str) -> dict:`
Returns a dictionary containing the values from an Options csv

### Reference Variants to Visibility
***Change variants that swap reference path to visibility switch***<br>
(*scripts/reference_variants_to_visibility.py*)<br>
Find all variants that add a payload or reference to a prim and move them directly onto a new child prim.<br>
It then modifies the variant to toggle on the visibility of the prim that holds the reference, and visibility off on the prims that hold the remaining references.<br> 
Optionally allows to convert payloads to references, or references to payloads.
#### Code Reference
##### Convert - `def convert(convert_payloads_to_refs: bool=False, convert_references_to_payloads: bool=False) -> None:`
Script's entry point. Accepts two Booleans for converting payloads to references and references to payloads.
##### Move References - `def _move_references(layer: Sdf.Layer, prim: Sdf.PrimSpec) -> None:`
Creates child prims for each variant and moves references & payloads to them.
##### Move References Iter - `def _move_references_iter(layer: Sdf.Layer, vSpec: Sdf.PrimSpec) -> None:`
Contains the main logic for performing the moving references and payloads to a new prim.
##### Set Visibility - `def _set_visibility() -> None:`
Applies the visibility toggling behavior for variants.

### Switch Variant
***Create visibility variants for each switch variant***<br>
(*scripts/switch_variant.py*)<br>
This module will build switch variants using existing prims in a stage. A "switch variant" is a term used in certain apps such as DELTAGEN, which are variants that are used for toggling on the visibility of a prim within a set and toggling off the visibility of the other prims in the set.<br> 
When executed, a new variant set will be added to all prims that have matching names with the provided switch_prims list.<br>
The variant set will contain one visibility toggle variant for each child prim.<br>
#### Code Reference
##### Create - `def create(switch_prims: List[str] = ["Switch"], new_variant_set: str = "switchVariant") -> None:`
Script's entry point. Receives a list of prim names to perform this operation against and a variant set name to be created on those prims.

### Resize Textures
***Resize images on hard drive***<br>
(*scripts/resize_textures.py*)<br>
Resize textures sizes from hard drive. Made to act on a Configurator Published folder on your local hard drive to optimize configurator performance before packaging it for GDN.
#### Code Reference
##### Get Files Of Type - `def get_files_of_type(root_folder: str, file_extension: str) -> List[str]:`
At the bottom of the script, modify the target_root directory to the directory you want the script to act on.
The files list uses a function that will find all files of a type - the default is png files.
##### Print Info - `def print_info(files: List[str], max_size:int=2048):`
Scout function to console print all files found larger than the passed in max size argument. Will also inform files with a higher bit depth than 8.
##### Down Res - `def down_res(files: List[str], max_size:int=1024, enforce_8_bit_depth:bool=False):`
Down res files to the passed in max size integer and optionally enforce 8 bit images.

## Snippets
Bite sized code snippets to show you how to achieve a specific task.

### Enable Streaming Extensions
(*snippets/enable_streaming_extensions.py*)<br>
Demonstrates how to load the streaming extensions via Python. Just change the extension list to modify this to load any extensions you like via Python.

```python 
import omni.kit.app

manager = omni.kit.app.get_app().get_extension_manager()
extensions = ['omni.kit.livestream.messaging', 'omni.kit.livestream.webrtc.setup', 'omni.services.streamclient.webrtc']
for extension in extensions:
    manager.set_extension_enabled_immediate(extension, True)
```

### Picking Mode
(*snippets/picking_mode.py*)<br>
Demonstrates how to set what is selectable via mouse click within a kit viewport. 
When executed, only the prims associated with the supplied prim type(s) will be selectable via mouse 
click in the viewport.
```python 
import carb

ALL = "type:ALL"
MESH = "type:Mesh"
CAMERA = "type:Camera" 
LIGHTS = "type:CylinderLight;type:DiskLight;type:DistantLight;type:DomeLight;type:GeometryLight;type:Light;type:RectLight;type:SphereLight"

if __name__ == "__main__":
    # change MESH to ALL, CAMERA or LIGHTS for those prim types to be selectable
    carb.settings.get_settings().set("/persistent/app/viewport/pickingMode", MESH)
```


