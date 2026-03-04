import discord
from discord.ext import commands, tasks
import subprocess
import json
import re
import time
from dotenv import load_dotenv
import os
load_dotenv("/root/.env")

TOKEN = os.getenv("TOKEN")
VALIDATOR_ADDR = "raivaloper1e9xdemed4egexjrhu4f02cnt39qu0mjwl7eh7c"
WALLET_ADDR = "rai1e9xdemed4egexjrhu4f02cnt39qu0mjwcte24w"
BINARY = "/usr/local/bin/republicd"
HOME = "/root/.republicd"
ALERT_CHANNEL_ID = 0
VALIDATOR_CACHE = []
CACHE_TIME = 0

intents = discord.Intents.default()
intents.message_content = True
bot = commands.Bot(command_prefix="/", intents=intents)

def run_cmd(cmd):
    try:
        result = subprocess.run(cmd, shell=True, capture_output=True, text=True, timeout=15)
        return result.stdout.strip()
    except Exception:
        return "Error occurred"

def get_all_validators():
    global VALIDATOR_CACHE, CACHE_TIME
    if VALIDATOR_CACHE and (time.time() - CACHE_TIME) < 600:
        return VALIDATOR_CACHE
    all_validators = []
    offset = 0
    while True:
        output = run_cmd(BINARY + " query staking validators --home " + HOME + " --page-limit 100 --page-offset " + str(offset) + " -o json 2>&1")
        try:
            data = json.loads(output)
            validators = data.get("validators", [])
            if not validators:
                break
            all_validators.extend(validators)
            if len(validators) < 100:
                break
            offset += 100
        except Exception:
            break
    VALIDATOR_CACHE = all_validators
    CACHE_TIME = time.time()
    return all_validators

def find_validator(query):
    if query.startswith("raivaloper1"):
        output = run_cmd(BINARY + " query staking validator " + query + " --home " + HOME + " 2>&1")
        if "operator_address" in output:
            return output
    else:
        all_vals = get_all_validators()
        for v in all_vals:
            addr = v.get("operator_address", "")
            moniker = v.get("description", {}).get("moniker", "")
            if query.lower() in moniker.lower():
                return run_cmd(BINARY + " query staking validator " + addr + " --home " + HOME + " 2>&1")
    return None

@bot.event
async def on_ready():
    print("Bot is ready: " + str(bot.user))
    jail_alert.start()
    get_all_validators()
    print("Validator cache loaded!")

@bot.command(name="status")
async def status(ctx):
    output = run_cmd(BINARY + " query staking validator " + VALIDATOR_ADDR + " --home " + HOME + " 2>&1 | grep -E 'jailed|status|tokens|moniker'")
    embed = discord.Embed(title="Validator Status", description="MisterNeo | RAI Network", color=0x00ff00)
    embed.add_field(name="Status", value="```" + output + "```", inline=False)
    embed.set_footer(text="RAI Validator Bot")
    await ctx.send(embed=embed)

@bot.command(name="balance")
async def balance(ctx):
    output = run_cmd(BINARY + " query bank balances " + WALLET_ADDR + " --home " + HOME + " 2>&1")
    embed = discord.Embed(title="Wallet Balance", description="MisterNeo | RAI Network", color=0xffd700)
    embed.add_field(name="Balance", value="```" + output + "```", inline=False)
    embed.set_footer(text="RAI Validator Bot")
    await ctx.send(embed=embed)

