import discord
from discord.ext import commands
import re
import aiohttp
import zipfile
import tarfile
import io
import py7zr

class TokenGuardCog(commands.Cog):
    def __init__(self, bot):
        self.bot = bot
        self.token_pattern = re.compile(r'[M][A-Za-z\d]{23}')

    @commands.Cog.listener()
    async def on_message(self, message):
        if message.author.bot:
            return

        if self.token_pattern.search(message.content):
            await self.handle_token_message(message)
        
        if message.attachments:
            for attachment in message.attachments:
                await self.check_attachment_for_token(message, attachment)
        
    async def handle_token_message(self, message):
        try:
            await message.delete()
            await message.author.send("Your message contains a bot token and has been deleted. You have been muted.")
            
        except discord.Forbidden:
            pass

    async def check_attachment_for_token(self, message, attachment):
        async with aiohttp.ClientSession() as session:
            async with session.get(attachment.url) as response:
                if response.status == 200:
                    file_bytes = await response.read()
                    filename = attachment.filename.lower()
                    if filename.endswith('.rar'):
                        await self.check_rar_for_token(message, file_bytes)
                    elif filename.endswith('.7z') or filename.endswith('.7zip'):
                        await self.check_7z_for_token(message, file_bytes)
                    elif filename.endswith('.zip'):
                        await self.check_zip_for_token(message, file_bytes)
                    elif filename.endswith('.tar.gz'):
                        await self.check_tar_gz_for_token(message, file_bytes)
                    elif filename.endswith('.gz') or filename.endswith('.gzip'):
                        await self.check_gzip_for_token(message, file_bytes)
                    elif filename.endswith('.bz2'):
                        await self.check_bzip_for_token(message, file_bytes)

    async def check_rar_for_token(self, message, file_bytes):
        with py7zr.SevenZipFile(io.BytesIO(file_bytes), mode='r') as z:
            for filename in z.getnames():
                if any(filename.endswith(ext) for ext in ('.txt', '.yml', '.yaml', '.xml', '.java', '.json')):
                    file_content = z.read(filename).decode('utf-8')
                    if self.token_pattern.search(file_content):
                        await self.handle_token_message(message)
                elif filename.endswith('/') and filename[:-1].endswith(('/', '\\')):
                    await self.check_folder_for_token(message, z, filename)

    async def check_7z_for_token(self, message, file_bytes):
        with py7zr.SevenZipFile(io.BytesIO(file_bytes), mode='r') as z:
            for filename in z.getnames():
                if any(filename.endswith(ext) for ext in ('.txt', '.yml', '.yaml', '.xml', '.java', '.json')):
                    file_content = z.read(filename).decode('utf-8')
                    if self.token_pattern.search(file_content):
                        await self.handle_token_message(message)
                elif filename.endswith('/') and filename[:-1].endswith(('/', '\\')):
                    await self.check_folder_for_token(message, z, filename)

    async def check_zip_for_token(self, message, file_bytes):
        with zipfile.ZipFile(io.BytesIO(file_bytes)) as z:
            for file in z.namelist():
                if any(file.endswith(ext) for ext in ('.txt', '.yml', '.yaml', '.xml', '.java', '.json')):
                    with z.open(file) as f:
                        file_content = f.read().decode('utf-8')
                        if self.token_pattern.search(file_content):
                            await self.handle_token_message(message)
                elif file.endswith('/') and file[:-1].endswith(('/', '\\')):
                    await self.check_folder_for_token(message, z, file)

    async def check_tar_gz_for_token(self, message, file_bytes):
        with tarfile.open(fileobj=io.BytesIO(file_bytes), mode='r:gz') as z:
            for member in z.getmembers():
                if member.isfile() and any(member.name.endswith(ext) for ext in ('.txt', '.yml', '.yaml', '.xml', '.java', '.json')):
                    f = z.extractfile(member)
                    if f:
                        file_content = f.read().decode('utf-8')
                        if self.token_pattern.search(file_content):
                            await self.handle_token_message(message)
                elif member.isdir() and any(c in member.name for c in ('/', '\\')):
                    await self.check_folder_for_token(message, z, member.name)

    async def check_gzip_for_token(self, message, file_bytes):
        with tarfile.open(fileobj=io.BytesIO(file_bytes), mode='r:gz') as z:
            for member in z.getmembers():
                if member.isfile() and any(member.name.endswith(ext) for ext in ('.txt', '.yml', '.yaml', '.xml', '.java', '.json')):
                    f = z.extractfile(member)
                    if f:
                        file_content = f.read().decode('utf-8')
                        if self.token_pattern.search(file_content):
                            await self.handle_token_message(message)
                elif member.isdir() and any(c in member.name for c in ('/', '\\')):
                    await self.check_folder_for_token(message, z, member.name)

    async def check_bzip_for_token(self, message, file_bytes):
        with tarfile.open(fileobj=io.BytesIO(file_bytes), mode='r:bz2') as z:
            for member in z.getmembers():
                if member.isfile() and any(member.name.endswith(ext) for ext in ('.txt', '.yml', '.yaml', '.xml', '.java', '.json')):
                    f = z.extractfile(member)
                    if f:
                        file_content = f.read().decode('utf-8')
                        if self.token_pattern.search(file_content):
                            await self.handle_token_message(message)
                elif member.isdir() and any(c in member.name for c in ('/', '\\')):
                    await self.check_folder_for_token(message, z, member.name)

    async def check_folder_for_token(self, message, zip_file, folder):
        for file in zip_file.namelist():
            if file.startswith(folder):
                if not file.endswith('/'):
                    with zip_file.open(file) as f:
                        file_content = f.read().decode('utf-8')
                        if self.token_pattern.search(file_content):
                            await self.handle_token_message(message)
                else:
                    await self.check_folder_for_token(message, zip_file, file)

async def setup(bot: commands.Bot):
    await bot.add_cog(TokenGuardCog(bot))