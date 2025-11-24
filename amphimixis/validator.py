"""Module for validating an existing input file"""

# pylint: disable=W0603, C0103

from ipaddress import ip_address
from re import compile as re_compile
import yaml

from amphimixis.general import general
from amphimixis.build_systems import build_systems_dict
from amphimixis.logger import setup_logger

DEFAULT_PORT = 22

errors_count = 0

logger = setup_logger("validator")


def validate(file_name: str) -> None:
    """Module enter funtcion"""

    try:
        with open(file_name, "r", encoding="UTF-8") as file:

            global errors_count

            file_dict = yaml.safe_load(file)

            build_system = file_dict.get("build_system")
            if (
                not isinstance(build_system, str)
                or build_system.lower() not in build_systems_dict
            ):
                logger.warning("Invalid build_system: %s", build_system)
                errors_count += 1

            runner = file_dict.get("runner")
            if not isinstance(runner, str) or runner.lower() not in build_systems_dict:
                logger.warning("Invalid runner: %s", runner)
                errors_count += 1

            # validate platforms
            platforms = file_dict.get("platforms", {})
            if platforms is None:
                logger.warning("Platforms not found")
                errors_count += 1

            for platform in platforms:
                __is_valid_platform(platform)

            # validate recipes
            recipes = file_dict.get("recipes", {})
            if recipes is None:
                logger.warning("Recipes not found")
                errors_count += 1

            for recipe in recipes:
                _is_valid_recipe(recipe)

            # validate builds
            builds = file_dict.get("builds", {})
            if builds is None:
                logger.warning("Builds not found")
                errors_count += 1

            for build in builds:
                _is_valid_build(build)

        logger.info("Validation completed, errors found: %s", errors_count)

    except FileNotFoundError:
        logger.error("File not found")


def __is_valid_platform(platform: dict[str, str]):
    """Function to check whether plafrom is valid"""

    global errors_count

    pl_id = platform.get("id")
    if not isinstance(pl_id, int):
        logger.warning("Invalid id in platform: %s", pl_id)
        errors_count += 1

    arch = platform.get("arch")
    if not isinstance(arch, str) or arch.lower() not in general.Arch:
        logger.warning("Invalid arch in platform %s: %s", pl_id, arch)
        errors_count += 1

    address = platform.get("address")
    if address is not None and (
        not isinstance(address, str) or not _is_valid_address(address)
    ):
        logger.warning("Invalid address in platform %s: %s", pl_id, address)
        errors_count += 1

    username = platform.get("username")
    if (
        address is None and (username is not None and not isinstance(username, str))
    ) or (address is not None and not isinstance(username, str)):
        logger.warning("Invalid username in platform %s: %s", pl_id, username)
        errors_count += 1

    password = platform.get("password")
    if password is not None and not isinstance(password, str):
        logger.warning("Invalid password in platform %s: %s", pl_id, password)
        errors_count += 1

    port = platform.get("port", DEFAULT_PORT)
    if not isinstance(port, int) or not 1 <= port <= 65535:
        logger.warning("Invalid port in platform %s: %s", pl_id, port)
        errors_count += 1


def _is_valid_recipe(recipe: dict[str, str]):
    """Function to check whether recipe is valid"""

    global errors_count

    re_id = recipe.get("id")
    if not isinstance(re_id, int):
        logger.warning("Invalid id in recipe: %s", re_id)
        errors_count += 1

    config_flags = recipe.get("config_flags")
    if not isinstance(config_flags, str):
        logger.warning("Invalid config_flags in recipe %s: %s", re_id, config_flags)
        errors_count += 1

    compiler_flags = recipe.get("compiler_flags")
    if not isinstance(compiler_flags, str):
        logger.warning("Invalid compiler_flags in recipe %s: %s", re_id, compiler_flags)
        errors_count += 1


def _is_valid_build(build: dict[str, str]):
    """Function to check whether build is valid"""

    global errors_count

    build_machine = build.get("build_machine")
    if not isinstance(build_machine, int):
        logger.warning("Invalid build_machine in build: %s", build_machine)
        errors_count += 1

    run_machine = build.get("run_machine")
    if not isinstance(run_machine, int):
        logger.warning("Invalid run_machine in build: %s", run_machine)
        errors_count += 1

    recipe_id = build.get("recipe_id")
    if not isinstance(recipe_id, int):
        logger.warning("Invalid recipe_id in build: %s", recipe_id)
        errors_count += 1

    toolchain = build.get("toolchain")
    if toolchain is not None and not isinstance(toolchain, str):
        logger.warning("Invalid toolchain in build: %s", toolchain)
        errors_count += 1

    sysroot = build.get("sysroot")
    if sysroot is not None and not isinstance(sysroot, str):
        logger.warning("Invalid sysroot in build: %s", sysroot)
        errors_count += 1


def _is_valid_address(address: str) -> bool:
    """Function to check whether addtess id valid"""

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
