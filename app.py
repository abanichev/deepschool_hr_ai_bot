#!/usr/bin/env python3

import logging

import os
import tempfile

from telegram import Update
from telegram.ext import Application, CommandHandler, MessageHandler, filters, ContextTypes
from telegram.constants import ParseMode
import PyPDF2
from together import Together
from dotenv import load_dotenv

class HRBot:
    def __init__(self):
        self.logger = logging.getLogger(self.__class__.__name__)

        self.cv_storage = {}
        self.job_storage = {}
        self.chat_storage = {}

        self.llm = self.setup_together()
        self.bot = self.setup_bot_application()

    def setup_together(self):
        self.logger.info("Setting up Together client...")
        client = Together(
            api_key=os.getenv("TOGETHER_API_KEY"),
            base_url="https://litellm.deepschool.ru",
        )
        self.logger.info("Together client setup complete.")
        return client

    def setup_bot_application(self):
        self.logger.info("Setting up bot...")
        bot = Application.builder()
        bot = bot.token(os.getenv('TELEGRAM_BOT_TOKEN'))
        bot = bot.build()
        self.logger.info("Adding bot command handlers...")
        bot.add_handler(CommandHandler("start", self.start_command))
        bot.add_handler(CommandHandler("clear", self.clear_command))
        bot.add_handler(CommandHandler("reset", self.reset_command))
        bot.add_handler(CommandHandler("analyze", self.analyze_command))
        self.logger.info("Adding bot message handlers...")
        bot.add_handler(MessageHandler(filters.Document.PDF, self.handle_document))
        bot.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, self.handle_text))
        bot.add_handler(MessageHandler(None, self.fallback_handler))
        self.logger.info("Bot setup complete.")
        return bot

    def run(self):
        self.logger.info("Starting bot...")
        self.bot.run_polling(allowed_updates=Update.ALL_TYPES)

    async def analyze_candidates(self, cvs, job):
        self.logger.info(f"Analyzing {len(cvs)} candidates for '{job}' position...")
        prompt = ""

        prompt += f"JOB DESCRIPTION:\n{job}\n\n"

        for i, cv in enumerate(cvs, start=1):
            prompt += f"CV #{i}:\n---\n{cv}\n---\n\n"

        prompt += ("INSTRUCTIONS:\n"
                   "You are an HR specialist with 10 years of experience in IT industry. Analyze the above CVs "
                   "against the JOB DESCRIPTION. Select the **single most suitable** candidate. "
                   "For the **first** user message respond **only** with this format:\n"
                   "```\n"
                   "Candidate: [Full Name] ([Job Title])\n"
                   "Reason: [One-sentence explanation]\n"
                   "```\n"
                   "If no CV matches the job requirements, respond:\n"
                   "```\n"
                   "No suitable candidate found.\n"
                   "```\n"
                   "Do not add any other text or analysis. Starting from the user's **second** message, provide assistance.")

        message = {"role": "user", "content": prompt}

        result = self.llm.chat.completions.create(
            model="meta-llama/Llama-3.3-70B-Instruct-Turbo-Free",
            messages=[message],
            max_tokens=2000
        )

        return message, result.choices[0].message.content

    async def start_command(self, update, context):
        self.logger.info("Handling /start command...")
        welcome_message = ("Добро пожаловать в отдел кадров!"
                           "\n\nДля начала отправьте резюме ваших кандидатов в формате PDF."
                           "\nКогда все резюме будут отправлены, опишите вакансию, кандидатов на которую вы ищете."
                           "\nЗатем отправьте команду `/analyze` для начала процедуры выбора кандидата."
                           "\n\nДля удаления сохраненных резюме и вакансии отправьте команду `/clear`.")
        await update.message.reply_text(welcome_message, parse_mode=ParseMode.MARKDOWN)

    async def clear_command(self, update, context):
        self.logger.info("Handling /clear command...")
        user_id = update.effective_user.id
        self.cv_storage[user_id] = []
        self.job_storage[user_id] = ""
        await update.message.reply_text("Резюме и описание вакансии удалены!")

    async def reset_command(self, update, context):
        self.logger.info("Handling /reset command...")
        user_id = update.effective_user.id
        self.cv_storage[user_id] = []
        self.job_storage[user_id] = ""
        del self.cv_storage[user_id]
        await update.message.reply_text("Я как заново родился... Начнем сначала!")

    async def analyze_command(self, update, context):
        self.logger.info("Handling /analyze command...")
        user_id = update.effective_user.id

        if user_id not in self.cv_storage or not self.cv_storage[user_id]:
            await update.message.reply_text("Сначала отправьте одно или более резюме.")
            return

        if user_id not in self.job_storage or not self.job_storage[user_id]:
            await update.message.reply_text("Сначала отправьте описание вакансии.")
            return

        analyzing_msg = await update.message.reply_text("Приступаю к анализу...")

        prompt, result = await self.analyze_candidates(self.cv_storage[user_id], self.job_storage[user_id])

        await analyzing_msg.delete()
        await update.message.reply_text(result)

        message = {"role": "assistant", "content": result}
        self.chat_storage = create_or_append(self.chat_storage, user_id, prompt)
        self.chat_storage = create_or_append(self.chat_storage, user_id, message)


    async def handle_document(self, update, context):
        self.logger.info("Retrieving document...")
        user_id = update.effective_user.id
        document = update.message.document

        if user_id in self.cv_storage and len(self.cv_storage[user_id]) >= 5:
            await update.message.reply_text("Извините, слишком много кандидатов. Ограничьтесь 5 резюме.")
            return

        if not document.file_name.lower().endswith('.pdf'):
            await update.message.reply_text("Принимаются только резюме в формате PDF.")
            return

        file = await context.bot.get_file(document.file_id)

        with tempfile.NamedTemporaryFile(delete=False, suffix='.pdf') as temp_file:
            temp_file_name = temp_file.name
            self.logger.debug(f"Downloading PDF to '{temp_file_name}'...")
            await file.download_to_drive(temp_file_name)

        try:
            with open(temp_file_name, 'rb') as temp_file:
                self.logger.debug(f"Reading PDF...")
                pdf = PyPDF2.PdfReader(temp_file)
                text = ""
                for page in pdf.pages:
                    text += page.extract_text()
        finally:
            self.logger.debug(f"Removing '{temp_file_name}'...")
            os.unlink(temp_file_name)
        self.cv_storage = create_or_append(self.cv_storage, user_id, text)
        await update.message.reply_text("Файл принят!")

    async def handle_text(self, update, context):
        self.logger.info("Reading text message...")
        user_id = update.effective_user.id
        text = update.message.text

        if user_id not in self.job_storage:
            self.job_storage[user_id] = text
            await update.message.reply_text(f"Описание вакансии принято!")
        else:
            message = {"role": "user", "content": text}
            messages = self.chat_storage[user_id]

            result = self.llm.chat.completions.create(
                model="meta-llama/Llama-3.3-70B-Instruct-Turbo-Free",
                messages=messages,
                max_tokens=2000
            )
            response = result.choices[0].message.content
            await update.message.reply_text(response)
            self.chat_storage = create_or_append(self.chat_storage, user_id, message)
            self.chat_storage = create_or_append(self.chat_storage, user_id, {"role": "assistant", "content": response})


    async def fallback_handler(self, update, context):
        self.logger.info("Got unsupported update...")
        await update.message.reply_text(f"Такое мне больше не присылай!")


def create_or_append(storage, user_id, item):
    if user_id not in storage:
        storage[user_id] = []
    storage[user_id].append(item)
    return storage


def main():
    logging.basicConfig(format="%(asctime)s - %(name)s - %(levelname)s - %(message)s", level=logging.INFO)
    logging.getLogger("httpx").setLevel(logging.WARNING)

    bot = HRBot()
    bot.run()


if __name__ == '__main__':
    load_dotenv()
    main()
