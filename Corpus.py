import discord
from discord.ext import commands
from discord.commands import SlashCommandGroup, Option
import csv
import os
from datetime import datetime

CANAL_REVISION_ID = 1381723730064965683

BOT_TOKEN = "MTM4MTQyMTU5NDc5NDAwMDM4NA.GiSDmr.ZwVc_oYiQTW8mTBMuqrel0-grpltPhWX9aaP2Y"

intents = discord.Intents.default()
intents.message_content = True
intents.members = True

bot = commands.Bot(command_prefix="!", intents=intents)

LENGUAS_ARCHIVOS = {
    "Caló": "calo.csv",
    "Cherja": "cherja.csv",
    "Haketía": "haketia.csv"
}
LENGUAS_DISPONIBLES = list(LENGUAS_ARCHIVOS.keys())

# --- COG DE COMANDOS ---
class CorpusCog(commands.Cog):
    def __init__(self, bot):
        self.bot = bot

    corpus = SlashCommandGroup("corpus", "Comandos para el corpus lingüístico")

    @corpus.command(
        name="aportar",
        description="Añade una nueva frase y su traducción al corpus."
    )
    async def aportar(
        self,
        ctx: discord.ApplicationContext,
        lengua: discord.Option(str, "Lengua a la que estás traduciendo", choices=LENGUAS_DISPONIBLES, required=True),
        idioma_origen: discord.Option(str, "Idioma original de la frase", choices=["Español", "Inglés"], required=True),
        frase_original: discord.Option(str, "Frase original", required=True),
        frase_traducida: discord.Option(str, "Traducción", required=True),
    ):

        nombre_archivo = LENGUAS_ARCHIVOS[lengua]

        nueva_fila = [
            datetime.now().isoformat(),
            ctx.author.id,
            str(ctx.author),
            idioma_origen,
            frase_original,
            frase_traducida
        ]

        try:
            with open(nombre_archivo, mode='a', newline='', encoding='utf-8') as f:
                writer = csv.writer(f)
                writer.writerow(nueva_fila)

            # Enviar al canal de revisión
            canal_revision = bot.get_channel(CANAL_REVISION_ID)
            if canal_revision:
                embed_rev = discord.Embed(
                    title="📝 Nueva Aportación para Revisión",
                    color=discord.Color.orange()
                )
                embed_rev.add_field(name="Lengua", value=lengua, inline=True)
                embed_rev.add_field(name="Idioma Original", value=idioma_origen, inline=True)
                embed_rev.add_field(name="Usuario", value=str(ctx.author), inline=False)
                embed_rev.add_field(name="Frase Original", value=frase_original, inline=False)
                embed_rev.add_field(name="Traducción", value=frase_traducida, inline=False)
                embed_rev.set_footer(text=f"ID Usuario: {ctx.author.id}")

                mensaje = await canal_revision.send(embed=embed_rev)
                await mensaje.add_reaction("✅")
                await mensaje.add_reaction("❌")

            await ctx.respond("✅ ¡Aportación guardada y enviada para revisión!", ephemeral=True)

        except Exception as e:
            print(f"Error al guardar aportación: {e}")
            await ctx.respond("❌ Hubo un error al guardar la aportación.", ephemeral=True)


    @corpus.command(
        name="descargar",
        description="[Solo Admin] Descarga el CSV"
    )
    async def descargar(
        self,
        ctx: discord.ApplicationContext,
        lengua: Option(str, "Elige la lengua", choices=LENGUAS_DISPONIBLES)
    ):
        await ctx.defer()
    
        # Verificar si el autor tiene el rol correcto
        rol_admin = discord.utils.get(ctx.author.roles, name="🧑‍💻 | ADMINISTRADORES")
    
        if rol_admin is None:
            await ctx.respond("❌ No tienes permiso para usar este comando.", ephemeral=True)
            return

        archivo = LENGUAS_ARCHIVOS[lengua]
        if os.path.exists(archivo):
            await ctx.followup.send(file=discord.File(archivo))
        else:
            await ctx.followup.send(f"No se encontró el archivo para {lengua}.")
            
    @corpus.command(
        name="estadisticas",
        description="Muestra el ranking de usuarios que más han contribuido."
    )
    async def estadisticas(self, ctx: discord.ApplicationContext):
        contador = {}

        for archivo in LENGUAS_ARCHIVOS.values():
            try:
                with open(archivo, mode='r', encoding='utf-8') as f:
                    reader = csv.DictReader(f)
                    for fila in reader:
                        user = fila['user_name']
                        contador[user] = contador.get(user, 0) + 1
            except Exception as e:
                print(f"Error leyendo {archivo}: {e}")

        if not contador:
            await ctx.respond("⚠️ Aún no hay aportaciones registradas.")
            return

        ranking = sorted(contador.items(), key=lambda x: x[1], reverse=True)
        embed = discord.Embed(
            title="🏆 Ranking de Contribuidores",
            color=discord.Color.blue()
        )

        for i, (usuario, total) in enumerate(ranking[:10], 1):
            embed.add_field(name=f"{i}. {usuario}", value=f"Aportes: {total}", inline=False)

        await ctx.respond(embed=embed)




    # Importante: registrar el grupo de comandos
    @commands.Cog.listener()
    async def on_ready(self):
        print(f"¡Bot conectado como {self.bot.user}!")
        for archivo in LENGUAS_ARCHIVOS.values():
            if not os.path.exists(archivo):
                with open(archivo, 'w', newline='', encoding='utf-8') as f:
                    writer = csv.writer(f)
                    writer.writerow(['timestamp', 'user_id', 'user_name', 'frase_original_es', 'frase_traducida'])
@bot.event
async def on_message(message):
    if message.author.bot:
        return  # Evitar bucles si el bot se responde a sí mismo

    if message.channel.name == "🈸｜corpus-paralelo":
        try:
            await message.delete()
        except Exception as e:
            print(f"No se pudo borrar un mensaje en {message.channel.name}: {e}")
    else:
        await bot.process_commands(message)


# --- INICIAR ---
bot.add_cog(CorpusCog(bot))
bot.run(BOT_TOKEN)
