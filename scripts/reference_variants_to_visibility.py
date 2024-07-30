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
This script will find all variants that add a payload or reference to a prim and move them directly
onto a new child prim. It then modifies the variant to toggle on the visibility of the prim that holds 
the reference, and visibilty off on the prims that hold the remaining references.

Version: 1.0.0
"""

import omni.usd
from pxr import Usd, UsdGeom, Sdf


def convert(convert_payloads_to_refs: bool=False, convert_references_to_payloads: bool=False) -> None:
    """
    Iterates through the currently opened stage's layer stack and converts reference & payload variants to visibility toggles.
    """
    variant_prim_map = {}

    def _move_references(layer: Sdf.Layer, prim: Sdf.PrimSpec) -> None:
        """
        Creates child prims for each variant and moves references & payloads to them.
        """
        for child in prim.nameChildren:
            _move_references(layer, child)

        # Process variant sets in the current prim
        for variantSet in prim.variantSets:
            for variant in variantSet.variants:
                varPrimSpec = variant.primSpec

                _move_references(layer, varPrimSpec)
                
                def _move_references_iter(layer: Sdf.Layer, vSpec: Sdf.PrimSpec) -> None:
                    if bool(vSpec.referenceList.prependedItems) or bool(vSpec.payloadList.prependedItems):
                        root_prim_path = vSpec.path.StripAllVariantSelections()
                        root_prim_spec = layer.GetPrimAtPath(root_prim_path)

                        # ensure that the new prim that the reference/payload is moved to is unique 
                        new_prim_spec_path = Sdf.Path(omni.usd.get_stage_next_free_path(omni.usd.get_context().get_stage(), root_prim_spec.path.AppendPath(variant.name).pathString, False))
                        prim_spec = Sdf.PrimSpec(root_prim_spec, new_prim_spec_path.name, Sdf.SpecifierDef, "Xform")

                        if variantSet not in variant_prim_map:
                            variant_prim_map[variantSet] = {}

                        if variant not in variant_prim_map[variantSet]:
                            variant_prim_map[variantSet][variant] = []
                        
                        # store the parts of the path without the variant selection so that the other variants can later
                        # get substituted for setting visibility
                        variant_root_pathstring = variant.owner.owner.path.pathString
                        variant_prim_map[variantSet][variant].append((variant_root_pathstring, prim_spec.path.pathString.split(variant_root_pathstring)[-1].lstrip("/")))
                        
                        for reference in vSpec.referenceList.prependedItems:
                            if convert_references_to_payloads is True:
                                prim_spec.payloadList.Prepend(Sdf.Payload(reference.assetPath))
                            else:
                                prim_spec.referenceList.Prepend(reference)
                        vSpec.referenceList.prependedItems.clear()

                        for payload in vSpec.payloadList.prependedItems:
                            if convert_payloads_to_refs is True:
                                prim_spec.referenceList.Prepend(Sdf.Reference(payload.assetPath))
                            else:
                                prim_spec.payloadList.Prepend(payload)
                        vSpec.payloadList.prependedItems.clear()


                    for child in vSpec.nameChildren:
                        _move_references_iter(layer, child)
                        
                _move_references_iter(layer, varPrimSpec)
               
    def _set_visibility() -> None:
        """
        Apply visibility toggling behavior for variants.
        """
        def _set(variant_set: str, variant: str, prefix: str, suffix: str, visible: bool) -> None:
            varstring = "{%s=%s}" % (variant_set, variant)
            var_path = f"{prefix}{varstring}{suffix}"
            vis_attr_path = Sdf.Path(var_path).AppendProperty(UsdGeom.Tokens.visibility)
            Sdf.JustCreatePrimAttributeInLayer(layer, vis_attr_path, Sdf.ValueTypeNames.Token)
            vis_attr = layer.GetAttributeAtPath(vis_attr_path)
            vis_attr.default = UsdGeom.Tokens.inherited if visible == True else UsdGeom.Tokens.invisible


        for variant_set, variants in variant_prim_map.items():
            for current_variant, paths in variants.items():
                for path in paths:
                    _set(variant_set.name, current_variant.name, path[0], path[1], True)
                
                for other_variant, other_paths in variants.items():
                    if other_variant != current_variant:
                        for other_path in other_paths:
                            _set(variant_set.name, current_variant.name, other_path[0], other_path[1], False)
                    
    stage: Usd.Stage = omni.usd.get_context().get_stage()
    with Sdf.ChangeBlock():
        for layer in stage.GetLayerStack():
            for prim_spec in layer.rootPrims:
                _move_references(layer, prim_spec)
        
        _set_visibility()
         

if __name__ == "__main__":
    convert(convert_payloads_to_refs=False, convert_references_to_payloads=False)
