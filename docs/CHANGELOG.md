# Changelog

The format is based on [Keep a Changelog](https://keepachangelog.com/en/1.0.0/).

## [1.0.2] - 2024-10-10
### Added
- Generate & Validate Cache (cache/generate_validate_cache.bat) - Leveraging the scripts in the cache directory to automate UJITSO caching and validation.
- Run Variants (cache/run_variants.py) - Run all variants in a stage awaiting the stage to be ready between each variant being set. Works both with caching graph and generic Python as back up triggering variants found.
- Copy Configurator (cache/copy_configurator.py) - Copy the configurator to another folder on the local disk.
- Validate Log (cache/validate_log.py) - Find UJITSO errors in log file.
  
## [1.0.1] - 2024-08-15
### Added
- csv_to_json.py dataset for Concept Car asset

### Changed
- Renamed csv_to_json.py dataset for Ragnarok asset

## [1.0.0] - 2024-06-25
### Added
- Optimize File (optimize_file.py) - Conform a Detagen export to Omniverse best practices
- Visibility Switches (visibility_switches.py) - Modify the switch variant functionality from Deltagen exports to visibility toggles
- CSV Material Replacements (csv_material_replacements.py) - A data driven material replacement workflow
- CSV Material Variants (csv_material_variants.py) - A data driven material variant creation workflow
- CSV to Json (csv_to_json.py) - Option packages data generation
- Reference Variants to Visibility (reference_variants_to_visibility.py) - Change variants that swap reference path to visibility switch
- Switch Variant (switch_variant.py) - Create visibility variants for each "switch variant"
- Resize Textures (resize_textures.py) - Resize images on hard drive
- Enable Streaming Extensions (enable_streaming_extensions.py) - snippet to load extensions
- Picking Mode (picking_mode.py) - snippet to set what is selectable in viewport



