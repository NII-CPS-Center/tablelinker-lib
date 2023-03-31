# flake8: noqa
from logging import getLogger
import regex as re

from datetime import datetime, timedelta

logger = getLogger(__name__)


def is_integer(s):
    s = s.strip()
    try:
        int(s)
    except ValueError:
        return False
    else:
        return True


url = r"https?://[\w/:%#\$&\?\(\)~\.=\+\-]+"

excel_date = r"[34]\d{4}(?:\.\d*)?"

era = r"[MTSHR明大昭平令]"
year_special = r"(?:本|今|再?来|一?昨)年度?"
year_4digits = r"(?:1[356789]|2[01])\d{2}"
year_2digits = r"(?:\d{2}| ?\d)"
year_era = era + r"(?: \d|\d{1,2})"
year_era_first = era + r"元"
year_num = r"(?:" + year_4digits + r"|" + year_era + r")"
year_jp = r"(?:" + year_num + r"年度?|" + year_special + r")"
year = r"(?:" + year_num + r"|" + year_jp + r")"

month_special = r"(?:今|再?来|先)月"
month_2digits = r"(?: [1-9]|0[1-9]|1[0-2])"
month_1digit = r"[1-9]"
month_num = r"(?:" + month_2digits + r"|" + month_1digit + r")"
month_jp = r"(?:" + month_num + r"月|" + month_special + r")"
month = r"(?:" + month_num + r"|" + month_jp + r")"

youbi_char = r"[日月火水木金土]"
youbi_one = youbi_char + r"曜日?"
youbi_par = r"(?:\(" + youbi_char + r"\))"
youbi = (
    r"(?:(?:毎週|(?:毎月)?第[1-5一二三四五](?:[,\.・〜]?第?[1-5一二三四五])*週?)?(?:"
    + youbi_char
    + r"・)*"
    + youbi_one
    + r"|"
    + youbi_par
    + r")"
)

day_special = (
    r"(?:(?:初|上|中|下)旬(?:頃|ころ|ごろ)?|(?:本|今|明(?:明?後)?|(?:一咋?)?昨|翌|毎|祝休?|休|末|同)日|年末年始|お盆)"
)
# day_3digits = r" (?:[12][0-9]|3[01])"
day_2digits = r"(?: [1-9]|0[1-9]|[12]\d|3[01])"
day_1digit = r"[1-9]"
day_num = r"(?:" + day_2digits + r"|" + day_1digit + r")"
# day_num = r"(?:" + day_3digits + r"|" + day_2digits + r"|" + day_1digit + r")"
day_jp = r"(?:" + day_num + r"日|" + day_special + r"|" + youbi + r")"
day = r"(?:" + day_num + r"|" + day_jp + r")"

time_special = (
    r"(?P<hour_time_special>正午(?:過ぎ|すぎ)?(?:頃|ころ|ごろ)?|午前中?|昼間帯|午後|夕方(?:頃|ころ|ごろ)?|夜間?|未明)"
)

# hh
hour_2digits = r"(?:[01]\d|2[0-4])"
hour_1digit = r"\d"
hour_num = r"(?:" + hour_2digits + r"|" + hour_1digit + r")"
hour_jp = r"(?:(?:午前|午後)?1?\d|2[0-4])時"

# mm
minute_num = r"(?:[0-5]\d|60)"
minute_jp = r"(?:(?:[0-5]?\d|60)分|半)"

# ss
second_num = r"(?:[0-5]\d|60)"
second_jp = r"(?:[0-5]?\d|60)秒"

# hhmmss
time_num = (
    r"T?(?P<hour_time_num>"
    + hour_num
    + r"):(?P<minute_time_num>"
    + minute_num
    + r")(?::(?P<second_time_num>"
    + second_num
    + r"))?(?:\+\d[2]:\d[2])?"
)

hms_jp = (
    r"(?P<hour_hms_jp>"
    + hour_jp
    + r")((?P<minute_hms_jp>"
    + minute_jp
    + r")(?P<second_hms_jp>"
    + second_jp
    + r")?)?(?:過ぎ|すぎ)?(?:頃|ころ|ごろ)?"
)

time_jp = r"(?:" + hms_jp + r"|" + time_special + r")"

time = r"(?:" + time_num + r"|" + time_jp + r")"