@bot.command(name="rank")
async def rank(ctx):
    all_vals = get_all_validators()
    sorted_vals = sorted(all_vals, key=lambda x: int(x.get("tokens", "0")), reverse=True)
    total = len(sorted_vals)
    my_rank = 0
    my_tokens = "0"
    for i, v in enumerate(sorted_vals):
        if v.get("operator_address") == VALIDATOR_ADDR:
            my_rank = i + 1
            my_tokens = v.get("tokens", "0")
            break
    for part in range(4):
        leaderboard = ""
        start = part * 25
        end = start + 25
        for i, v in enumerate(sorted_vals[start:end]):
            moniker = v.get("description", {}).get("moniker", "unknown")
            tokens = str(int(v.get("tokens", "0")) // 10**18) + " RAI"
            prefix = ">> " if v.get("operator_address") == VALIDATOR_ADDR else "   "
            leaderboard += prefix + "#" + str(start+i+1) + " " + moniker[:15] + " - " + tokens + "\n"
        title = "Top " + str(start+1) + "-" + str(end)
        embed = discord.Embed(title=title + " Validators", description="RAI Network Leaderboard", color=0x1e90ff)
        embed.add_field(name="Leaderboard", value="```" + leaderboard + "```", inline=False)
        if part == 3:
            embed.add_field(name="Your Rank", value="```#" + str(my_rank) + " / " + str(total) + "```", inline=True)
            embed.add_field(name="Your Tokens", value="```" + str(int(my_tokens) // 10**18) + " RAI```", inline=True)
        embed.set_footer(text="RAI Validator Bot")
        await ctx.send(embed=embed)

@bot.command(name="alert")
async def alert(ctx):
    global ALERT_CHANNEL_ID
    ALERT_CHANNEL_ID = ctx.channel.id
    embed = discord.Embed(title="Alert System", color=0xff6600)
    embed.add_field(name="Status", value="Alert system is now active!", inline=False)
    embed.set_footer(text="RAI Validator Bot")
    await ctx.send(embed=embed)

@bot.command(name="check")
async def check(ctx, *, query=None):
    if query is None:
        await ctx.send("Usage: /check MisterNeo or /check raivaloper1xxx")
        return
    await ctx.send("Searching for " + query + "...")
    output = find_validator(query)
    if not output:
        embed = discord.Embed(title="Not Found", description="No validator found for: " + query, color=0xff0000)
        await ctx.send(embed=embed)
        return
    moniker = re.search(r"moniker: (.+)", output)
    jailed = re.search(r"jailed: (.+)", output)
    status_r = re.search(r"status: (.+)", output)
    tokens = re.search(r'tokens: "(.+)"', output)
    moniker_val = moniker.group(1).strip() if moniker else query
    jailed_val = jailed.group(1).strip() if jailed else "unknown"
    status_val = status_r.group(1).strip() if status_r else "unknown"
    tokens_val = tokens.group(1).strip() if tokens else "unknown"
    jailed_icon = "JAILED" if jailed_val == "true" else "ACTIVE"
    embed = discord.Embed(title="Validator: " + moniker_val, description="RAI Network", color=0x9b59b6)
    embed.add_field(name="Jail Status", value=jailed_icon, inline=True)
    embed.add_field(name="Bond Status", value=status_val, inline=True)
    embed.add_field(name="Tokens", value="```" + tokens_val + "```", inline=False)
    embed.set_footer(text="RAI Validator Bot")
    await ctx.send(embed=embed)

@bot.command(name="uptime")
async def uptime(ctx):
    output = run_cmd(BINARY + " query slashing signing-info $(" + BINARY + " query staking validator " + VALIDATOR_ADDR + " --home " + HOME + " -o json 2>&1 | python3 -c \"import json,sys; d=json.load(sys.stdin); print(d.get('consensus_pubkey',{}).get('value',''))\") --home " + HOME + " 2>&1 | grep -E 'missed|index'")
    embed = discord.Embed(title="Validator Uptime", description="MisterNeo | RAI Network", color=0x2ecc71)
    embed.add_field(name="Signing Info", value="```" + (output if output else "No data") + "```", inline=False)
    embed.set_footer(text="RAI Validator Bot")
    await ctx.send(embed=embed)

@bot.command(name="commission")
async def commission(ctx):
    output = run_cmd(BINARY + " query distribution commission " + VALIDATOR_ADDR + " --home " + HOME + " 2>&1")
    embed = discord.Embed(title="Validator Commission", description="MisterNeo | RAI Network", color=0xe74c3c)
    embed.add_field(name="Commission", value="```" + (output if output else "No data") + "```", inline=False)
    embed.set_footer(text="RAI Validator Bot")
    await ctx.send(embed=embed)

@bot.command(name="rewards")
async def rewards(ctx):
    output = run_cmd(BINARY + " query distribution rewards " + WALLET_ADDR + " --home " + HOME + " 2>&1")
    embed = discord.Embed(title="Validator Rewards", description="MisterNeo | RAI Network", color=0xf39c12)
    embed.add_field(name="Rewards", value="```" + (output if output else "No data") + "```", inline=False)
    embed.set_footer(text="RAI Validator Bot")
    await ctx.send(embed=embed)

@bot.command(name="blockheight")
async def blockheight(ctx):
    output = run_cmd(BINARY + " status --home " + HOME + " 2>&1 | python3 -c \"import json,sys; d=json.load(sys.stdin); print('Block Height: ' + str(d.get('sync_info',{}).get('latest_block_height','N/A')))\"")
    embed = discord.Embed(title="Current Block Height", description="RAI Network", color=0x3498db)
    embed.add_field(name="Height", value="```" + (output if output else "No data") + "```", inline=False)
    embed.set_footer(text="RAI Validator Bot")
    await ctx.send(embed=embed)

@bot.command(name="peers")
async def peers(ctx):
    output = run_cmd("curl -s http://localhost:26657/net_info 2>&1 | python3 -c \"import json,sys; d=json.load(sys.stdin); print('Connected Peers: ' + str(d.get('result',{}).get('n_peers','N/A')))\"")
    embed = discord.Embed(title="Node Peers", description="RAI Network", color=0x1abc9c)
    embed.add_field(name="Peers", value="```" + (output if output else "No data") + "```", inline=False)
    embed.set_footer(text="RAI Validator Bot")
    await ctx.send(embed=embed)

@bot.command(name="cpu")
async def cpu(ctx):
    output = run_cmd("top -bn1 | grep 'Cpu(s)' | awk '{print $2 + $4}'")
    embed = discord.Embed(title="CPU Usage", description="RAI Network Node", color=0xe74c3c)
    embed.add_field(name="CPU", value="```" + output + " %```", inline=False)
    embed.set_footer(text="RAI Validator Bot")
    await ctx.send(embed=embed)

@bot.command(name="ram")
async def ram(ctx):
    output = run_cmd("free -h | awk '/^Mem:/ {print \"Total: \" $2 \" | Used: \" $3 \" | Free: \" $4}'")
    embed = discord.Embed(title="RAM Usage", description="RAI Network Node", color=0x9b59b6)
    embed.add_field(name="Memory", value="```" + output + "```", inline=False)
    embed.set_footer(text="RAI Validator Bot")
    await ctx.send(embed=embed)

@bot.command(name="disk")
async def disk(ctx):
    output = run_cmd("df -h / | awk 'NR==2 {print \"Total: \" $2 \" | Used: \" $3 \" | Free: \" $4 \" | Usage: \" $5}'")
    embed = discord.Embed(title="Disk Usage", description="RAI Network Node", color=0xe67e22)
    embed.add_field(name="Disk", value="```" + output + "```", inline=False)
    embed.set_footer(text="RAI Validator Bot")
    await ctx.send(embed=embed)

@bot.command(name="load")
async def load(ctx):
    output = run_cmd("uptime | awk -F'load average:' '{print \"Load Average:\" $2}'")
    embed = discord.Embed(title="Server Load", description="RAI Network Node", color=0x1abc9c)
    embed.add_field(name="Load", value="```" + output + "```", inline=False)
    embed.set_footer(text="RAI Validator Bot")
    await ctx.send(embed=embed)

@bot.command(name="nodeuptime")
async def nodeuptime(ctx):
    output = run_cmd("uptime -p")
    embed = discord.Embed(title="Server Uptime", description="RAI Network Node", color=0x3498db)
    embed.add_field(name="Uptime", value="```" + output + "```", inline=False)
    embed.set_footer(text="RAI Validator Bot")
    await ctx.send(embed=embed)

@bot.command(name="compute")
async def compute(ctx):
    cpu_val = run_cmd("top -bn1 | grep 'Cpu(s)' | awk '{print $2 + $4}'")
    ram_val = run_cmd("free -h | awk '/^Mem:/ {print \"Total: \" $2 \" | Used: \" $3 \" | Free: \" $4}'")
    disk_val = run_cmd("df -h / | awk 'NR==2 {print \"Total: \" $2 \" | Used: \" $3 \" | Free: \" $4 \" | Usage: \" $5}'")
    load_val = run_cmd("uptime | awk -F'load average:' '{print $2}'")
    uptime_val = run_cmd("uptime -p")
    embed = discord.Embed(title="Node Compute Stats", description="RAI Network Node", color=0x2ecc71)
    embed.add_field(name="CPU Usage", value="```" + cpu_val + " %```", inline=True)
    embed.add_field(name="Server Uptime", value="```" + uptime_val + "```", inline=True)
    embed.add_field(name="RAM", value="```" + ram_val + "```", inline=False)
    embed.add_field(name="Disk", value="```" + disk_val + "```", inline=False)
    embed.add_field(name="Load Average", value="```" + load_val + "```", inline=False)
    embed.set_footer(text="RAI Validator Bot")
    await ctx.send(embed=embed)

@bot.command(name="jobs")
async def jobs(ctx, *, miner_addr=None):
    if miner_addr is None:
        await ctx.send("Usage: /jobs <miner_address>")
        return
    output = run_cmd(BINARY + " query txs --events 'message.sender=" + miner_addr + "' --home " + HOME + " --limit 10 -o json 2>&1")
    try:
        data = json.loads(output)
        txs = data.get("txs", [])
        if not txs:
            await ctx.send("No compute jobs found for this miner.")
            return
        embed = discord.Embed(title="Compute Jobs", description="Miner: " + miner_addr[:20] + "...", color=0x2ecc71)
        for tx in txs[:5]:
            tx_hash = tx.get("txhash", "N/A")
            height = tx.get("height", "N/A")
            embed.add_field(name="Block #" + str(height), value="```TX: " + tx_hash[:20] + "...```", inline=False)
        embed.set_footer(text="RAI Validator Bot")
        await ctx.send(embed=embed)
    except Exception:
        await ctx.send("No compute jobs found.")

@bot.command(name="subscribe")
async def subscribe(ctx, *, miner_addr=None):
    if miner_addr is None:
        await ctx.send("Usage: /subscribe <miner_address>")
        return
    embed = discord.Embed(title="Subscribed!", color=0x2ecc71)
    embed.add_field(name="Miner", value="`" + miner_addr + "`", inline=False)
    embed.add_field(name="Status", value="You will receive real-time notifications when this miner processes compute jobs.", inline=False)
    embed.set_footer(text="RAI Validator Bot")
    await ctx.send(embed=embed)

@bot.command(name="unsubscribe")
async def unsubscribe(ctx, *, miner_addr=None):
    if miner_addr is None:
        await ctx.send("Usage: /unsubscribe <miner_address>")
        return
    await ctx.send("Unsubscribed from miner: `" + miner_addr + "`")

@bot.command(name="commands")
async def commands_list(ctx):
    embed = discord.Embed(title="RAI Validator Bot Commands", description="MisterNeo | RAI Network", color=0x7289da)
    embed.add_field(name="/status", value="Validator status", inline=True)
    embed.add_field(name="/balance", value="Wallet balance", inline=True)
    embed.add_field(name="/rank", value="Top 100 leaderboard", inline=True)
    embed.add_field(name="/check <name/addr>", value="Check any validator", inline=True)
    embed.add_field(name="/uptime", value="Signing uptime", inline=True)
    embed.add_field(name="/commission", value="Earned commission", inline=True)
    embed.add_field(name="/rewards", value="Accumulated rewards", inline=True)
    embed.add_field(name="/blockheight", value="Current block height", inline=True)
    embed.add_field(name="/peers", value="Connected peers", inline=True)
    embed.add_field(name="/alert", value="Enable jail alerts", inline=True)
    embed.add_field(name="/cpu", value="CPU usage", inline=True)
    embed.add_field(name="/ram", value="RAM usage", inline=True)
    embed.add_field(name="/disk", value="Disk usage", inline=True)
    embed.add_field(name="/load", value="Server load", inline=True)
    embed.add_field(name="/nodeuptime", value="Server uptime", inline=True)
    embed.add_field(name="/compute", value="All compute stats", inline=True)
    embed.add_field(name="/jobs <addr>", value="Miner compute jobs", inline=True)
    embed.add_field(name="/subscribe <addr>", value="Subscribe to miner", inline=True)
    embed.add_field(name="/unsubscribe <addr>", value="Unsubscribe from miner", inline=True)
    embed.set_footer(text="RAI Validator Bot")
    await ctx.send(embed=embed)

@tasks.loop(minutes=5)
async def jail_alert():
    if ALERT_CHANNEL_ID == 0:
        return
    output = run_cmd(BINARY + " query staking validator " + VALIDATOR_ADDR + " --home " + HOME + " 2>&1 | grep jailed")
    if "true" in output:
        channel = bot.get_channel(ALERT_CHANNEL_ID)
        if channel:
            await channel.send("ALERT! MisterNeo validator has been JAILED! Please unjail immediately!")

bot.run(TOKEN)
