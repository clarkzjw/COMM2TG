from pymongo import MongoClient
from telegram.ext import Updater, CommandHandler
import logging
# Enable logging
logging.basicConfig(format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
                                        level=logging.DEBUG)
logger = logging.getLogger(__name__)
def search(bot, update, args):
    agentid = args[0]
    print(agentid)
    conn = MongoClient('Mongo Address')
    db = conn['COMM_Hangzhou']
    collection = db.entries
    res = collection.find({"$text": {"$search": agentid}})
    for i in res:
        print(i)
        bot.sendMessage(update.message.chat_id, text=str(i))
def start(bot, update):
    bot.sendMessage(update.message.chat_id, text="Hi! Use /search agentid to start, no need for @")
def error(bot, update, error):
        logger.warn('Update "%s" caused error "%s"' % (update, error))
def main():
    updater = Updater('Telegram Bot ID')
    dp = updater.dispatcher
    dp.add_handler(CommandHandler("start", start))
    dp.add_handler(CommandHandler("help", start))
    dp.add_handler(CommandHandler("search", search, pass_args=True))
    dp.add_error_handler(error)
    updater.start_polling()
    updater.idle()
if __name__ == "__main__":
    main()
