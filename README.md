# Republic AI Testnet Node & Validator Setup Guide

This guide has been prepared for those who want to set up a Republic AI Testnet node from scratch and become a validator. Simply follow the steps below in order.

---

## System Requirements

| Component | Requirement |
|-----------|-------------|
| CPU | Minimum 4 cores |
| RAM | Minimum 8 GB |
| Disk | Minimum 200 GB SSD |
| OS | Ubuntu 22.04 / 24.04 LTS |

---

## 1. Connect to Your Server

```bash
ssh root@YOUR_SERVER_IP
```

---

## 2. Update System

```bash
sudo apt update && sudo apt upgrade -y
sudo apt install -y curl wget git jq build-essential
```

---

## 3. Install Binary

```bash
wget -O /usr/local/bin/republicd <BINARY_URL>
chmod +x /usr/local/bin/republicd
republicd version
```

---

## 4. Initialize Node

```bash
republicd init "YOUR_MONIKER" --chain-id raitestnet_77701-1 --home $HOME/.republicd
```

Download genesis file:

```bash
wget -O $HOME/.republicd/config/genesis.json <GENESIS_URL>
```

---

## 5. Wallet Setup

Create a new wallet:

```bash
republicd keys add YOUR_WALLET --home $HOME/.republicd
```

> ⚠️ **Save your mnemonic phrase (24 words) in a safe place. You cannot recover your wallet without it.**

Recover an existing wallet:

```bash
republicd keys add YOUR_WALLET --recover --home $HOME/.republicd
```

Check your wallet:

```bash
republicd keys list --home $HOME/.republicd
```

---

## 6. Create System Service

```bash
sudo tee /etc/systemd/system/republicd.service > /dev/null <<EOF
[Unit]
Description=Republic Protocol Node
After=network-online.target

[Service]
User=root
WorkingDirectory=/root
ExecStart=/usr/local/bin/republicd start --home /root/.republicd --chain-id raitestnet_77701-1
Restart=always
RestartSec=3
LimitNOFILE=65535

[Install]
WantedBy=multi-user.target
EOF
```

Enable and start the service:

```bash
sudo systemctl daemon-reload
sudo systemctl enable republicd
sudo systemctl start republicd
```

Check node status:

```bash
systemctl status republicd
```

Follow logs:

```bash
journalctl -u republicd -f
```

---

## 7. Create Validator

```bash
republicd tx staking create-validator \
  --amount 1000000000000000000arai \
  --from YOUR_WALLET \
  --commission-rate 0.1 \
  --commission-max-rate 0.2 \
  --commission-max-change-rate 0.01 \
  --min-self-delegation 1 \
  --moniker "YOUR_MONIKER" \
  --chain-id raitestnet_77701-1 \
  --home $HOME/.republicd \
  --gas auto \
  --gas-adjustment 1.5 \
  --fees 200000000000000000arai \
  -y
```

---

## 8. Useful Commands

Check sync status:

```bash
republicd status --home $HOME/.republicd | jq .sync_info
```

Check validator status:

```bash
republicd query staking validator YOUR_VALIDATOR_ADDR --home $HOME/.republicd | grep -E "jailed|status"
```

Check account balance:

```bash
republicd query bank balances YOUR_WALLET_ADDRESS --home $HOME/.republicd
```

Check account sequence:

```bash
republicd query auth account YOUR_WALLET_ADDRESS --home $HOME/.republicd
```

---

## 9. Unjail Validator

If your validator gets jailed (e.g. due to downtime), follow these steps:

**Step 1:** Check if your wallet is loaded:

```bash
republicd keys list --home $HOME/.republicd
```

**Step 2:** If empty, recover your wallet with mnemonic:

```bash
republicd keys add YOUR_WALLET --recover --home $HOME/.republicd
```

**Step 3:** Watch the account sequence until it stabilizes:

```bash
watch -n 5 "republicd query auth account YOUR_WALLET_ADDRESS --home $HOME/.republicd | grep sequence"
```

**Step 4:** Send the unjail transaction:

```bash
republicd tx slashing unjail \
  --from YOUR_WALLET \
  --chain-id raitestnet_77701-1 \
  --home $HOME/.republicd \
  --gas auto \
  --gas-adjustment 1.5 \
  --fees 200000000000000000arai \
  -y
```

**Step 5:** Confirm validator is active:

```bash
republicd query staking validator YOUR_VALIDATOR_ADDR --home $HOME/.republicd | grep -E "jailed|status"
```

Expected result:

```
jailed: false
status: BOND_STATUS_BONDED
```

---

## 10. Common Errors & Solutions

| Error | Cause | Solution |
|-------|-------|----------|
| `command not found` | Binary not installed or not in PATH | Check with `systemctl cat republicd.service` |
| `No records in keyring` | Wallet not imported | Recover wallet with mnemonic |
| `account sequence mismatch` | Pending tx in mempool | Wait and watch sequence with `watch` command |
| `provided fee < minimum global fee` | Fee too low | Use `--fees 200000000000000000arai` |
| `validator not jailed` | Unjail already succeeded | Check status — validator is BONDED ✅ |

---

## 11. Remove Node

```bash
sudo systemctl stop republicd
sudo systemctl disable republicd
sudo rm /etc/systemd/system/republicd.service
sudo rm /usr/local/bin/republicd
rm -rf $HOME/.republicd
```

---

> Made with ❤️ by **MisterNeo**
> Chain ID: `raitestnet_77701-1`

---

## 🤖 Discord Validator Bot

A Discord bot for monitoring your RAI Network validator node in real-time.

### Commands

| Command | Description |
|---------|-------------|
| `/status` | Show validator status (jailed/bonded) |
| `/balance` | Show wallet balance |
| `/rank` | Show total validators and your token count |
| `/check <name or address>` | Check any validator by name or address |
| `/uptime` | Show signing uptime and missed blocks |
| `/commission` | Show earned commission |
| `/rewards` | Show accumulated rewards |
| `/blockheight` | Show current block height |
| `/peers` | Show connected peer count |
| `/alert` | Enable jail alert notifications |
| `/commands` | Show all available commands |

---

### Bot Setup

#### 1. Create Discord Bot

1. Go to [discord.com/developers/applications](https://discord.com/developers/applications)
2. Click **"New Application"** → Name it (e.g. `RAI Validator Bot`)
3. Go to **"Bot"** → Click **"Reset Token"** → Copy your token
4. Enable **"Message Content Intent"** under Privileged Gateway Intents
5. Go to **"OAuth2"** → **"OAuth2 URL Generator"** → Select **"bot"** + **"Administrator"**
6. Open the generated link and add the bot to your server

#### 2. Install Dependencies

```bash
apt install python3 python3-pip -y
pip3 install discord.py --break-system-packages
```

#### 3. Create Bot File

```bash
nano /root/rai_bot.py
```

Paste the bot code and set your token:

```python
TOKEN = "YOUR_DISCORD_BOT_TOKEN"
VALIDATOR_ADDR = "YOUR_VALIDATOR_ADDRESS"
WALLET_ADDR = "YOUR_WALLET_ADDRESS"
```

#### 4. Create System Service

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

#### 5. Check Bot Status

```bash
systemctl status rai_bot
journalctl -u rai_bot -f
```

---

> Made with ❤️ by **MisterNeo**
> Chain ID: `raitestnet_77701-1`

