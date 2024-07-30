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
This script will get all files of a type off of a target folder on your local machine. 
You can then scale these images using a max size input.
You can also change the bit depth to 8 if you have 16 or 32 bit textures.

Version: 1.0.0
"""

from typing import List
import sys


# If we are running the script inside a kit app, auto install missing libraries
if sys.executable.endswith('kit.exe'):
    import omni.kit.pipapi
    try:
        from PIL import Image
    except ImportError:
        omni.kit.pipapi.install("PIL", module="PIL")
        from PIL import Image
    try:
        import numpy
    except ImportError:
        omni.kit.pipapi.install("numpy", module="numpy")
        import numpy
else:
    from PIL import Image
    import numpy

import glob
import pathlib


def get_image_bit_depth(image_path: str) -> int:
    """Get the bit depth of the image passed in

    Args:
        image_path (str): Path string of the image

    Raises:
        NotImplementedError: An unaccounted for bit depth - this should not happen

    Returns:
        int: bit depth integer
    """
    image = None
    try:
        image = Image.open(image_path)
    except:
        print(f'Error opening image - {image_path}')
        return

    image_array = numpy.array(image)
    if image_array.dtype == numpy.uint8:
        return 8
    if image_array.dtype == numpy.int8:
        return 8
    if image_array.dtype == numpy.uint16:
        return 16
    if image_array.dtype == numpy.int16:
        return 16
    if image_array.dtype == numpy.uint32:
        return 32
    if image_array.dtype == numpy.int32:
        return 32
    if image_array.dtype == numpy.float32:
        return 32
    if image_array.dtype == numpy.float64:
        return 64

    raise NotImplementedError(f'The following bit depth is not counted for - {image_array.dtype}\nImage path - {image_path}')


def get_files_of_type(root_folder: str, file_extension: str) -> List[str]:
    """Get all files of the file extension from the root folder passed in

    Args:
        root_folder (str): Path string to root folder
        file_extension (str): The file types we are looking for

    Returns:
        list: list of files found
    """
    files = []
    for file_path in glob.iglob(root_folder + f'/**/*{file_extension}', recursive=True):
        files.append(pathlib.Path(file_path).as_posix())
    return files


def down_res(files: List[str], max_size:int=1024, enforce_8_bit_depth:bool=False):
    """Down res files and optionally enforce 8 bit images

    Args:
        files (list): a list of file paths of images to down res
        max_size (int, optional): Max size of images, anything square aspect ratio files will get reduced in resolution. Defaults to 1024.
        enforce_8_bit_depth (bool, optional): Enforce 8 bit images. Defaults to False.
    """
    for file in files:
        im = Image.open(file)
        size_x = im.size[0]
        size_y = im.size[1]

        # Only fix square images
        if size_x == size_y:
            if im.size[0] > max_size:
                print(f'Resizing - From {size_x} - to {max_size} - {file}')
                im = im.resize((max_size, max_size))
        
        # Enforce 8 bits (optionally)
        if enforce_8_bit_depth:
            bit_depth = get_image_bit_depth(file)
            if bit_depth > 8:
                print(f'Changing bit depth - From {bit_depth} - to 8 - {file}')
                array = numpy.uint8(numpy.array(im) / 256)
                im = Image.fromarray(array)

        im.save(fp=file)


def print_info(files: List[str], max_size:int=2048):
    """Scout function to console print all files found larger than max size. Will also inform files with a higher bit depth than 8

    Args:
        files (list): a list of file paths of images to investigate
        max_size (int, optional): Max size of images, anything square aspect ratio files will get inspected. Defaults to 2048.
    """
    for file in files:
        im = Image.open(file)
        size_x = im.size[0]
        size_y = im.size[1]

        # Only inspect square images
        if size_x == size_y:
            if im.size[0] > max_size:
                print(f'Size larger - {size_x} - {file}')
        else:
            print(f'Skipping - {file} - not square ratio: x:{size_x}, y:{size_y}')
        
        # Inform if bit depth is higher than 8
        bit_depth = get_image_bit_depth(file)
        if bit_depth > 8:
            print(f'Bit depth higher - {bit_depth} - {file}')


if __name__ == "__main__":
    # Set this to your root directory with textures you want to get info on or down res
    target_root="C:/Configurators/ProductA"
    files = get_files_of_type(target_root, '.png')
    # files.extend(get_files_of_type(target_root, '.jpg'))
    print_info(files=files, max_size=1024)
    # down_res(files=files, max_size=1024, enforce_8_bit_depth=True)
