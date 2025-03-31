import json
import os
import threading
import telebot
import random
import datetime
import pytz
from config import ALLOWED_USERS, BACKGROUND_IMAGE, CHAT_ID, COLOR_NAME, COLOR_TEXT, DATA_FILE, FONT_NAME, FONT_SIZE_NAME, FONT_SIZE_TEXT, FONT_TEXT, MEDIA_FOLDER, RIGHT_NOW_FILE, TOKEN
from data import members, metro_lines, metro_stations, TIME_VARIANTS, THOUGHTFUL_PHRASES, savee_data
import telebot
from telebot.types import ChatPermissions
from PIL import Image, ImageDraw, ImageFont
from io import BytesIO
import re
import time

bot = telebot.TeleBot(TOKEN)

bot.set_my_commands([
    telebot.types.BotCommand("start", "Привет, спишь?"),
    telebot.types.BotCommand("info", "Информация о человеке"),
    telebot.types.BotCommand("ship", "Случайно объединяет двух людей в пару"),
    telebot.types.BotCommand("okdnya", "Определяет ОКа дня"),
    telebot.types.BotCommand("quote", "Увековечить цитату"),
    telebot.types.BotCommand("think", "Цитата к размышлению"),
    telebot.types.BotCommand("when", "Заглянуть в будущее"),
    telebot.types.BotCommand("daddy", "Отец бота"),
    telebot.types.BotCommand("compat", "Рассчёт совместимости двух ОКов"),
    telebot.types.BotCommand("who", "Определяет, кто из нас..."),
    telebot.types.BotCommand("prob", "Определяет вероятность события"),
    telebot.types.BotCommand("top", "Выводит лучших в указанной сфере"),
    telebot.types.BotCommand("ranking", "Рейтинг ОК - неОК"),
    telebot.types.BotCommand("ok", "ОКнуть человека (ответом на его сообщение)"),
    telebot.types.BotCommand("neok", "неОКнуть человека (ответом на его сообщение)"),
    telebot.types.BotCommand("help", "Показать список команд"),
])


@bot.message_handler(commands=["start"])
def start(message):
    bot.reply_to(message, "Привет! Я бот для флуда ОКов 2025! Введи /help, чтобы узнать, что я умею.")
  
    
@bot.message_handler(commands=['metro'])
def find_members_by_metro(message):
    line_query = message.text.split(maxsplit=1)
    if len(line_query) < 2:
        bot.reply_to(message, "Пожалуйста, укажите номер, цвет или название линии метро.")
        return
    
    line_input = line_query[1].strip().lower()
    line_number = None
    
    for num, names in metro_lines.items():
        if line_input in [num] + [name.lower() for name in names]:
            line_number = num
            break
    
    if not line_number:
        bot.reply_to(message, "Не удалось найти указанную линию метро.")
        return
    
    stations_on_line = metro_stations.get(line_number, [])
    found_members = [f"{m['first_name']} {m['last_name']} ({m['metro']})" for m in members if m['metro'] in stations_on_line]
    
    if found_members:
        bot.reply_to(message, f"Обучающие Координаторы, живущие на {line_number} линии метро:\n" + "\n".join(found_members))
    else:
        bot.reply_to(message, "На этой линии метро нет ни одного ОКа. Не повезло ей!")


def send_member_info(message, member):
    """Функция отправки информации о человеке."""
    info = (
        f"👤 {member['formal_last_name']} {member['formal_first_name']} {member['mrespectdle_name']}\n"
        f"📅 Дата рождения: {member['birth_date']}\n"
        f"🏫 Факультет: {member['faculty']}\n"
        f"🎓 Группа: {member['group']}\n"
        f"📞 Телефон: {member['phone']}\n"
        f"📧 Почта: {member['email']}\n"
        f"💬 Telegram: {member['telegram']}\n"
        f"🚇 Станция метро: {member['metro']}\n"
        f"Интересный факт про Лилю (она очень просила добавить): в 8 лет чуть не утонула в лягушатнике (детском бассейне в школе)"
    )
    bot.reply_to(message, info)

