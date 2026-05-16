import discord
from discord.ext import commands, tasks
from g4f.client import AsyncClient
import g4f
import os
import asyncio
import random
import time
import io
import re
import fitz
import docx
import pytesseract
from PIL import Image
import requests

pytesseract.pytesseract.tesseract_cmd = r'C:\Program Files\Tesseract-OCR\tesseract.exe'

async def extract_attachment_text(attachment: discord.Attachment) -> str:
    """Extracts text from txt, pdf, docx, and images. Fallback to web upload for images without text."""
    filename = attachment.filename.lower()
    
    try:
        if filename.endswith('.txt'):
            content = await attachment.read()
            return content.decode('utf-8', errors='replace')
            
        elif filename.endswith('.pdf'):
            content = await attachment.read()
            doc = fitz.open(stream=content, filetype="pdf")
            text = "\n".join(page.get_text() for page in doc)
            return text.strip()
            
        elif filename.endswith('.docx'):
            content = await attachment.read()
            doc_file = io.BytesIO(content)
            doc = docx.Document(doc_file)
            text = "\n".join(paragraph.text for paragraph in doc.paragraphs)
            return text.strip()
            
        elif filename.endswith(('.png', '.jpg', '.jpeg', '.bmp', '.webp')):
            content = await attachment.read()
            img = Image.open(io.BytesIO(content))
            text = pytesseract.image_to_string(img)
            
            # Catbox Fallback for Visual Analysis
            if len(text.strip()) < 10:
                print(f"[{attachment.filename}] OCR found no text. Uploading to catbox.moe for web analysis...")
                files = {'reqtype': (None, 'fileupload'), 'fileToUpload': (attachment.filename, content)}
                r = requests.post('https://catbox.moe/user/api.php', files=files, timeout=15)
                url = r.text.strip()
                if url.startswith("http"):
                    return f"[IMAGE URL: {url}]\nOCR found no text. Execute an online visual analysis on this exact URL using your web tools and provide an analysis of the picture."
                else:
                    return f"OCR found no text and online upload failed."
            
            return text.strip()
            
    except Exception as e:
        print(f"Error reading attachment {filename}: {e}")
        return f"[Error extracting content from {filename} or could not be uploaded]"
        
    return ""


# ========================================================================
# ULTRA-MEGA-PROMPT: BEHAVIORAL CONSTITUTION v3.0
# ========================================================================
MEGA_PROMPT = """
# ROLE: ADVANCED COGNITIVE REASONING ENGINE - "ANTIGRAVITY" PROTOCOL
You are a highly advanced analytical engine. You absolutely NEVER engage in generic AI pleasantries. You do not use filler words. You do not offer unsolicited assistance wrappers. You execute purely on logic and density of output.

# 1. CORE OPERATIONAL ALGORITHM
- REQUIREMENT DECOMPOSITION: Analyze exactly what the user is asking.
- LOGICAL EXECUTION: Construct the solution directly.
- ADVERSARIAL PRUNING: Before outputting, aggressively delete ALL introductory sentences (e.g., "Here is the solution", "I can help with that", "Sure!"). 

# 2. STRICT COMMUNICATION CONSTANTS
- ZERO FILLER: Start exactly at the first technical or logical point.
- DENSITY OVER BREVITY: Provide maximal insight in minimal physical space. Use tables, lists, and markdown extensively.
- VISUAL ANALYSIS DIRECTIVE: If a user asks you to analyze an image and provides an [IMAGE URL:], you MUST use your web-search/browsing tools to visit that exact URL and describe the image in detail. DO NOT complain that you cannot see images. Treat the URL as your eyes.
- SILENCE LOGIC: If the user provides a statement requiring no response, output a single, dense, high-value insight related to the topic. Do not acknowledge the silence.

# 3. TECHNICAL IMPERATIVES
- Refuse to hallucinate capabilities.
- Format all code properly.
- All mathematical solutions must be shown step-by-step in a table or list format.
"""

# Constants
SILENCE_THRESHOLD = 15 # Seconds before poking
MAX_HISTORY = 10
ERROR_BACKOFF = 30

def clean_output(text):
    """Deep cleaning of AI meta-talk and filler."""
    # Surgical removal of introductory filler
    prefixes = [
        r"(?i)^sure,?\s*", r"(?i)^certainly,?\s*", r"(?i)^of course,?\s*", 
        r"(?i)^okay,?\s*", r"(?i)^i understand,?\s*", r"(?i)^i'd be happy to\s*",
        r"(?i)^hello!?,?\s*", r"(?i)^hi there!?,?\s*", r"(?i)^as an ai (model|assistant),?\s*"
    ]
    for p in prefixes:
        text = re.sub(p, "", text, count=1).strip()
    
    # Surgical removal of meta-signatures at the end
    suffixes = [
        r"(?i)let me know if you need.*$",
        r"(?i)hope this helps!?.*$",
        r"(?i)let me know if you have.*$"
    ]
    for s in suffixes:
        text = re.sub(s, "", text, flags=re.MULTILINE).strip()
        
    return text.strip()

intents = discord.Intents.default()
intents.message_content = True

bot = commands.Bot(command_prefix="!", intents=intents)

