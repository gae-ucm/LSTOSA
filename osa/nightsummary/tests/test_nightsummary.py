from pathlib import Path


def test_get_nightsummary_file():
    from osa.nightsummary.nightsummary import get_runsummary_file
    from osa.configs.config import cfg

    cfg.get("LST1", "RUN_SUMMARY_DIR")
    summary_filename = get_runsummary_file("2020_01_01")
    assert summary_filename == Path(cfg.get("LST1", "RUN_SUMMARY_DIR")) /\
           "RunSummary_20200101.ecsv"


def test_run_summary_table():
    from osa.nightsummary.nightsummary import run_summary_table

    date = "2020_01_17"
    summary = run_summary_table(date)

    assert "run_id" in summary.columns