@bot.message_handler(commands=["дуэль"])
def duel(message):
    if not message.reply_to_message:
        bot.reply_to(message, "Команду нужно использовать ответом на сообщение.")
        return

    challenger = message.from_user  # Автор команды
    opponent = message.reply_to_message.from_user  # Тот, на кого ответили

    if challenger.id == opponent.id:
        bot.reply_to(message, "Ты не можешь вызвать дуэль сам с собой!")
        return

    # Определяем Telegram usernames участников
    challenger_telegram = f"@{challenger.username}" if challenger.username else None
    opponent_telegram = f"@{opponent.username}" if opponent.username else None

    # Получаем их first name из списка members
    challenger_name = next((m["first_name"] for m in members if m["telegram"] == challenger_telegram), challenger.first_name)
    opponent_name = next((m["first_name"] for m in members if m["telegram"] == opponent_telegram), opponent.first_name)

    # Выбираем случайного победителя
    winner, loser = random.sample([(challenger, challenger_name), (opponent, opponent_name)], 2)
    loser_telegram = f"@{loser[0].username}" if loser[0].username else None

    if loser_telegram in ALLOWED_USERS:
        bot.reply_to(
            message,
            f"💥 Дуэль состоялась! Победитель — {winner[1]}!\n"
            f"🎭 {loser[1]} проиграл, но ему прощается эта дуэль!"
        )
        return

    # Определяем длительность мута
    mute_duration = random.randint(60, 1200)  # 1 минута или 10 минут

    # Отправляем сообщение о победителе
    bot.reply_to(
        message,
        f"💥 Дуэль состоялась! Победитель — {winner[1]}!\n"
        f"😵 {loser[1]} проиграл и получает мут на {mute_duration // 60} минут!"
    )

    # Блокируем проигравшего
    try:
        bot.restrict_chat_member(
            message.chat.id,
            loser[0].id,
            until_date=int(time.time()) + mute_duration,
            can_send_messages=False,
            can_send_media_messages=False,
            can_send_other_messages=False,
            can_add_web_page_previews=False
        )
    except Exception as e:
        bot.reply_to(message, f"Ошибка при блокировке: {e}")

@bot.message_handler(commands=["мут"])
def mute_command(message):
    if message.from_user.username and f"@{message.from_user.username}" not in ALLOWED_USERS:
        bot.reply_to(message, "🚫 У вас нет прав на использование этой команды!")
        return

    if not message.reply_to_message:
        bot.reply_to(message, "⚠ Нужно ответить на сообщение пользователя, которого хотите замьютить!")
        return

    user_id = message.reply_to_message.from_user.id
    username = f"@{message.reply_to_message.from_user.username}" if message.reply_to_message.from_user.username else None

    # Спецпроверка для @samolil
    if username in ALLOWED_USERS:
        bot.reply_to(message, f"🎭 {username} не подвержен муту!")
        return

    # Если мутящий находится в списке ALLOWED_USERS, то мут на 1 минуту, иначе на 10 минут
    mute_time = 600  # 1 минута или 10 минут
    until_timestamp = int(time.time()) + mute_time

    try:
        bot.restrict_chat_member(
            chat_id=message.chat.id,
            user_id=user_id,
            permissions=telebot.types.ChatPermissions(can_send_messages=False),
            until_date=until_timestamp
        )
        bot.reply_to(message, f"🔇 {message.reply_to_message.from_user.first_name} замьючен на {mute_time // 60} минут!")
    except Exception as e:
        bot.reply_to(message, f"⚠ Ошибка при муте: {e}")


@bot.message_handler(commands=["анмут"])
def unmute_command(message):
    if message.from_user.username and f"@{message.from_user.username}" not in ALLOWED_USERS:
        bot.reply_to(message, "🚫 У вас нет прав на использование этой команды!")
        return

    if not message.reply_to_message:
        bot.reply_to(message, "⚠ Нужно ответить на сообщение пользователя, которого хотите размьютить!")
        return

    user_id = message.reply_to_message.from_user.id

    try:
        bot.restrict_chat_member(
            chat_id=message.chat.id,
            user_id=user_id,
            permissions=telebot.types.ChatPermissions(
                can_send_messages=True,
                can_send_media_messages=True,
                can_send_polls=True,
                can_send_other_messages=True,
                can_add_web_page_previews=True,
                can_change_info=True,
                can_invite_users=True,
                can_pin_messages=True
            )
        )
        bot.reply_to(message, f"🔊 {message.reply_to_message.from_user.first_name} теперь может говорить!")
    except Exception as e:
        bot.reply_to(message, f"⚠ Ошибка при размьюте: {e}")

@bot.message_handler(func=lambda message: re.search(r'\bспокойной\b.*\bночи\b.*\bоки\b', message.text, re.IGNORECASE))
def good_morning_kvs(message):
    user_telegram = f"@{message.from_user.username}" if message.from_user.username else None
    member = next((m for m in members if m["telegram"] == user_telegram), None)

    first_name = member["first_name"] if member else "неизвестный ОК"

    bot.reply_to(message, f"Спокойной ночи, {first_name} 💜\nЗавтра ты будешь снова светить!")


@bot.message_handler(commands=["хуй"])
def dick_size(message):
    sender_username = f"@{message.from_user.username}" if message.from_user.username else None
    member = next((m for m in members if m["telegram"] == sender_username), None)

    name = member["first_name"] if member else message.from_user.first_name
    size = int(1000 * (random.random() ** 3))-1
    bot.reply_to(message, f"{name}, твой хуй {size} см 🍆")


