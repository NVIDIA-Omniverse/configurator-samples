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
The purpose of this module is to modify the USD files exported from Deltagen for enhanced usability.
Execute on the top-level USD file.

Version: 1.0.0
"""
from typing import List, Set
import carb
import omni.usd
from pxr import Usd, Sdf
import omni.kit.commands
import omni.kit.window.file


CHECKPOINT_COMMENT = "DG Optimize File - 1.0.0"


class _CheckpointCommentContext:
    """This context is used to create checkpoints when saving or exporting layers."""

    def __init__(self, comment: str):
        self._comment = comment

    def __enter__(self):
        try:
            import omni.usd_resolver
            omni.usd_resolver.set_checkpoint_message(self._comment)
        except Exception as e:
            carb.log_error(f"Failed to import omni.usd_resolver: {str(e)}.")

        return self

    def __exit__(self, type, value, trace):
        try:
            import omni.usd_resolver
            omni.usd_resolver.set_checkpoint_message("")
        except Exception:
            pass


def _fix_texture_paths(source_layer: Sdf.Layer) -> Set[str]:
    """Traverse source layer and fix all filepaths with backslashes."""

    fixed_parms = set([])
    root_path = Sdf.Path.absoluteRootPath.AppendChild(source_layer.defaultPrim)

    # this is a layer traversal callback that processes each spec path
    def _on_prim_spec_path(spec_path):
        if spec_path.IsPropertyPath():
            return

        prim_spec = source_layer.GetPrimAtPath(spec_path)
        if not prim_spec:
            return

        if prim_spec.typeName == "Shader":
            attributes = prim_spec.attributes
            if "inputs:file" in attributes:
                path_attr = attributes.get("inputs:file")
                file_path = path_attr.default.path
                if file_path.find("\\") != -1:
                    path_attr.default = file_path.replace("\\", "/")
                    fixed_parms.add(path_attr)

    # traverse all prim spec paths under root path
    source_layer.Traverse(root_path, _on_prim_spec_path)
    return fixed_parms


def fix_texture_paths(paths: List[str]) -> Set[str]:
    """This fixes all of the layers that have backslashes in file texture paths."""

    updated_layers = set([])
    # reversing paths to start from weakest layer first.
    paths.reverse()
    for layer_path in paths:
        layer_name = layer_path.rsplit("/", 1)[-1]
        layer = Sdf.Layer.FindOrOpen(layer_path)
        if not layer:
            continue
        # weakest layer is usually model (no materials) so we skip it.
        if layer_path not in [paths[0]]:
            fixed_parms = _fix_texture_paths(layer)
            if fixed_parms:
                updated_layers.add(layer)
                carb.log_warn(f"Fixed {len(fixed_parms)} texture paths with backslashes in {layer_name}.")
    return updated_layers


def optimize_layers(paths: List[str], new_name: str) -> Set[Sdf.Layer]:
    """Validate layers with proper root name, root type and texture paths."""

    updated_layers = set([])
    # reversing paths to start from weakest layer first.
    paths.reverse()
    for layer_path in paths:
        result = []
        # layer_name = layer_path.rsplit("/", 1)[-1]
        stage = Usd.Stage.Open(layer_path)
        layer = Sdf.Layer.FindOrOpen(layer_path)
        if not layer:
            continue

        new_path = Sdf.Path.absoluteRootPath.AppendChild(new_name)
        cur_path = Sdf.Path.absoluteRootPath.AppendChild(layer.defaultPrim)
        if layer.defaultPrim != new_name:
            Sdf.CreatePrimInLayer(layer, new_path)
            Sdf.CopySpec(layer, cur_path, layer, new_path)
            stage.RemovePrim(cur_path)
            layer.defaultPrim = new_name
            updated_layers.add(layer)
            result.append(f"renamed roots to {new_name}")

        new_spec = layer.GetPrimAtPath(new_path)
        if new_spec.typeName != "Xform":
            new_spec.typeName = "Xform"
            updated_layers.add(layer)
            result.append("set roots to Xform")

        if layer_path.lower().endswith("_mat.usdc") or layer_path.lower().endswith("_mat.usda"):
            children = stage.GetDefaultPrim().GetChildren()
            if len(children) == 1:
                child = children[0]
                child_spec = layer.GetPrimAtPath(child.GetPath())
                if child_spec.typeName != "Xform":
                    child_spec.typeName = "Xform"
                    result.append("set `materials` stage default prim child to Xform")

        if new_spec:
            ref_specs = new_spec.GetInfo(Sdf.PrimSpec.ReferencesKey).ApplyOperations([])
            if not ref_specs:
                continue
            for item in ref_specs:
                if item.assetPath.find("\\") != -1:
                    updated_layers.add(layer)
            if layer in updated_layers:
                result.append("fixed backslashes in references")
                target_prim = stage.GetPrimAtPath(new_path)
                target_prim.GetReferences().SetReferences([])
                for item in ref_specs:
                    ref_path = item.assetPath.replace("%5C", "/").replace("\\", "/")
                    target_prim.GetReferences().AddReference(assetPath=ref_path)
        if result:
            carb.log_warn(f"Changes: {', '.join(result)}.")
    return updated_layers


def create_optimized_stage(paths: List[str], root_name="World") -> None:
    """This is the master function that orchestrates all of the changes."""

    cur_stage = omni.usd.get_context().get_stage()
    cur_layer = cur_stage.GetRootLayer()
    cur_path = Sdf.Path.absoluteRootPath.AppendChild(cur_layer.defaultPrim)
    new_path = Sdf.Path.absoluteRootPath.AppendChild(root_name)
    cur_file = cur_layer.identifier

    changed_layers = set([])
    prim_spec = cur_layer.GetPrimAtPath(cur_path)
    ref_specs = None
    save = False
    if prim_spec:
        ref_specs = prim_spec.GetInfo(Sdf.PrimSpec.ReferencesKey).ApplyOperations([])
        if ref_specs:
            prim_spec.ClearReferenceList()
            if cur_path != new_path:
                cur_stage.RemovePrim(cur_path)
                source_path = new_path
                cur_path = cur_stage.GetPrimAtPath(source_path)
                cur_layer.defaultPrim = source_path.name
                save = True

    changed_layers.update(optimize_layers(paths, root_name))
    changed_layers.update(fix_texture_paths(paths))

    if not changed_layers:
        carb.log_warn("All layers are valid, no changes necessary.")
    else:
        layer_names = [ly.identifier.rsplit("/", 1)[-1] for ly in changed_layers if ly]
        carb.log_warn(f"Saving: {', '.join(layer_names)}")
        for layer in changed_layers:
            with _CheckpointCommentContext(CHECKPOINT_COMMENT):
                layer.Save()
            layer.Reload()

    if ref_specs:
        for ref in ref_specs:
            abs_path = omni.client.combine_urls(cur_file, ref.assetPath)
            abs_path = abs_path.replace("\\", "/")
            if abs_path not in cur_layer.subLayerPaths:
                try:
                    cur_layer.subLayerPaths.insert(0, abs_path)
                    save = True
                except Exception:
                    cur_layer.Reload()

    if save:
        path = omni.usd.get_context().get_stage_url()
        omni.kit.window.file.save_layers(path, [], None, True, CHECKPOINT_COMMENT)


def optimize_main(root_prim: Usd.Prim = None, root_name:str="World", safe_word:str=None) -> None:
    """This is the starter function that gets the ball rolling and does a few prelim checks."""

    paths = []
    stage = omni.usd.get_context().get_stage()
    source_layer = stage.GetRootLayer()

    if source_layer.anonymous:
        carb.log_error("You need to open an actual scene first.")
        return

    new_path = Sdf.Path.absoluteRootPath.AppendChild(source_layer.defaultPrim)
    root_prim = stage.GetPrimAtPath(new_path)

    if root_prim is None:
        root_prim = stage.GetPrimAtPath("/scene")

    if not root_prim:
        carb.log_error("No valid root primitive selected.")
        return

    if root_prim.HasAuthoredReferences():
        paths = list(source_layer.subLayerPaths)
        for (ref, layer) in omni.usd.get_composed_references_from_prim(root_prim, True):
            abs_path = omni.client.combine_urls(source_layer.identifier, ref.assetPath)
            abs_path = abs_path.replace("%5C", "/")
            if omni.client.stat(abs_path)[0] == omni.client.Result.OK:
                if safe_word is not None and abs_path.lower().find(safe_word.lower()) != -1:
                    carb.log_error(f"{abs_path} contains {safe_word} - copy assets outside or change safeword.")
                    return
                if abs_path not in paths:
                    paths.append(abs_path)
            else:
                carb.log_error(f"Invalid path: {abs_path}")

        create_optimized_stage(paths, root_name)


if __name__ == "__main__":
    optimize_main()
