import os
from dotenv import load_dotenv
import requests
from bs4 import BeautifulSoup as bs
from telegram import Update
from telegram.ext import Application, CommandHandler, CallbackContext, Job

load_dotenv()

# * Token of the telegram bot
TOKEN = os.getenv("TOKEN")

# * Url of the product and all the filters
url = "https://www.ebay.com/sch/i.html?_from=R40&_nkw=s9+fe&_sop=15&_ipg=240&_stpos=19720"

# & Converting string price to float
def to_float(num_str: str) -> float:
    num_float = ''.join(char for char in num_str if char.isdigit() or char in ".,-")
    return float(num_float)


# & Get soup by url
def get_soup(url: str, headers: dict[str:str] = {}) -> bs:
    r = requests.get(url, headers=headers)
    soup = bs(r.content, "html.parser")
    return soup


# & Getting all the listings with given url
def get_listings(url: str) -> list:
    r = requests.get(url)
    soup = bs(r.content, "html.parser")
    listing_soups = soup.find("ul", {"class": "srp-results srp-list clearfix"}).find_all("li")
    listings = []
    
    for listing in listing_soups:
        if "s-item" in listing.get("class"):
            listings.append({})
            url = listing.find("a").get("href")
            listings[-1]["url"] = url

            # ! Dividing listings to buy it nows and auctions
            # ~ Only auctions have "s-item__bids" class
            # ? Formats: 1 - Buy it now, 2 - Auction, 3 - Auction with but it now price
            if listing.find("span", {"class": "s-item__bids"}) is None:
                format =  1
            else:
                if len(listing.find_all("span", {"class": "s-item__price"})) > 1:
                    format =  3
                format =  2
                listings[-1]["time_left"] = listing.find("span", {"class": "s-item__time-left"}).text[:-5]

            listings[-1]["format"] = format
            try: listings[-1]["price"] = [to_float(price.text.split("to")[0]) for price in listing.find_all("span", {"class": "s-item__price"})]
            except ValueError: del listings[-1] # ~ The "tap to see price" listings

        else:
            break

    return listings


# & Finding offers with given max price
def find_offers(listings: list[dict], max_price: int):
    offers = []
    for listing in listings:
        price = listing["price"][0]
        print(price)
        if listing["format"] == 1:
            if price <= max_price:
                offers.append(listing["url"])
        elif listing["format"] == 2:
            if price <= max_price and ('m' in listing["time_left"] and not 'h' in listing["time_left"]) or ('s' in listing["time_left"] and not 'm' in listing["time_left"]):
                if ('s' in price) or ('m' in price and int(price[:-1]) < 30):
                    offers.append(listing["url"])
        elif listing["format"] == 3:
            if listing["price"][1] <= max_price:
                offers.append(listing["url"])
    return offers


# & Checks if function found anything every n period of time and notifies if it does
async def check_function(context: CallbackContext):
    job = context.job
    chat_id = job.data 
    listings = get_listings(url)
    urls = find_offers(listings, 200)
    if urls:
        await context.bot.send_message(chat_id=chat_id, text="Found!, check the links: " + ",  ".join(urls))


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