@bot.message_handler(commands=["инфа", "info"])
def get_member_info(message):
    args = message.text.split(maxsplit=2)

    if len(args) == 1 and message.reply_to_message:  # Если команда отправлена в ответ на сообщение и без аргументов
        reply_user = message.reply_to_message.from_user.username
        if reply_user:
            member = next((m for m in members if m['telegram'].strip('@') == reply_user), None)
            if member:
                send_member_info(message, member)
                return

    if len(args) < 2:
        bot.reply_to(message, "Использование: /инфа Фамилия [Имя (необязательно)] или отправь команду в ответ на сообщение без дополнительных слов.")
        return

    last_name = args[1].strip().lower()
    first_name = args[2].strip().lower() if len(args) > 2 else None

    found_members = [
        m for m in members if (m["last_name"].lower() == last_name or m["formal_last_name"].lower() == last_name)
        and (first_name is None or m["first_name"].lower() == first_name or m["formal_first_name"].lower() == first_name)
    ]

    if not found_members:
        bot.reply_to(message, "ОК не найден.")
        return

    if len(found_members) > 1 and first_name is None:
        # Формируем список доступных команд
        commands_list = "\n".join(f"`/инфа {m['last_name']} {m['first_name']}`" for m in found_members)
        bot.reply_to(message, f"Найдено несколько ОКов с фамилией {last_name.capitalize()}.\n"
                              f"Выбери одного из них, введя одну из команд:\n{commands_list}", parse_mode="Markdown")
        return

    # Если найден ровно один квасёныш
    send_member_info(message, found_members[0])

        

# Храним время последнего вызова команды каждым пользователем
last_all_request = {}

moscow_tz = pytz.timezone("Europe/Moscow")


@bot.message_handler(commands=["all", "все"])
def mention_everyone(message):
    user_telegram = f"@{message.from_user.username}" if message.from_user.username else None

    # Проверяем, есть ли пользователь в списке разрешённых
    if user_telegram not in ALLOWED_USERS:
        bot.reply_to(message, "Только для оргкома!")
        return

    now = time.time()  # Текущее время в секундах
    last_request = last_all_request.get(user_telegram, 0)

    # Если прошло меньше 20 секунд с последнего вызова
    if now - last_request < 20:
        mentions = " ".join(m["telegram"] for m in members if m["telegram"])
        # mentions = "@melankolya"
        bot.send_message(message.chat.id, mentions)
    else:
        # Обновляем время вызова команды
        last_all_request[user_telegram] = now

        current_time = datetime.datetime.now(moscow_tz).strftime("%H:%M")
        bot.reply_to(
            message,
            f"Ты уверен(-а), что хочешь отметить всех участников чата? Сейчас {current_time}\n"
            f"Для подтверждения отправь команду ещё раз: `/all`",
        parse_mode="Markdown")


def send_wakeup_message(chat_id, member):
    """Функция отправки сообщений пользователю."""
    wakeup_text = f"{member['telegram']} {member['telegram']} {member['telegram']}\n\n" \
                  f"Проснись! Вот номер телефона: {member['phone']}. Позвоните ему уже!"
    bot.send_message(chat_id, wakeup_text)
    

@bot.message_handler(commands=["разделить"])
def divide_into_teams(message):
    args = message.text.split()
    
    if len(args) < 2 or not args[1].isdigit():
        bot.reply_to(message, "Нужно указать количество команд. Например: /разделить 3")
        return
    
    num_teams = int(args[1])
    if num_teams < 1:
        bot.reply_to(message, "Количество команд должно быть больше нуля.")
        return
    
    # Фильтруем только тех, кто не "Оргком"
    ok_members = [m for m in members if m.get("role") != "Оргком"]
    
    if num_teams > len(ok_members):
        bot.reply_to(message, f"Слишком много команд! У нас всего {len(ok_members)} ОКов.")
        return

    # Перемешиваем список, чтобы команды были случайными
    random.shuffle(ok_members)
    
    # Разделение на примерно равные группы
    teams = [[] for _ in range(num_teams)]
    for i, member in enumerate(ok_members):
        teams[i % num_teams].append(member)

    # Формируем сообщение с командами
    response = "Разделение на команды:\n\n"
    for i, team in enumerate(teams, 1):
        response += f"Команда {i}:\n"
        for member in team:
            response += f" - {member['first_name']} {member['last_name']}\n"
        response += "\n"

    bot.reply_to(message, response)
    