# YYYYMM
ym_6digits = (
    r"(?P<year_ym_6digits>"
    + year_4digits
    + r")(?P<month_ym_6digits>"
    + month_2digits
    + r")"
)
ym_delimiter = (
    r"(?P<year_ym_delimiter>" + year +
    r")[-/\.](?P<month_ym_delimiter>" + month + r")"
)
ym_jp = (
    r"(?P<year_ym_jp>" + year_jp + r"(?:頃|ころ|ごろ)?)(?P<month_ym_jp>" + month_jp + r")"
)
ym = r"(?:" + ym_6digits + r"|" + ym_delimiter + r"|" + ym_jp + r")"

# MMDD
md_delimiter = (
    r"(?P<month_md_delimiter>" + month +
    r")[-/\.](?P<day_md_delimiter>" + day + r")"
)
md_jp = (
    r"(?P<month_md_jp>"
    + month_jp
    + r")(?P<day_md_jp>"
    + day_jp
    + r")"
    + youbi_par
    + r"?"
)
md = r"(?:" + md_delimiter + r"|" + md_jp + \
    r"(?:頃|ころ|ごろ)?(?:[ の]?" + time_jp + r")?)"

# MMDDYYYY
mdy_delimiter = (
    r"(?P<month_mdy_delimiter>"
    + month
    + r")(?P<delimiter_mdy>[-/\.])(?P<day_mdy_delimiter>"
    + day
    + r")(?P=delimiter_mdy)(?P<year_mdy_delimiter>"
    + year
    + r")"
)
mdy_jp = (
    r"(?P<month_mdy_jp>"
    + month_jp
    + r")(?P<day_mdy_jp>"
    + day_jp
    + r")(?P<year_mdy_jp>"
    + year_jp
    + r")"
)
mdy = r"(?:" + mdy_delimiter + r"|" + mdy_jp + r")"

# YYYYMM.DD
ym_d = (
    r"(?P<year_ym_d>"
    + year_era_first
    + r")(?P<month_ym_d>"
    + month_num
    + r")\.(?P<day_ym_d>"
    + day_num
    + r")"
)

# YYYY-MMDD
y_md = (
    r"(?P<year_y_md>"
    + year_num
    + r")-(?P<month_y_md>"
    + month_jp
    + r"|"
    + month_2digits
    + r")(?P<day_y_md>"
    + day_special
    + r")"
)

# YYYYMMDD
ymd_8digits = (
    r"(?P<year_ymd_8digits>"
    + year_4digits
    + r")(?P<month_ymd_8digits>"
    + month_2digits
    + r")(?P<day_ymd_8digits>"
    + day_2digits
    + r")"
)
ymd_delimiter = (
    r"(?P<year_ymd_delimiter>"
    + year
    + r"|"
    + year_2digits
    + r")(?P<delimiter_ymd>[-/\.,])(?P<month_ymd_delimiter>"
    + month
    + r")(?P=delimiter_ymd)(?P<day_ymd_delimiter>"
    + day
    + r")"
)
ymd_jp = (
    r"(?P<year_ymd_jp>"
    + year_jp
    + r")(?P<month_ymd_jp>"
    + month_jp
    + r")(?P<day_ymd_jp>"
    + day_jp
    + r")"
    + youbi_par
    + r"?(?:頃|ころ|ごろ)?"
)
ymd = (
    r"(?:"
    + ymd_8digits
    + r"(?P<hour_2digits>"
    + hour_2digits
    + r")?|"
    + ymd_delimiter
    + r"(?: ?"
    + time_num
    + r")?|"
    + ymd_jp
    + r"(?:[ の]?"
    + time_jp
    + r")?)"
)

date = (
    r"("
    + ymd
    + r"|"
    + y_md
    + r"|"
    + ym_d
    + r"|"
    + mdy
    + r"|"
    + md
    + r"|"
    + ym
    + r"|(?P<day_jp>"
    + day_jp
    + r")"
    + youbi_par
    + r"?(?:"
    + time_jp
    + r")?|(?P<month_jp>"
    + month_jp
    + r")|(?P<year_jp>"
    + year_jp
    + r")|(?P<year_era>"
    + year_era
    + r")|(?P<year_4digits>"
    + year_4digits
    + r")(?![号番])|"
    + time
    + r")"
)

