def get_level(balance):
    """بر اساس موجودی، سطح و نشان رو برمی‌گردونه"""
    if balance < 100:
        return "🥉", "تازه‌کار", 1
    elif balance < 500:
        return "🥈", "حرفه‌ای", 2
    elif balance < 1000:
        return "🥇", "استاد", 3
    elif balance < 5000:
        return "💎", "افسانه", 4
    else:
        return "👑", "پادشاه", 5


def get_next_level_info(balance):
    """اطلاعات سطح بعدی"""
    if balance < 100:
        return 100 - balance, "🥈 حرفه‌ای"
    elif balance < 500:
        return 500 - balance, "🥇 استاد"
    elif balance < 1000:
        return 1000 - balance, "💎 افسانه"
    elif balance < 5000:
        return 5000 - balance, "👑 پادشاه"
    else:
        return 0, "حداکثر سطح"