@bot.message_handler(commands=["разбудить"])
def set_wakeup_call(message):
    """Обработчик команды /разбудить."""
    command_parts = message.text.split()
    if len(command_parts) != 2:
        bot.reply_to(message, "❌ Введите время в формате ЧЧ:ММ, например: /разбудить 08:30")
        return

    match = re.fullmatch(r"([01]\d|2[0-3]):([0-5]\d)", command_parts[1])
    if not match:
        bot.reply_to(message, "❌ Некорректное время! Введите в формате ЧЧ:ММ (например, 07:45).")
        return

    hours, minutes = map(int, match.groups())

    # Найти пользователя в members
    sender_username = f"@{message.from_user.username}" if message.from_user.username else None
    member = next((m for m in members if m["telegram"] == sender_username), None)

    if not member:
        bot.reply_to(message, "❌ Вас нет в базе, не могу вас разбудить.")
        return

    now = datetime.datetime.now(moscow_tz)
    wakeup_time = now.replace(hour=hours, minute=minutes, second=0, microsecond=0)

    # Если время уже прошло сегодня — ставим будильник на следующий день
    if wakeup_time <= now:
        wakeup_time += datetime.timedelta(days=1)

    time_diff = (wakeup_time - now).total_seconds()

    bot.reply_to(message, f"✅ Будильник установлен на {wakeup_time.strftime('%H:%M')}. Беги высыпаться, 2 часа сна - неОК!")

    # Отложенный запуск
    threading.Thread(target=lambda: (time.sleep(time_diff), send_wakeup_message(message.chat.id, member))).start()


@bot.message_handler(commands=['шипперить', "ship"])
def ship_people(message):
    phrases = ['отлично смотрятся вместе', 'с удовольствием поработают на одном факультете', 'подходят друг другу']
    
    if message.reply_to_message:  # Проверяем, есть ли ответ на сообщение
        reply_user = message.reply_to_message.from_user.username
        if reply_user:
            person1 = next((m for m in members if m['telegram'].strip('@') == reply_user), None)
            if person1:
                person2 = random.choice([m for m in members if m != person1])  # Выбираем случайного второго
                ship_message = f"{person1['first_name']} {person1['last_name']} и {person2['first_name']} {person2['last_name']} {random.choice(phrases)}"
                bot.reply_to(message, ship_message)
                return
    
    # Если нет ответа на сообщение или не найден юзер — шипперим случайных людей
    person1, person2 = random.sample(members, 2)
    ship_message = f"{person1['first_name']} {person1['last_name']} и {person2['first_name']} {person2['last_name']} {random.choice(phrases)}"
    bot.reply_to(message, ship_message)
    

@bot.message_handler(commands=["совместимость", "compat"])
def compatibility(message):
    if message.reply_to_message:  # Проверяем, есть ли ответ на сообщение
        reply_user = message.reply_to_message.from_user.username
        if reply_user:
            person1 = next((m for m in members if m['telegram'].strip('@') == reply_user), None)
            if person1:
                person2 = random.choice([m for m in members if m != person1])  # Выбираем случайного второго
                compatibility_score = random.randint(-100, 100)
                result_message = (
                    f"🔮 Совместимость {person1['first_name']} {person1['last_name']} и "
                    f"{person2['first_name']} {person2['last_name']}: {compatibility_score}!"
                )
                bot.reply_to(message, result_message)
                return

    # Если нет ответа на сообщение или не найден юзер — выбираем двух случайных людей
    person1, person2 = random.sample(members, 2)
    compatibility_score = random.randint(-100, 100)
    result_message = (
        f"🔮 Совместимость {person1['first_name']} {person1['last_name']} и "
        f"{person2['first_name']} {person2['last_name']}: {compatibility_score}!"
    )

    bot.reply_to(message, result_message)


@bot.message_handler(commands=['кто', "who"])
def who(message):
    person = random.sample(members, 1)[0]
    ret_message = f"{person['first_name']} {person['last_name']} {' '.join(message.text.split(' ')[1:]) if len(message.text.split(' ')) > 1 else ''}"
    bot.reply_to(message, ret_message)
    

moscow_tz = pytz.timezone("Europe/Moscow")

# Функция для загрузки данных
def load_data():
    if os.path.exists(DATA_FILE):
        with open(DATA_FILE, "r", encoding="utf-8") as f:
            return json.load(f)
    return {"last_pidor": None, "last_date_p": None, "last_xozyain": None, "last_date_x": None}

# Функция для сохранения данных
def save_data(data):
    with open(DATA_FILE, "w", encoding="utf-8") as f:
        json.dump(data, f, ensure_ascii=False, indent=4)

# Загружаем сохраненные данные
data = load_data()

@bot.message_handler(commands=['окдня', "okdnya"])
def get_hero_of_the_day(message):
    now = datetime.datetime.now(moscow_tz)
    today = str(now.date())  # Дата в строковом формате

    if data["last_date_x"] != today or data["last_xozyain"] is None:
        chosen_xozyain = random.choice(members)
        data["last_xozyain"] = chosen_xozyain
        data["last_date_x"] = today
        save_data(data)  # Сохраняем изменения

    last_xozyain = data["last_xozyain"]

    activist_message = (
        f"ОК дня - {last_xozyain['first_name']} {last_xozyain['last_name']}! 🎉\n"
        f"Поздравляем {last_xozyain['telegram']} {last_xozyain['telegram']} {last_xozyain['telegram']}!!!"
    )
    bot.reply_to(message, activist_message)