date_span = r"(" + date + r"(?:(?:〜|～|~|から|及び|および|と|、|・)" + date + r")+)"


convert_dic = {
    "０": "0",
    "１": "1",
    "２": "2",
    "３": "3",
    "４": "4",
    "５": "5",
    "６": "6",
    "７": "7",
    "８": "8",
    "９": "9",
    #
    "．": ".",
    "（": "(",
    "）": ")",
    #
    "Ｒ": "R",
    "Ｈ": "H",
    "Ｓ": "S",
    "Ｔ": "T",
    "Ｍ": "M",
    "R.": "R",
    "H.": "H",
    "S.": "S",
    "T.": "T",
    "M.": "M",
    "令和": "R",
    "平成": "H",
    "昭和": "S",
    "大正": "T",
    "明治": "M",
    #
    "元年": "1年",
    "元.": "1.",
    #
    "January": "1",
    "February": "2",
    "March": "3",
    "April": "4",
    "May": "5",
    "June": "6",
    "July": "7",
    "August": "8",
    "September": "9",
    "October": "10",
    "November": "11",
    "December": "12",
    "Jan": "1",
    "Feb": "2",
    "Mar": "3",
    "Apr": "4",
    "May": "5",
    "Jun": "6",
    "Jul": "7",
    "Aug": "8",
    "Sep": "9",
    "Oct": "10",
    "Nov": "11",
    "Dec": "12",
    #
    "-年": "年",
    "-月": "月",
    "-日": "日",
}

year_dic = {
    "令": 2018,
    "平": 1988,
    "昭": 1925,
    "大": 1911,
    "明": 1867,
    #
    "R": 2018,
    "H": 1988,
    "S": 1925,
    "T": 1911,
    "M": 1867,
}


def convert_excel_date(num):
    return datetime(1899, 12, 30) + timedelta(days=num)


# 文字列の正規化
def convert_string(s):
    for k, v in convert_dic.items():
        s = s.replace(k, v)
    return s


# 年表記の正規化
def convert_year(y):
    for k, v in year_dic.items():
        if k in str(y):
            return v + int(
                y.replace(k, "").replace("年度", "").replace(
                    "年", "").replace("元", "1")
            )
    return (
        int(y.replace("年度", "").replace("年", ""))
        if is_integer(y.replace("年度", "").replace("年", ""))
        else str(y)
    )


# 時間表記の正規化
def convert_hour(h):
    if "午後" in h and is_integer(h.replace("午後", "").replace("時", "")):
        return 12 + int(h.replace("午後", "").replace("時", ""))
    elif is_integer(h.replace("午前", "").replace("時", "")):
        return int(h.replace("午前", "").replace("時", ""))
    else:
        return h


# 分表記の正規化
def convert_minute(m):
    if m == "半":
        return 30
    elif is_integer(m.replace("分", "")):
        return int(m.replace("分", ""))
    else:
        return m


def search_group(groups, group_name):
    ret = groups.group(group_name)
    if ret is None:
        return ""
    else:
        return ret


max_date_count = 0
count = 0

re_url = re.compile(url)
re_datespan = re.compile(date_span)
re_date = re.compile(date)


