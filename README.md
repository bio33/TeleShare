# DGSC Tracker ### 🔧 Bot Commands
- `/start` - Initialize your account and see ### Requesting Items
1. Use `/list` to see all DGSCs or `/search <name>` to find specific ones
2. Click "Request" button for items you need
3. Optionally add a message explaining why you need it
4. Wait for the current owner to respond

### Managing Requests
1. Use `/pending_requests` to see incoming requests
2. Click "Accept" or "Reject" for each request
3. Accepted requests automatically transfer ownership
4. Check `/my_requests` to see your outgoing requests

## Database Schema

The bot uses SQLite with the following tables:

- **users**: Store Telegram user information
- **pendrives**: Track all registered DGSCs and current owners  
- **requests**: Handle transfer requests with status tracking
- **transactions**: Complete audit trail of all ownership changes/help` - Display help information and available commands
- `/my_items` - View all DGSCs you currently possess
- `/add_dgsc` - Register a new DGSC in the system
- `/list` - View all DGSCs in the system with current owners
- `/search <name>` - Search for DGSCs by name or description
- `/my_requests` - Check status of your pending requests
- `/pending_requests` - View and respond to incoming requests Bot

A Telegram bot for tracking and sharing physical DGSCs (Digital Storage Devices) among team members. This bot helps employees keep track of who has which DGSC, request items from colleagues, and maintain a complete history of all transfers.

## Features

### 🎯 Core Functionality
- **Possession Tracking**: See all items you currently own
- **Request System**: Send and receive requests for DGSCs
- **Search**: Find any DGSC and see who currently has it
- **List All Items**: View all DGSCs in the system with current owners and request buttons
- **Approval Workflow**: Accept or reject incoming requests
- **Transaction History**: Complete audit trail of all transfers
- **Real-time Notifications**: Get notified when someone requests your items

### 🔧 Bot Commands
- `/start` - Initialize your account and see welcome message
- `/help` - Display help information and available commands
- `/my_items` - View all pendrives you currently possess
- `/add_pendrive` - Register a new pendrive in the system
- `/search <name>` - Search for pendrives by name or description
- `/my_requests` - Check status of your pending requests
- `/pending_requests` - View and respond to incoming requests

## Setup Instructions

### Prerequisites
- Python 3.7 or higher
- A Telegram Bot Token (get from [@BotFather](https://t.me/botfather))

### Installation

1. **Clone or download this project**
   ```bash
   cd tele_share
   ```

2. **Install dependencies**
   ```bash
   pip install -r requirements.txt
   ```

3. **Configure environment variables**
   - Copy `.env` file and update with your bot token:
   ```
   BOT_TOKEN=your_actual_bot_token_here
   DATABASE_PATH=./dgsc_tracker.db
   ```

4. **Run the bot**
   ```bash
   python bot.py
   ```

### Getting a Bot Token
1. Open Telegram and search for [@BotFather](https://t.me/botfather)
2. Start a chat and send `/newbot`
3. Follow the instructions to create your bot
4. Copy the provided token to your `.env` file

## Usage Workflow

### For New Users
1. Start a chat with your bot
2. Send `/start` to register your account
3. Use `/help` to see available commands

### Adding DGSCs
1. Use `/add_dgsc` command
2. Enter the DGSC name when prompted
3. Optionally add a description
4. The DGSC is automatically assigned to you

### Requesting Items
1. Use `/search <name>` to find pendrives
2. Click "Request" button for items you need
3. Optionally add a message explaining why you need it
4. Wait for the current owner to respond

### Managing Requests
1. Use `/pending_requests` to see incoming requests
2. Click "Accept" or "Reject" for each request
3. Accepted requests automatically transfer ownership
4. Check `/my_requests` to see your outgoing requests

## Database Schema

The bot uses SQLite with the following tables:

- **users**: Store Telegram user information
- **pendrives**: Track all registered pendrives and current owners  
- **requests**: Handle transfer requests with status tracking
- **transactions**: Complete audit trail of all ownership changes

## File Structure

```
tele_share/
├── bot.py              # Main bot application
├── database.py         # Database operations and models
├── requirements.txt    # Python dependencies
├── .env               # Environment configuration
└── README.md          # This file
```

## Development

### Running in Development
```bash
python bot.py
```

### Adding New Features
The bot architecture supports easy extension:
- Add new commands in `bot.py`
- Extend database schema in `database.py`
- Use conversation handlers for multi-step interactions

### Error Handling
- Database operations include proper error handling
- Users receive friendly error messages
- Logging is configured for debugging

## Troubleshooting

### Common Issues
1. **Bot not responding**: Check if your bot token is correct
2. **Database errors**: Ensure write permissions in the project directory
3. **Users not getting notifications**: They need to start a conversation with the bot first

### Logs
The bot logs important events to the console. Check for error messages if something isn't working.

## Security Considerations

- Bot token should be kept secret
- Database file contains user information - secure appropriately
- Consider user privacy when deploying in production

## License

This project is provided as-is for educational and internal use purposes.