@bot.message_handler(commands=["+", "-", "ok", "neok"])
def change_respect(message):
    if not message.reply_to_message:  
        return  # Игнорируем, если нет ответа на сообщение

    reply_user = message.reply_to_message.from_user.username
    sender_user = message.from_user.username

    if not reply_user or not sender_user or (reply_user == sender_user and sender_user != "melankolya"):
        return  # Игнорируем, если не удалось определить пользователей или это самореспект

    member = next((m for m in members if m['telegram'].strip('@') == reply_user), None)
    if not member:
        return  # Игнорируем, если пользователя нет в списке

    if "respect" not in member:
        member["respect"] = 0  

    if message.text.startswith("/+") or message.text.startswith("/ok"):
        value = 1
        if sender_user == "melankolya":
            parts = message.text.split()
            if len(parts) > 1:
                try:
                    value = int(parts[1])
                except ValueError:
                    pass
        member["respect"] += value
        if value == 1:
            bot.reply_to(message, f"Ты жёстко респектнул(-а) доброму человеку! {member['first_name']}, ты -настоящий маяк! \nУ тебя уже {member['respect']} балл(-ов)!")
        else:
            bot.reply_to(message, f"ПАПОЧКА ХВАЛИТ!\nУ тебя уже {member['respect']} балл(-ов)!")
    elif message.text.startswith("/-") or message.text.startswith("/neok"):
        value = 1
        if sender_user == "melankolya":
            parts = message.text.split()
            if len(parts) > 1:
                try:
                    value = int(parts[1])
                except ValueError:
                    pass
        member["respect"] -= value
        if value == 1:
            bot.reply_to(message, f"Не недостаток, а зона роста! Свети ярче, {member['first_name']}... \nТеперь у тебя {member['respect']} балл(-ов).")
        else:
            bot.reply_to(message, f"ГНЕВ ПАПОЧКИ! Свети ярче, {member['first_name']}... \nТеперь у тебя {member['respect']} балл(-ов).")
    savee_data()

@bot.message_handler(commands=["рейтинг", "ranking"])
def show_respect_ranking(message):
    sorted_members = sorted(members, key=lambda m: m.get("respect", 0), reverse=True)

    ranking = "".join(
        f"{i + 1}. {m['first_name']} {m['last_name']} — {m.get('respect', 0)}\n" if m.get("respect") != 0 else ""
        for i, m in enumerate(sorted_members)
    )

    bot.reply_to(message, f"🏆 *Рейтинг:* 🏆\n\n{ranking}", parse_mode="Markdown")
    

@bot.message_handler(commands=['вероятность', "prob"])
def probability_command(message):
    text = message.text.replace('/вероятность', '').strip()  # Убираем команду из текста
    if not text.lower().startswith("что "):  # Проверяем, начинается ли текст с "что "
        bot.reply_to(message, "Напиши фразу после `/вероятность`, начиная со слова 'что'. Например: `/вероятность что я сдам сессию`")
        return
    text = text[4:].strip()  # Убираем слово "что " из текста
    probability = random.randint(0, 100)  # Генерируем случайное число от 0 до 100
    response = f"{text} с вероятностью {probability}%"
    bot.reply_to(message, response)
    

@bot.message_handler(commands=['топ', "top"])
def top_command(message):
    text = message.text.replace('/топ', '').replace('/top', '').strip()
    
    words = text.split()
    
    if words and words[0].isdigit():  # Если первое слово — число
        count = int(words[0])
        category = " ".join(words[1:]) if len(words) > 1 else "лучших"
    else:  # Если число не указано, ставим 5 по умолчанию
        count = 5
        category = text if text else "лучших"
    
    count = min(count, len(members))  # Ограничиваем количество участников

    top_members = random.sample(members, count)  # Берем случайных людей

    response = f"Топ {count} {category} среди ОКов:\n"
    response += "\n".join([f"{i+1}. {member['first_name']} {member['last_name']}" for i, member in enumerate(top_members)])

    bot.reply_to(message, response)
    

@bot.message_handler(commands=['монетка', "coin"])
def coin(message):
    response = random.choice(["Орел", "Решка"])
    bot.reply_to(message, response)
        
@bot.message_handler(commands=['sosal', 'сосал'])
def sosal(message):
    bot.reply_to(message, "ДААААААААААААААА")

@bot.message_handler(func=lambda message: re.search(r'\bвам\b.*\bвсё\b.*\bпонятно\b', message.text, re.IGNORECASE))
def sosal(message):
    bot.reply_to(message, "пятьдесят два")
    
@bot.message_handler(func=lambda message: re.search(r'\bя\b.*\bне\b.*\bслышу\b', message.text, re.IGNORECASE))
def sosal(message):
    bot.reply_to(message, "ПЯТЬДЕСЯТ ДВААААА")
        
@bot.message_handler(commands=['daddy', 'папочка'])
def daddy(message):
    bot.reply_to(message, "@melankolya")

