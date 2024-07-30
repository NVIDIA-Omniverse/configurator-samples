
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
The purpose of this module is to show you how you could implement a script that can replace materials 
with other materials in a repeatable way. The use case this script was created for was to replace 
USD Preview Surface materials coming out of DeltaGen with mdl materials from the Omniverse Automotive library.

Note: You could export mdl materials that are custom built for your specific setup and replace with that custom
library.

Version: 1.0.0
"""
from typing import List
import os
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


CSV_COLUMNS = ['source', 'target', 'new_instance', 'modifications', 'material_name', 'sub_identifier']
MATERIAL_ROOT_PATH = '/World/Looks'

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

def get_materials_from_stage(filter_out_unbound: bool = False):
    """Get a lost of all materials from the stage

    Args:
        filter_out_unbound (bool, optional): filter out unbound materials. Defaults to False.

    Returns:
        list: list of pxr.Usd.Prim
    """
    all_materials = list(filter(lambda x: UsdShade.Material(x), get_stage().Traverse()))
    if filter_out_unbound:
        return [material for material in all_materials if is_mdl_bound(material)]
    return all_materials

def is_mdl_bound(material: pxr.Usd.Prim) -> bool:
    """Check if material is bound

    Args:
        material (UsdShade.Material): material to check

    Returns:
        bool: True/False if material is bound
    """
    stage = get_stage()
    return omni.mdl.usd_converter.is_material_bound_to_prim(stage, material)

def get_selected_prims() -> List[pxr.Usd.Prim]:
    """Get selected prims

    Returns:
        list of pxr.Usd.Prim: Selected prims
    """
    usd_context = get_usd_context()
    stage = get_stage()
    if stage:
        return [stage.GetPrimAtPath(prim_path) for prim_path in usd_context.get_selection().get_selected_prim_paths()]

def get_available_prim_path(base_path: str) -> str:
    """Generate a valid prim path using the input name

    Args:
        base_path (str): prim path that we would like to use

    Returns:
        str: Available prim path
    """
    index = 1
    available_path = base_path
    while get_stage().GetPrimAtPath(available_path):
        available_path = Sdf.Path(f'{base_path}_{str(index)}')
        index += 1
    return available_path

########################################################################################
########################## WRITING MATERIAL CSV               ##########################
########################## READING AND REPLACING MATERIAL CSV ##########################
########################################################################################

def write(csv_file_path: str) -> None:
    """Writes a csv file with all the material prim paths in the open stage.
    If the file already exists, only materials that does not already exist in the file will be added and any replacements and
    modifications would be retained.

    Tip: Because of it's additive nature you can build a project wide material replacement csv file that can be applied to many stages.

    Args:
        csv_file_path (str): A file path where the csv file should be written.
    """
    all_materials = get_materials_from_stage()
    if not all_materials:
        return
    
    material_replacement_list = []
    source_dict = {}
    if os.path.exists(csv_file_path):
        with open(csv_file_path, mode='r', newline='') as csv_file:
                csv_reader = csv.reader(csv_file)

                # Skip the header row
                next(csv_reader)

                for row in csv_reader:
                    source_material = row[0]
                    target_material = row[1]
                    new_instance = row[2]
                    modifications = row[3]
                    material_name = row[4]
                    sub_identifier = row[5]
                    row_list = [target_material, new_instance, modifications, material_name, sub_identifier]
                    source_dict[source_material] = row_list

    for material_prim in all_materials:
        # If we already have a csv_file and
        # If the shader is already present, use already existing data
        if source_dict and material_prim.GetPath().pathString in source_dict.keys():
            options_list = source_dict[material_prim.GetPath().pathString]
            material_replacement_list.append({'source':material_prim.GetPath().pathString, 'target':options_list[0], 'new_instance':options_list[1], 'modifications':options_list[2], 'material_name':options_list[3], 'sub_identifier':options_list[4]})
        else:
            material_replacement_list.append({'source':material_prim.GetPath().pathString})

    # writing to csv file
    with open(csv_file_path, 'w', newline='') as csv_file:
        writer = csv.DictWriter(csv_file, fieldnames=CSV_COLUMNS)
        writer.writeheader()
        writer.writerows(material_replacement_list)

def create_material_library(csv_file_path: str) -> None:
    """This will parse the csv file and create the materials that will be used to replace the original materials that are written out in the first step.
    This is useful, because it gives us a clean material USD file that we can also run the variant creation on. This can be sublayered into a file,
    and then we can run the material replacement function, that will now use the existing materials instead of also creating the materials, which is another option.

    Read csv file and create material under the MATERIAL_ROOT_PATH. 

    Optionally, it will create a new shader, even if the shader already exists (otherwise it will automatically re-use)
    Example from the csv "new_instance" column - TRUE

    Optionally, it will also apply modifications to the new shaders if a dict with property name and values are encoded.
    Example from the csv "modifications" column - {"inputs:coat_color":(0.0, 0.0, 0.0), "inputs:enable_flakes":0}

    Note: make sure that the dict is encoded correctly - the string is evaluated into a dictionary and will report an error if syntax is incorrect.
    Tip: If you are going to create variants for certain properties on the shader, avoid creating a local opinion on that property at this step.

    Optionally, you can also provide a new name for the shader. There is no need to flag "new_instance" when you do this the first time, only if
    you want to keep the same provided base name and create a new instance for modification reasons.
    Example from the csv "shader_name" column - Glass_Reflectors_Base_Dark_Yellow
    
    Tip: Make a new sub-layer and set it to "current authoring layer" before running this script. This will put the material replacements 
    and the materials in a new usd file that you can add in at any point in your project setup.

    Args:
        csv_file_path (str): path to the csv file.
    """
    shader_modifications = {}
    with open(csv_file_path, mode='r', newline='') as csv_file:
        csv_reader = csv.reader(csv_file)

        # Skip the header row
        next(csv_reader)

        for row in csv_reader:
            target_material = row[1]
            if not target_material:
                continue
            source_material = row[0]

            new_instance = False if not row[2] or row[2] == 'FALSE' else True
            modifications = {}
            if row[3]:
                try:
                    modifications = eval(row[3])
                except:
                    omni.log.error(f"An error occurred when trying to evaluate the modifications dict. \nPlease correct this entry:\nSource material - {source_material}\nErroneous Entry - {row[3]}")
            material_base_name = pathlib.Path(target_material).stem
            material_name = material_base_name if not row[4] else row[4].replace(' ', '_')
            if row[5]:
                material_base_name = row[5]

            material_path = f"{MATERIAL_ROOT_PATH}/{material_name}"
            target_material_prim = omni.usd.get_prim_at_path(Sdf.Path(material_path))
            if not target_material_prim.IsValid():
                omni.kit.commands.execute("CreateMdlMaterialPrim", mtl_url=target_material, mtl_name=material_base_name , mtl_path=material_path)

            else:
                if new_instance:
                    material_path = get_available_prim_path(material_path)
                    omni.kit.commands.execute("CreateMdlMaterialPrim", mtl_url=target_material, mtl_name=material_base_name , mtl_path=material_path)
                
            target_material_prim = omni.usd.get_prim_at_path(Sdf.Path(material_path))
            target_material = UsdShade.Material(target_material_prim)
            shader = omni.usd.get_shader_from_material(target_material)

            if modifications:
                shader_modifications[shader] = modifications

    if shader_modifications:
        # This needs to be async because the shaders must be selected for the properties to exist
        asyncio.ensure_future(setup_modify_shaders(shader_modifications))


def read_replace(csv_file_path: str) -> None:
    """Read csv file and replace all materials in the current stage if they have a replacement encoded. 

    Optionally, it will create a new shader, even if the shader already exists (otherwise it will automatically re-use)
    Example from the csv "new_instance" column - TRUE

    Optionally, it will also apply modifications to the new shaders if a dict with property name and values are encoded.
    Example from the csv "modifications" column - {"inputs:coat_color":(0.0, 0.0, 0.0), "inputs:enable_flakes":0}

    Note: make sure that the dict is encoded correctly - the string is evaluated into a dictionary and will report an error if syntax is incorrect.

    Optionally, you can also provide a new name for the shader. There is no need to flag "new_instance" when you do this the first time, only if
    you want to keep the same provided base name and create a new instance for modification reasons.
    Example from the csv "shader_name" column - Glass_Reflectors_Base_Dark_Yellow
    
    Tip: Make a new sub-layer and set it to "current authoring layer" before running this script. This will put the material replacements 
    and the materials in a new usd file that you can add in at any point in your project setup.

    Args:
        csv_file_path (str): Path to the csv file to read and act on.
    """
    shader_modifications = {}
    instance_counter = {}
    with open(csv_file_path, mode='r', newline='') as csv_file:
        csv_reader = csv.reader(csv_file)

        # Skip the header row
        next(csv_reader)

        for row in csv_reader:
            target_material = row[1]
            if not target_material:
                continue
            source_material = row[0]
            source_material_prim = omni.usd.get_prim_at_path(Sdf.Path(source_material))
            if not source_material_prim.IsValid():
                continue

            new_instance = False if not row[2] or row[2] == 'FALSE' else True
            modifications = {}
            if row[3]:
                try:
                    modifications = eval(row[3])
                except:
                    omni.log.error(f"An error occurred when trying to evaluate the modifications dict. \nPlease correct this entry:\nSource material - {source_material}\nErroneous Entry - {row[3]}")
            
            material_base_name = pathlib.Path(target_material).stem
            material_name = material_base_name if not row[4] else row[4].replace(' ', '_')
            if row[5]:
                material_base_name = row[5]
            material_path = f"{MATERIAL_ROOT_PATH}/{material_name}"
            target_material_prim = omni.usd.get_prim_at_path(Sdf.Path(material_path))
            # Material does not exist
            if not target_material_prim.IsValid():
                omni.kit.commands.execute("CreateMdlMaterialPrim", mtl_url=target_material, mtl_name=material_base_name , mtl_path=material_path)
            # Existing material, re-use, but we might have a new instance already existing. Need to make an assumption that we want to use an existing library if a new instance path is found.
            else:
                if new_instance:
                    # Check if we already have a library material for the instance flag
                    index = '1'
                    if material_path in instance_counter.keys():
                        index = instance_counter[material_path].split('_')[-1]
                    test_material_path = f'{material_path}_{index}'
                    if omni.usd.get_prim_at_path(Sdf.Path(test_material_path)):
                        instance_counter[material_path] = f'{material_path}_{str(int(index)+1)}'
                        material_path = test_material_path
                    else:
                        material_path = get_available_prim_path(material_path)
                        omni.kit.commands.execute("CreateMdlMaterialPrim", mtl_url=target_material, mtl_name=material_base_name , mtl_path=material_path)
                
            target_material_prim = omni.usd.get_prim_at_path(Sdf.Path(material_path))
            target_material = UsdShade.Material(target_material_prim)
            shader = omni.usd.get_shader_from_material(target_material)

            # Assign Shader
            omni.usd.get_context().get_selection().clear_selected_prim_paths()
            paths = []
            for prim in omni.usd.get_context().get_stage().Traverse():
                if omni.usd.is_prim_material_supported(prim):
                    mat, rel = UsdShade.MaterialBindingAPI(prim).ComputeBoundMaterial()
                    if mat and mat.GetPrim().GetPath() == source_material_prim.GetPath():
                        paths.append(prim.GetPath().pathString)

            omni.usd.get_context().get_selection().set_selected_prim_paths(paths, True)
            target_material = UsdShade.Material(target_material_prim)
            selected_prims = get_selected_prims()
            for selected_prim in selected_prims:
                UsdShade.MaterialBindingAPI(selected_prim).Bind(target_material)

            if modifications:
                shader_modifications[shader] = modifications

    if shader_modifications:
        # This needs to be async because the shaders must be selected for the properties to exist
        asyncio.ensure_future(setup_modify_shaders(shader_modifications))


# This needs to be async because the shaders must be selected for the properties to exist
async def setup_modify_shaders(shader_modifications: dict) -> None:
    """Main call to initiate all the shader modifications

    Args:
        shader_modifications (dict): dict with shader prim key and dictionary of property name : property value modifications
    """
    for shader, modifications in shader_modifications.items():
        await modify_shader(shader, modifications)


# Select, give shader properties a bit of time to populate, then modify.
async def modify_shader(shader: pxr.UsdShade.Shader, modifications: dict) -> None:
    """Modify an individual shader with the modifications

    Args:
        shader (UsdShade.Shader): The shader to be modified
        modifications (dict): dictionary of property name key(s) and property value value(s)
    """
    omni.usd.get_context().get_selection().clear_selected_prim_paths()
    omni.usd.get_context().get_selection().set_selected_prim_paths([shader.GetPath().pathString], True)

    # If the shaders do not get modified correctly, please increase the #5 value. 
    # This is how many ticks we give the shader properties to be accessible
    for _ in range(5):
        await omni.kit.app.get_app().next_update_async()  

    for attr_name, attr_value in modifications.items():
        attr = shader.GetPrim().GetAttribute(f"{attr_name}")
        if not attr.IsValid():
            print(f'Skipping invalid attribute name - {attr_name} - on prim {shader.GetPath().pathString}')
            continue
        attr.Set(attr_value)


if __name__ == '__main__':
    # Open stage if you need to...
    # usd_stage_path = pathlib.Path("D:/Configurator/DeltaGenExample/70Mustang/70Mustang_Ingest/70Mustang_mono.usdc").as_posix()
    # get_usd_context().open_stage(usd_stage_path)

    # Change this path
    csv_file_path = pathlib.Path("D:/Configurator/DeltaGenExample/70Mustang/material_replacements.csv").as_posix()
    # Dump the material paths to the csv file where we will encode the material replacements
    write(csv_file_path) # <--- Un-comment to write
    """Writes a csv file with all the material prim paths in the open stage.
    If the file already exists, only materials that does not already exist in the file will be added and any replacements and
    modifications would be retained.

    Tip: Because of it's additive nature you can build a project wide material replacement csv file that can be applied to many stages.

    Args:
        csv_file_path (str): A file path where the csv file should be written.
    """


    # Once file has been encoded, read the file and create a material library. This can then be inserted as a sub-layer and the materials will automatically be used in the next step.
    # create_material_library(csv_file_path)
    """This will parse the csv file and create the materials that will be used to replace the original materials that are written out in the first step.
    This is useful, because it gives us a clean material USD file that we can also run the variant creation on. This can be sublayered into a file,
    and then we can run the material replacement function, that will now use the existing materials instead of also creating the materials, which is another option.

    Read csv file and create material under the MATERIAL_ROOT_PATH. 

    Optionally, it will create a new shader, even if the shader already exists (otherwise it will automatically re-use)
    Example from the csv "new_instance" column - TRUE

    Optionally, it will also apply modifications to the new shaders if a dict with property name and values are encoded.
    Example from the csv "modifications" column - {"inputs:coat_color":(0.0, 0.0, 0.0), "inputs:enable_flakes":0}

    Note: make sure that the dict is encoded correctly - the string is evaluated into a dictionary and will report an error if syntax is incorrect.
    Tip: If you are going to create variants for certain properties on the shader, avoid creating a local opinion on that property at this step.

    Optionally, you can also provide a new name for the shader. There is no need to flag "new_instance" when you do this the first time, only if
    you want to keep the same provided base name and create a new instance for modification reasons.
    Example from the csv "shader_name" column - Glass_Reflectors_Base_Dark_Yellow
    
    Tip: Make a new sub-layer and set it to "current authoring layer" before running this script. This will put the material replacements 
    and the materials in a new usd file that you can add in at any point in your project setup.

    Args:
        csv_file_path (str): path to the csv file.
    """


    # Once file has been encoded, read the file, make replacements and optionally, modifications.
    # read_replace(csv_file_path) # <--- Un-comment to read
    """Read csv file and replace all materials in the current stage if they have a replacement encoded. 

    Optionally, it will create a new shader, even if the shader already exists (otherwise it will automatically re-use)
    Example from the csv "new_instance" column - TRUE

    Optionally, it will also apply modifications to the new shaders if a dict with property name and values are encoded.
    Example from the csv "modifications" column - {"inputs:coat_color":(0.0, 0.0, 0.0), "inputs:enable_flakes":0}

    Note: make sure that the dict is encoded correctly - the string is evaluated into a dictionary and will report an error if syntax is incorrect.

    Tip: Make a new sub-layer and set it to "current authoring layer" before running this script. This will put the material replacements 
    and the materials in a new usd file that you can add in at any point in your project setup.

    Args:
        csv_file_path (str): Path to the csv file to read and act on.
    """