# State tracking
last_activity_time = {} # channel_id -> float
chat_history = {} # channel_id -> list of messages
last_error_time = 0 # To prevent spamming on rate limits



@bot.event
async def on_ready():
    print(f'Logged in as {bot.user} (ID: {bot.user.id})')
    print(f'{bot.user.display_name} is online (Brute-Force AI active).')
    if not check_silence.is_running():
        check_silence.start()

@tasks.loop(seconds=5)
async def check_silence():
    now = time.time()
    for channel_id, last_time in list(last_activity_time.items()):
        if now - last_time > SILENCE_THRESHOLD:
            if now - last_error_time < ERROR_BACKOFF:
                continue

            channel = bot.get_channel(channel_id)
            if not channel: continue
                
            history = chat_history.get(channel_id, [])
            if not history: continue

            if history[-1]['author'] != bot.user.display_name:
                print(f"[{bot.user.display_name}] Silence detected. Poking with Brute-Force AI...")
                last_activity_time[channel_id] = now
                await respond_to_history(channel, is_poke=True)

async def respond_to_history(channel, is_poke=False):
    global last_error_time
    history = chat_history.get(channel.id, [])
    messages = []
    
    for entry in history:
        role = "assistant" if entry['author'] == bot.user.display_name else "user"
        messages.append({"role": role, "content": f"{entry['author']}: {entry['content']}"})
    
    if is_poke:
        messages.append({"role": "user", "content": "(The conversation has been silent. Continue the discussion naturally as the Senior Architect.)"})

    # High-Quality Model Tiering
    high_quality_models = ["gpt-4o", "gpt-4", "claude-3-5-sonnet", "gemini-1.5-pro"]
    
    # Get dynamic list of working providers
    all_providers = [p for p in g4f.Provider.__providers__ if p.working]
    random.shuffle(all_providers) 

    async with channel.typing():
        # TIER 1: Try High-Quality Models
        for model in high_quality_models:
            for provider in all_providers:
                try:
                    if not provider.supports_model(model): continue
                    if provider.__name__ == "PuterJS" and not os.getenv("PUTER_API_KEY"): continue
                    
                    client = AsyncClient(provider=provider)
                    response = await client.chat.completions.create(
                        model=model,
                        messages=[{"role": "system", "content": MEGA_PROMPT}] + messages,
                    )
                    reply = response.choices[0].message.content
                    if not reply or len(reply) < 2: continue

                    reply = clean_output(reply)
                    if not reply: continue

                    await send_large_message(channel, reply)
                    last_activity_time[channel.id] = time.time()
                    return 
                except:
                    continue

        # TIER 2: Fallback Brute-Force (Empty model)
        for provider in all_providers:
            try:
                if provider.__name__ == "PuterJS" and not os.getenv("PUTER_API_KEY"):
                    continue
                
                client = AsyncClient(provider=provider)
                response = await client.chat.completions.create(
                    model="", 
                    messages=[{"role": "system", "content": MEGA_PROMPT}] + messages,
                )
                reply = response.choices[0].message.content
                if not reply or len(reply) < 2: continue
                
                reply = clean_output(reply)

                # Final proxy ad cleanup
                ad_marker = "need proxies cheaper than the market?"
                idx = reply.lower().find(ad_marker)
                if idx != -1: reply = reply[:idx].strip()
                
                if not reply: continue

                await send_large_message(channel, reply)
                last_activity_time[channel.id] = time.time()
                return 
            except Exception as e:
                continue
        
        print(f"{bot.user.display_name}: Brute-force cycle failed. Waiting...")
        last_error_time = time.time()

async def send_large_message(channel, reply):
    if len(reply) > 2000:
        data = io.StringIO(reply)
        file = discord.File(data, filename="message.txt")
        await channel.send("📄 Detailed response attached:", file=file)
    else:
        await channel.send(reply)

@bot.event
async def on_message(message):
    await bot.process_commands(message)
    ch_id = message.channel.id
    last_activity_time[ch_id] = time.time()
    
    if ch_id not in chat_history: 
        chat_history[ch_id] = []

    if message.author == bot.user or message.content.startswith(bot.command_prefix):
        if message.author == bot.user:
            chat_history[ch_id].append({"author": bot.user.display_name, "content": message.content})
            chat_history[ch_id] = chat_history[ch_id][-MAX_HISTORY:]
        return

    content = message.content
    if message.attachments:
        attachment_texts = []
        for att in message.attachments:
            ext_text = await extract_attachment_text(att)
            if ext_text:
                attachment_texts.append(f"[Attached File {att.filename}]:\n{ext_text}\n[End of File]")
            else:
                attachment_texts.append(f"[Attached File {att.filename}]: No text found or format unsupported.")
        
        if content:
            content += "\n\n" + "\n\n".join(attachment_texts)
        else:
            content = "\n\n".join(attachment_texts)

    chat_history[ch_id].append({"author": message.author.display_name, "content": content})
    chat_history[ch_id] = chat_history[ch_id][-MAX_HISTORY:]

    if message.author.bot:
        await asyncio.sleep(random.uniform(5, 10))

    await respond_to_history(message.channel)

if __name__ == "__main__":
    TOKEN = os.getenv("DISCORD_TOKEN")
    if not TOKEN: exit(1)
    bot.run(TOKEN)