@bot.message_handler(commands=['granny', 'бабуля'])
def granny(message):
    if message.from_user.username == "enniuum":
        bot.reply_to(message, "Ой привет любимая бабуля! Я всегда рад с тобой пообщаться!")
        return
    bot.reply_to(message, "@enniuum")

@bot.message_handler(commands=["help"])
def show_help(message):
    help_text = (
        "🤖 *Список команд бота ОК:*\n\n"
        "📌 */инфа [фамилия] [имя]* – вся информация о нужном ОКе.\n"
        "📌 */шипперить* – случайным образом объединяет двух людей в пару.\n"
        "📌 */мысль* – выводит случайную цитату.\n"
        "📌 */вероятность что [фраза]* – проверь вероятность какого-то события.\n"
        "📌 */топ [число] [категория]* – выводит отличившихся ОКов в какой-то сфере.\n"
        "📌 */цитата* – делает красивую картинку из высказывания.\n"
        "📌 */когда* – предсказывает будущее.\n"
        "📌 */рейтинг* – показывает рейтинг ок/неок.\n"
        "📌 */совместимость* – показывает совместимость двух ОКов.\n"
        "📌 */+* – окнуть ОКа, ответив командой на его сообщение.\n"
        "📌 */-* – неОКнуть ока, ответив командой на его сообщение.\n"
        "📌 */help* – показывает этот список команд.\n"
    )
    bot.reply_to(message, help_text, parse_mode="Markdown")
    

# Функция для генерации цитаты
def generate_quote_image(text, author_name):
    # Загружаем фон
    bg = Image.open(BACKGROUND_IMAGE).convert("RGB")
    img_width, img_height = bg.size
    img = bg.copy()
    draw = ImageDraw.Draw(img)

    # Загружаем шрифты
    font_text = ImageFont.truetype(FONT_TEXT, FONT_SIZE_TEXT)
    font_name = ImageFont.truetype(FONT_NAME, FONT_SIZE_NAME)

    # Ограничиваем длину текста
    text = text[:200] + "..." if len(text) > 300 else text
    text = f"«{text}»"  # Добавляем ёлочные кавычки

    # Разбиваем цитату на строки, если она слишком длинная
    max_width = img_width * 0.55
    lines = []
    words = text.split()
    current_line = ""
    for word in words:
        test_line = f"{current_line} {word}".strip()
        if draw.textbbox((0, 0), test_line, font=font_text)[2] < max_width:
            current_line = test_line
        else:
            lines.append(current_line)
            current_line = word
    lines.append(current_line)

    # Вычисляем высоту блока текста
    total_text_height = len(lines) * FONT_SIZE_TEXT * 1.2
    text_y = (img_height - total_text_height) / 2 - 70  # Центрируем по вертикали

    # Рисуем цитату (с выравниванием по центру)
    for line in lines:
        text_width = draw.textbbox((0, 0), line, font=font_text)[2]
        text_x = (img_width - text_width) / 2  # Центрируем по горизонтали
        draw.text((text_x, text_y), line, font=font_text, fill=COLOR_TEXT)
        text_y += FONT_SIZE_TEXT * 1.2  # Межстрочный интервал

    # Позиция имени автора (без изменений)
    if "None" in author_name:
        author_name = author_name[:-5]
    name_width = draw.textbbox((0, 0), author_name, font=font_name)[2]
    name_x = img_width - name_width - 200  # 80 пикселей от правого края
    name_y = img_height - 150  # Внизу изображения

    draw.text((name_x, name_y), author_name, font=font_name, fill=COLOR_NAME)

    # Сохраняем в буфер
    output = BytesIO()
    img.save(output, format="PNG")
    output.seek(0)
    return output


# Команда /цитата
@bot.message_handler(commands=["цитата", "quote"])
def send_quote(message):
    if not message.reply_to_message or not message.reply_to_message.text:
        bot.reply_to(message, "Необходимо ответить на сообщение с текстом.")
        return  # Игнорируем, если нет ответа на сообщение
    text = message.reply_to_message.text
    author_telegram = f"@{message.reply_to_message.from_user.username}" if message.reply_to_message.from_user.username else None
    author_name = f"{message.reply_to_message.from_user.first_name} {message.reply_to_message.from_user.last_name}".strip() or "Неизвестный ОК"

    # Ищем автора в списке members
    author = next((m for m in members if m["telegram"] == author_telegram), None)
    if author:
        author_name = f"{author['first_name']} {author['last_name']}"

    # Генерируем изображение
    img = generate_quote_image(text, author_name)
    os.makedirs(MEDIA_FOLDER, exist_ok=True)
    file_path = os.path.join(MEDIA_FOLDER, f"quote_{message.message_id}.jpg")
    with open(file_path, "wb") as f:
        f.write(img.getvalue())
    img = generate_quote_image(text, author_name)
    bot.send_photo(message.chat.id, img, reply_to_message_id=message.message_id)

