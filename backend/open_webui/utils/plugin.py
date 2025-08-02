"""
Modification Log:
------------------
| Date       | Author         | MOD TAG            | Description                                       |
|------------|----------------|--------------------|---------------------------------------------------|
| 2025-02-18 | AAK7S          | CWE-94             | FIx for Code Injection                            |
| 2025-02-18 | Bala           | CWE-400            |Polynomial regular expression used on uncontrolled data
"""
import os
import re
import subprocess
import sys
from importlib import util
import types
import tempfile
import logging
import ast

from open_webui.env import (
     SRC_LOG_LEVELS, 
     PIP_OPTIONS, 
     PIP_PACKAGE_INDEX_OPTIONS,
     SAFE_BUILTINS,              #ENH : CWE-94   
     ALLOWED_MODULES,            #ENH : CWE-94   
)
from open_webui.models.functions import Functions
from open_webui.models.tools import Tools

log = logging.getLogger(__name__)
log.setLevel(SRC_LOG_LEVELS["MAIN"])

#ENH_START : CWE-94   
def safe_exec(content, filename):
    """
    Executes the given content in a restricted environment with limited built-ins.
    """

    # Create a restricted __import__ that only allows whitelisted modules.
    original_import = __import__
    def safe_import(name, globals=None, locals=None, fromlist=(), level=0):
        base_module = name.split('.')[0]
        if  ALLOWED_MODULES.get(base_module) is not None:
            raise ImportError(
                f"Importing module '{name}' is not allowed in the restricted execution environment."
            )
        return original_import(name, globals, locals, fromlist, level)
    
    # Make sure __build_class__ is available in SAFE_BUILTINS:
    import builtins
    SAFE_BUILTINS["__import__"] = safe_import
    SAFE_BUILTINS["__build_class__"] = builtins.__build_class__
 
    # Set up a restricted global namespace.
    safe_globals = {"__builtins__": SAFE_BUILTINS, "__file__": filename, "__name__": "__main__"}
 
    # Optionally perform AST analysis for additional safety checks.
    try:
        tree = ast.parse(content, mode='exec')
        # Additional AST checks can be added here if desired.
    except SyntaxError as e:
        raise Exception(f"Syntax error in code: {e}")
 
    # Compile and execute the code in the restricted environment.
    code_obj = compile(tree, filename, "exec")
    try:
        exec(code_obj, safe_globals)
    except :
        raise ImportError(
                f"Compilation error in code."
            )
    return safe_globals

#ENH_END : CWE-94 

 
def extract_frontmatter(content):
    """
    Extract frontmatter as a dictionary from the provided content string.
    """
    frontmatter = {}
    frontmatter_started = False
    frontmatter_ended = False
    # CWE-400 Polynomial regular expression used on uncontrolled data  
    frontmatter_pattern = re.compile(r"^\s*([a-z_]+):\s*([^\n]*)\s*$", re.IGNORECASE)

    try:
        lines = content.splitlines()
        if len(lines) < 1 or lines[0].strip() != '"""':
            # The content doesn't start with triple quotes
            return {}

        frontmatter_started = True

        for line in lines[1:]:
            if '"""' in line:
                if frontmatter_started:
                    frontmatter_ended = True
                    break

            if frontmatter_started and not frontmatter_ended:
                match = frontmatter_pattern.match(line)
                if match:
                    key, value = match.groups()
                    frontmatter[key.strip()] = value.strip()

    except Exception as e:
        log.exception(f"Failed to extract frontmatter: {e}")
        return {}

    return frontmatter


def replace_imports(content):
    """
    Replace the import paths in the content.
    """
    replacements = {
        "from utils": "from open_webui.utils",
        "from apps": "from open_webui",
        "from main": "from open_webui.main",
        "from config": "from open_webui.config",
    }

    for old, new in replacements.items():
        content = content.replace(old, new)

    return content


