import pytest

import jp_dates


def test_main_holiday_rc0():
    assert jp_dates.main(["jp_dates.py", "holiday", "2026-07-13"]) == 0


def test_main_addbiz_rc0():
    assert jp_dates.main(["jp_dates.py", "addbiz", "2026-07-11", "3"]) == 0


def test_main_addbiz_exclude_yearend(capsys):
    # 12/28(月)+1 with --exclude-yearend -> 2027-01-04 (jp_dates内部と同じ年末年始境界)
    rc = jp_dates.main(["jp_dates.py", "addbiz", "2026-12-28", "1", "--exclude-yearend"])
    out = capsys.readouterr().out.strip()
    assert rc == 0
    assert out == "2027-01-04"


def test_main_addbiz_typo_flag_rejected():
    with pytest.raises(SystemExit):
        jp_dates.main(["jp_dates.py", "addbiz", "2026-07-11", "3", "--exclude-yearnd"])


def test_main_wareki_rc0():
    assert jp_dates.main(["jp_dates.py", "wareki", "R6.4.1"]) == 0


def test_main_fy_rc0():
    assert jp_dates.main(["jp_dates.py", "fy", "2026-07-13"]) == 0


def test_main_unknown_subcommand_rejected():
    with pytest.raises(SystemExit):
        jp_dates.main(["jp_dates.py", "nosuchcmd", "2026-07-13"])


def test_main_holiday_bad_date_raises_valueerror():
    with pytest.raises(ValueError):
        jp_dates.main(["jp_dates.py", "holiday", "notdate"])
