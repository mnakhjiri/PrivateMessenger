import django
import os

os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'PrivateMessenger.settings')
django.setup()
from account.models import *
from Messenger.models import *
from PrivateMessenger.settings import TELEGRAM_BOT_TOKEN
import telebot
from telebot import types

bot = telebot.TeleBot(TELEGRAM_BOT_TOKEN)
reply_mode = {}


# bot menu
def menu(message):
    chat_id = message.chat.id
    user_info = UserInfo.objects.get(chat_id=chat_id)
    markup = types.ReplyKeyboardMarkup(resize_keyboard=True)
    item = types.KeyboardButton('ارتباط با ادمین')
    item2 = types.KeyboardButton('راهنما')
    item3 = types.KeyboardButton('مشاهده پیام های دریافتی')
    item4 = types.KeyboardButton('ارسال پیام به کاربر')
    if user_info.silent_notifications:
        item5 = types.KeyboardButton('فعال کردن اعلان ها')
    else:
        item5 = types.KeyboardButton('غیر فعال کردن اعلان ها')
    markup.row(item)
    markup.row(item4, item3)
    markup.row(item2, item5)
    bot.send_message(message.chat.id, "دستور خود را وارد کنید", reply_markup=markup)


def user_show_help(message):
    user_information = UserInfo.objects.get(chat_id=message.chat.id)
    # bold text
    help_text = "*راهنمای بات*" + "\n\n"
    if user_information.silent_notifications:
        help_text += "اعلان ها غیر فعال است." + "\n"
    else:
        help_text += "اعلان ها فعال است." + "\n\n"
    help_text += "آیدی کاربری : " + str(user_information.id) + "\n\n"
    help_text += "شما می‌توانید با اشتراک گذاری آیدی کاربری خود با دیگران، از طریق بات با آنها ارتباط برقرار کنید." + "\n"
    help_text += "برای ارسال پیام به کاربر از دکمه ارسال پیام به کاربر استفاده کنید." + "\n"
    help_text += "برای مشاهده پیام های دریافتی از دکمه مشاهده پیام های دریافتی استفاده کنید." + "\n"

    bot.send_message(message.chat.id, help_text, parse_mode='Markdown')


# handling start of the bot in private mode
@bot.message_handler(commands=['start'])
def greet(message):
    UserInfo.objects.get_or_create(chat_id=message.chat.id)
    bot.send_message(message.chat.id, "سلام " + message.chat.first_name)
    menu(message)


# handling menu

@bot.message_handler(regexp="غیر فعال کردن اعلان ها")
def handle_message(message):
    if message.chat.type == "private":
        user = UserInfo.objects.get(chat_id=message.chat.id)
        user.silent_notifications = True
        user.save(update_fields=['silent_notifications'])
        bot.send_message(message.chat.id, "اعلان ها غیر فعال شد.")
        menu(message)


@bot.message_handler(regexp="فعال کردن اعلان ها")
def handle_message(message):
    if message.chat.type == "private":
        user = UserInfo.objects.get(chat_id=message.chat.id)
        user.silent_notifications = False
        user.save(update_fields=['silent_notifications'])
        bot.send_message(message.chat.id, "اعلان ها فعال شد.")
        menu(message)


@bot.message_handler(regexp="ارسال پیام به کاربر")
def handle_message(message):
    if message.chat.type == "private":
        reply_mode[message.chat.id] = "ask_for_user_to_send_message"
        custom_keyboard = types.ReplyKeyboardMarkup(resize_keyboard=True)
        custom_keyboard.row(types.KeyboardButton('برگشت'))
        bot.send_message(message.chat.id, "آیدی یوزر را وارد نمایید.", reply_markup=custom_keyboard)


