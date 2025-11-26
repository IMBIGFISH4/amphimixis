"""Module for configuring a new build"""

import pickle
from os import getcwd, path
from platform import machine as local_arch

import yaml

from amphimixis.build_systems import build_systems_dict
from amphimixis.general import general
from amphimixis.logger import setup_logger
from amphimixis.shell import Shell
from amphimixis.validator import validate

DEFAULT_PORT = 22

logger = setup_logger("configurator")


def parse_config(project: general.Project, config_file_path: str) -> None:
    """Module enter function"""

    if not path.exists(project.path):
        logger.error("Incorrect project path @_@, check input arguments")
        raise FileNotFoundError()

    project.builds = []

    if not validate(config_file_path):
        logger.error("Incorrect input file")
        raise SyntaxError()

    try:
        with open(config_file_path, "r", encoding="UTF-8") as file:
            input_config = yaml.safe_load(file)

            build_system = input_config.get("build_system")
            runner = input_config.get("runner")

            project.build_system = build_systems_dict[build_system.lower()]
            project.runner = build_systems_dict[runner.lower()]

            for build in input_config["builds"]:

                toolchain = build.get("toolchain")
                sysroot = build.get("sysroot")

                _create_build(
                    project,
                    _get_by_id(input_config["platforms"], build["build_machine"]),
                    _get_by_id(input_config["platforms"], build["run_machine"]),
                    _get_by_id(input_config["recipes"], build["recipe_id"]),
                    toolchain,
                    sysroot,
                )

    except FileNotFoundError as e:
        logger.error("Error opening file, check input data %s", e)

    logger.info("Configuration completed successfully!")


def _create_build(  # pylint: disable=R0913,R0917
    project: general.Project,
    build_machine_info: dict[str, str],
    run_machine_info: dict[str, str],
    recipe_info: dict[str, str],
    toolchain: str | None,
    sysroot: str | None,
) -> None:
    """Function to create a new build and save its configuration to a Pickle file"""

    build_path = _generate_build_path(
        build_machine_info["id"], run_machine_info["id"], recipe_info["id"]
    )

    build_machine = _create_machine(build_machine_info)
    run_machine = _create_machine(run_machine_info)
    _has_valid_arch(run_machine)

    build = general.Build(build_machine, run_machine, build_path, toolchain, sysroot)

    build.config_flags = recipe_info["config_flags"]
    build.compiler_flags = recipe_info["compiler_flags"]

    project.builds.append(build)

    config_name = f"{build_path}_config"
    with open(config_name, "wb") as file:
        pickle.dump(build, file)


def _create_machine(machine_info: dict[str, str]) -> general.MachineInfo:
    """Function to create a new machine"""

    arch = str(machine_info.get("arch"))
    address = machine_info.get("address")
    auth = None

    if address is not None:
        username = str(machine_info.get("username"))
        password = machine_info.get("password")
        port = int(machine_info.get("port", DEFAULT_PORT))

        auth = general.MachineAuthenticationInfo(username, password, port)

    machine = general.MachineInfo(general.Arch(arch.lower()), address, auth)

    return machine


def _generate_build_path(build_id: str, run_id: str, recipe_id: str) -> str:
    """Function to create path to build, depending on build, run and recipes ids"""

    return path.normpath(path.join(getcwd(), f"{build_id}_{run_id}_{recipe_id}"))


def _get_by_id(items: list[dict[str, str]], target_id: str) -> dict[str, str]:
    """Function to find platform or recipe by id"""

    for item in items:
        if item["id"] == target_id:
            return item

    logger.error("Item id didn't match any existed id, check input file")
    raise LookupError()


def _has_valid_arch(machine: general.MachineInfo) -> None:
    """Function to check whether run machine arch is valid"""

    if machine.address is None:
        if machine.arch.lower() not in local_arch().lower():
            logger.error(
                "Invalid local machibe arch: %s, your machine is %s",
                machine.arch.name.lower(),
                local_arch().lower(),
            )
            raise TypeError()

    else:
        shell = Shell(machine).connect()
        error_code, stdout, _ = shell.run("uname -m")
        if error_code != 0:
            logger.error(
                "An error occured during reading remote machine arch, check remote machine"
            )
            raise ValueError()

        remote_arch = stdout[0][0]
        if machine.arch.lower() not in remote_arch.lower():
            logger.error(
                "Invalid remote machibe arch: %s, remote machine is %s",
                machine.arch.name.lower(),
                remote_arch.lower(),
            )
            raise TypeError()
