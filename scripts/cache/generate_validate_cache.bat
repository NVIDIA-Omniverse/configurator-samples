@echo off 
:: For how to build using the Kit application template (KAT) - https://github.com/NVIDIA-Omniverse/kit-app-template?tab=readme-ov-file#quick-
:: Set the paths below to where the files are on your hard drive.
set KIT_PATH=D:/Builds/kit-app-template/_build/windows-x86_64/release/kit/kit.exe
set KIT_APP=D:/Builds/kit-app-template/_build/windows-x86_64/release/apps/my_company.my_usd_viewer.kit
set CONFIGURATOR_SOURCE_FOLDER=C:/configurator/
set CONFIGURATOR_MOVE_DIR=C:/moved/configurator/
set SCRIPT_ROOT=C:/Code/configurator-samples/scripts/cache/

:: These paths are derived - only change if you need to
set CONFIGURATOR_SOURCE_FILE=product_configurator_base.usd
set CONFIGURATOR_SOURCE_PATH=%CONFIGURATOR_SOURCE_FOLDER%%CONFIGURATOR_SOURCE_FILE%
set CACHE_GENERATION_PATH=%CONFIGURATOR_SOURCE_FOLDER%cache
set CACHE_GENERATION_LOG=%CONFIGURATOR_SOURCE_FOLDER%ujitso.log
set CONFIGURATOR_MOVED_PATH=%CONFIGURATOR_MOVE_DIR%%CONFIGURATOR_SOURCE_FILE%
set CACHE_VALIDATION_PATH=%CONFIGURATOR_MOVE_DIR%cache
set CACHE_VALIDATION_LOG=%CONFIGURATOR_MOVE_DIR%cache_validation.log
set SCRIPT_RUN_VARIANTS=%SCRIPT_ROOT%run_variants.py
set SCRIPT_COPY_CONFIGURATOR=%SCRIPT_ROOT%copy_configurator.py
set SCRIPT_CACHE_VALIDATION=%SCRIPT_ROOT%validate_log.py

ECHO -----------------------------------------------
ECHO Kit Path: %KIT_PATH%
ECHO Kit App: %KIT_APP%
ECHO Configurator Source: %CONFIGURATOR_SOURCE_PATH%
ECHO Configurator Validation: %CONFIGURATOR_MOVED_PATH%
ECHO Script Root: %SCRIPT_ROOT%
ECHO -----------------------------------------------

ECHO --- Running Cache Generation ---
ECHO Caching options in: %CONFIGURATOR_SOURCE_PATH%
ECHO Using Script: %SCRIPT_RUN_VARIANTS%
ECHO Generating Cache to: %CACHE_GENERATION_PATH%
ECHO Log Path: %CACHE_GENERATION_LOG%
call %KIT_PATH% %KIT_APP% --/UJITSO/datastore/localCachePath="%CACHE_GENERATION_PATH%" --/UJITSO/writeCacheWithAssetRoot="%CONFIGURATOR_SOURCE_FOLDER%" --exec %SCRIPT_RUN_VARIANTS% --/log/file=%CACHE_GENERATION_LOG% --/app/auto_load_usd="%CONFIGURATOR_SOURCE_PATH%" --no-window
ECHO --- Cache Generation Complete ---

ECHO -----------------------------------------------
ECHO --- Running Configurator Copy ---
ECHO Copy from: %CONFIGURATOR_SOURCE_FOLDER%
ECHO Copy to: %CONFIGURATOR_MOVE_DIR%
ECHO Using Script: %SCRIPT_COPY_CONFIGURATOR% with overwrite flag
call %KIT_PATH% --exec "%SCRIPT_COPY_CONFIGURATOR% --source_file %CONFIGURATOR_SOURCE_PATH% --target_root %CONFIGURATOR_MOVE_DIR% --overwrite"
ECHO --- Configurator Copy Complete ---

ECHO -----------------------------------------------
ECHO --- Running Cache Validation ---
ECHO Validating cache from: %CONFIGURATOR_MOVED_PATH%
ECHO Using Script: %SCRIPT_RUN_VARIANTS%
ECHO Validating Cache: %CACHE_VALIDATION_PATH%
ECHO Log Path: %CACHE_VALIDATION_LOG%
call %KIT_PATH% %KIT_APP% --/UJITSO/datastore/localCachePath="%CACHE_VALIDATION_PATH%" --/UJITSO/readCacheWithAssetRoot="%CONFIGURATOR_MOVE_DIR%" --/UJITSO/failedDepLoadingLogging=true --exec %SCRIPT_RUN_VARIANTS% --/log/file=%CACHE_VALIDATION_LOG% --/app/auto_load_usd="%CONFIGURATOR_MOVED_PATH%" --no-window
ECHO --- Cache Validation Complete ---

ECHO -----------------------------------------------
ECHO --- Checking log for UJITSO Errors ---
ECHO Log Path: %CACHE_VALIDATION_LOG%
ECHO Using Script: %SCRIPT_CACHE_VALIDATION%
call %KIT_PATH% --exec "%SCRIPT_CACHE_VALIDATION% --log_file %CACHE_VALIDATION_LOG%"
