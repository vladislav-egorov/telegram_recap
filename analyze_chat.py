import datetime
import json
import re
from collections import Counter

import pandas as pd

# --- НАСТРОЙКИ ---
INPUT_FILE = 'result.json'
OUTPUT_FILE = 'chat_stats.json'

STOP_WORDS = {
    'и', 'в', 'во', 'не', 'что', 'он', 'на', 'я', 'с', 'со', 'как', 'а', 'то', 'все', 'она', 'так',
    'его', 'но', 'да', 'ты', 'к', 'у', 'же', 'вы', 'за', 'бы', 'по', 'только', 'ее', 'мне', 'было',
    'вот', 'от', 'меня', 'еще', 'нет', 'о', 'из', 'ему', 'теперь', 'когда', 'даже', 'ну', 'вдруг',
    'ли', 'если', 'уже', 'или', 'ни', 'быть', 'был', 'него', 'до', 'вас', 'нибудь', 'опять', 'уж',
    'вам', 'ведь', 'там', 'потом', 'себя', 'ничего', 'ей', 'может', 'они', 'тут', 'где', 'есть',
    'надо', 'ней', 'для', 'мы', 'тебя', 'их', 'чем', 'была', 'сам', 'чтоб', 'без', 'будто', 'чего',
    'раз', 'тоже', 'себе', 'под', 'будет', 'ж', 'тогда', 'кто', 'этот', 'того', 'потому', 'этого',
    'какой', 'совсем', 'ним', 'здесь', 'этом', 'один', 'почти', 'мой', 'тем', 'чтобы', 'нее', 'сейчас',
    'были', 'куда', 'зачем', 'всех', 'никогда', 'можно', 'при', 'наконец', 'два', 'об', 'другой',
    'хоть', 'после', 'над', 'больше', 'тот', 'через', 'эти', 'нас', 'про', 'всего', 'них', 'какая',
    'много', 'разве', 'три', 'эту', 'моя', 'впрочем', 'хорошо', 'свою', 'этой', 'перед', 'иногда',
    'лучше', 'чуть', 'том', 'нельзя', 'такой', 'им', 'более', 'всегда', 'конечно', 'всю', 'между',
    'это', 'как-то', 'что-то', 'кто-то', 'всё',
    'the', 'a', 'an', 'in', 'on', 'at', 'to', 'for', 'of', 'and', 'is', 'are', 'was', 'were',
    'it', 'that', 'this', 'i', 'you', 'he', 'she', 'we', 'they', 'me', 'my', 'be', 'so', 'not',
    'щас', 'ща', 'крч', 'типа', 'просто', 'короче', 'ваще', 'вообще', 'кстати', 'норм',
    'спс', 'пож', 'плиз', 'прив', 'мб', 'хз', 'лол', 'кек', 'блин', 'ок', 'окей', 'давай',
    'думаю', 'знаю', 'почему', 'сегодня', 'вчера', 'завтра', 'сразу', 'очень'
}


def extract_text(text_obj):
    if isinstance(text_obj, str):
        return text_obj
    elif isinstance(text_obj, list):
        text = ""
        for item in text_obj:
            if isinstance(item, str):
                text += item
            elif isinstance(item, dict) and item.get('type') != 'mention':
                text += item.get('text', '')
        return text
    return ""


def count_links(text):
    if not text: return 0
    return len(re.findall(r'https?://[^\s]+', text))


def main():
    print(f"Загружаю {INPUT_FILE}...")
    try:
        with open(INPUT_FILE, encoding='utf-8') as f:
            data = json.load(f)
    except FileNotFoundError:
        print("Ошибка: Файл result.json не найден.")
        return

    messages = data.get('messages', [])
    chat_name = data.get('name', 'Unknown Chat')
    msgs = [m for m in messages if m['type'] == 'message']

    if not msgs:
        print("В файле нет сообщений.")
        return

    df = pd.DataFrame(msgs)

    # Очистка
    df['clean_text'] = df['text'].apply(extract_text)
    df['from'] = df['from'].fillna('Deleted Account') if 'from' in df.columns else 'Unknown'

    # Даты (ДЛЯ ПЕРИОДА)
    df['date_dt'] = pd.to_datetime(df['date'])
    df['day_str'] = df['date_dt'].dt.strftime('%d.%m.%Y')  # Формат ДД.ММ.ГГГГ

    # Находим первую и последнюю дату
    first_date = df['date_dt'].min().strftime('%d.%m.%Y')
    last_date = df['date_dt'].max().strftime('%d.%m.%Y')
    year_of_recap = df['date_dt'].max().year  # Год для заголовка

    # Медиа
    is_sticker_mask = pd.Series([False] * len(df), index=df.index)
    is_photo_mask = pd.Series([False] * len(df), index=df.index)
    if 'sticker' in df.columns: is_sticker_mask |= df['sticker'].notna()
    if 'media_type' in df.columns: is_sticker_mask |= (df['media_type'] == 'sticker')
    if 'photo' in df.columns: is_photo_mask |= df['photo'].notna()
    df['is_sticker'] = is_sticker_mask.astype(int)
    df['is_photo'] = is_photo_mask.astype(int)
    df['link_count'] = df['clean_text'].apply(count_links)

    # Сбор статистики
    def get_user_stats(column, method='sum'):
        if method == 'sum':
            res = df.groupby('from')[column].sum()
        else:
            res = df['from'].value_counts()
        return res[res > 0].sort_values(ascending=False).to_dict()

    # Топ слов
    all_text = " ".join(df['clean_text'].tolist()).lower()
    all_text = re.sub(r'[^\w\s-]', '', all_text)
    words = [w for w in all_text.split() if w not in STOP_WORDS and len(w) > 3 and not w.isdigit()]
    top_words = Counter(words).most_common(10)

    stats = {
        "meta": {
            "chat_name": chat_name,
            "year": year_of_recap,  # Год рекапа
            "period_start": first_date,  # Дата начала
            "period_end": last_date,  # Дата конца
            "generated_at": datetime.datetime.now().isoformat()
        },
        "totals": {
            "messages": len(df),
            "participants": df['from'].nunique(),
            "stickers": int(df['is_sticker'].sum()),
            "images": int(df['is_photo'].sum()),
            "links": int(df['link_count'].sum())
        },
        "top_words": top_words,
        "activity": {"top_days": df['day_str'].value_counts().head(5).to_dict()},
        "users": {
            "message_count": get_user_stats('id', method='count'),
            "sticker_count": get_user_stats('is_sticker'),
            "image_count": get_user_stats('is_photo'),
            "link_count": get_user_stats('link_count')
        }
    }

    with open(OUTPUT_FILE, 'w', encoding='utf-8') as f:
        json.dump(stats, f, ensure_ascii=False, indent=4)

    print(f"Готово! Статистика сохранена (с {first_date} по {last_date}).")


if __name__ == "__main__":
    main()
