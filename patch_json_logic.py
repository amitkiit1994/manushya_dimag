#!/usr/bin/env python3
"""
Patch script to fix json_logic library compatibility with Python 3.10+
"""
import os


def patch_json_logic():
    """Patch the json_logic library to fix Python 3.10+ compatibility."""
    try:
        import json_logic

        json_logic_path = os.path.dirname(json_logic.__file__)
        init_file = os.path.join(json_logic_path, "__init__.py")

        print(f"Patching json_logic at: {init_file}")

        # Read the current file
        with open(init_file) as f:
            content = f.read()

        # Replace the problematic line
        if "op = tests.keys()[0]" in content:
            content = content.replace(
                "op = tests.keys()[0]", "op = list(tests.keys())[0]"
            )

            # Write the patched content back
            with open(init_file, "w") as f:
                f.write(content)

            print("✅ Successfully patched json_logic library")

            # Test the patch
            from json_logic import jsonLogic

            # Test with a simple rule
            rule = {"==": [{"var": "test"}, "value"]}
            context = {"test": "value"}
            result = jsonLogic(rule, context)
            print(f"✅ Test successful: {result}")

        else:
            print("❌ Could not find the problematic line to patch")

    except Exception as e:
        print(f"❌ Error patching json_logic: {e}")


if __name__ == "__main__":
    patch_json_logic()
