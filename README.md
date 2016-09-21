## About Bensbach

**Bensbach** is an Unreal Engine 3 (UE3) compiler and decompiler made for games' mods creation. Decompiles from UE3 bytecode - to **UCB** source code. Compiles from **UCB** source code - to UE3 bytecode.

**UCB** - convenient, simple language for those people who knows what UE3 bytecode is. And easily understandable for others.

## It was used 

to create [https://github.com/FI-Mihej/Realistic-Damage-Model-mod-for-Long-War](https://github.com/FI-Mihej/Realistic-Damage-Model-mod-for-Long-War)

## To highlight 

mods source code in Notepad++ you may use [https://github.com/FI-Mihej/UCB-Source-Code-highlighter](https://github.com/FI-Mihej/UCB-Source-Code-highlighter)

## Example of formatted UCB code:

![Example of formatted code](https://github.com/FI-Mihej/UCB-Source-Code-highlighter/blob/master/Img/Notepad%2B%2B/UCB%20Original%20Source%20Code%20Example.png?raw=true "Example of formatted code")

## Files

* **Compiler and Decompiler:**
    * `unreal_script_byte_code_compiller_decompiller.py` - compiler and decompiler
    * `ucb_compiler_decompiler_description_words.py` - preprocessor keywords for mods' source code
* **Tools:**
    * **Installation:**
        * `compile_and_install_mod.py`
        * `get_bytecode_by_name.py`
    * **Work with UPK files:**
        * **File Cache:**
            * `ucb_tools_files_cache_manager.py`
        * `ucb_tools_kernel.py`
        * `prepare_local_upk_files.py`
        * `ucb_tools_config.py`
    * **not yet implemented:**
        * `profiler_result_reader.py`
        * `remote_ucb_compiler_decompiler.py`
        * `ucb_compiler_decompiler.py`

## Caution

Current project state was obtained at the beginning of 2016: after publishing mod and before my main lib refactoring. Also it is not ready for standalone-app distribution.

## License

Copyright © 2016 ButenkoMS. All rights reserved.

Licensed under the Apache License, Version 2.0.
