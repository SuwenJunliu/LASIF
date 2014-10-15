#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""
Test cases for the CLI interface.

Many of these test are very similar to the project tests. But this is what the
CLI interface is supposed to provide: an easy way to interface with the
project's components.

Furthermore many tests are simple mock tests only asserting that the proper
methods are called.

In many cases ``patch.assert_called_once_with()`` and
``assert patch.call_count == 1`` is used. That is because it is really easy
to mistype the method and then mock just ignores it resulting in nothing
being actually tested. So its just an additional design decision.

:copyright:
    Lion Krischer (krischer@geophysik.uni-muenchen.de), 2013-2014
:license:
    GNU General Public License, Version 3
    (http://www.gnu.org/copyleft/gpl.html)
"""
import matplotlib as mpl
mpl.use("agg")

import numpy as np
import mock
import os
import shutil

import lasif
from lasif.scripts import lasif_cli

from lasif.tests.testing_helpers import communicator, cli  # NOQA
from lasif.tests.testing_helpers import reset_matplotlib

# Get a list of all available commands.
CMD_LIST = [key.replace("lasif_", "")
            for (key, value) in lasif_cli.__dict__.iteritems()
            if (key.startswith("lasif_") and callable(value))]


def setup_function(function):
    """
    Make sure matplotlib behaves the same on every machine.
    """
    reset_matplotlib()


def test_test_sanity():
    """
    Quick test to test the tests...
    """
    assert len(CMD_LIST) >= 10
    assert "info" in CMD_LIST
    assert "init_project" in CMD_LIST


def test_invocation_without_parameters(cli):
    """
    Tests the invocation without any parameters.
    """
    default_output = cli.run("lasif")
    # Should be the same as if invoced with --help.
    assert default_output == cli.run("lasif --help")
    # It should furthermore contain a list of all commands.
    for cmd in CMD_LIST:
        assert cmd in default_output.stdout


def test_help_messages(cli):
    """
    Tests the help messages.
    """
    for cmd in CMD_LIST:
        # Both invocations should work
        assert cli.run("lasif %s --help" % cmd) == \
            cli.run("lasif help %s" % cmd)
        # Some things should always be shown. This also more or less tests that
        # the argparse parser is used everywhere.
        help_string = cli.run("lasif %s --help" % cmd).stdout
        assert help_string.startswith("usage: lasif %s" % cmd)
        assert "show this help message and exit" in help_string
        assert "optional arguments:" in help_string


def test_command_tolerance(cli):
    """
    Tests that upper and lowercase subcommands are not distinguished.
    """
    with mock.patch("lasif.scripts.lasif_cli.lasif_info") as patch:
        cli.run("lasif info")
    patch.assert_called_once()
    assert patch.call_count == 1

    with mock.patch("lasif.scripts.lasif_cli.lasif_info") as patch:
        cli.run("lasif INFO")
    patch.assert_called_once()
    assert patch.call_count == 1

    with mock.patch("lasif.scripts.lasif_cli.lasif_info") as patch:
        cli.run("lasif InFo")
    patch.assert_called_once()
    assert patch.call_count == 1


def test_unknown_command(cli):
    """
    Tests the message when an unknown command is called.
    """
    out = cli.run("lasif asdflkjaskldfj")
    assert out.stdout == ""
    assert out.stderr == ("lasif: 'asdflkjaskldfj' is not a LASIF command. "
                          "See 'lasif --help'.\n")


def test_fuzzy_command_matching(cli):
    """
    If the user enters a slightly wrong subcommand, the user should be notified
    of alternatives.
    """
    out = cli.run("lasif infi")
    assert out.stdout == ""
    assert out.stderr == (
        "lasif: 'infi' is not a LASIF command. See 'lasif --help'.\n\n"
        "Did you mean this?\n"
        "\tinfo\n")

    out = cli.run("lasif plot_eventos")
    assert out.stdout == ""
    assert out.stderr == (
        "lasif: 'plot_eventos' is not a LASIF command. See 'lasif --help'.\n\n"
        "Did you mean one of these?\n"
        "    list_events\n"
        "    plot_event\n"
        "    plot_events\n"
        "    plot_windows\n")


def test_cli_parsing_corner_cases(cli):
    """
    Tests any funky corner cases related to the command line parsing.
    """
    out = cli.run("lasif help --help")
    assert out.stdout == ""
    assert out.stderr == "lasif: Invalid command. See 'lasif --help'.\n"


def test_project_init_without_arguments(cli):
    """
    Tests the project initialization with the CLI interface without passed
    arguments.
    """
    # Invocation without a folder path fails.
    log = cli.run("lasif init_project")
    assert "error: too few arguments" in log.stderr


def test_project_init(cli):
    """
    Tests the project initialization.
    """
    # Delete all contents of directory to be able to start with a clean one.
    root_path = cli.comm.project.paths["root"]
    for filename in os.listdir(root_path):
        file_path = os.path.join(root_path, filename)
        if os.path.isfile(file_path):
            os.remove(file_path)
        else:
            shutil.rmtree(file_path)

    # Initialize project.
    out = cli.run("lasif init_project TestDummy")
    assert out.stderr == ""
    assert "Initialized project in" in out.stdout

    # Make sure all the expected things are there.
    project_dir = os.path.join(root_path, "TestDummy")
    assert os.path.exists(project_dir)
    contents = sorted(os.listdir(project_dir))
    assert contents == sorted([
        "ADJOINT_SOURCES_AND_WINDOWS", "CACHE", "config.xml", "DATA", "EVENTS",
        "ITERATIONS", "KERNELS", "LOGS", "MODELS", "OUTPUT", "STATIONS",
        "SYNTHETICS", "WAVEFIELDS"])

    # Test the generated config file.
    expected = "\n".join([
        "<?xml version='1.0' encoding='UTF-8'?>",
        "<lasif_project>",
        "  <name>TestDummy</name>",
        "  <description></description>",
        "  <download_settings>",
        "    <seconds_before_event>300</seconds_before_event>",
        "    <seconds_after_event>3600</seconds_after_event>",
        "    <interstation_distance_in_m>1000.0</interstation_distance_in_m>",
        "    <channel_priorities>",
        "      <priority>BH[Z,N,E]</priority>",
        "      <priority>LH[Z,N,E]</priority>",
        "      <priority>HH[Z,N,E]</priority>",
        "      <priority>EH[Z,N,E]</priority>",
        "      <priority>MH[Z,N,E]</priority>",
        "    </channel_priorities>",
        "    <location_priorities>",
        "      <priority></priority>",
        "      <priority>00</priority>",
        "      <priority>10</priority>",
        "      <priority>20</priority>",
        "      <priority>01</priority>",
        "      <priority>02</priority>",
        "    </location_priorities>",
        "  </download_settings>",
        "  <domain>",
        "    <global>false</global>",
        "    <domain_bounds>",
        "      <minimum_longitude>-20</minimum_longitude>",
        "      <maximum_longitude>20</maximum_longitude>",
        "      <minimum_latitude>-20</minimum_latitude>",
        "      <maximum_latitude>20</maximum_latitude>",
        "      <minimum_depth_in_km>0.0</minimum_depth_in_km>",
        "      <maximum_depth_in_km>200.0</maximum_depth_in_km>",
        "      <boundary_width_in_degree>3.0</boundary_width_in_degree>",
        "    </domain_bounds>",
        "    <domain_rotation>",
        "      <rotation_axis_x>1.0</rotation_axis_x>",
        "      <rotation_axis_y>1.0</rotation_axis_y>",
        "      <rotation_axis_z>1.0</rotation_axis_z>",
        "      <rotation_angle_in_degree>-45.0</rotation_angle_in_degree>",
        "    </domain_rotation>",
        "  </domain>",
        "</lasif_project>\n"])
    with open(os.path.join(project_dir, "config.xml"), "rt") as fh:
        actual = fh.read()
    assert actual == expected


def test_plotting_functions(cli):
    """
    Tests if the correct plotting functions are called.
    """
    vs = "lasif.components.visualizations.VisualizationsComponent."
    with mock.patch(vs + "plot_domain") as patch:
        cli.run("lasif plot_domain")
    patch.assert_called_once_with()
    assert patch.call_count == 1

    with mock.patch(vs + "plot_event") as patch:
        cli.run("lasif plot_event EVENT_NAME")
    patch.assert_called_once_with("EVENT_NAME")
    assert patch.call_count == 1

    # Test the different variations of the plot_events function.
    with mock.patch(vs + "plot_events") as patch:
        cli.run("lasif plot_events")
    patch.assert_called_once_with("map")
    assert patch.call_count == 1

    with mock.patch(vs + "plot_events") as patch:
        cli.run("lasif plot_events --type=map")
    patch.assert_called_once_with("map")
    assert patch.call_count == 1

    with mock.patch(vs + "plot_events") as patch:
        cli.run("lasif plot_events --type=time")
    patch.assert_called_once_with("time")
    assert patch.call_count == 1

    with mock.patch(vs + "plot_events") as patch:
        cli.run("lasif plot_events --type=depth")
    patch.assert_called_once_with("depth")
    assert patch.call_count == 1

    # Misc plotting functionality.
    with mock.patch(vs + "plot_raydensity") as patch:
        cli.run("lasif plot_raydensity")
    patch.assert_called_once_with()
    assert patch.call_count == 1


def test_download_utitlies(cli):
    """
    Testing the invocation of the downloaders.
    """
    # SPUD interface downloader.
    with mock.patch("lasif.scripts.iris2quakeml.iris2quakeml") as patch:
        cli.run("lasif add_spud_event https://test.org")
    patch.assert_called_once_with(
        "https://test.org", cli.comm.project.paths["events"])
    assert patch.call_count == 1

    # Test the download data invocation.
    with mock.patch("lasif.components.downloads.DownloadsComponent"
                    ".download_data") \
            as download_patch:
        out = cli.run("lasif download_data "
                      "GCMT_event_TURKEY_Mag_5.1_2010-3-24-14-11")
    assert out.stderr == ""
    download_patch.assert_called_once_with(
        "GCMT_event_TURKEY_Mag_5.1_2010-3-24-14-11", providers=None)
    assert download_patch.call_count == 1

    # Test setting the providers.
    with mock.patch("lasif.components.downloads.DownloadsComponent"
                    ".download_data") \
            as download_patch:
        out = cli.run("lasif download_data "
                      "GCMT_event_TURKEY_Mag_5.1_2010-3-24-14-11 "
                      "--providers IRIS ORFEUS")
    assert out.stderr == ""
    download_patch.assert_called_once_with(
        "GCMT_event_TURKEY_Mag_5.1_2010-3-24-14-11",
        providers=["IRIS", "ORFEUS"])
    assert download_patch.call_count == 1


def test_lasif_info(cli):
    """
    Tests the 'lasif info' command.
    """
    out = cli.run("lasif info").stdout
    assert "\"ExampleProject\"" in out
    assert "Toy Project used in the Test Suite" in out
    assert "2 events" in out
    assert "4 station files" in out
    assert "4 raw waveform files" in out
    assert "0 processed waveform files" in out
    assert "6 synthetic waveform files" in out


def test_various_list_functions(cli):
    """
    Tests all the "lasif list_" functions.
    """
    events = cli.run("lasif list_events").stdout
    assert "2 events" in events
    assert "GCMT_event_TURKEY_Mag_5.1_2010-3-24-14-11" in events
    assert "GCMT_event_TURKEY_Mag_5.9_2011-5-19-20-15" in events

    iterations = cli.run("lasif list_iterations").stdout
    assert "0 iterations" in iterations
    with open(os.path.join(cli.comm.project.paths["iterations"],
                           "ITERATION_1.xml"), "wt") as fh:
        fh.write("<>")
    iterations = cli.run("lasif list_iterations").stdout
    assert "1 iteration" in iterations
    with open(os.path.join(cli.comm.project.paths["iterations"],
                           "ITERATION_2.xml"), "wt") as fh:
        fh.write("<>")
    iterations = cli.run("lasif list_iterations").stdout
    assert "2 iteration" in iterations

    models = cli.run("lasif list_models").stdout
    assert "0 models" in models
    os.makedirs(os.path.join(cli.comm.project.paths["models"], "BLUB"))
    models = cli.run("lasif list_models").stdout
    assert "1 model" in models


def test_iteration_creation_and_stf_plotting(cli):
    """
    Tests the generation of an iteration and the supsequent STF plotting.
    """
    cli.run("lasif create_new_iteration 1 8.0 100.0 SES3D_4_1")
    assert cli.comm.iterations.has_iteration("1")

    with mock.patch("lasif.visualization.plot_tf") as patch:
        cli.run("lasif plot_stf 1")
    patch.assert_called_once()
    assert patch.call_count == 1
    data, delta = patch.call_args[0]
    np.testing.assert_array_equal(
        data,
        cli.comm.iterations.get("1").get_source_time_function()["data"])
    assert delta == 0.75


def test_lasif_event_info(cli):
    """
    Tests the event info function.
    """
    event_1 = cli.run("lasif event_info "
                      "GCMT_event_TURKEY_Mag_5.1_2010-3-24-14-11").stdout
    event_2 = cli.run("lasif event_info "
                      "GCMT_event_TURKEY_Mag_5.9_2011-5-19-20-15").stdout

    assert "5.1 Mw" in event_1
    assert "TURKEY" in event_1
    assert "38.820" in event_1
    assert "available at 4 stations" in event_1

    assert "5.9 Mw" in event_2
    assert "TURKEY" in event_2
    assert "39.150" in event_2
    assert "available at 0 stations" in event_2


def test_input_file_generation(cli):
    """
    Mock test to see if the input file generation routine is called. The
    routine is tested partially by the event tests and more by the input file
    generation module.
    """
    ac = "lasif.components.actions.ActionsComponent."
    # No simluation type specified.
    with mock.patch(ac + "generate_input_files") as patch:
        out = cli.run("lasif generate_input_files 1 "
                      "GCMT_event_TURKEY_Mag_5.1_2010-3-24-14-11")
    assert out.stderr == ""
    patch.assert_called_once_with(
        "1", "GCMT_event_TURKEY_Mag_5.1_2010-3-24-14-11",
        "normal simulation")
    assert patch.call_count == 1

    # Normal simulation
    with mock.patch(ac + "generate_input_files") as patch:
        out = cli.run("lasif generate_input_files 1 "
                      "GCMT_event_TURKEY_Mag_5.1_2010-3-24-14-11 "
                      "--simulation_type=normal_simulation")
    assert out.stderr == ""
    patch.assert_called_once_with(
        "1", "GCMT_event_TURKEY_Mag_5.1_2010-3-24-14-11",
        "normal simulation")
    assert patch.call_count == 1

    # Adjoint forward.
    with mock.patch(ac + "generate_input_files") as patch:
        out = cli.run("lasif generate_input_files 1 "
                      "GCMT_event_TURKEY_Mag_5.1_2010-3-24-14-11 "
                      "--simulation_type=adjoint_forward")
    assert out.stderr == ""
    patch.assert_called_once_with(
        "1", "GCMT_event_TURKEY_Mag_5.1_2010-3-24-14-11",
        "adjoint forward")
    assert patch.call_count == 1

    # Adjoint reverse.
    with mock.patch(ac + "generate_input_files") as patch:
        out = cli.run("lasif generate_input_files 1 "
                      "GCMT_event_TURKEY_Mag_5.1_2010-3-24-14-11 "
                      "--simulation_type=adjoint_reverse")
    assert out.stderr == ""
    patch.assert_called_once_with(
        "1", "GCMT_event_TURKEY_Mag_5.1_2010-3-24-14-11",
        "adjoint reverse")
    assert patch.call_count == 1


def test_finalize_adjoint_sources(cli):
    """
    Simple mock test.
    """
    with mock.patch("lasif.components.actions.ActionsComponent"
                    ".finalize_adjoint_sources") as p:
        out = cli.run("lasif finalize_adjoint_sources 1 "
                      "GCMT_event_TURKEY_Mag_5.1_2010-3-24-14-11")
    assert out.stderr == ""
    p.assert_called_once_with(
        "1", "GCMT_event_TURKEY_Mag_5.1_2010-3-24-14-11")
    assert p.call_count == 1


def test_launch_misfit_gui(cli):
    with mock.patch("lasif.misfit_gui.misfit_gui.launch") as patch:
        cli.run("lasif launch_misfit_gui")

    assert patch.call_count == 1


def test_preprocessing(cli):
    """
    Tests the proprocessing.
    """
    cli.run("lasif create_new_iteration 1 8.0 100.0 SES3D_4_1")

    event = "GCMT_event_TURKEY_Mag_5.1_2010-3-24-14-11"
    data_path = cli.comm.project.paths["data"]
    processing_tag = cli.comm.iterations.get("1").processing_tag
    preprocessing_path = os.path.join(data_path, event, processing_tag)

    # Nothing should exist yet.
    assert not os.path.exists(preprocessing_path)

    # Preprocess some data.
    cli.run("lasif preprocess_data 1")

    assert os.path.exists(preprocessing_path)
    assert len(os.listdir(preprocessing_path)) == 4


def test_preprocessing_event_limiting_works(cli):
    """
    Asserts that the event parsing is correct.
    """
    ac = "lasif.components.actions.ActionsComponent."
    cli.run("lasif create_new_iteration 1 8.0 100.0 SES3D_4_1")

    # No event should result in None.
    with mock.patch(ac + "preprocess_data") as patch:
        cli.run("lasif preprocess_data 1")
    assert patch.call_count == 1
    patch.assert_called_once_with("1", None)

    # One specified event should result in one event.
    with mock.patch(ac + "preprocess_data") as patch:
        cli.run("lasif preprocess_data 1 "
                "GCMT_event_TURKEY_Mag_5.1_2010-3-24-14-11")
    assert patch.call_count == 1
    patch.assert_called_once_with(
        "1", ["GCMT_event_TURKEY_Mag_5.1_2010-3-24-14-11"])

    # Multiple result in multiple.
    with mock.patch(ac + "preprocess_data") as patch:
        cli.run("lasif preprocess_data 1 "
                "GCMT_event_TURKEY_Mag_5.1_2010-3-24-14-11 "
                "GCMT_event_TURKEY_Mag_5.9_2011-5-19-20-15")
    assert patch.call_count == 1
    patch.assert_called_once_with(
        "1", ["GCMT_event_TURKEY_Mag_5.1_2010-3-24-14-11",
              "GCMT_event_TURKEY_Mag_5.9_2011-5-19-20-15"])

    out = cli.run("lasif preprocess_data 1 blub wub").stdout
    assert "Event 'blub' not found." in out


def test_iteration_info(cli):
    """
    Tests the 'lasif iteration_info' command.
    """
    cli.run("lasif create_new_iteration 1 8.0 100.0 SES3D_4_1")

    out = cli.run("lasif iteration_info 1").stdout
    assert "LASIF Iteration" in out
    assert "Name: 1" in out
    assert "Solver: SES3D 4.1" in out


def test_remove_empty_coordinate_entries(cli):
    """
    Simple mock test.
    """
    with mock.patch("lasif.components.inventory_db.InventoryDBComponent"
                    ".remove_coordinate_less_stations")\
            as patch:
        out = cli.run("lasif remove_empty_coordinate_entries")
    assert out.stderr == ""
    patch.assert_run_once_with()
    assert patch.call_count == 1


def test_validate_data(cli):
    """
    Simple mock test.
    """
    vc = "lasif.components.validator.ValidatorComponent."
    with mock.patch(vc + "validate_data") as patch:
        cli.run("lasif validate_data")
        patch.assert_called_once_with(station_file_availability=False,
                                      raypaths=False, waveforms=False)

    with mock.patch(vc + "validate_data") as patch:
        cli.run("lasif validate_data --full")
        patch.assert_called_once_with(station_file_availability=True,
                                      raypaths=True, waveforms=True)


def test_open_tutorial(cli):
    """
    Simple mock test.
    """
    with mock.patch("webbrowser.open") as patch:
        cli.run("lasif tutorial")
        patch.assert_called_once_with("http://krischer.github.io/LASIF/")


def test_iteration_status_command(cli):
    """
    The iteration status command returns the current state of any iteration. It
    returns the number of already preprocessed data files, how many synthetics
    are available, the windows and adjoint sources.
    """
    cli.run("lasif create_new_iteration 1 8.0 100.0 SES3D_4_1")
    out = cli.run("lasif iteration_status 1").stdout.splitlines()
    assert [_i.strip() for _i in out] == [
        "Iteration 1 is defined for 1 events:",
        "GCMT_event_TURKEY_Mag_5.1_2010-3-24-14-11",
        "0.00 % of the events stations have picked windows",
        "Lacks processed data for 4 stations",
        "Lacks synthetic data for 2 stations",
    ]

    cli.run("lasif preprocess_data 1")
    out = cli.run("lasif iteration_status 1").stdout.splitlines()
    assert [_i.strip() for _i in out] == [
        "Iteration 1 is defined for 1 events:",
        "GCMT_event_TURKEY_Mag_5.1_2010-3-24-14-11",
        "0.00 % of the events stations have picked windows",
        "Lacks synthetic data for 2 stations",
    ]

    # Copy the data for the first event to the second.
    shutil.rmtree(os.path.join(
        cli.comm.project.paths["data"],
        "GCMT_event_TURKEY_Mag_5.9_2011-5-19-20-15"))
    shutil.copytree(
        os.path.join(cli.comm.project.paths["data"],
                     "GCMT_event_TURKEY_Mag_5.1_2010-3-24-14-11"),
        os.path.join(cli.comm.project.paths["data"],
                     "GCMT_event_TURKEY_Mag_5.9_2011-5-19-20-15"))
    # The iteration has to be recreated.
    os.remove(os.path.join(cli.comm.project.paths["iterations"],
                           "ITERATION_1.xml"))

    cli.run("lasif create_new_iteration 1 8.0 100.0 SES3D_4_1")
    out = cli.run("lasif iteration_status 1").stdout.splitlines()
    assert [_i.strip() for _i in out] == [
        "Iteration 1 is defined for 2 events:",
        "GCMT_event_TURKEY_Mag_5.1_2010-3-24-14-11",
        "0.00 % of the events stations have picked windows",
        "Lacks synthetic data for 2 stations",
        "GCMT_event_TURKEY_Mag_5.9_2011-5-19-20-15",
        "0.00 % of the events stations have picked windows",
        "Lacks synthetic data for 4 stations",
    ]


def test_Q_model_plotting(cli):
    """
    Tests the Q model plotting via mocking.
    """
    cli.run("lasif create_new_iteration 1 7.0 70.0 SES3D_4_1")
    with mock.patch("lasif.tools.Q_discrete.plot") as patch:
        out = cli.run("lasif plot_Q_model 1")

    assert out.stderr == ""
    assert patch.call_count == 1
    kwargs = patch.call_args[1]

    assert round(kwargs["f_min"] - 1.0 / 70.0, 5) == 0
    assert round(kwargs["f_max"] - 1.0 / 7.0, 5) == 0


def test_Q_model_calculating(cli):
    """
    Tests the Q model calculation via mocking.
    """
    with mock.patch("lasif.tools.Q_discrete.calculate_Q_model") as patch:
        patch.return_value = ([1, 2, 3], [4, 5, 6])
        out = cli.run("lasif calculate_constant_Q_model 12 234").stdout
    assert patch.call_count == 1
    kwargs = patch.call_args[1]

    assert round(kwargs["f_min"] - 1.0 / 234, 5) == 0
    assert round(kwargs["f_max"] - 1.0 / 12, 5) == 0

    assert out == (
        "Weights: 1, 2, 3\n"
        "Relaxation Times: 1, 2, 3\n")


def test_debug_information(cli):
    """
    Tests the debugging information.
    """
    # Files not found.
    out = cli.run("lasif debug DUMMY_1 DUMMY_2").stdout
    assert "Path 'DUMMY_1' does not exist." in out
    assert "Path 'DUMMY_2' does not exist." in out

    # Check a file to make sure the binding works. Other file types are
    # tested elsewhere.
    out = cli.run("lasif debug " + cli.comm.project.paths["config_file"])
    assert "The main project configuration file" in out.stdout


def test_version_str(cli):
    """
    Tests if the version is printed correctly.
    """
    out = cli.run("lasif --version")
    assert out.stderr == ""
    assert out.stdout.strip() == "LASIF version %s" % lasif.__version__