def _get_ymdhms(d):
    year = (
        search_group(d, "year_ymd_8digits")
        + search_group(d, "year_ymd_delimiter")
        + search_group(d, "year_ymd_jp")
        #
        + search_group(d, "year_y_md")
        + search_group(d, "year_ym_d")
        #
        + search_group(d, "year_mdy_delimiter")
        + search_group(d, "year_mdy_jp")
        #
        + search_group(d, "year_ym_6digits")
        + search_group(d, "year_ym_delimiter")
        + search_group(d, "year_ym_jp")
        #
        + search_group(d, "year_jp")
        #
        + search_group(d, "year_era")
        #
        + search_group(d, "year_4digits")
    )
    month = (
        search_group(d, "month_ymd_8digits")
        + search_group(d, "month_ymd_delimiter")
        + search_group(d, "month_ymd_jp")
        #
        + search_group(d, "month_y_md")
        + search_group(d, "month_ym_d")
        #
        + search_group(d, "month_mdy_delimiter")
        + search_group(d, "month_mdy_jp")
        #
        + search_group(d, "month_ym_6digits")
        + search_group(d, "month_ym_delimiter")
        + search_group(d, "month_ym_jp")
        #
        + search_group(d, "month_md_delimiter")
        + search_group(d, "month_md_jp")
        #
        + search_group(d, "month_jp")
    )
    day = (
        search_group(d, "day_ymd_8digits")
        + search_group(d, "day_ymd_delimiter")
        + search_group(d, "day_ymd_jp")
        #
        + search_group(d, "day_y_md")
        + search_group(d, "day_ym_d")
        #
        + search_group(d, "day_mdy_delimiter")
        + search_group(d, "day_mdy_jp")
        #
        + search_group(d, "day_md_delimiter")
        + search_group(d, "day_md_jp")
        #
        + search_group(d, "day_jp")
    )
    hour = (
        search_group(d, "hour_time_num")
        + search_group(d, "hour_hms_jp")
        + search_group(d, "hour_time_special")
        + search_group(d, "hour_2digits")
    )
    minute = search_group(d, "minute_time_num") + search_group(
        d, "minute_hms_jp"
    )
    second = search_group(d, "second_time_num") + search_group(
        d, "second_hms_jp"
    )

    # 正規化
    year = convert_year(year)
    if is_integer(month.replace("月", "")):
        month = int(month.replace("月", ""))

    if is_integer(day.replace("日", "")):
        day = int(day.replace("日", ""))

    hour = convert_hour(hour)
    minute = convert_minute(minute)

    if is_integer(second.replace("秒", "")):
        second = int(second.replace("秒", ""))
    else:
        second = None

    return [year, month, day, hour, minute, second]


def get_datetime(datestr: str):
    """
    文字列を日時または期間として取得します。
    """
    datestr = convert_string(datestr.strip())
    text = re_url.sub("<URL>", datestr).strip()  # URL を除去
    text = re.sub(r"\s+", "", text)  # 空白を除去

    if re.fullmatch(excel_date, text):
        # Excel 形式の日付
        ymdt = convert_excel_date(float(text))
        return {
            "datetime": [[
                int(ymdt.year),
                int(ymdt.month),
                int(ymdt.day),
                int(ymdt.hour),
                int(ymdt.minute),
                int(ymdt.second),
            ]],
            "text": text,
            "format": "EXCEL_DATE",
        }

    # 期間を検索
    m = re_datespan.search(text)
    if m is not None:
        result = {
            "text": m.group(0),
            "format": "SPAN",
        }
        date_list = re_date.finditer(text)
        datetimes = []
        for d in date_list:
            ymdhms = _get_ymdhms(d)
            datetimes.append(ymdhms)

        result["datetime"] = datetimes
        return result

    # 日時を検索
    m = re_date.search(text)
    if m is not None:
        result = {
            "text": m.group(0),
            "format": "DATETIME",
        }
        date_list = re_date.finditer(text)
        datetimes = []
        for d in date_list:
            ymdhms = _get_ymdhms(d)
            datetimes.append(ymdhms)

        result["datetime"] = datetimes
        return result

    result = {
        "datetime": [],
        "text": text,
        "format": "NOT_DATETIME",
    }

    return result


