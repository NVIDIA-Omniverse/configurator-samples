"""
This module will create a json file with all the variant data in the opened stage. 
It will await stage loading complete before doing so.
The idea is that you remove the variants that you do not want to cache in the caching process as sometimes you deal with large amounts of variants on the incoming configurable asset.

Example Usage to generate json data (change to your local paths):
D:/Builds/kit-app-template/_build/windows-x86_64/release/kit/kit.exe D:/Builds/kit-app-template/_build/windows-x86_64/release/apps/my_company.my_usd_viewer.kit  --exec "C:/Code/configurator-samples/scripts/cache/create_variant_json_data.py --json_path C:/configurator/variant_data.json" --/log/file=C:/configurator/variant_json_output.log --/app/auto_load_usd='C:/configurator/product_configurator_base.usd' --no-window
"""

import omni.kit.app
import omni.usd
import asyncio
import carb
import omni.log
import time
import argparse
import json
from typing import List
import pxr

CONFIGURATOR_READY_EVENT_NAME = "ConfiguratorReady"

class StateManager:
    """This class keep tabs on the event stream inside the kit app. It signals when a stage is fully loaded.
    When setting variants, this class is used to query when the variant has been set and the stage is no longer busy.
    """
    def __init__(self):
        super().__init__()
        self._event_stream = omni.kit.app.get_app().get_message_bus_event_stream()
        self._stage_sub = (
            omni.usd.get_context()
            .get_stage_event_stream()
            .create_subscription_to_pop(self._on_stage_event, name="product_configurator_loaded")
        )
        self._event_sub = False
        self._initialized = False
        self._non_default_stage = False

    def _on_stage_event(self, event: carb.events.IEvent) -> None:
        """
        Manage extension state via the stage event stream. When a new stage is open we reload the data model
        and set the state for the UI.

        Args:
            event (carb.events.IEvent): Event type
        """
        RTX_STREAMING_STATUS_EVENT: int = carb.events.type_from_string("omni.rtx.StreamingStatus")
        if event.type == int(omni.usd.StageEventType.OPENING):
            omni.log.verbose(f'Configurator Loaded Signal - OPENING STAGE - event subscription to RTX streaming manager created')
            self._event_sub = self._event_stream.create_subscription_to_pop_by_type(RTX_STREAMING_STATUS_EVENT, self.on_msg_bus_payload, name="streaming_status_listener")

        elif event.type == int(omni.usd.StageEventType.OPENED):
            omni.log.verbose(f'Configurator Loaded Signal - OPENED STAGE - Configurator initialization evaluation async called')
            asyncio.ensure_future(self._evaluate_initialization())

        elif event.type == int(omni.usd.StageEventType.CLOSED):
            omni.log.verbose(f'Configurator Loaded Signal - CLOSED STAGE - Resetting extension state')
            self._reset_state()

    def on_msg_bus_payload(self, event: carb.events.IEvent) -> None:
        """Streaming status event listener

        Args:
            event (carb.events.IEvent): Contains payload sender and type - https://docs.omniverse.nvidia.com/kit/docs/kit-manual/105.0/carb.events/carb.events.IEvent.html
        """
        isBusy = event.payload['isBusy']
        if not isBusy:
            omni.log.verbose('Configurator Loaded Signal - Streaming Manager Not busy - evaluating stage for default')
            path = omni.usd.get_context().get_stage().GetRootLayer().resolvedPath.GetPathString()
            if path:
                omni.log.verbose(f'Configurator Loaded Signal - Streaming Manager Not busy - Stage IS NOT default - {path}')
                self._non_default_stage = True

            else:
                omni.log.verbose(f'Configurator Loaded Signal - Streaming Manager Not busy - Stage IS default')
                self._non_default_stage = False
            omni.log.verbose(f'Configurator Loaded Signal - Streaming Manager Not busy - Stage initialized (weather default or not)')
            self._initialized = True

    async def _evaluate_initialization(self) -> None:
        """Evaluate initialization
        If initialized and we are using a non default stage, a signal is emitted that the configurator is ready.
        Note: Even if a default stage is loaded, the initialized state is True, but the _non_default_stage is False
        """
        while not self._initialized:
            await omni.kit.app.get_app().next_update_async()
        if self._non_default_stage:
            for _ in range(2):
                await omni.kit.app.get_app().next_update_async()
            self._event_stream.push(carb.events.type_from_string(CONFIGURATOR_READY_EVENT_NAME))
            omni.log.info(f'Stage Fully Loaded - Signal Emitted name:{CONFIGURATOR_READY_EVENT_NAME}')

    def on_shutdown(self) -> None:
        """Clean up subscriptions
        """
        self._stage_sub.unsubscribe()
        if self._event_sub:
            self._event_sub.unsubscribe()

    def _reset_state(self) -> None:
        """Reset the internal state - ready for new stage to be loaded
        """
        self._initialized = False
        self._non_default_stage = False
        if self._event_sub:
            self._event_sub.unsubscribe()
        omni.log.verbose(f'Configurator Loaded Signal - STATE RESET')

    @property
    def initialized(self) -> bool:
        """State of initialization

        Returns:
            bool: True/False
        """
        return self._initialized


def get_prims_with_variant_sets() -> List[pxr.Usd.Prim]:
    """Get all prims with variant sets"""
    context = omni.usd.get_context()
    stage = context.get_stage()
    if not stage:
        return []
    return [prim for prim in stage.Traverse() if prim.GetVariantSets().GetNames()]



async def main(json_path: str) -> None:
    """
    This function runs through all variants either through graph or Python. 
    It will also evaluate the readiness of the stage before going to the next variant for the Python implementation.
    The graph has its own delay mechanism.
    """
    return_code = 0
    state_manager = StateManager()
    while not state_manager.initialized:
        for _ in range(2):
            await omni.kit.app.get_app().next_update_async()

    stage = omni.usd.get_context().get_stage()
    prims = get_prims_with_variant_sets()
    variant_dict = {}
    for prim in prims:
        variant_sets = prim.GetVariantSets()
        variant_set_dict = {}
        for variant_set_name in variant_sets.GetNames():
            usd_variant_set = variant_sets.GetVariantSet(variant_set_name)
            variant_names = usd_variant_set.GetVariantNames()
            variant_list = []
            for variant_name in variant_names:
                variant_list.append(variant_name)
                print(f'Writing variant data for  {prim} - {variant_name} - {variant_set_name}')
                omni.log.info(f'Writing variant data for  {prim} - {variant_name} - {variant_set_name}')
            variant_set_dict[variant_set_name] = variant_list
        variant_dict[prim.GetPrimPath().pathString] = variant_set_dict

    if not variant_dict:
        print('No variants found in stage')
        return_code = -1
    else:
        with open(json_path, "w") as outfile: 
            print(f'Writing json variant data to {json_path}')
            omni.log.info(f'Writing json variant data to {json_path}')
            json.dump(variant_dict, outfile, indent=4)
    omni.kit.app.get_app().post_quit(return_code)


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="Generate json file out of all variants in the stage")
    parser.add_argument("--json_path", help="Optional path to json file with variants (can be generated with create_variant_json_data.py).")
    args = parser.parse_args()
    asyncio.ensure_future(main(args.json_path))