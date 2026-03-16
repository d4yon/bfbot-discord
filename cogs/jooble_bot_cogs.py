import discord
from discord import app_commands
from discord.ext import commands
import http.client
import json

class JoobleCog(commands.Cog):
    def __init__(self, bot):
        self.bot = bot
        self.jooble_key = '403156ce-2f05-453d-b73b-5f6d67f5f576'

    @app_commands.command(name="jobs", description="Rechercher un emploi sur Jooble Belgique")
    @app_commands.describe(keywords="Profession", location="Ville")
    async def jobs(self, interaction: discord.Interaction, keywords: str, location: str):
        await interaction.response.defer(ephemeral=True)

        try:
            # RETOUR SUR L'HÔTE BELGE (Indispensable pour la pertinence locale)
            host = 'be.jooble.org'
            connection = http.client.HTTPSConnection(host)
            
            # HEADERS ROBUSTES (Pour éviter le 403)
            headers = {
                "Content-type": "application/json; charset=utf-8",
                "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/122.0.0.0 Safari/537.36",
                "Accept": "application/json"
            }
            
            # CORPS DE LA REQUÊTE (On ajoute searchMode 0 pour être plus large)
            body_dict = {
                "keywords": keywords, 
                "location": location,
                "radius": "25",
                "searchMode": "0" 
            }
            body = json.dumps(body_dict, ensure_ascii=False).encode('utf-8')

            connection.request('POST', f'/api/{self.jooble_key}', body, headers)
            response = connection.getresponse()
            raw_data = response.read().decode('utf-8')

            # Debug console
            print(f"DEBUG: Recherche '{keywords}' à '{location}' | Status: {response.status}")

            if response.status == 200:
                data = json.loads(raw_data)
                
                # Jooble renvoie parfois une liste vide si les critères sont trop précis
                if "jobs" in data and data["jobs"]:
                    embed = discord.Embed(
                        title=f"🔍 Offres pour '{keywords}'", 
                        description=f"📍 Secteur : {location}",
                        color=discord.Color.green()
                    )
                    
                    for job in data["jobs"][:5]:
                        title = job.get('title', '').replace("<b>", "").replace("</b>", "")
                        company = job.get('company', 'Inconnue')
                        link = job.get('link', '#')
                        # On affiche aussi le lieu réel de l'offre
                        job_loc = job.get('location', location)
                        
                        embed.add_field(
                            name=title, 
                            value=f"🏢 {company} | 📍 {job_loc}\n🔗 [Voir l'offre]({link})", 
                            inline=False
                        )
                    
                    await interaction.followup.send(embed=embed, ephemeral=True)
                else:
                    await interaction.followup.send(f"❌ Aucun résultat sur be.jooble.org pour '{keywords}' à '{location}'.", ephemeral=True)
            else:
                await interaction.followup.send(f"⚠️ Erreur API Jooble : {response.status}", ephemeral=True)

        except Exception as e:
            print(f"ERREUR : {e}")
            await interaction.followup.send(f"⚠️ Une erreur technique est survenue.", ephemeral=True)
        finally:
            connection.close()

async def setup(bot):
    await bot.add_cog(JoobleCog(bot))