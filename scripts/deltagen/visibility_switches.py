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
This script will modify the behavior of switch variants from Deltagen USD exports so that they become visibility toggles. 
Execute this script directly on an opened stage that contains switch variants. For Deltagen exports, this is the 'model' 
export that contains geometry. 

Version: 1.0.0
"""

import omni.log
import omni.usd
from pxr import Usd, UsdGeom, Sdf


def switchToVisibility() -> None:
    """
    Converts Deltagen prim switchers to visbility variants.
    """
    stage: Usd.Stage = omni.usd.get_context().get_stage()
    layer: Sdf.Layer = stage.GetRootLayer()
    prim_spec: Sdf.PrimSpec = layer.GetPrimAtPath(stage.GetDefaultPrim().GetPath())
    
    with Sdf.ChangeBlock():
        try:
            _switchToVisibility(layer, prim_spec)
            
        except Exception as ex:
            omni.log.error(f"An error occurred while switching to visibility!")
            raise ex


def _switchToVisibility(layer: Sdf.Layer, prim: Sdf.PrimSpec) -> None:
    # Depth first conversion
    for child in prim.nameChildren:
        _switchToVisibility(layer, child)

    # Process variant sets in the current prim
    for variantSet in prim.variantSets:
        if variantSet.name == "switchVariant":
            for variant in variantSet.variants:
                varPrim = variant.primSpec

                # Depth first conversion
                _switchToVisibility(layer, varPrim)

                # If the owner prim already contains a child with the same name as the variant,
                # then we assume the conversion was already done, and we skip the variant.
                if varPrim.name in prim.nameChildren:
                    omni.log.info(f"{prim.path} already contained a child prim {varPrim.name}, skipping")
                    continue

                numChildren = len(varPrim.nameChildren)

                if numChildren == 1:
                    child = varPrim.nameChildren[0]
                    if child.name != variant.name:
                        omni.log.error(
                            f"Expected child {child.path} to have the same name as variant {variant.name}"
                        )
                        continue
                    targetPath = prim.path.AppendChild(variant.name)
                    Sdf.CopySpec(layer, child.path, layer, targetPath)
                    varPrim.nameChildren.clear()
                elif numChildren > 1:
                    omni.log.warn(f"Expected no more than one child in {variant.path}")
                    continue

                # Move payloads to prim
                for payload in varPrim.payloadList.prependedItems:
                    prim.payloadList.Prepend(payload)
                varPrim.payloadList.prependedItems.clear()

                # Move references to prim
                for reference in varPrim.referenceList.prependedItems:
                    prim.referenceListPrepend(reference)
                varPrim.referenceList.prependedItems.clear()

                # For each variant, just show the associated prim, hide the other ones
                geomTokens = UsdGeom.Tokens
                tokenType = Sdf.ValueTypeNames.Token

                for visVariant in variantSet.variants:
                    visPrimPath = varPrim.path.AppendChild(visVariant.name)
                    Sdf.CreatePrimInLayer(layer, visPrimPath)

                    visAttrPath = visPrimPath.AppendProperty(geomTokens.visibility)
                    Sdf.JustCreatePrimAttributeInLayer(layer, visAttrPath, tokenType)

                    visAttr = layer.GetAttributeAtPath(visAttrPath)
                    visAttr.default = geomTokens.inherited if visVariant == variant else geomTokens.invisible


if __name__ == "__main__":
    switchToVisibility()