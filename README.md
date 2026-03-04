# 🤖 RAI Validator Discord Bot

A Discord bot for monitoring your RAI Network validator node in real-time.

---

## Commands

| Command | Description |
|---------|-------------|
| `/status` | Show validator status (jailed/bonded) |
| `/balance` | Show wallet balance |
| `/rank` | Show total validators and your token count |
| `/check <name or address>` | Check any validator by name or validator address |
| `/uptime` | Show signing uptime and missed blocks |
| `/commission` | Show earned commission |
| `/rewards` | Show accumulated rewards |
| `/blockheight` | Show current block height |
| `/peers` | Show connected peer count |
| `/alert` | Enable jail alert notifications |
| `/commands` | Show all available commands |

---

## Setup Guide

### 1. Create Discord Bot

1. Go to [discord.com/developers/applications](https://discord.com/developers/applications)
2. Click **"New Application"** → Name it (e.g. `RAI Validator Bot`)
3. Go to **"Bot"** → Click **"Reset Token"** → Copy your token
4. Enable **"Message Content Intent"** under Privileged Gateway Intents
5. Go to **"OAuth2"** → **"OAuth2 URL Generator"** → Select **"bot"** + **"Administrator"**
6. Open the generated link and add the bot to your server

### 2. Install Dependencies

```bash
apt install python3 python3-pip -y
pip3 install discord.py --break-system-packages
```

### 3. Configure Bot

Open `rai_bot.py` and set your details:

```python
TOKEN = "YOUR_DISCORD_BOT_TOKEN"
VALIDATOR_ADDR = "YOUR_VALIDATOR_ADDRESS"    # raivaloper1xxx
WALLET_ADDR = "YOUR_WALLET_ADDRESS"          # rai1xxx
```

### 4. Create System Service

```bash
sudo tee /etc/systemd/system/rai_bot.service > /dev/null <<EOF
[Unit]
Description=RAI Validator Discord Bot
After=network-online.target

[Service]
User=root
WorkingDirectory=/root
ExecStart=/usr/bin/python3 /root/rai_bot.py
Restart=always
RestartSec=3

[Install]
WantedBy=multi-user.target
EOF

sudo systemctl daemon-reload
sudo systemctl enable rai_bot
sudo systemctl start rai_bot
```

### 5. Check Status

```bash
# Check if bot is running
systemctl status rai_bot

# Follow logs
journalctl -u rai_bot -f
```

---

## Common Errors

| Error | Solution |
|-------|----------|
| `CommandNotFound` | Check command name in bot file |
| `PrivilegedIntentsRequired` | Enable Message Content Intent in Developer Portal |
| `LoginFailure` | Reset token and update in bot file |

---

> Made with ❤️ by **MisterNeo**
> Chain ID: `raitestnet_77701-1`
