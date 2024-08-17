from django.shortcuts import render
from django.http import HttpResponse
import nest_asyncio
import asyncio
from telegram import Update, InlineKeyboardMarkup, InlineKeyboardButton, InputFile, ForceReply
import telepot
from telegram.ext import Application, CommandHandler, CallbackContext, CallbackQueryHandler, MessageHandler, filters, ContextTypes, ConversationHandler
from PIL import Image, ImageDraw, ImageFont
from django.templatetags.static import static
from datetime import datetime, timedelta, timezone


# Initialize the bot with your token
bot = telepot.Bot("7210689134:AAFJEl6tOmwYbpF8vcfkCL5C3RoBgDyc6W8")
# Apply nest_asyncio to allow nested event loops
nest_asyncio.apply()
# Define states for the conversation
(ASKING_QUESTIONS_SET1, ASKING_QUESTIONS_SET2, FILL_TEMPLATE) = range(3)
# Define questions manually
questions1 = [
    "Permit Number:",
    "Date Issued:",
    "Start Date & Time:",
    "End Date & Time:",
    "Work Location / Area:",
    "Name:",
    "Worker ID:",
    "Gender:",
    "Skillset:",
    "Work at height activity description:"
]
questions2 = [
    "Has a risk assessment been conducted for the work at height activity? (Yes/No):",
    "Conducted a thorough inspection of the work area and identified potential hazards? (Yes/No):",
    "Ensured all necessary precautions have been taken to mitigate risks associated with work at height? (Yes/No):"
]
# Dictionary to store user responses
user_responses = {}
    
