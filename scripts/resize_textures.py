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
(New) Detect and scale single color images.
(New) Scale non square images based on largest side and aspect ratio maintained.
(New) Separate square and non square images.

Version: 1.1.0
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

    raise NotImplementedError(
        f'The following bit depth is not counted for - {image_array.dtype}\nImage path - {image_path}')


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


def has_single_color(image_path: str):
    """Down res files and optionally enforce 8 bit images

    Args:
        image_path (str): file to check for single color status

    Returns:
        bool: True or False if the image has a single color
    """
    im = Image.open(image_path)
    im = im.convert('RGB')  # Convert to RGB color space
    colors = im.getcolors(maxcolors=16777216)  # Get all colors in the image
    return len(colors) == 1  # Check if only one color is present


def down_res(image_files: List[str], max_size: int = 1024, enforce_8_bit_depth: bool = False, include_square: bool = True, include_non_square: bool = True, enforce_single_color_image_size: bool = False, single_color_image_max_size: int = 128):
    """Down res files and optionally enforce 8 bit images

    Args:
        image_files (list): a list of file paths of images to down res
        max_size (int, optional): Max size of images, anything square aspect ratio files will get reduced in resolution. Defaults to 1024.
        enforce_8_bit_depth (bool, optional): Enforce 8 bit images. Defaults to False.
        include_square (bool, optional): Scale square images. Defaults to False.
        include_non_square (bool, optional): Also scale non-square images on the largest axis while maintaining aspect ratio. Defaults to True.
        enforce_single_color_image_size (bool, optional): Make sure all images with single color is not larger than single_color_image_max_size. Defaults to False
        single_color_image_max_size (int, optional): Make sure all images with single color is not larger than this size. Defaults to 128
    """
    for file in image_files:
        im = Image.open(file)
        size_x = im.size[0]
        size_y = im.size[1]
        single_color_image = has_single_color(file) if enforce_single_color_image_size else False
        largest = max(size_x, size_y)
        if single_color_image and largest > single_color_image_max_size:
            # Square Images
            if size_x == size_y:
                print(f'Resizing - Single Color Image - From {largest} - to {single_color_image_max_size} - {file}')
                im = im.resize((single_color_image_max_size, single_color_image_max_size))
            # Non-Square Images
            else:
                # Larger width
                if size_x > size_y:
                    percent = (single_color_image_max_size / float(size_x))
                    y_size = int((float(size_y) * float(percent)))
                    print(f'Resizing - Single Color Image - From ({size_x}, {size_y}) - to ({single_color_image_max_size}, {y_size}) - {file}')
                    im = im.resize((single_color_image_max_size, y_size))
                # Larger height
                else:
                    percent = (single_color_image_max_size / float(size_y))
                    x_size = int((float(size_x) * float(percent)))
                    print(f'Resizing - Single Color Image - From ({size_x}, {size_y}) - to ({x_size}, {single_color_image_max_size}) - {file}')
                    im = im.resize((x_size, single_color_image_max_size))

        else:
            if largest > max_size:
                # Square images
                if include_square:
                    if size_x == size_y:
                        print(f'Resizing - Square - From {size_x} - to {max_size} - {file}')
                        im = im.resize((max_size, max_size))
                # Non square
                if include_non_square:
                    # Larger width
                    if size_x > size_y:
                        percent = (max_size / float(size_x))
                        y_size = int((float(size_y) * float(percent)))
                        print(f'Resizing - Non-Square - From ({size_x}, {size_y}) - to ({max_size}, {y_size}) - {file}')
                        im = im.resize((max_size, y_size))
                    # Larger height
                    if size_y > size_x:
                        percent = (max_size / float(size_y))
                        x_size = int((float(size_x) * float(percent)))
                        print(f'Resizing - Non-Square - From ({size_x}, {size_y}) - to ({x_size}, {max_size}) - {file}')
                        im = im.resize((x_size, max_size))

        # Enforce 8 bits (optionally)
        if enforce_8_bit_depth:
            bit_depth = get_image_bit_depth(file)
            if bit_depth > 8:
                print(f'Changing bit depth - From {bit_depth} - to 8 - {file}')
                array = numpy.uint8(numpy.array(im) / 256)
                im = Image.fromarray(array)

        im.save(fp=file)


def print_info(image_files: List[str], max_size: int = 2048, include_square: bool = True, include_non_square: bool = True, inform_single_color_images: bool = False, single_color_image_max_size: int = 128):
    """Scout function to console print all files found larger than max size. Will also inform files with a higher bit depth than 8.
    Control over square and non-square ratios as well as finding single color images over an input size.

    Args:
        image_files (list): a list of file paths of images to investigate
        max_size (int, optional): Max size of images. Defaults to 2048.
        include_square (bool, optional): Consider square images Defaults to True.
        include_non_square (bool, optional): Consider non-square images. Largest side is compared to max_size. Defaults to True.
        inform_single_color_images (bool, optional): Find single color images larger than single_color_image_max_size. Defaults to False.
        single_color_image_max_size (int): If we are finding single color images, what is the allowed max size - anything above will get reported. Defaults to 128.

    """
    report_square = []
    report_non_square = []
    report_single_color = []
    report_bit_depth = []

    for file in image_files:
        im = Image.open(file)
        size_x = im.size[0]
        size_y = im.size[1]
        single_color_image = has_single_color(file) if inform_single_color_images else False
        largest = max(size_x, size_y)

        if single_color_image and largest > single_color_image_max_size:
            report_single_color.append(f'{size_x} by {size_y} - {file}')
        else:
            # Square images
            if largest > max_size:
                if size_x == size_y:
                    if include_square:
                        if im.size[0] > max_size:
                            report_square.append(f'{size_x} - {file}')
                else:
                    if include_non_square:
                        report_non_square.append(f'{size_x} by {size_y} - {file}')

        # Inform if bit depth is higher than 8
        bit_depth = get_image_bit_depth(file)
        if bit_depth > 8:
            report_bit_depth.append(f'Bit depth higher - {bit_depth} - {file}')

    report_square.sort()
    report_non_square.sort()
    report_bit_depth.sort()
    report_single_color.sort()
    if report_square:
        print('Square Images:')
        for r_i in report_square:
            print(r_i)
        print('\n')
    if report_non_square:
        print('Non Square Images:')
        for r_i in report_non_square:
            print(r_i)
        print('\n')
    if report_bit_depth:
        print('Images with higher bit depth:')
        for r_i in report_bit_depth:
            print(r_i)
        print('\n')
    if report_single_color:
        print('Images with single color:')
        for r_i in report_single_color:
            print(r_i)
        print('\n')


if __name__ == "__main__":
    # Set this to your root directory with textures you want to get info on or down res
    # Note : Informing and enforcing single color image is a bit more time consuming since the pixel information needs to be read.
    target_root = "C:/Configurators/ProductA"
    files = get_files_of_type(target_root, '.png')
    files.extend(get_files_of_type(target_root, '.jpg'))
    print_info(image_files=files, max_size=2048, include_square=True, include_non_square=True, inform_single_color_images=True, single_color_image_max_size=128)
    #down_res(image_files=files, max_size=2048, enforce_8_bit_depth=True, include_square=True, include_non_square=True, enforce_single_color_image_size=True, single_color_image_max_size=128)