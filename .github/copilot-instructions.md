<!-- Use this file to provide workspace-specific custom instructions to Copilot. For more details, visit https://code.visualstudio.com/docs/copilot/copilot-customization#_use-a-githubcopilotinstructionsmd-file -->

# DGSC Tracker Telegram Bot

This is a Python-based Telegram bot for tracking shared physical DGSCs among employees.

## Key Features:
- User registration and authentication via Telegram
- DGSC registration and ownership tracking
- Request/approval system for transferring items
- Search functionality for finding DGSCs
- Complete transaction history in SQLite database
- Real-time notifications for requests

## Architecture:
- `bot.py`: Main bot logic with Telegram handlers
- `database.py`: SQLite database operations and models
- Uses python-telegram-bot library for Telegram API
- Conversation handlers for multi-step interactions
- Inline keyboards for interactive responses

## Database Schema:
- `users`: Store Telegram user information
- `pendrives`: Track all registered DGSCs and current owners
- `requests`: Handle transfer requests with status tracking
- `transactions`: Complete audit trail of all ownership changes

## Best Practices:
- Use proper error handling for database operations
- Follow Telegram bot conversation patterns
- Maintain data consistency during transfers
- Include user-friendly messages and help text
- Log important events for debugging
