import asyncio
import requests
import random
from datetime import datetime, timedelta
from aiogram import Bot, Dispatcher
from aiogram.filters import Command, CommandStart
from aiogram.types import Message
from googletrans import Translator
from config import TOKEN, THE_CAT_API_KEY, NASA_API_KEY, SPOONACULAR_API_KEY

# Создаём объект бота и диспетчера
bot = Bot(token=TOKEN)
dp = Dispatcher()

# Создаём объект для перевода
translator = Translator()


# Функция для работы с The Cat API
def get_cat_info():
    url = "https://api.thecatapi.com/v1/images/search"
    headers = {"x-api-key": THE_CAT_API_KEY}
    response = requests.get(url)
    if response.status_code == 200:
        data = response.json()
        return data[0]["url"]  # Возвращаем ссылку на изображение
    return None


# Функция для работы с NASA API
def get_random_nasa_image():
    start_date = datetime.now() - timedelta(days=365)
    random_date = start_date + timedelta(days=random.randint(0, 365))
    date_str = random_date.strftime("%Y-%m-%d")
    url = f"https://api.nasa.gov/planetary/apod?api_key={NASA_API_KEY}&date={date_str}"
    response = requests.get(url)
    if response.status_code == 200:
        data = response.json()
        return data.get("url"), data.get("title")  # Возвращаем URL и заголовок
    return None, None


# Функция для работы с The Joke API с переводом
def get_joke():
    url = "https://v2.jokeapi.dev/joke/Any"
    response = requests.get(url)
    if response.status_code == 200:
        data = response.json()
        if data.get("type") == "single":
            joke = data.get("joke")  # Одиночная шутка
        elif data.get("type") == "twopart":
            joke = f"{data.get('setup')} - {data.get('delivery')}"  # Двухчастная шутка
        else:
            joke = "Не удалось получить шутку 😢."

        # Переводим шутку на русский
        translated = translator.translate(joke, src="en", dest="ru")
        return translated.text
    return "Не удалось получить шутку 😢. Попробуйте позже."


# Функция для Spoonacular API
def get_recipe_from_spoonacular(ingredients):
    url = (
        f"https://api.spoonacular.com/recipes/findByIngredients?ingredients={ingredients}"
        f"&number=1&apiKey={SPOONACULAR_API_KEY}"
    )
    response = requests.get(url)
    if response.status_code == 200:
        data = response.json()
        if data:
            recipe = data[0]
            return (
                recipe["title"],  # Название рецепта
                f"https://spoonacular.com/recipe/{recipe['id']}",  # Ссылка на рецепт
                recipe["image"],  # Картинка рецепта
            )
    return None, None, None


# Обработчик команды /start
@dp.message(CommandStart())
async def start_command(message: Message):
    await message.answer(
        "Привет! Я бот, который может:\n"
        "🐾 Показывать котиков\n"
        "🌌 Делиться космическими фотографиями\n"
        "😂 Рассказывать шутки\n"
        "🍴 Искать рецепты по ингредиентам\n"
        "Попробуй команды:\n"
        "/cat – Увидеть случайного котика\n"
        "/nasa – Космическое изображение дня\n"
        "/joke – Услышать смешную шутку\n"
        "/recipe – Найти рецепт по ингредиентам\n"
        "/help – Посмотреть доступные команды"
    )


# Обработчик команды /cat
@dp.message(Command("cat"))
async def send_cat_photo(message: Message):
    cat_url = get_cat_info()
    if cat_url:
        await message.answer_photo(photo=cat_url, caption="Вот случайный котик для вас!")
    else:
        await message.answer("Не удалось получить фото котика 😿. Попробуйте позже.")


# Обработчик команды /nasa
@dp.message(Command("nasa"))
async def send_nasa_photo(message: Message):
    photo_url, title = get_random_nasa_image()
    if photo_url:
        await message.answer_photo(photo=photo_url, caption=f"🌌 {title}")
    else:
        await message.answer("Не удалось получить изображение NASA. Попробуйте позже.")


# Обработчик команды /joke
@dp.message(Command("joke"))
async def send_joke(message: Message):
    joke = get_joke()
    await message.answer(f"😂 {joke}")


# Обработчик команды /recipe
@dp.message(Command("recipe"))
async def send_recipe(message: Message):
    await message.answer("Введите ингредиенты через запятую (например: курица, картошка, сыр).")

    @dp.message()
    async def handle_ingredients(msg: Message):
        # Переводим ингредиенты на английский
        translated_ingredients = translator.translate(msg.text, src="ru", dest="en").text.replace(" ", "").lower()

        name, url, image = get_recipe_from_spoonacular(translated_ingredients)
        if name:
            await msg.answer_photo(
                photo=image,
                caption=f"🍴 {name}\n\nРецепт: [Ссылка]({url})",
                parse_mode="Markdown"
            )
        else:
            await msg.answer("Не удалось найти рецепт. Попробуйте другие ингредиенты.")


# Главная функция для запуска бота
async def main():
    await dp.start_polling(bot)


if __name__ == "__main__":
    asyncio.run(main())
