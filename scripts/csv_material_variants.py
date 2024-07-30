
# SPDX-FileCopyrightText: Copyright (c) 2024 NVIDIA CORPORATION & AFFILIATES. All rights reserved.
# SPDX-License-Identifier: LicenseRef-NvidiaProprietary
#
# NVIDIA CORPORATION, its affiliates and licensors retain all intellectual
# property and proprietary rights in and to this material, related
# documentation and any modifications thereto. Any use, reproduction,
# disclosure or distribution of this material and related documentation
# without an express license agreement from NVIDIA CORPORATION or
# its affiliates is strictly prohibited.

"""
The purpose of this module is to show you how you could implement a script that can create material variants based off of csv data.

Version: 1.0.0
"""
import csv
import pathlib
import asyncio
from pxr import UsdShade, Sdf
import pxr
import omni.usd
import omni.mdl.usd_converter
import omni.kit.commands
import omni.kit.app
import omni.log


CSV_COLUMNS = ['material_prim_path', 'variant_set_name', 'variant_name', 'variant_values', 'default']

###############################################################
########################## UTILITIES ##########################
###############################################################

def get_usd_context() -> omni.usd.UsdContext:
    """Get the usd context

    Returns:
        omni.usd._usd.UsdContext: https://docs.omniverse.nvidia.com/kit/docs/omni.usd/latest/omni.usd/omni.usd.UsdContext.html#omni.usd.UsdContext
    """
    return omni.usd.get_context()

def get_stage() -> pxr.Usd.Stage:
    """Get stage

    Returns:
        pxr.Usd.Stage: https://openusd.org/dev/api/class_usd_stage.html
    """
    usd_context = get_usd_context()
    return usd_context.get_stage()




########################################################################################
########################## READING AND CREATING VARIANTS ###############################
########################################################################################
  
def create_variants(csv_file_path: str) -> None:
    """Read csv file and create variants. 

    The csv file is encoded like this:
    column:material_prim_path - /World/Looks/Carpaint_05
    column:variant_set_name - Car_Paint
    column:variant_name - black
    column:variant_values - {"inputs:diffuse_reflection_color":(0.023102053, 0.023102075, 0.023102283), "inputs:coat_color":(0, 0, 0)}
    column:default - TRUE

    Modifications are encoded in the csv as a dictionary.
    Example from the csv "variant_values" column - {"inputs:diffuse_reflection_color":(0.03653, 0.078187, 0.02887), "inputs:coat_color":(1.0, 1.0, 1.0)}

    Note: make sure that the dict is encoded correctly - the string is evaluated into a dictionary and will report an error if syntax is incorrect.

    Args:
        csv_file_path (str): Path to the csv file to read and act on.
    """
    variant_creation_data = []
    with open(csv_file_path, mode='r', newline='') as csv_file:
        csv_reader = csv.reader(csv_file)

        # Skip the header row
        next(csv_reader)
        for row in csv_reader:
            row_data = []
            material_prim_path = row[0]
            if not material_prim_path:
                continue
            source_material_prim = omni.usd.get_prim_at_path(Sdf.Path(material_prim_path))
            if not source_material_prim.IsValid():
                continue
            
            variant_set_name = row[1]
            variant_name = row[2]
            variant_values = {}
            if row[3]:
                try:
                    variant_values = eval(row[3])
                except:
                    omni.log.error(f"An error occurred when trying to evaluate the modifications dict. \nPlease correct this entry:\nSource material - {material_prim_path}\nErroneous Entry - {row[3]}")
                    continue
            default_state = row[4]
            row_data.append(material_prim_path)
            row_data.append(variant_set_name)
            row_data.append(variant_name)
            row_data.append(variant_values)
            row_data.append(default_state)
            variant_creation_data.append(row_data)

    if variant_creation_data:
        # This needs to be async because the shaders must be selected for the properties to exist
        asyncio.ensure_future(setup_variants(variant_creation_data))
    

