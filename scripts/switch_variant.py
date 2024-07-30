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
This module will build switch variants using existing prims in a stage. A "switch variant" is a term used in
certain apps such a Deltagen, which are variants that are used for toggling on the visibility of a prim within a set,
and toggling off the visibility of the other prims in the set. 

When executed, a new variant set will be added to all prims that have matching names with the provided `switch_prims` list. 
The variant set will contain one visibility toggle variant for each child prim.

Version: 1.0.0
"""

from typing import List
import omni.usd
from pxr import Usd, UsdGeom, Sdf


def create(switch_prims: List[str] = ["Switch"], new_variant_set: str = "switchVariant") -> None:
    """
    Creates switch variants for all matching prim names.

    :param switch_prims: List of prim names to add variant set to
    :param new_variant_set: The name of the new variant sets
    :return: Nothing
    """
    stage: Usd.Stage = omni.usd.get_context().get_stage()
    prim: Sdf.Prim = stage.GetDefaultPrim()
    
    for prim in stage.Traverse():
        if prim.GetName() in switch_prims:
            children = prim.GetAllChildren()
            if len(children) > 0:
                variant_sets = prim.GetVariantSets()
                if not variant_sets.HasVariantSet(new_variant_set):
                    variant_set = variant_sets.AddVariantSet(new_variant_set)
                else:
                    variant_set = variant_sets.GetVariantSet(new_variant_set)

                default_visible_switch = None
                for child in children:
                    variant_name = child.GetName()
                    variant_set.AddVariant(variant_name)
                    attr = UsdGeom.Imageable(child).GetVisibilityAttr()
                    
                    # if one of the children is visible, capture it so that its variant switch can be enabled
                    if attr.Get() == "inherited":
                        default_visible_switch = child

                    # remove local edits so that the variants can switch visibility
                    attr.Clear()
                    
                    variant_set.SetVariantSelection(variant_name)
                    with variant_set.GetVariantEditContext():
                        for vis_prim in children:
                            attr = UsdGeom.Imageable(vis_prim).GetVisibilityAttr()
                            if child == vis_prim:
                                attr.Set("inherited")
                            else:
                                attr.Set("invisible")
                    
                    if default_visible_switch is not None:
                        variant_set.SetVariantSelection(default_visible_switch.GetName())


if __name__ == "__main__":
    create()