def extract_date(row):
    text_raw = convert_string(row[2].strip())
    text = re.sub(url, "<URL>", text_raw).strip()
    date_span_texts = []

    if not re.fullmatch(excel_date, text) is None:
        ymdt = convert_excel_date(float(text))
        ret = [
            date_span_texts,
            ymdt.microsecond,
            [
                [
                    text,
                    int(ymdt.year),
                    int(ymdt.month),
                    int(ymdt.day),
                    int(ymdt.hour),
                    int(ymdt.minute),
                    int(ymdt.second),
                ],
            ],
            text_raw,
            "EXCEL_DATE",
        ]
        if "." not in text:
            ret[1] = ""
    else:
        date_span_text = re.findall(date_span, text)
        for span in date_span_text:
            date_span_texts.append(span[0])
        date_texts = re.findall(date, text)
        date_list = re.finditer(date, text)
        date_count = sum(1 for _ in date_list)
        if date_count == 0:
            ret = [
                date_span_texts,
                text_raw,
                [["", "", "", "", "", "", ""]],
                text_raw,
                "",
            ]
        else:
            global max_date_count
            if max_date_count < date_count:
                max_date_count = date_count
            date_list = re.finditer(date, text)
            ret = [date_span_texts]
            for date_text in date_texts:
                text_raw = text_raw.replace(date_text[0], "")
            ret.append(text_raw.strip())
            ret.append([])
            text_annotated = text
            matching_pattern = text
            for d in date_list:
                year = (
                    search_group(d, "year_ymd_8digits")
                    + search_group(d, "year_ymd_delimiter")
                    + search_group(d, "year_ymd_jp")
                    #
                    + search_group(d, "year_y_md")
                    + search_group(d, "year_ym_d")
                    #
                    + search_group(d, "year_mdy_delimiter")
                    + search_group(d, "year_mdy_jp")
                    #
                    + search_group(d, "year_ym_6digits")
                    + search_group(d, "year_ym_delimiter")
                    + search_group(d, "year_ym_jp")
                    #
                    + search_group(d, "year_jp")
                    #
                    + search_group(d, "year_era")
                    #
                    + search_group(d, "year_4digits")
                )
                month = (
                    search_group(d, "month_ymd_8digits")
                    + search_group(d, "month_ymd_delimiter")
                    + search_group(d, "month_ymd_jp")
                    #
                    + search_group(d, "month_y_md")
                    + search_group(d, "month_ym_d")
                    #
                    + search_group(d, "month_mdy_delimiter")
                    + search_group(d, "month_mdy_jp")
                    #
                    + search_group(d, "month_ym_6digits")
                    + search_group(d, "month_ym_delimiter")
                    + search_group(d, "month_ym_jp")
                    #
                    + search_group(d, "month_md_delimiter")
                    + search_group(d, "month_md_jp")
                    #
                    + search_group(d, "month_jp")
                )
                day = (
                    search_group(d, "day_ymd_8digits")
                    + search_group(d, "day_ymd_delimiter")
                    + search_group(d, "day_ymd_jp")
                    #
                    + search_group(d, "day_y_md")
                    + search_group(d, "day_ym_d")
                    #
                    + search_group(d, "day_mdy_delimiter")
                    + search_group(d, "day_mdy_jp")
                    #
                    + search_group(d, "day_md_delimiter")
                    + search_group(d, "day_md_jp")
                    #
                    + search_group(d, "day_jp")
                )
                hour = (
                    search_group(d, "hour_time_num")
                    + search_group(d, "hour_hms_jp")
                    + search_group(d, "hour_time_special")
                    + search_group(d, "hour_2digits")
                )
                minute = search_group(d, "minute_time_num") + search_group(
                    d, "minute_hms_jp"
                )
                second = search_group(d, "second_time_num") + search_group(
                    d, "second_hms_jp"
                )
                matching_text = text[d.start(): d.end()]
                annotated_pattern = matching_text
                masked_pattern = matching_text
                if len(year) > 0:
                    annotated_pattern = annotated_pattern.replace(
                        year, "<year></year>", 1
                    )
                    masked_pattern = masked_pattern.replace(year, "YYYY", 1)
                if len(month) > 0:
                    annotated_pattern = annotated_pattern.replace(
                        month, "<month></month>", 1
                    )
                    masked_pattern = masked_pattern.replace(month, "MM", 1)
                if len(day) > 0:
                    annotated_pattern = annotated_pattern.replace(
                        day, "<day></day>", 1)
                    masked_pattern = masked_pattern.replace(day, "DD", 1)
                if len(hour) > 0:
                    annotated_pattern = annotated_pattern.replace(
                        hour, "<hour></hour>", 1
                    )
                    masked_pattern = masked_pattern.replace(hour, "hh", 1)
                if len(minute) > 0:
                    annotated_pattern = annotated_pattern.replace(
                        minute, "<minute></minute>", 1
                    )
                    masked_pattern = masked_pattern.replace(minute, "mm", 1)
                if len(second) > 0:
                    annotated_pattern = annotated_pattern.replace(
                        second, "<second></second>", 1
                    )
                    masked_pattern = masked_pattern.replace(second, "ss", 1)

                annotated_pattern = annotated_pattern.replace(
                    "<year></year>", "<year>" + year + "</year>", 1
                )
                annotated_pattern = annotated_pattern.replace(
                    "<month></month>", "<month>" + month + "</month>", 1
                )
                annotated_pattern = annotated_pattern.replace(
                    "<day></day>", "<day>" + day + "</day>", 1
                )
                annotated_pattern = annotated_pattern.replace(
                    "<hour></hour>", "<hour>" + hour + "</hour>", 1
                )
                annotated_pattern = annotated_pattern.replace(
                    "<minute></minute>", "<minute>" + minute + "</minute>", 1
                )
                annotated_pattern = annotated_pattern.replace(
                    "<second></second>", "<second>" + second + "</second>", 1
                )

                text_annotated = text_annotated.replace(
                    matching_text, annotated_pattern
                )
                matching_pattern = matching_pattern.replace(
                    matching_text, masked_pattern
                )
                while (
                    (
                        "<year><year>" in text_annotated
                        and "</year></year>" in text_annotated
                    )
                    or (
                        "<month><month>" in text_annotated
                        and "</month></month>" in text_annotated
                    )
                    or (
                        "<day><day>" in text_annotated
                        and "</day></day>" in text_annotated
                    )
                    or (
                        "<hour><hour>" in text_annotated
                        and "</hour></hour>" in text_annotated
                    )
                    or (
                        "<minute><minute>" in text_annotated
                        and "</minute></minute>" in text_annotated
                    )
                    or (
                        "<second><second>" in text_annotated
                        and "</second></second>" in text_annotated
                    )
                ):
                    text_annotated = (
                        text_annotated.replace("<year><year>", "<year>")
                        .replace("</year></year>", "</year>")
                        .replace("<month><month>", "<month>")
                        .replace("</month></month>", "</month>")
                        .replace("<day><day>", "<day>")
                        .replace("</day></day>", "</day>")
                        .replace("<hour><hour>", "<hour>")
                        .replace("</hour></hour>", "</hour>")
                        .replace("<minute><minute>", "<minute>")
                        .replace("</minute></minute>", "</minute>")
                        .replace("<second><second>", "<second>")
                        .replace("</second></second>", "</second>")
                    )

                ret[2].append(
                    [
                        matching_text,
                        convert_year(year),
                        int(month.replace("月", ""))
                        if is_integer(month.replace("月", ""))
                        else month,
                        int(day.replace("日", ""))
                        if is_integer(day.replace("日", ""))
                        else day,
                        convert_hour(hour),
                        convert_minute(minute),
                        int(second.replace("秒", ""))
                        if is_integer(second.replace("秒", ""))
                        else second,
                    ]
                )
            ret.append(text_annotated)
            ret.append(matching_pattern)

    # パターン分析用
    pattern = []
    pattern.append(r"\d{4}-\d{1,2}-\d{1,2}(T\d{2}:\d{2}:\d{2}\+\d{2}:\d{2})?")
    pattern.append(r"\d{4}-\d{1,2}-\d{1,2} \d{1,2}:\d{2}:\d{2}")
    pattern.append(r"\d{4}-\d{1,2}-\d{1,2}／（[日月火水木金土]）")
    pattern.append(r"\d{4}\.\d{1,2}\.\d{1,2}(、\d{4}\.\d{1,2}\.\d{1,2})*")
    pattern.append(r"\d{4}/\d{1,2}(/\d{1,2})?")
    pattern.append(r"\d{4}/\d{1,2}/\d{1,2} \d{1,2}:\d{2}")
    pattern.append(r"\d{4}/\d{1,2}/\d{1,2} \d{1,2}:\d{2}:\d{2}")
    #
    pattern.append(r"\d{1,2}[\.．]\d{1,2}([\.．]\d{1,2})?")
    pattern.append(r"\d{1,2}/\d{1,2}")
    #
    pattern.append(r"\d{1,2}月[初上中下]旬")
    pattern.append(
        r"\d{1,2}月\d{1,2}日([\(（][日月火水木金土][\)）])?(〜\d{1,2}月\d{1,2}日([\(（][日月火水木金土][\)）])?)?"
    )
    pattern.append(r"\d{1,2}月\d{1,2}日(頃|ころ|ごろ)")
    pattern.append(
        r"((明治|大正|昭和|平成|令和)\d{1,2}年)?\d{1,2}月\d{1,2}日([\(（][日月火水木金土][\)）])?午[前後](\d{1,2}時半?(頃|ころ|ごろ))?"
    )
    pattern.append(r"\d{1,2}月\d{1,2}日午[前後]\d{1,2}時\d{1,2}分(頃|ころ|ごろ)")
    #
    pattern.append(r"(明治|大正|昭和|平成|令和)\d{1,2}\.\d{1,2}\.\d{1,2}")
    pattern.append(r"(明治|大正|昭和|平成|令和)元\.\d{1,2}\.\d{1,2}")
    pattern.append(r"[明大昭平令]\d{1,2}\.\d{1,2}\.\d{1,2}")
    pattern.append(r"[MTSHR]\.\d{1,2}/\d{1,2}/\d{1,2}")
    pattern.append(r"[MTSHR]\d{1,2},\d{1,2},\d{1,2}")
    pattern.append(r"\d{1,2}\.\d{1,2}\.[MTSHR]\d{1,2}")
    pattern.append(
        r"[MTSHRＭＴＳＨＲ]\.?( \d|\d{1,2})\.( \d|\d{1,2})\.( \d|\d{1,2})")
    # pattern.append(r"[MTSHR]元\d{1,2}\.\d{1,2}")
    pattern.append(r"\d{1,2}月\d{1,2}日(明治|大正|昭和|平成|令和)\d{1,2}年")
    pattern.append(r"(明治|大正|昭和|平成|令和)元年( \d|\d{1,2})月( \d|\d{1,2})日")
    pattern.append(
        r"(明治|大正|昭和|平成|令和)( \d|\d{1,2})年( \d|\d{1,2})月( \d|\d{1,2})日")
    pattern.append(r"(明治|大正|昭和|平成|令和)\d{1,2}年\d{1,2}月[初上中下]旬(?:頃|ころ|ごろ)")
    #
    pattern.append(r"(明治|大正|昭和|平成|令和)\d{1,2}年\d{1,2}月")
    pattern.append(r"[MTSHRＭＴＳＨＲ]\d{1,2}[\.．]\d{1,2}([\.．]\d{1,2})?")
    pattern.append(r"[MTSHR]\d{1,2}年\d{1,2}月")
    #
    pattern.append(r"[MTSHR]\d{1,2}")
    #
    pattern.append(r"\d{4}年\d{1,2}月\d{1,2}日(から\d{4}年\d{1,2}月\d{1,2}日)?")
    pattern.append(r"\d{4}年\d{1,2}月\d{1,2}日\d{1,2}時")
    #
    pattern.append(r"\d{4}-\d{2}")
    #
    pattern.append(r"\d{4}-\d{2}-?[初上中下]旬")
    pattern.append(r"\d{4}-\d{2}月[初上中下]旬")
    #
    pattern.append(r"\d{1,2}月\d{1,2}日\d{4}年")
    pattern.append(r"\d{1,2}月計?")
    pattern.append(r"\d{1,2}日")
    pattern.append(r"\d{1,2}/\d{1,2}/\d{4}")
    pattern.append(r"\d{10}")
    pattern.append(r"\d{8}")
    pattern.append(r"\d{6}")
    pattern.append(r"\d{4}")
    pattern.append(r"4\d{4}")
    pattern.append(r"4\d{4}\.\d{2,5}")
    pattern.append(r"[日月火水木金土]曜日(（月\d回）)?")
    pattern.append(r"毎週[日月火水木金土](・[日月火水木金土])*曜日")
    pattern.append(r"毎週[日月火水木金土]曜")
    pattern.append(r"第\d(・\d)*[日月火水木金土]曜")
    pattern.append(r"毎月第\d[日月火水木金土]曜日")
    pattern.append(r"(\d{1,2}月)?第\d([,・]\d)*週?[日月火水木金土]曜日")
    pattern.append(r"第\d〜\d[日月火水木金土]曜日")
    pattern.append(r"[本昨]日")
    pattern.append(r"今月")

    pattern.append(r"\d{2}:\d{2}:\d{2}")

    pattern.append(r"(不明|[-−ー〃]|\d{1,2}|年計|月計|比率|合計|未定|適用なし|[日月火水木金土])")
    pattern.append(url)

    for p in pattern:
        if re.fullmatch(p, row[2].strip()):
            return ret

    global count
    count += 1

    # [date_span_text(list), other, dates(list), annotated_text, matching_pattern]
    return ret
