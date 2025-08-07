import os
import sys
import shutil
import logging

import maya.cmds as cmds
import maya.mel as mel

ENV_MAYA_MODULE_PATH = "MAYA_MODULE_PATH"
ENV_ICON_PATH = "XBMLANGPATH"

MODULE_NAME = "sppaint3d"
MODULE_FILE_NAME = "{0}.mod".format(MODULE_NAME)
MODULE_PATH = os.path.dirname(__file__)
ICON_FILE_NAME = "sppaint3d_icon.png"

SCRIPTS_PATH = os.path.join(MODULE_PATH, "scripts")
ICONS_PATH = os.path.join(MODULE_PATH, "icons")

SHELF_NAME = "ExternalTools"

BUTTON_ADD_TO_CURRENT_SHELF = "Add to current shelf"
BUTTON_ADD_TO_NEW_SHELF = "Add to a new shelf"
BUTTON_ADD_TO_SHELF = "Add to shelf"
BUTTON_SKIP = "Skip"
BUTTON_QUIT = "Quit"

logger = logging.getLogger(__name__)


def is_module_loaded(module_name):
    """
    :rtype: bool
    """
    return module_name in cmds.moduleInfo(listModules=True)


def add_scripts_path(path):
    """
    :param str path:
    """
    sys.path.append(path)


def add_icons_path(path):
    """
    :param str path:
    """
    icon_paths = os.environ.get(ENV_ICON_PATH, "").split(";")
    icon_paths.append(path)
    os.environ[ENV_ICON_PATH] = ";".join(icon_paths)


def copy_module_to_user_folder(module_file_path):
    """
    :param str module_file_path:
    :rtype: str
    """
    # this is dumb -_-
    # apparently when running the os.path.expanduser("~") yield different result when running from inside Maya
    # or from a python terminal (at least with the windows version).
    # Also the behavior is different between Maya 2022 and prior releases (2017 for example)
    # But the problem here, we must find a path somewhere *inside* the documents folder, otherwise this won't be
    # found as a default module path in earlier version of Maya (probably for version having the python 2 runtime)
    if sys.platform == "win32":
        user_documents_folder = os.path.expandvars("%USERPROFILE%")
        user_documents_folder = os.path.join(user_documents_folder, "Documents")
    else:
        user_documents_folder = os.path.expanduser("~")
    user_modules_folder = os.path.join(user_documents_folder, "maya", "modules")

    if not os.path.exists(user_modules_folder):
        os.makedirs(user_modules_folder)

    shutil.copy2(module_file_path, user_modules_folder)
    destination_path = os.path.join(user_modules_folder, MODULE_FILE_NAME)
    if not os.path.exists(destination_path):
        return None

    with open(destination_path, "r") as fp:
        modules_lines = fp.readlines()

    if not modules_lines:
        return None

    first_line = modules_lines[0].strip()
    no_change, _, _ = first_line.rpartition(".")
    first_line = "{0}{1}".format(no_change, os.path.realpath(MODULE_PATH))
    modules_lines[0] = first_line

    with open(destination_path, "w") as fp:
        fp.write("\n".join(modules_lines))

    return destination_path


def add_to_shelf(destination_shelf=None):
    """
    :param str destination_shelf:
    """
    top_level_shelf = get_top_level_shelf()

    if destination_shelf is None:
        shelves = cmds.shelfTabLayout(top_level_shelf, query=True, childArray=True) or []
        destination_shelf = SHELF_NAME if SHELF_NAME in shelves else cmds.shelfLayout(SHELF_NAME,
                                                                                      parent=top_level_shelf)

    label = "spPaint3d"

    buttons = cmds.shelfLayout(destination_shelf, query=True, childArray=True) or []
    found = [b for b in buttons if
             cmds.objectTypeUI(b, isType="shelfButton") and cmds.shelfButton(b, query=True, label=True) == label]

    if found:
        logger.warning("Shelf button already exists! Removing the old button...")
        for button in found:
            cmds.deleteUI(button)

    shelf_button = {
        "label": label,
        "annotation": "Opens the spPaint3d Tool Interface",
        "image": os.path.join(ICONS_PATH, ICON_FILE_NAME),
        "scaleIcon": False,
        "width": 32,
        "height": 32,
        "command": "from sppaint3d import gui as sppaintgui; sppaintgui.spPaint3dWin()",
        "parent": destination_shelf,
    }

    cmds.shelfButton(**shelf_button)