async def start(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    """Starts the conversation and displays the menu."""
    keyboard = [
        [
            InlineKeyboardButton("Menu", callback_data='main_menu')
        ]
    ]
    reply_markup = InlineKeyboardMarkup(keyboard)
    await update.message.reply_text('Welcome to the bot! How can I assist you today?', reply_markup=reply_markup)

async def main_menu(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    """Displays the menu options."""
    query = update.callback_query
    await query.answer()

    keyboard = [
        [
            InlineKeyboardButton("Employee Login", callback_data='employee_login'),
            InlineKeyboardButton("Manage Work Permit", callback_data='work_permit'),
        ]
    ]
    reply_markup = InlineKeyboardMarkup(keyboard)
    await query.edit_message_text(text="Main Menu", reply_markup=reply_markup)

async def work_permit(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:

    query = update.callback_query
    await query.answer()

    keyboard = [
        [
            InlineKeyboardButton("Create New Entry", callback_data='create_entry'),
            InlineKeyboardButton("View Work Permit Status", callback_data='view_status')
        ],
        [
            InlineKeyboardButton("Back to Menu", callback_data='main_menu')
        ]
    ]
    reply_markup = InlineKeyboardMarkup(keyboard)
    await query.edit_message_text(text="Work Permit Options", reply_markup=reply_markup)

async def create_entry(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    """Handles the 'Create Entry' option."""
    query = update.callback_query
    await query.answer()

    # Initialize the response storage for the user
    user_id = update.effective_user.id
    user_responses[user_id] = []

    # Ask the first question
    await query.edit_message_text(text=questions1[0])

    return ASKING_QUESTIONS_SET1

ist_offset = timedelta(hours=5, minutes,30)
ist_timezone = timezone(ist_offset)

def get_current_ist_time():
    current_time_ist = datetime.now(ist_timezone)
    date_time_ist = current_time_ist.strftime("%Y-%m-%d %I:%M:%S %p")
    return date_time_ist

async def ask_questions_set1(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    """Ask all the questions from set 1 sequentially."""
    user_id = update.effective_user.id
    response = update.message.text
    user_responses[user_id].append(response)
    current_time = get_current_ist_time()
    user_responses[user_id].append(current_time)   
     

    if len(user_responses[user_id]) < len(questions1):
        next_question = questions1[len(user_responses[user_id])]
        await update.message.reply_text(next_question)
        return ASKING_QUESTIONS_SET1
    else:
        # Move to set 2 questions
        await update.message.reply_text(questions2[0])
        return ASKING_QUESTIONS_SET2

async def ask_questions_set2(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    """Ask all the questions from set 2 sequentially."""
    user_id = update.effective_user.id
    response = update.message.text
    user_responses[user_id].append(response)

    if len(user_responses[user_id]) < len(questions1) + len(questions2):
        next_question = questions2[len(user_responses[user_id]) - len(questions1)]
        await update.message.reply_text(next_question)
        return ASKING_QUESTIONS_SET2
    else:
        await update.message.reply_text("Thank you for providing all the information. Generating the filled form...")
        # Generate the filled JPEG
        filled_jpeg_path = generate_filled_jpeg(user_responses[user_id])
        await context.bot.send_photo(chat_id=update.effective_chat.id, photo=open(filled_jpeg_path, 'rb'))
        return ConversationHandler.END

def generate_filled_jpeg(responses):
    """Generates a filled JPEG with the provided responses."""
    template_path = 'Work-at-Height-Permit_page-0001.jpg'
    filled_path = 'filled_form.jpg'

    # Load the image
    image = Image.open(template_path)
    draw = ImageDraw.Draw(image)

    font_path = 'Timeless.ttf'
    font_size = 24
    font = ImageFont.truetype(font_path, font_size)

    # Example positions where responses will be written (you'll need to adjust these)
    positions_set1 = [
        (50, 270),  # Permit Number
        (450, 270),  # Date Issued
        (730, 270),  # Start Date & Time
        (1000, 270),  # End Date & Time
        (45, 370),  # Work Location / Area
        (50, 530),  # Name
        (400, 530),  # Worker ID
        (670, 530),  # Gender
        (865, 530),  # Skillset
        (50, 909),  # Work at height activity description
    ]

    positions_set2_yes = [
        (970, 1125),  # Risk assessment conducted
        (970, 1285),  # Thorough inspection
        (970, 1395),  # Necessary precautions taken
    ]

    positions_set2_no = [
        (1130, 1125),  # Risk assessment conducted
        (1130, 1285),  # Thorough inspection
        (1130, 1395),  # Necessary precautions taken
    ]

    # Fill set 1 responses
    for pos, response in zip(positions_set1, responses[:len(questions1)]):
        draw.text(pos, response, fill="black", font=font)

    # Fill set 2 responses
    for pos, response in zip(positions_set2_yes if response.lower() == "yes" else positions_set2_no, responses[len(questions1):]):
        draw.text(pos, "*", fill="black", font=font)

    image.save(filled_path)
    return filled_path

async def cancel(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    """Cancels and ends the conversation."""
    await update.message.reply_text('Bye! I hope we can talk again some day.')
    return ConversationHandler.END

async def stop(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    """Stops the bot."""
    await update.message.reply_text('Stopping the bot...')
    context.application.stop()

def main(request) -> None:
    """Run the bot."""
    application = Application.builder().token("7210689134:AAFJEl6tOmwYbpF8vcfkCL5C3RoBgDyc6W8").build()

    conv_handler = ConversationHandler(
        entry_points=[CallbackQueryHandler(create_entry, pattern='create_entry')],
        states={
            ASKING_QUESTIONS_SET1: [MessageHandler(filters.TEXT & ~filters.COMMAND, ask_questions_set1)],
            ASKING_QUESTIONS_SET2: [MessageHandler(filters.TEXT & ~filters.COMMAND, ask_questions_set2)],
        },
        fallbacks=[CommandHandler('cancel', cancel)],
    )

    application.add_handler(CommandHandler('start', start))
    application.add_handler(CallbackQueryHandler(main_menu, pattern='main_menu'))
    application.add_handler(CallbackQueryHandler(work_permit, pattern='work_permit'))
    application.add_handler(conv_handler)
    application.add_handler(CommandHandler('stop', stop))

    application.run_polling()

if __name__ == '__main__':
    main()