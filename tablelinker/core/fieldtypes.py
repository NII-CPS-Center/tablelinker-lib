import enum


class AttrType(enum.Enum):
    unknown = "不明"
    blank = "データなし"

    person = "人"
    contact = "連絡先"
    organization = "組織"
    location = "場所"
    model_number = "型番"
    facility_name = "施設名"
    weight = "重量"
    price = "価格"
    date = "日付"
    tel = "電話番号"
    count_of_people = "人数"
    coordinate = "座標"
    event = "イベント"
    quantity = "数量"
    length = "長さ"
    term = "期間"
    address = "住所"
    area = "面積"
    datetime = "日時"

    @classmethod
    def choices(cls):
        return tuple((attr.name, attr.value) for attr in cls)


class DataType(enum.Enum):
    unknown = "不明"
    string = "文字列"
    integer = "数値"
    float = "実数"
    datetime = "日付"
    boolean = "ブール値"
    uri = "URI"

    @classmethod
    def choices(cls):
        return tuple((attr.name, attr.value) for attr in cls)