quote_parts = []
quote_author = None

@bot.message_handler(commands=["запомни"])
def remember_quote(message):
    global quote_parts, quote_author
    
    if not message.reply_to_message or not message.reply_to_message.text:
        bot.reply_to(message, "Необходимо ответить на сообщение с текстом.")
        return
    
    if not quote_parts:
        quote_author = message.reply_to_message.from_user.username
    
    quote_parts.append(message.reply_to_message.text)
    bot.reply_to(message, "Запомнил!")

@bot.message_handler(commands=["отправь"])
def send_stored_quote(message):
    global quote_parts, quote_author
    
    if not quote_parts:
        bot.reply_to(message, "Нет сохранённой цитаты.")
        return
    
    author_name = "неизвестный ОК"
    if quote_author:
        author = next((m for m in members if m["telegram"] == f"@{quote_author}"), None)
        if author:
            author_name = f"{author['first_name']} {author['last_name']}"
    
    text = ", ".join(quote_parts)
    img = generate_quote_image(text, author_name)
    os.makedirs(MEDIA_FOLDER, exist_ok=True)
    file_path = os.path.join(MEDIA_FOLDER, f"quote_{message.message_id}.jpg")
    with open(file_path, "wb") as f:
        f.write(img.getvalue())
    bot.send_photo(message.chat.id, img, reply_to_message_id=message.message_id)
    
    quote_parts = []
    quote_author = None



@bot.message_handler(commands=["мысль", "think"])
def send_random_photo(message):
    """Выбирает и отправляет случайное фото из сохраненных."""
    files = [f for f in os.listdir(MEDIA_FOLDER) if f.endswith(".jpg")]
    
    if not files:
        bot.reply_to(message, "В базе пока нет изображений.")
        return
    
    random_file = random.choice(files)
    file_path = os.path.join(MEDIA_FOLDER, random_file)
    with open(file_path, "rb") as file:
        bot.send_photo(message.chat.id, file)


@bot.message_handler(commands=["когда", "when"])
def when_command(message):
    args = message.text.split(maxsplit=1)
    if len(args) < 2:
        bot.reply_to(message, "Использование: /когда [ваш вопрос]")
        return
    else:
        user_text = args[1].strip('?')

        # Заменяем "я" на "ты"
        user_text = re.sub(r'\bЯ\b', 'Ты', user_text, flags=re.IGNORECASE)

        # Заменяем глаголы совершенного вида на второе лицо единственного числа
        user_text = re.sub(r'\b(смогу|сделаю|куплю|узнаю|увижу|найду|пойму|закончу|начну|позову|скажу|напишу|пойду|приеду|прочитаю|выучу|построю|получу|добьюсь|расскажу|стану|возьму)\b', 
                        lambda m: {
                            'смогу': 'сможешь',
                            'сделаю': 'сделаешь',
                            'куплю': 'купишь',
                            'узнаю': 'узнаешь',
                            'увижу': 'увидишь',
                            'найду': 'найдёшь',
                            'пойму': 'поймёшь',
                            'закончу': 'закончишь',
                            'начну': 'начнёшь',
                            'позову': 'позовёшь',
                            'скажу': 'скажешь',
                            'напишу': 'напишешь',
                            'пойду': 'пойдёшь',
                            'приеду': 'приедешь',
                            'прочитаю': 'прочитаешь',
                            'выучу': 'выучишь',
                            'построю': 'построишь',
                            'получу': 'получишь',
                            'добьюсь': 'добьёшься',
                            'расскажу': 'расскажешь',
                            'стану': 'станешь',
                            'возьму': 'возьмёшь'
                        }[m.group()], user_text)

        # Другие возможные замены
        user_text = re.sub(r'\bмой\b', 'твой', user_text)
        user_text = re.sub(r'\bмоя\b', 'твоя', user_text)
        user_text = re.sub(r'\bмои\b', 'твои', user_text)
        random_time = random.choice(TIME_VARIANTS)
        
        bot.reply_to(message, f"{user_text} {random_time}.")


@bot.message_handler(commands=['faculty', 'факультет'])
def filter_by_faculty(message):
    faculty_name = message.text.split(maxsplit=1)[1] if len(message.text.split()) > 1 else ''
    filtered_members = [member for member in members if member["faculty"].lower() == faculty_name.lower()]
    
    if not filtered_members:
        bot.reply_to(message, "Никого не найдено на этом факультете.")
        return
    
    response = "Обучающие Координаторы с факультета {}:\n".format(faculty_name)
    for member in filtered_members:
        response += "{} {} ({})\n".format(
            member["first_name"], member["last_name"], member["group"]
        )
    
    bot.reply_to(message, response)
    

