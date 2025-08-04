import os
import logging
from typing import Dict, Any
from telegram import Update, InlineKeyboardButton, InlineKeyboardMarkup
from telegram.ext import (
    Application, ApplicationBuilder, CommandHandler, CallbackQueryHandler, 
    MessageHandler, ConversationHandler, ContextTypes, filters
)
from dotenv import load_dotenv
from database import Database

# Load environment variables
load_dotenv()

# Enable logging
logging.basicConfig(
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    level=logging.WARNING
)
logger = logging.getLogger(__name__)

# Conversation states
ADDING_DGSC_NAME, ADDING_DGSC_DESC, REQUESTING_MESSAGE = range(3)

class DGSCBot:
    def __init__(self):
        self.token = os.getenv('BOT_TOKEN')
        self.db = Database(os.getenv('DATABASE_PATH', './dgsc_tracker.db'))
        self.application = None
    
    def setup_handlers(self):
        """Setup all command and callback handlers"""
        # Command handlers
        self.application.add_handler(CommandHandler("start", self.start_command))
        self.application.add_handler(CommandHandler("help", self.help_command))
        self.application.add_handler(CommandHandler("my_items", self.my_items_command))
        self.application.add_handler(CommandHandler("search", self.search_command))
        self.application.add_handler(CommandHandler("my_requests", self.my_requests_command))
        self.application.add_handler(CommandHandler("pending_requests", self.pending_requests_command))
        self.application.add_handler(CommandHandler("list", self.list_all_items_command))
        
        # Conversation handler for adding DGSCs
        add_dgsc_handler = ConversationHandler(
            entry_points=[CommandHandler('add_dgsc', self.add_dgsc_start)],
            states={
                ADDING_DGSC_NAME: [MessageHandler(filters.TEXT & ~filters.COMMAND, self.add_dgsc_name)],
                ADDING_DGSC_DESC: [MessageHandler(filters.TEXT & ~filters.COMMAND, self.add_dgsc_description)],
            },
            fallbacks=[CommandHandler('cancel', self.cancel)]
        )
        self.application.add_handler(add_dgsc_handler)
        
        # Conversation handler for requesting items
        request_handler = ConversationHandler(
            entry_points=[CallbackQueryHandler(self.request_item_start, pattern=r'^request_\d+$')],
            states={
                REQUESTING_MESSAGE: [MessageHandler(filters.TEXT & ~filters.COMMAND, self.request_item_message)],
            },
            fallbacks=[CommandHandler('cancel', self.cancel)]
        )
        self.application.add_handler(request_handler)
        
        # Callback query handlers (for accept/reject buttons)
        self.application.add_handler(CallbackQueryHandler(self.handle_callback, pattern=r'^(accept|reject)_\d+$'))
    
    async def start_command(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        """Handle /start command"""
        user = update.effective_user
        self.db.add_user(user.id, user.username, user.first_name, user.last_name)
        
        welcome_text = (
            f"👋 Welcome to DGSC Tracker, {user.first_name}!\n\n"
            "This bot helps you and your team keep track of shared DGSCs.\n\n"
            "Available commands:\n"
            "• /my_items - View items you currently possess\n"
            "• /add_dgsc - Add a new DGSC to the system\n"
            "• /list - View all items in the system\n"
            "• /search - Search for specific DGSCs\n"
            "• /my_requests - View your pending requests\n"
            "• /pending_requests - View requests waiting for your approval\n"
            "• /help - Show this help message"
        )
        
        await update.message.reply_text(welcome_text)
    
    async def help_command(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        """Handle /help command"""
        help_text = (
            "🔧 DGSC Tracker Help\n\n"
            "Main Commands:\n"
            "• /my_items - See all DGSCs you currently own\n"
            "• /add_dgsc - Register a new DGSC in the system\n"
            "• /list - View all DGSCs in the system with current owners\n"
            "• /search <name> - Find DGSCs by name or description\n"
            "• /my_requests - Check status of your requests\n"
            "• /pending_requests - Approve/reject incoming requests\n\n"
            "How it works:\n"
            "1. Add DGSCs to the system using /add_dgsc\n"
            "2. Browse all items using /list or search using /search\n"
            "3. Request items from other users\n"
            "4. Accept or reject requests from others\n"
            "5. All transactions are automatically tracked\n\n"
            "Need help? Contact your system administrator."
        )
        
        await update.message.reply_text(help_text)
    
    async def my_items_command(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        """Show items currently owned by the user"""
        user_id = update.effective_user.id
        dgscs = self.db.get_user_dgscs(user_id)
        
        if not dgscs:
            await update.message.reply_text(
                "📦 You don't currently possess any DGSCs.\n"
                "Use /search to find available items or /add_dgsc to register new ones."
            )
            return
        
        text = "📦 Your Current Items:\n\n"
        for dgsc_id, name, description, created_at in dgscs:
            text += f"• {name}\n"
            if description:
                text += f"  {description}\n"
            text += f"  Added: {created_at[:10]}\n\n"
        
        await update.message.reply_text(text)
    
    async def search_command(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        """Search for DGSCs"""
        # Update user info to ensure current data
        user = update.effective_user
        self.db.add_user(user.id, user.username, user.first_name, user.last_name)
        
        if not context.args:
            await update.message.reply_text(
                "🔍 Please provide a search term.\n"
                "Usage: `/search <DGSC name>`\n"
                "Example: `/search usb drive`"
            )
            return
        
        search_term = ' '.join(context.args)
        results = self.db.search_dgsc(search_term)
        
        if not results:
            await update.message.reply_text(
                f"❌ No DGSCs found matching '{search_term}'\n"
                "Try a different search term or check the spelling."
            )
            return
        
        text = f"🔍 Search Results for '{search_term}':\n\n"
        keyboard = []
        
        for dgsc_id, name, description, owner_id, username, first_name, last_name in results:
            # Create a better display name for the owner
            if first_name and first_name.strip():
                owner_display = first_name.strip()
            elif username and username.strip():
                owner_display = username.strip()
            elif last_name and last_name.strip():
                owner_display = last_name.strip()
            else:
                owner_display = f"User {owner_id}"
                
            text += f"• {name}\n"
            if description:
                text += f"  {description}\n"
            text += f"  📍 Currently with: {owner_display}\n\n"
            
            # Add request button if not owned by current user
            if owner_id != update.effective_user.id:
                keyboard.append([
                    InlineKeyboardButton(
                        f"🙋‍♂️ Request {name}", 
                        callback_data=f"request_{dgsc_id}"
                    )
                ])
        
        reply_markup = InlineKeyboardMarkup(keyboard) if keyboard else None
        await update.message.reply_text(text, reply_markup=reply_markup)
    
    async def list_all_items_command(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        """List all items in the system with their current owners"""
        # Update user info to ensure current data
        user = update.effective_user
        self.db.add_user(user.id, user.username, user.first_name, user.last_name)
        
        user_id = update.effective_user.id
        all_items = self.db.get_all_dgscs()
        
        if not all_items:
            await update.message.reply_text(
                "📦 No DGSCs are registered in the system yet.\n"
                "Use /add_dgsc to register the first one!"
            )
            return
        
        text = "📦 All DGSCs in the System:\n\n"
        keyboard = []
        
        for dgsc_id, name, description, owner_id, username, first_name, last_name, created_at in all_items:
            # Create a better display name for the owner
            if first_name and first_name.strip():
                owner_display = first_name.strip()
            elif username and username.strip():
                owner_display = username.strip()
            elif last_name and last_name.strip():
                owner_display = last_name.strip()
            else:
                owner_display = f"User {owner_id}"
            
            # Add item info
            text += f"• {name}\n"
            if description:
                text += f"  {description}\n"
            text += f"  📍 Currently with: {owner_display}\n"
            text += f"  📅 Added: {created_at[:10]}\n\n"
            
            # Add request button if not owned by current user
            if owner_id != user_id:
                keyboard.append([
                    InlineKeyboardButton(
                        f"🙋‍♂️ Request {name}", 
                        callback_data=f"request_{dgsc_id}"
                    )
                ])
        
        # Add note if user owns all items
        if not keyboard:
            text += "You currently own all DGSCs in the system."
        
        reply_markup = InlineKeyboardMarkup(keyboard) if keyboard else None
        await update.message.reply_text(text, reply_markup=reply_markup)
    
    async def add_dgsc_start(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        """Start the add DGSC conversation"""
        await update.message.reply_text(
            "📝 Let's add a new DGSC to the system!\n\n"
            "Please enter the name of the DGSC:"
        )
        return ADDING_DGSC_NAME
    
    async def add_dgsc_name(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        """Get DGSC name"""
        context.user_data['dgsc_name'] = update.message.text
        await update.message.reply_text(
            f"Great! Now please enter a description for '{update.message.text}':\n"
            "(You can also type 'skip' to leave it empty)"
        )
        return ADDING_DGSC_DESC
    
    async def add_dgsc_description(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        """Get DGSC description and save to database"""
        name = context.user_data['dgsc_name']
        description = update.message.text if update.message.text.lower() != 'skip' else ''
        user_id = update.effective_user.id
        
        success = self.db.add_dgsc(name, description, user_id)
        
        if success:
            await update.message.reply_text(
                f"✅ Successfully added '{name}' to the system!\n"
                f"You are now the owner of this DGSC.\n\n"
                f"Others can find it using `/search {name}`"
            )
        else:
            await update.message.reply_text(
                f"❌ Failed to add '{name}'. A DGSC with this name already exists.\n"
                "Please choose a different name."
            )
        
        return ConversationHandler.END
    
    async def my_requests_command(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        """Show user's pending requests"""
        user_id = update.effective_user.id
        requests = self.db.get_user_requests(user_id)
        
        if not requests:
            await update.message.reply_text(
                "📋 You haven't made any requests yet.\n"
                "Use /search to find items and request them!"
            )
            return
        
        text = "📋 Your Requests:\n\n"
        for req_id, dgsc_id, dgsc_name, owner_id, owner_username, owner_first_name, status, created_at in requests:
            # Create a better display name for the owner
            if owner_first_name and owner_first_name.strip():
                owner_display = owner_first_name.strip()
            elif owner_username and owner_username.strip():
                owner_display = owner_username.strip()
            else:
                owner_display = f"User {owner_id}"
                
            status_emoji = {"pending": "⏳", "accepted": "✅", "rejected": "❌"}.get(status, "❓")
            
            text += f"{status_emoji} {dgsc_name}\n"
            text += f"  From: {owner_display}\n"
            text += f"  Status: {status.title()}\n"
            text += f"  Requested: {created_at[:10]}\n\n"
        
        await update.message.reply_text(text)
    
    async def pending_requests_command(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        """Show pending requests for user's items"""
        user_id = update.effective_user.id
        requests = self.db.get_pending_requests_for_user(user_id)
        
        if not requests:
            await update.message.reply_text(
                "📬 No pending requests for your items.\n"
                "You'll be notified when someone requests your DGSCs!"
            )
            return
        
        text = "📬 Pending Requests for Your Items:\n\n"
        keyboard = []
        
        for req_id, dgsc_id, dgsc_name, requester_id, requester_username, requester_first_name, message, created_at in requests:
            # Create a better display name for the requester
            if requester_first_name and requester_first_name.strip():
                requester_display = requester_first_name.strip()
            elif requester_username and requester_username.strip():
                requester_display = requester_username.strip()
            else:
                requester_display = f"User {requester_id}"
            
            text += f"🙋‍♂️ {dgsc_name} requested by {requester_display}\n"
            if message:
                text += f"  Message: {message}\n"
            text += f"  Requested: {created_at[:10]}\n\n"
            
            keyboard.append([
                InlineKeyboardButton("✅ Accept", callback_data=f"accept_{req_id}"),
                InlineKeyboardButton("❌ Reject", callback_data=f"reject_{req_id}")
            ])
        
        reply_markup = InlineKeyboardMarkup(keyboard)
        await update.message.reply_text(text, reply_markup=reply_markup)
    
    async def request_item_start(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        """Start requesting an item"""
        query = update.callback_query
        await query.answer()
        
        dgsc_id = int(query.data.split('_')[1])
        context.user_data['requesting_dgsc_id'] = dgsc_id
        
        dgsc_info = self.db.get_dgsc_by_id(dgsc_id)
        if not dgsc_info:
            await query.edit_message_text("❌ This DGSC no longer exists.")
            return ConversationHandler.END
        
        dgsc_name = dgsc_info[1]
        # dgsc_info: (id, name, description, current_owner_id, username, first_name, last_name)
        owner_id = dgsc_info[3]
        username = dgsc_info[4]
        first_name = dgsc_info[5]
        last_name = dgsc_info[6] if len(dgsc_info) > 6 else None
        
        # Create a better display name for the owner
        if first_name and first_name.strip():
            owner_name = first_name.strip()
        elif username and username.strip():
            owner_name = username.strip()
        elif last_name and last_name.strip():
            owner_name = last_name.strip()
        else:
            owner_name = f"User {owner_id}"
        
        await query.edit_message_text(
            f"📝 You're requesting {dgsc_name} from {owner_name}.\n\n"
            f"Would you like to include a message with your request?\n"
            f"(Type your message or 'skip' to send without a message)"
        )
        
        return REQUESTING_MESSAGE
    
    async def request_item_message(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        """Handle request message and create the request"""
        message = update.message.text if update.message.text.lower() != 'skip' else ''
        dgsc_id = context.user_data['requesting_dgsc_id']
        requester_id = update.effective_user.id
        
        # Get DGSC info to find current owner
        dgsc_info = self.db.get_dgsc_by_id(dgsc_id)
        if not dgsc_info:
            await update.message.reply_text("❌ This DGSC no longer exists.")
            return ConversationHandler.END
        
        current_owner_id = dgsc_info[3]
        dgsc_name = dgsc_info[1]
        
        if current_owner_id == requester_id:
            await update.message.reply_text("❌ You already own this DGSC!")
            return ConversationHandler.END
        
        request_id = self.db.create_request(dgsc_id, requester_id, current_owner_id, message)
        
        await update.message.reply_text(
            f"✅ Your request for {dgsc_name} has been sent!\n"
            f"The current owner will be notified and can accept or reject your request.\n\n"
            f"Check the status anytime with /my_requests"
        )
        
        # Notify the owner (if they have a chat with the bot)
        try:
            owner_name = update.effective_user.first_name or update.effective_user.username
            notification_text = (
                f"🔔 New Request!\n\n"
                f"{owner_name} has requested your {dgsc_name}\n"
                f"Use /pending_requests to respond."
            )
            await context.bot.send_message(current_owner_id, notification_text)
        except Exception as e:
            logger.info(f"Could not notify user {current_owner_id}: {e}")
        
        return ConversationHandler.END
    
    async def handle_callback(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        """Handle inline keyboard callbacks"""
        query = update.callback_query
        await query.answer()
        
        data = query.data
        
        if data.startswith('accept_'):
            request_id = int(data.split('_')[1])
            success = self.db.accept_request(request_id)
            
            if success:
                await query.edit_message_text(
                    "✅ Request accepted! The DGSC ownership has been transferred.\n"
                    "Use /pending_requests to see other pending requests."
                )
            else:
                await query.edit_message_text("❌ Failed to accept request. It may have already been processed.")
        
        elif data.startswith('reject_'):
            request_id = int(data.split('_')[1])
            success = self.db.reject_request(request_id)
            
            if success:
                await query.edit_message_text(
                    "❌ Request rejected.\n"
                    "Use /pending_requests to see other pending requests."
                )
            else:
                await query.edit_message_text("❌ Failed to reject request. It may have already been processed.")
    
    async def cancel(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        """Cancel current conversation"""
        await update.message.reply_text("Operation cancelled.")
        return ConversationHandler.END
    
    def run(self):
        """Start the bot"""
        if not self.token:
            logger.error("BOT_TOKEN not found in environment variables!")
            return
        
        logger.info("Starting DGSC Tracker Bot...")
        
        # Build the application with explicit builder
        try:
            # builder = ApplicationBuilder()
            # builder.token(self.token)
            # application = builder.build()
            self.application = ApplicationBuilder().token(self.token).build()
            
            # Setup handlers after application is built
            self.setup_handlers()
            
            # Run the bot
            self.application.run_polling()
            
        except Exception as e:
            logger.error(f"Error running bot: {e}")
            raise

if __name__ == '__main__':
    bot = DGSCBot()
    bot.run()
