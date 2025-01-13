import os
from dotenv import load_dotenv
from telegram import Update
from telegram.ext import Application, CommandHandler, CallbackContext, Job

load_dotenv()
TOKEN = os.getenv("TOKEN")

# & Finding offers function
def find_offers():
    return True 

# & Checks if function found anything every n period of time and notifies if it does
async def check_function(context: CallbackContext):
    job = context.job
    chat_id = job.data 
    if find_offers():
        await context.bot.send_message(chat_id=chat_id, text="Found!")

# & /start function
async def start(update: Update, context: CallbackContext):
    chat_id = update.message.chat_id
    context.job_queue.run_repeating(check_function, interval=30, first=0, data=chat_id)
    await update.message.reply_text('Bot started! It will check the product every 30 seconds.')

# & Main function
def main():
    application = Application.builder().token(TOKEN).build()
    application.add_handler(CommandHandler("start", start))
    application.run_polling()

if __name__ == '__main__':
    main()