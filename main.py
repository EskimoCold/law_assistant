from time import time
import warnings
warnings.filterwarnings(action="ignore")

import telebot

from packages import db_manager
from packages.networks import *
import config

bot = telebot.TeleBot(config.TOKEN)

markup = telebot.types.ReplyKeyboardMarkup(row_width=2)
help_button = telebot.types.KeyboardButton("Help")
report_button = telebot.types.KeyboardButton("Github")
markup.add(help_button, report_button)

survey_kb = telebot.types.InlineKeyboardMarkup()
yes_button = telebot.types.InlineKeyboardButton(text="Yes", callback_data="Yes")
no_button = telebot.types.InlineKeyboardButton(text="No", callback_data="No")
survey_kb.add(yes_button, no_button)

hello_sticker = open('stickers/hello.webp', 'rb')
work_sticker = open('stickers/work.webp', 'rb')
done_sticker = open('stickers/done.webp', 'rb')
error_sticker = open('stickers/error.webp', 'rb')

qa_pipline, sentence_model, kw_model = load_all_neuralnetworks()

db_manager.create_db() # create db if not exists

@bot.message_handler(commands=['start'])
def start_command(message):
    bot.send_sticker(message.chat.id, hello_sticker)
    bot.send_message(message.chat.id, 'Hi, my name is wiki_assistant_bot and I\'ll answer your questions!', reply_markup=markup)


@bot.callback_query_handler(func=lambda callback: True)
def inline(callback):
    satisfied = None
    
    if callback.data == "Yes":
        satisfied = True
    if callback.data == "No":
        satisfied = False

    if satisfied is not None:
        db_manager.update_satisfied(callback.message.chat.id, satisfied)
        bot.send_message(callback.message.chat.id, "Thank you, It was noted on your last question!")


@bot.message_handler(content_types=['text'])
def text_handler(message):
    if message.text == "Help":
        bot.send_message(message.chat.id, "To use the bot, just write him your question or ask it by using your voice.\n\nAfter the bot has responded, please leave your opinion about its work.")
    
    elif message.text == "Github":
        bot.send_message(message.chat.id, "https://github.com/EskimoCold/wiki_assistant")

    else:
        try:
            question = message.text

            bot.send_sticker(message.chat.id, work_sticker)

            print(f"question from {message.chat.id}: {question}")

            try:
                answer, url = question_to_answer(question, qa_pipline, sentence_model, kw_model)

                db_manager.save_q_and_a(question, answer, message.chat.id)

                print(f"answer on {message.chat.id}:{answer}")
                print(f"url on {message.chat.id}:{url}")

                if answer is None:
                    bot.send_sticker(message.chat.id, error_sticker)
                    bot.send_message(message.chat.id, "Sorry, I can\'t answer your question(")
                    
                else:
                    bot.send_sticker(message.chat.id, done_sticker)
                    bot.send_message(message.chat.id, f"{answer}\n\nHere you can read all information: {url}")
                    bot.send_message(message.chat.id, "Are you satisfied with the answer?", reply_markup=survey_kb)
                    
            except:
                bot.send_sticker(message.chat.id, error_sticker)
                bot.send_message(message.chat.id, "Sorry, I can\'t answer your question(")
                
        except:
            pass


@bot.message_handler(content_types=['voice'])
def voice_processing(message):
    file_info = bot.get_file(message.voice.file_id)
    downloaded_file = bot.download_file(file_info.file_path)
    
    with open(f'voice_msgs/{message.chat.id}_{int(time())}.ogg', 'wb') as new_file:
        new_file.write(downloaded_file)
        
    name = f'voice_msgs/{message.chat.id}_{int(time())}.ogg'
    transcription = get_large_audio_transcription(name)
    
    if transcription == 0:
        bot.send_message(message.chat.id, 'Could\'t recognize your voice')
        
    else:
        question = transcription[:-2]+'?'
        bot.send_message(message.chat.id, f'Your voice was recognized as: {question}')
        
        try:
            bot.send_sticker(message.chat.id, work_sticker)

            print(f"question from {message.chat.id}: {question}")

            try:
                answer, url = question_to_answer(question, qa_pipline, sentence_model, kw_model)

                db_manager.save_q_and_a(question, answer, message.chat.id)

                print(f"answer on {message.chat.id}:{answer}")
                print(f"url on {message.chat.id}:{url}")

                if answer is None:
                    bot.send_sticker(message.chat.id, error_sticker)
                    bot.send_message(message.chat.id, "Sorry, I can\'t answer your question(")
                    
                else:
                    bot.send_sticker(message.chat.id, done_sticker)
                    bot.send_message(message.chat.id, f"{answer}\n\nHere you can read all information: {url}")
                    bot.send_message(message.chat.id, "Are you satisfied with the answer?", reply_markup=survey_kb)
                    
            except:
                bot.send_sticker(message.chat.id, error_sticker)
                bot.send_message(message.chat.id, "Sorry, I can\'t answer your question(")
                
        except:
            pass        


if __name__ == "__main__":
    print('bot started!')
    bot.polling(non_stop=config.NONE_STOP)