def get_zodiac_sign(day, month):
    zodiac_dates = [
        ((1, 20), (2, 18), "Водолей"),
        ((2, 19), (3, 20), "Рыбы"),
        ((3, 21), (4, 19), "Овен"),
        ((4, 20), (5, 20), "Телец"),
        ((5, 21), (6, 20), "Близнецы"),
        ((6, 21), (7, 22), "Рак"),
        ((7, 23), (8, 23), "Лев"),
        ((8, 24), (9, 22), "Дева"),
        ((9, 23), (10, 22), "Весы"),
        ((10, 23), (11, 21), "Скорпион"),
        ((11, 22), (12, 21), "Стрелец"),
        ((12, 22), (1, 19), "Козерог")
    ]
    for start, end, sign in zodiac_dates:
        if (month == start[0] and day >= start[1]) or (month == end[0] and day <= end[1]):
            return sign
    return "Неизвестный знак"

@bot.message_handler(commands=['zodiac', 'знак'])
def filter_by_zodiac(message):
    zodiac_name = message.text.split(maxsplit=1)[1] if len(message.text.split()) > 1 else ''
    
    if zodiac_name.lower() == "водолея":
        lyrics = [
            "ВСЁ ОТДАЛА И НИ О ЧЁМ НЕ ЖАЛЕЮ",
            "ВСЁ ОТДАЛА И НИЧЕГО НЕ ОСТАЛОСЬ",
            "А РЯДОМ СТОЛЬКО ЧЕЛОВЕК ПОТЕРЯЛОСЬ",
            "Я ЭТИМ ЧУВСТВОМ УЖЕ ВЕК НЕ БОЛЕЮ",
            "ВСЁ ОТДАЛА И НИ О ЧЁМ НЕ ЖАЛЕЮ",
            "И ВОПРЕКИ ЛЕЧУ ВСЕМ АВТОПИЛОТАМ",
            "ЖИВУ НАЗЛО ГОРОСКОПАМ"
        ]
        for line in lyrics:
            bot.send_message(message.chat.id, line)
            time.sleep(7)
        return 
    
    filtered_members = []
    
    for member in members:
        day, month, _ = map(int, member["birth_date"].split('.'))
        if get_zodiac_sign(day, month).lower() == zodiac_name.lower():
            filtered_members.append(member)
    
    if not filtered_members:
        bot.reply_to(message, "Никого не найдено с таким знаком зодиака.")
        return
    
    response = "Обучающие Координаторы со знаком зодиака {}:\n".format(zodiac_name)
    for member in filtered_members:
        response += "{} {} ({})\n".format(
            member["first_name"], member["last_name"], member["birth_date"]
        )
    
    bot.reply_to(message, response)
    
@bot.message_handler(func=lambda message: message.reply_to_message is not None)
def auto_respect(message):
    reply_user = message.reply_to_message.from_user.username
    sender_user = message.from_user.username

    if not reply_user or not sender_user or (reply_user == sender_user and sender_user != "melankolya"):
        return  # Игнорируем, если не удалось определить пользователей или это самореспект

    member = next((m for m in members if m['telegram'].strip('@') == reply_user), None)
    if not member:
        return  # Игнорируем, если пользователя нет в списке

    if "respect" not in member:
        member["respect"] = 0  
    
    text = message.text.lower()
    if any(word in text for word in ["+", "❤️", "пасиб", "спс", "благодар", "респект"]):
        member["respect"] += 1
        bot.reply_to(message, f"Спасибо на хлеб не намажешь, а дополнительный балл - это всегда приятно. {member['first_name']}, \nТеперь у тебя {member['respect']} балл(-ов)!")
    savee_data()
    
@bot.message_handler(func=lambda message: True)
def stosorok(message):
    text = message.text.lower()
    if text == "а":
        lyrics = [
            "А-А-А-А, О-О-О-О",
            "140 — СКОРОСТЬ НА КРАЙ СВЕТА В НАПРАВЛЕНИИ ВЕТРА",
            "А-А-А-А, О-О-О-О",
            "БЫЛИ СВЯЗАННЫЕ ЛЕНТОЙ КРАСНОГО ЗАКАТА",
            "А-А-А-А, О-О-О-О",
            "140 — СКОРОСТЬ НА КРАЙ СВЕТА В НАПРАВЛЕНИИ ВЕТРА",
            "А-А-А-А, О-О-О-О",
            "БЫЛИ СВЯЗАННЫЕ ЛЕНТОЙ КРАСНОГО ЗАКАТА"
        ]
        for line in lyrics:
            bot.send_message(message.chat.id, line)
            time.sleep(7)
        return

while True:
    try:
        bot.polling(none_stop=True, timeout=60)
    except KeyboardInterrupt:
        print("Бот остановлен вручную.")
        break  # Выходим из цикла, если нажато Ctrl + C
    except Exception as e:
        print(f"⚠ Ошибка: {e}")  # Выводим текст ошибки
        time.sleep(10)  # Ждём 10 секунд перед новым запуском
        