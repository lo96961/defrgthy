import sqlite3
from telebot import TeleBot, types
from datetime import datetime

bot = TeleBot('')

def get_db_connection():
    return sqlite3.connect('events.db')


@bot.message_handler(commands=['start'])
def send_welcome(message):
    bot.reply_to(message, "Привет! Я могу показать тебе список мероприятий. Что хочешь сделать?")
    show_main_menu(message.chat.id)

def show_main_menu(chat_id):
    keyboard = types.InlineKeyboardMarkup()
    button1 = types.InlineKeyboardButton(text="Посмотреть мероприятия", callback_data='view_events')
    button2 = types.InlineKeyboardButton(text="Зарегистрироваться на мероприятие", callback_data='register_event')
    button3 = types.InlineKeyboardButton(text="Добавить мероприятие", callback_data='add_event')
    keyboard.add(button1, button2, button3)
    bot.send_message(chat_id, "Выбери действие:", reply_markup=keyboard)

@bot.callback_query_handler(func=lambda call: True)
def handle_callback(call):
    chat_id = call.message.chat.id
    if call.data == 'view_events':
        view_events(chat_id)
    elif call.data == 'register_event':
        register_event(chat_id)
    elif call.data == 'add_event':
        add_event_step_1(call)

def view_events(chat_id):
    conn = get_db_connection()
    cursor = conn.cursor()
    cursor.execute("SELECT * FROM events")
    rows = cursor.fetchall()
    
    if not rows:
        bot.send_message(chat_id, "Мероприятия отсутствуют.")
    else:
        for row in rows:
            event_info = f"{row[0]} {row[1]} {row[2]} {row[3]} {row[4]}"
            bot.send_message(chat_id, event_info)
            
    conn.close()

def register_event(chat_id):
    bot.send_message(chat_id, "Введите ID мероприятия, на которое хотите зарегистрироваться:")
    @bot.message_handler(func=lambda message: True)
    def handle_registration(message):
        event_id = int(message.text.strip())

        conn = get_db_connection()
        cursor = conn.cursor()
        cursor.execute(f"SELECT * FROM events WHERE id={event_id}")
        event = cursor.fetchone()
        
        if event is None:
            bot.send_message(chat_id, "Мероприятие с таким ID не найдено.")
        else:
            bot.send_message(chat_id, f"Ты успешно зарегистрирован на мероприятие: {event[1]}.")
        
        conn.close()

new_event = {}

@bot.callback_query_handler(func=lambda call: call.data == 'add_event')
def add_event_step_1(call):
    chat_id = call.message.chat.id
    msg = bot.send_message(chat_id, "Введите название мероприятия:")
    bot.register_next_step_handler(msg, process_name)

def process_name(message):
    global new_event
    new_event['name'] = message.text
    msg = bot.send_message(message.chat.id, "Введите дату мероприятия (в формате ДД.ММ.ГГГГ):")
    bot.register_next_step_handler(msg, process_date)

def process_date(message):
    try:
        datetime.strptime(message.text, '%d.%m.%Y')
    except ValueError:
        msg = bot.reply_to(message, 'Неверный формат даты. Пожалуйста, введите дату в формате ДД.ММ.ГГГГ.')
        bot.register_next_step_handler(msg, process_date)
        return
    new_event['date'] = message.text
    msg = bot.send_message(message.chat.id, "Введите место проведения мероприятия:")
    bot.register_next_step_handler(msg, process_location)

def process_location(message):
    new_event['location'] = message.text
    msg = bot.send_message(message.chat.id, "Введите категорию мероприятия:")
    bot.register_next_step_handler(msg, process_category)

def process_category(message):
    new_event['category'] = message.text
    save_event(new_event)
    bot.send_message(message.chat.id, "Мероприятие добавлено!")

def save_event(event):
    conn = get_db_connection()
    cursor = conn.cursor()
    cursor.execute(
        "INSERT INTO events (name, date, location, category) VALUES (:name, :date, :location, :category)",
        {
            'name': event['name'],
            'date': event['date'],
            'location': event['location'],
            'category': event['category']
        }
    )
    conn.commit()
    conn.close()

if __name__ == '__main__':
    bot.polling(none_stop=True)
