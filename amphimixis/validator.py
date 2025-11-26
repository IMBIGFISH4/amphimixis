"""Module for validating an existing input file"""

# pylint: disable=W0603, C0103

from ipaddress import ip_address
from re import compile as re_compile

import yaml

from amphimixis.build_systems import build_systems_dict
from amphimixis.general import general
from amphimixis.logger import setup_logger

DEFAULT_PORT = 22

errors_count = 0

logger = setup_logger("validator")


def validate(config_file_path: str) -> bool:
    """Main function to validate config file

    :rtype: bool
    :return: Outcome value :\n
         True if config is valid
         False if config is invalid
    """

    try:
        with open(config_file_path, "r", encoding="UTF-8") as file:

            file_dict = yaml.safe_load(file)

            build_system = file_dict.get("build_system")
            if (
                not isinstance(build_system, str)
                or build_system.lower() not in build_systems_dict
            ):
                _warn(f"Invalid build_system: {build_system}")

            runner = file_dict.get("runner")
            if not isinstance(runner, str) or runner.lower() not in build_systems_dict:
                _warn(f"Invalid runner: {runner}")

            # validate platforms
            platforms = file_dict.get("platforms", {})
            if platforms == {}:
                _warn("Platforms not found")

            for platform in platforms:
                __is_valid_platform(platform)

            # validate recipes
            recipes = file_dict.get("recipes", {})
            if recipes == {}:
                _warn("Recipes not found")

            for recipe in recipes:
                _is_valid_recipe(recipe)

            # validate builds
            builds = file_dict.get("builds", {})
            if builds == {}:
                _warn("Builds not found")

            for build in builds:
                _is_valid_build(build)

        logger.info("Validation completed, errors found: %s", errors_count)

        # True if config is valid (0 errors)
        # False if config is invalid (>0 errors)
        return not bool(errors_count)

    except FileNotFoundError:
        logger.error("File not found")
        return False


def __is_valid_platform(platform: dict[str, str]):
    """Function to check whether plafrom is valid"""

    pl_id = platform.get("id")
    if not isinstance(pl_id, int):
        _warn(f"Invalid id in platform: {pl_id}")

    arch = platform.get("arch")
    if not isinstance(arch, str) or arch.lower() not in general.Arch:
        _warn(f"Invalid arch in platform {pl_id}: {arch}")

    address = platform.get("address")
    if address is not None and (
        not isinstance(address, str) or not _is_valid_address(address)
    ):
        _warn(f"Invalid address in platform {pl_id}: {address}")

    username = platform.get("username")
    if (
        address is None and (username is not None and not isinstance(username, str))
    ) or (address is not None and not isinstance(username, str)):
        _warn(f"Invalid username in platform {pl_id}: {username}")

    password = platform.get("password")
    if password is not None and not isinstance(password, str):
        _warn(f"Invalid password in platform {pl_id}: {password}")

    port = platform.get("port", DEFAULT_PORT)
    if not isinstance(port, int) or not 1 <= port <= 65535:
        _warn(f"Invalid port in platform {pl_id}: {port}")


def _is_valid_recipe(recipe: dict[str, str]):
    """Function to check whether recipe is valid"""

    re_id = recipe.get("id")
    if not isinstance(re_id, int):
        _warn(f"Invalid id in recipe: {re_id}")

    config_flags = recipe.get("config_flags")
    if not isinstance(config_flags, str):
        _warn(f"Invalid config_flags in recipe {re_id}: {config_flags}")

    compiler_flags = recipe.get("compiler_flags")
    if not isinstance(compiler_flags, str):
        _warn(f"Invalid compiler_flags in recipe {re_id}: {compiler_flags}")


def _is_valid_build(build: dict[str, str]):
    """Function to check whether build is valid"""

    build_machine = build.get("build_machine")
    if not isinstance(build_machine, int):
        _warn(f"Invalid build_machine in build: {build_machine}")

    run_machine = build.get("run_machine")
    if not isinstance(run_machine, int):
        _warn(f"Invalid run_machine in build: {run_machine}")

    recipe_id = build.get("recipe_id")
    if not isinstance(recipe_id, int):
        _warn(f"Invalid recipe_id in build: {recipe_id}")

    toolchain = build.get("toolchain")
    if toolchain is not None and not isinstance(toolchain, str):
        _warn(f"Invalid toolchain in build: {toolchain}")

    sysroot = build.get("sysroot")
    if sysroot is not None and not isinstance(sysroot, str):
        _warn(f"Invalid sysrott in build: {sysroot}")


def _is_valid_address(address: str) -> bool:
    """Function to check whether address is valid

    :rtype: bool
    :return: Outcome value :\n
         True if address is valid
         False if address is invalid
    """

    try:
        ip_address(address)
        return True
    except ValueError:
        if all(part.isdigit() for part in address.rstrip(".").split(".")):
            return False

        # this string checks whether domain name is valid, here some rules:
        # 1. Length <= 253
        # 2. Separate part length <= 63
        # 3. Contains only letters, digits and dash
        # 4. Doesn't start or end with dash
        # 5. May have dot at the end
        hostname_pattern = re_compile(
            r"^(?=.{1,253}$)(?!-)[A-Za-z0-9-]{1,63}(?<!-)"
            r"(\.(?!-)[A-Za-z0-9-]{1,63}(?<!-))*\.?$"
        )
        return bool(hostname_pattern.match(address))


def _warn(msg: str) -> None:
    """Function that handles messages due to invalid fields in config"""
    global errors_count
    errors_count += 1
    logger.warning(msg)