def get_top_level_shelf():
    return mel.eval("global string $gShelfTopLevel; $temp = $gShelfTopLevel;")


def add_to_current_shelf():
    top_level_shelf = get_top_level_shelf()
    current_shelf = cmds.tabLayout(top_level_shelf, query=True, selectTab=True)
    add_to_shelf(destination_shelf=current_shelf)


def install_module(shelf_only=False):
    if not shelf_only:
        module_file_path = os.path.join(MODULE_PATH, MODULE_FILE_NAME)
        if not os.path.exists(module_file_path):
            logger.error("Installation aborted! Unable to locate the file: {0}".format(module_file_path))
            return False

        module_environment = os.environ.get(ENV_MAYA_MODULE_PATH, "")

        normalized_module_path = os.path.normcase(MODULE_PATH)
        if any(p for p in module_environment.split(';') if os.path.normcase(p) == normalized_module_path):
            logger.warning(
                "The {0} environment variable already contains the module path. Maya should be restarted and the module should be available...".format(
                    ENV_MAYA_MODULE_PATH))
            return False

        logger.info("Copying the module to the user's documents folder...")
        module_file_path = copy_module_to_user_folder(module_file_path)
        logger.info("Module file successfully copied to: {0}".format(module_file_path))

        logger.info("Loading module and adding the needed paths to the running environment...")
        cmds.loadModule(load=module_file_path)
        add_scripts_path(SCRIPTS_PATH)
        add_icons_path(ICONS_PATH)

        success = try_import()
        if not success:
            return False

    shelf_action = confirm_message("Would you like to install a shelf icon in the current shelf?",
                                   buttons=[BUTTON_ADD_TO_CURRENT_SHELF, BUTTON_ADD_TO_NEW_SHELF, BUTTON_SKIP])
    shelf_func = {
        BUTTON_ADD_TO_CURRENT_SHELF: add_to_current_shelf,
        BUTTON_ADD_TO_NEW_SHELF: add_to_shelf,
    }.get(shelf_action)

    if shelf_func:
        shelf_func()
    else:
        logger.warning("Unexpected dialog choice, skipping the installation to the shelf!")

    return True


def try_import():
    """
    Try importing the script in case it was manually installed somewhere
    :rtype: bool
    """
    try:
        from sppaint3d import gui as sppaintgui
    except ImportError:
        return False
    return True


def confirm_message(message, buttons=None):
    buttons = ["Ok"] if buttons is None else buttons
    return cmds.confirmDialog(title='Module installation', message=message, button=buttons)


def onMayaDroppedPythonFile(*args, **kwargs):
    """Entry point from dropping a python script onto a viewport"""

    logger.info("Processing '{0}' module installation...".format(MODULE_NAME))

    shelf_only = False

    if try_import():
        message_lines = [
            "No installation needed!",
            "The {0} script is already accessible...".format(MODULE_NAME),
        ]

        logger.warning(" ".join(message_lines))
        message_lines.extend(["", "Would you like to install the shelf icon again?"])
        choice = confirm_message(os.linesep.join(message_lines), buttons=[BUTTON_ADD_TO_SHELF, BUTTON_QUIT])
        if choice == BUTTON_QUIT:
            logger.info("Installation aborted!")
            return
        shelf_only = True

    if is_module_loaded(MODULE_NAME):
        logger.warning(
            "The module seems to be loaded, yet the scripts are not importable...! Attempting to deploy the module again!")

    try:
        success = install_module(shelf_only=shelf_only)
    except Exception as e:
        message_lines = ["The installation failed!", "Additional information should be visible in the script editor."]
        logger.exception(message_lines[0], exc_info=True)
        confirm_message(os.linesep.join(message_lines))
        return

    messages = {
        True: "Installation finished.",
        False: "Installation failed!",
    }

    message = messages.get(success, "INVALID STATUS!")
    log_func = logger.info if success else logger.error

    log_func(message)
    confirm_message(message)
