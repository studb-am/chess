import sys

from utils.gsheet import extract_info_from_sheet_id


GOOGLE_SHEET_NAME = sys.argv[1]

extract_info_from_sheet_id(sheet_id=GOOGLE_SHEET_NAME)