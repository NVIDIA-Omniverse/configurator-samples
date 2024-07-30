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
This module demonstrates how to set what is selectable via mouse click within a kit viewport. 
When executed, only the prims associated with the supplied prim type(s) will be selectable via mouse 
click in the viewport.

Version: 1.0.0
"""

import carb


ALL = "type:ALL"
MESH = "type:Mesh"
CAMERA = "type:Camera" 
LIGHTS = "type:CylinderLight;type:DiskLight;type:DistantLight;type:DomeLight;type:GeometryLight;type:Light;type:RectLight;type:SphereLight"

if __name__ == "__main__":
    # change MESH to ALL, CAMERA or LIGHTS for those prim types to be selectable
    carb.settings.get_settings().set("/persistent/app/viewport/pickingMode", MESH)