def load_tools_module_by_id(toolkit_id, content=None):

    if content is None:
        tool = Tools.get_tool_by_id(toolkit_id)
        if not tool:
            raise Exception(f"Toolkit not found: {toolkit_id}")

        content = tool.content

        content = replace_imports(content)
        Tools.update_tool_by_id(toolkit_id, {"content": content})
    else:
        frontmatter = extract_frontmatter(content)
        # Install required packages found within the frontmatter
        install_frontmatter_requirements(frontmatter.get("requirements", ""))

    module_name = f"tool_{toolkit_id}"
    module = types.ModuleType(module_name)
    sys.modules[module_name] = module

    # Create a temporary file and use it to define `__file__` so
    # that it works as expected from the module's perspective.
    temp_file = tempfile.NamedTemporaryFile(delete=False)
    temp_file.close()
    try:
        with open(temp_file.name, "w", encoding="utf-8") as f:
            f.write(content)
        module.__dict__["__file__"] = temp_file.name

        ## ENH_START : CWE-94 Execute the code in a restricted environment.		 
        # exec(content, module.__dict__)		 
        safe_namespace = safe_exec(content, temp_file.name)
        module.__dict__.update(safe_namespace)
		## ENH_END : CWE-94 

        frontmatter = extract_frontmatter(content)
        # log.info(f"Loaded module: {module.__name__}")
        log.info(f"Loaded module: {module.__file__}")

        # Create and return the object if the class 'Tools' is found in the module
        if hasattr(module, "Tools"):
            return module.Tools(), frontmatter
        else:
            raise Exception("No Tools class found in the module")
    except Exception as e:
        log.error(f"Error loading module: {toolkit_id}: {e}")
        del sys.modules[module_name]  # Clean up
        raise e
    finally:
        os.unlink(temp_file.name)


def load_function_module_by_id(function_id, content=None):
    if content is None:
        function = Functions.get_function_by_id(function_id)
        if not function:
            raise Exception(f"Function not found: {function_id}")
        content = function.content

        content = replace_imports(content)
        Functions.update_function_by_id(function_id, {"content": content})
    else:
        frontmatter = extract_frontmatter(content)
        install_frontmatter_requirements(frontmatter.get("requirements", ""))

    module_name = f"function_{function_id}"
    module = types.ModuleType(module_name)
    sys.modules[module_name] = module

    # Create a temporary file and use it to define `__file__` so
    # that it works as expected from the module's perspective.
    temp_file = tempfile.NamedTemporaryFile(delete=False)
    temp_file.close()
    try:
        with open(temp_file.name, "w", encoding="utf-8") as f:
            f.write(content)
        module.__dict__["__file__"] = temp_file.name

        ## ENH_START : CWE-94  Execute the code in a restricted environment.
        #exec(content, module.__dict__)
        safe_namespace = safe_exec(content, temp_file.name)
        module.__dict__.update(safe_namespace)
        ## ENH_END : CWE-94
        frontmatter = extract_frontmatter(content)
        log.info(f"Loaded module: {module.__name__}")

        # Create appropriate object based on available class type in the module
        if hasattr(module, "Pipe"):
            return module.Pipe(), "pipe", frontmatter
        elif hasattr(module, "Filter"):
            return module.Filter(), "filter", frontmatter
        elif hasattr(module, "Action"):
            return module.Action(), "action", frontmatter
        else:
            raise Exception("No Function class found in the module")
    except Exception as e:
        log.error(f"Error loading module: {function_id}: {e}")
        del sys.modules[module_name]  # Cleanup by removing the module in case of error

        Functions.update_function_by_id(function_id, {"is_active": False})
        raise e
    finally:
        os.unlink(temp_file.name)


def install_frontmatter_requirements(requirements):
    if requirements:
        try:
            req_list = [req.strip() for req in requirements.split(",")]
            for req in req_list:
                ## ENH_START : CWE-94 Validate package name using a regex (allow letters, numbers, hyphens, underscores, and dots)
                if not re.match(r"^[a-zA-Z0-9\-_\.]+$", req):
                    raise Exception(f"Unsafe package name: {req}")
				## ENH_END : CWE-94	
                log.info(f"Installing requirement: {req}")
                subprocess.check_call(
                    [sys.executable, "-m", "pip", "install"]
                    + PIP_OPTIONS
                    + req
                    + PIP_PACKAGE_INDEX_OPTIONS
                 )
        except Exception as e:
            log.error(f"Error installing packages: {' '.join(req_list)}")
            raise e

    else:
        log.info("No requirements found in frontmatter.")
