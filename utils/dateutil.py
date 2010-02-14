
def date_to_week(d):
  iso_year, iso_week, iso_weekday = d.isocalendar()
  return iso_year * 100 + iso_week
  
def week_to_start_date(w):
  return iso_year_week_day_to_date(int(w / 100), w % 100, 1)
  
def week_to_end_date(w):
  return iso_year_week_day_to_date(int(w / 100), w % 100, 7)
  
def next_week(w, offset=1):
  from datetime import timedelta
  return date_to_week(week_to_start_date(w) + timedelta(days=7*offset))
  
def previous_week(w, offset=1):
  return next_week(w, -offset)
  
def iso_year_week_day_to_date(y, w, d):
  from datetime import date, timedelta
  
  jan4 = date(y, 1, 4)
  jan4_monday_offset = jan4.weekday()
  # bug fix -- dunno why this is wrong (or why I thought this was right)
  # if jan4_monday_offset == 0: jan4_monday_offset = 7
  
  result = jan4 + timedelta(days=(-jan4_monday_offset + 7*(w-1) + (d-1)))
  assert result.isocalendar() == (y, w, d)
  return result
