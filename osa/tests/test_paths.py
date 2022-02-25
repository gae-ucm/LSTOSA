from pathlib import Path

import pytest

from osa.configs import options
from osa.configs.config import cfg
from osa.utils.utils import lstdate_to_dir


def test_get_calibration_file(r0_data):
    from osa.paths import get_calibration_file
    for file in r0_data:
        assert file.exists()
    file = get_calibration_file(1805)
    file.exists()


def test_get_drs4_pedestal_file(r0_data):
    from osa.paths import get_drs4_pedestal_file
    for file in r0_data:
        assert file.exists()
    file = get_drs4_pedestal_file(1804)
    file.exists()


def test_get_time_calibration_file(drs4_time_calibration_files):
    from osa.paths import get_time_calibration_file
    for file in drs4_time_calibration_files:
        assert file.exists()

    run = 1616
    time_file = get_time_calibration_file(run)
    assert time_file == drs4_time_calibration_files[0]

    run = 1625
    time_file = get_time_calibration_file(run)
    assert time_file == drs4_time_calibration_files[0]

    run = 1900
    time_file = get_time_calibration_file(run)
    assert time_file == drs4_time_calibration_files[0]

    run = 4211
    time_file = get_time_calibration_file(run)
    assert time_file == drs4_time_calibration_files[1]

    run = 5000
    time_file = get_time_calibration_file(run)
    assert time_file == drs4_time_calibration_files[1]

    run = 5979
    time_file = get_time_calibration_file(run)
    assert time_file == drs4_time_calibration_files[2]

    run = 6000
    time_file = get_time_calibration_file(run)
    assert time_file == drs4_time_calibration_files[2]


def test_pedestal_ids_file_exists(pedestal_ids_file):
    from osa.paths import pedestal_ids_file_exists
    pedestal_ids_file.exists()
    assert pedestal_ids_file_exists(1808) is True


def test_get_datacheck_file(datacheck_dl1_files):
    from osa.paths import get_datacheck_files
    for file in datacheck_dl1_files:
        assert file.exists()
    dl1_path = Path("test_osa/test_files0/DL1/20200117/v0.1.0/tailcut84")
    files = get_datacheck_files(pattern="datacheck*.pdf", directory=dl1_path)
    expected_files = [
        dl1_path / "datacheck_dl1_LST-1.Run01808.pdf",
        dl1_path / "datacheck_dl1_LST-1.Run01807.pdf"
    ]
    assert set(files) == set(expected_files)


def test_destination_dir():
    from osa.paths import destination_dir

    options.date = "2020_01_17"
    datedir = lstdate_to_dir(options.date)
    options.dl1_prod_id = cfg.get("LST1", "DL1_PROD_ID")
    options.dl2_prod_id = cfg.get("LST1", "DL2_PROD_ID")
    options.prod_id = cfg.get("LST1", "PROD_ID")
    base_directory = cfg.get("LST1", "BASE")
    base_path = Path(base_directory)

    data_types = {
        "DL1AB": "DL1",
        "DATACHECK": "DL1",
        "MUON": "DL1",
        "DL2": "DL2",
    }

    for concept, dst_dir in data_types.items():
        directory = destination_dir(concept, create_dir=False)
        if concept in ["DL1AB", "DATACHECK"]:
            expected_directory = (
                base_path / dst_dir / datedir / options.prod_id / options.dl1_prod_id
            )
        elif concept == "DL2":
            expected_directory = (
                base_path / dst_dir / datedir / options.prod_id / options.dl2_prod_id
            )
        else:
            expected_directory = base_path / dst_dir / datedir / options.prod_id

        assert directory == expected_directory


def test_get_run_date(r0_data):
    from osa.paths import get_run_date
    assert get_run_date(1807) == "20200117"

    with pytest.raises(IOError):
        get_run_date(1200)