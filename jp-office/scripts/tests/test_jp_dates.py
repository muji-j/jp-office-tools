from datetime import date

import jp_dates


def test_is_holiday_ganjitsu():
    assert jp_dates.is_holiday(date(2026, 1, 1)) is not None  # 元日

def test_is_holiday_furikae():
    # 2026-05-03(憲法記念日)이 일요일 → 5/6이 振替休日
    assert jp_dates.is_holiday(date(2026, 5, 6)) is not None

def test_is_holiday_weekday_none():
    assert jp_dates.is_holiday(date(2026, 7, 10)) is None  # 평일 금요일

def test_add_business_days_over_weekend():
    assert jp_dates.add_business_days(date(2026, 7, 10), 1) == date(2026, 7, 13)  # 금→월

def test_add_business_days_over_holiday():
    # 2026-07-20(월)은 海の日 → 금요일+1영업일 = 화요일
    assert jp_dates.add_business_days(date(2026, 7, 17), 1) == date(2026, 7, 21)

def test_add_business_days_negative():
    assert jp_dates.add_business_days(date(2026, 7, 13), -1) == date(2026, 7, 10)

def test_add_business_days_yearend():
    # 12/29~1/3 제외 옵션: 2026-12-28(월)+1 → 2027-01-04(월)
    assert jp_dates.add_business_days(date(2026, 12, 28), 1, exclude_yearend=True) == date(2027, 1, 4)

def test_wareki_full():
    assert jp_dates.wareki_to_iso("令和6年4月1日") == "2024-04-01"

def test_wareki_abbrev():
    assert jp_dates.wareki_to_iso("R6.4.1") == "2024-04-01"
    assert jp_dates.wareki_to_iso("H31.1.4") == "2019-01-04"

def test_wareki_gannen():
    assert jp_dates.wareki_to_iso("令和元年5月1日") == "2019-05-01"

def test_wareki_not_a_date():
    assert jp_dates.wareki_to_iso("ただのテキスト") is None

def test_iso_to_wareki():
    assert jp_dates.iso_to_wareki("2024-04-01") == "令和6年4月1日"

def test_fiscal_year_boundary():
    assert jp_dates.fiscal_year(date(2026, 3, 31)) == 2025
    assert jp_dates.fiscal_year(date(2026, 4, 1)) == 2026