@bot.message_handler(regexp="مشاهده پیام های دریافتی")
def handle_message(message):
    if message.chat.type == "private":
        user = UserInfo.objects.get(chat_id=message.chat.id)
        messages = Message.get_inbox(user)
        if len(messages) == 0:
            bot.send_message(message.chat.id, "پیامی برای شما وجود ندارد.")
        else:
            for message_item in messages:
                if message_item.sender.superuser:
                    first_message_txt = "شما پیام جدید از ادمین دارید:" + "\n"
                else:
                    first_message_txt = \
                        "شما پیام جدید دارید." + "\n" + "پیام از کاربر " + f'`{str(message_item.sender.id)}`' + " : "
                bot.send_message(message.chat.id, first_message_txt,
                                 parse_mode='Markdown')
                # bot.forward_message(message.chat.id, message_item.sender.chat_id, message_item.message_id, )
                bot.send_message(message.chat.id, message_item.txt)
                message_item.is_read = True
                message_item.save(update_fields=['is_read'])
        menu(message)


@bot.message_handler(regexp="ارتباط با ادمین")
def handle_message(message):
    if message.chat.type == "private":
        reply_mode[message.chat.id] = "send_message"
        custom_keyboard = types.ReplyKeyboardMarkup(resize_keyboard=True)
        custom_keyboard.row(types.KeyboardButton('برگشت'))
        bot.send_message(message.chat.id, "لطفا پیام خود را وارد نمایید.", reply_markup=custom_keyboard)


@bot.message_handler(regexp="راهنما")
def handle_message(message):
    if message.chat.type == "private":
        user_show_help(message)
        menu(message)


# handling replies
@bot.message_handler()
def message_handler(message):
    if message.chat.type == "private" and message.text == "برگشت":
        if message.chat.id in reply_mode.keys():
            reply_mode.pop(message.chat.id)
        menu(message)
        return

    if message.chat.type == "private" and message.chat.id in reply_mode.keys():
        if reply_mode[message.chat.id] == "send_message":
            sender, _ = UserInfo.objects.get_or_create(chat_id=message.chat.id)
            recipients = UserInfo.get_super_users()
            for recipient in recipients:
                send_message_to_user(message, recipient, sender)
            bot.send_message(message.chat.id, "پیام مورد نظر ارسال شد.")
            menu(message)
        elif reply_mode[message.chat.id] == "ask_for_user_to_send_message":
            try:
                user = UserInfo.objects.get(id=message.text)
                reply_mode[message.chat.id] = "send_message_to_user:" + str(user.id)
                custom_keyboard = types.ReplyKeyboardMarkup(resize_keyboard=True)
                custom_keyboard.row(types.KeyboardButton('برگشت'))
                bot.send_message(message.chat.id, "لطفا پیام خود را وارد نمایید.", reply_markup=custom_keyboard)
                return
            except UserInfo.DoesNotExist:
                bot.send_message(message.chat.id, "کاربری با این آیدی وجود ندارد.")
                menu(message)
            except Exception as ve:
                print(ve)
                bot.send_message(message.chat.id, "کاربری با این آیدی وجود ندارد.")
                menu(message)
        elif "send_message_to_user:" in reply_mode[message.chat.id]:
            user_id = reply_mode[message.chat.id].split(":")[1]
            sender, _ = UserInfo.objects.get_or_create(chat_id=message.chat.id)
            recipient = UserInfo.objects.get(id=user_id)
            send_message_to_user(message, recipient, sender)
            bot.send_message(message.chat.id, "پیام مورد نظر ارسال شد.")
            menu(message)

    if message.chat.type == "private" and message.chat.id in reply_mode.keys():
        reply_mode.pop(message.chat.id)


def send_message_to_user(message, recipient, sender):
    message_item = Message.objects.create(message_id=message.message_id, sender=sender, recipient=recipient,
                                          txt=message.text)
    if not recipient.silent_notifications:
        if sender.superuser:
            first_message_txt = "شما پیام جدید از ادمین دارید:" + "\n"
        else:
            first_message_txt = \
                "شما پیام جدید دارید." + "\n" + "پیام از کاربر " + f'`{str(sender.id)}`' + " : "
        bot.send_message(recipient.chat_id, first_message_txt, parse_mode='Markdown')
        bot.send_message(recipient.chat_id, message_item.txt)
        # bot.forward_message(recipient.chat_id, sender.chat_id, message.message_id)
        message_item.is_read = True
        message_item.save(update_fields=['is_read'])


bot.infinity_polling()