# This needs to be async because the shaders must be selected for the properties to exist
async def setup_variants(variant_creation_data: list) -> None:
    """Main call to initiate variants setup

    Args:
        variant_creation_data (list): list of lists with [material_prim_path, variant_set_name, variant_name, variant_values, default]
    """
    # Store to see if we have a default, otherwise we need to initialize with a non defined default.
    for row_list in variant_creation_data:
        await create_variant(row_list)

    # Go through and initialize the variant default (if this is not done, you need to select the shader, then select the no variant, then select a variant)
    for row_list in variant_creation_data:
        default = True if row_list[4] == 'TRUE' else False
        if not default:
            continue

        material_prim_path = row_list[0]
        source_material_prim = omni.usd.get_prim_at_path(Sdf.Path(material_prim_path))
        source_material = UsdShade.Material(source_material_prim)
        shader = omni.usd.get_shader_from_material(source_material)
        
        variant_set_name = row_list[1].strip()
        variant_name = row_list[2].strip()
        variant_set = source_material_prim.GetVariantSet(variant_set_name)

        omni.usd.get_context().get_selection().clear_selected_prim_paths()
        omni.usd.get_context().get_selection().set_selected_prim_paths([shader.GetPath().pathString], True)

        for _ in range(2):
            await omni.kit.app.get_app().next_update_async()  

        variant_set.SetVariantSelection('')
        for _ in range(5):
            await omni.kit.app.get_app().next_update_async()  
        
        variant_set.SetVariantSelection(variant_name)
        for _ in range(5):
            await omni.kit.app.get_app().next_update_async()  

# Select, give shader properties a bit of time to populate, then modify.
async def create_variant(row_list) -> None:
    """Create the variant based on the data for the row

    Args:
        row_list (list): [material_prim_path, variant_set_name, variant_name, variant_values]
    """
    material_prim_path = row_list[0]
    source_material_prim = omni.usd.get_prim_at_path(Sdf.Path(material_prim_path))
    source_material = UsdShade.Material(source_material_prim)
    shader = omni.usd.get_shader_from_material(source_material)

    omni.usd.get_context().get_selection().clear_selected_prim_paths()
    omni.usd.get_context().get_selection().set_selected_prim_paths([shader.GetPath().pathString], True)

    # If the shaders do not get modified correctly, please increase the #5 value. 
    # This is how many ticks we give the shader properties to be accessible
    for _ in range(5):
        await omni.kit.app.get_app().next_update_async()  

    variant_set_name = row_list[1].strip()
    variant_name = row_list[2].strip()
    variant_values = row_list[3]

    variant_set = source_material_prim.GetVariantSet(variant_set_name)
    variant_set.AddVariant(variant_name)
    variant_set.SetVariantSelection(variant_name)

    for _ in range(5):
        await omni.kit.app.get_app().next_update_async()  
    with variant_set.GetVariantEditContext():
        for property_name, property_value in variant_values.items():

            attr = shader.GetPrim().GetAttribute(property_name)
            if not attr.IsValid():
                omni.log.warn(f'Skipping invalid attribute name - {property_name} - on prim {shader.GetPath().pathString}')
                continue
            try:
                attr.Set(property_value)
            except:
                pass


if __name__ == '__main__':
    # Open stage if you need to...
    # usd_stage_path = pathlib.Path("omniverse://Configurator/DeltaGenExample/Temp/csv_variants_test.usd").as_posix()
    # get_usd_context().open_stage(usd_stage_path)

    # Change this path
    csv_file_path = pathlib.Path("D:/Configurator/DeltaGenExample/70Mustang/material_variants_real.csv").as_posix()

    # Once file has been encoded, read the file, make replacements and optionally, modifications.
    create_variants(csv_file_path) # <--- Un-comment to read
    """Read csv file and create variants. 

    The csv file is encoded like this:
    column:material_prim_path - /World/Looks/Carpaint_05
    column:variant_set_name - Car_Paint
    column:variant_name - black
    column:variant_values - {"inputs:diffuse_reflection_color":(0.023102053, 0.023102075, 0.023102283), "inputs:coat_color":(0, 0, 0)}
    column:default - TRUE

    Modifications are encoded in the csv as a dictionary.
    Example from the csv "variant_values" column - {"inputs:diffuse_reflection_color":(0.03653, 0.078187, 0.02887), "inputs:coat_color":(1.0, 1.0, 1.0)}

    Note: make sure that the dict is encoded correctly - the string is evaluated into a dictionary and will report an error if syntax is incorrect.

    Args:
        csv_file_path (str): Path to the csv file to read and act on.
    """

