import json

INPUT_FILE = 'chat_stats.json'
OUTPUT_FILE = 'rewind_report.txt'

def format_number(num):
    return "{:,}".format(num).replace(',', ' ')

def main():
    try:
        with open(INPUT_FILE, encoding='utf-8') as f:
            data = json.load(f)
    except FileNotFoundError:
        print(f"❌ Файл {INPUT_FILE} не найден. Сначала запустите analyze_chat.py")
        return

    lines = []
    
    meta = data.get('meta', {})
    totals = data.get('totals', {})
    users = data.get('users', {})
    activity = data.get('activity', {})

    year = meta.get('year', '202X')
    
    # --- HEADER ---
    lines.append(f"⏪ TELEGRAM CHAT REWIND {year}")
    lines.append(f"📁 Чат: {meta.get('chat_name', 'Unknown')}")
    lines.append(f"📅 Период: {meta.get('period_start')} — {meta.get('period_end')}")
    lines.append("=" * 30)
    lines.append("")

    # --- GLOBAL STATS ---
    lines.append("📊 ОБЩАЯ СТАТИСТИКА")
    lines.append(f"• Сообщений:   {format_number(totals.get('messages', 0))}")
    lines.append(f"• Участников:  {format_number(totals.get('participants', 0))}")
    lines.append(f"• Стикеров:    {format_number(totals.get('stickers', 0))}")
    lines.append(f"• Изображений: {format_number(totals.get('images', 0))}")
    lines.append(f"• Ссылок:      {format_number(totals.get('links', 0))}")
    lines.append("-" * 30)
    lines.append("")

    # --- USER LEADERBOARD ---
    def add_section(title, data_dict, limit=5, suffix="", icon="👤"):
        if not data_dict: return
        
        lines.append(title)
        sorted_items = sorted(data_dict.items(), key=lambda item: item[1], reverse=True)[:limit]
        
        for i, (user, count) in enumerate(sorted_items):
            user_clean = user[:20] + "..." if len(user) > 20 else user
            lines.append(f"{i+1}. {user_clean}: {format_number(count)} {suffix}")
        lines.append("")

    add_section("🏆 ТОП УЧАСТНИКОВ (MESSAGES)", users.get('message_count'), limit=10)
    add_section("🎭 ЛЮБИТЕЛИ СТИКЕРОВ", users.get('sticker_count'), limit=5, suffix="stickers")
    add_section("🖼 МЕДИА-КОНТЕНТ (IMAGES)", users.get('image_count'), limit=3, suffix="imgs")
    add_section("🔗 LOREMASTERS (LINKS)", users.get('link_count'), limit=3, suffix="links")

    lines.append("-" * 30)
    lines.append("")

    # --- VOCABULARY ---
    top_words = data.get('top_words', [])
    if top_words:
        lines.append("💭 VOCABULARY (ТОП СЛОВ)")
        # Вывод: слово (120)
        formatted = [f"{w[0]} ({w[1]})" for w in top_words]
        lines.append(", ".join(formatted))
        lines.append("")

    # --- PEAK ACTIVITY ---
    top_days = activity.get('top_days', {})
    if top_days:
        lines.append("📆 ПИКОВАЯ АКТИВНОСТЬ")
        sorted_days = sorted(top_days.items(), key=lambda item: item[1], reverse=True)
        for date_str, count in sorted_days:
            lines.append(f"• {date_str}: {count} msgs")
        lines.append("")

    # --- FOOTER ---
    lines.append("=" * 30)
    lines.append("#TelegramRewind #Stats")

    # Сохранение
    with open(OUTPUT_FILE, 'w', encoding='utf-8') as f:
        f.write("\n".join(lines))
    
    print(f"✅ Отчет Rewind готов: {OUTPUT_FILE}")

if __name__ == "__main__":
    main()