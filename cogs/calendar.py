import discord
from discord.ext import commands
from discord import app_commands
from PIL import Image, ImageDraw, ImageFont
import pandas as pd
from datetime import datetime, timedelta
import calendar
import io
from langchain_core.messages import SystemMessage, HumanMessage

CSV_PATH = "data/planning.csv"

COLORS = {
    "background":   "#2C2F33",
    "header":       "#23272A",
    "grid":         "#40444B",
    "weekend":      "#37474F",
    "text":         "#FFFFFF",
    "text_muted":   "#FFFFFF",
    "today":        "#E74C3C",
    "ascent":       "#43B581",
    "cefora":       "#9B59B6",
    "selfstudy":    "#F1C40F",
    "empty":        "#37474F",
}

CELL_W = 180
CELL_H = 100
HEADER_H = 60
DAY_HEADER_H = 40
PADDING = 10

MOIS = {
    "janvier": 1, "février": 2, "mars": 3, "avril": 4,
    "mai": 5, "juin": 6, "juillet": 7, "août": 8,
    "septembre": 9, "octobre": 10, "novembre": 11, "décembre": 12
}

JOURS = ["Lundi", "Mardi", "Mercredi", "Jeudi", "Vendredi", "Samedi", "Dimanche"]
MOIS_NOM = ["janvier", "février", "mars", "avril", "mai", "juin",
            "juillet", "août", "septembre", "octobre", "novembre", "décembre"]


def clean_intervenant(intervenant: str) -> str:
    if not intervenant:
        return ""
    return intervenant.replace("Ascent - ", "").replace("Ascent -", "").strip()


def parse_date_fr(date_str: str):
    parts = date_str.strip().lower().split()
    if len(parts) != 4:
        return None
    try:
        jour = int(parts[1])
        mois = MOIS.get(parts[2])
        annee = int(parts[3])
        if not mois:
            return None
        return datetime(annee, mois, jour).date()
    except:
        return None


def load_planning():
    try:
        df = pd.read_csv(
            CSV_PATH,
            header=0,
            sep=None,
            engine="python",
            encoding="utf-8-sig"
        )
        df.columns = ["date", "intervenant", "cours"]
        df = df.fillna("")

        planning = {}

        for _, row in df.iterrows():
            dates_raw = str(row["date"]).strip()
            intervenants_raw = str(row["intervenant"]).strip()
            cours_raw = str(row["cours"]).strip()

            if not dates_raw or dates_raw in ("nan", "Date", "date"):
                continue

            dates = [d.strip() for d in dates_raw.split("\n") if d.strip()]
            intervenants = [i.strip() for i in intervenants_raw.split("\n") if i.strip()]
            cours_list = [c.strip() for c in cours_raw.split("\n") if c.strip()]

            for i, date_str in enumerate(dates):
                date = parse_date_fr(date_str)
                if date is None:
                    continue

                planning[date] = {
                    "intervenant": clean_intervenant(intervenants[i] if i < len(intervenants) else ""),
                    "cours": cours_list[i] if i < len(cours_list) else "",
                }

        return planning

    except Exception as e:
        raise e


def planning_to_context(planning: dict) -> str:
    lines = ["Voici le planning de formation complet :\n"]
    for date in sorted(planning.keys()):
        data = planning[date]
        intervenant = data.get("intervenant", "") or "—"
        cours = data.get("cours", "") or "—"
        lines.append(f"- {JOURS[date.weekday()]} {date.day} {MOIS_NOM[date.month - 1]} {date.year} : Intervenant = {intervenant} | Cours = {cours}")
    return "\n".join(lines)


def get_cell_color(intervenant: str, cours: str = "") -> str:
    cours_lower = cours.lower()
    intervenant_lower = intervenant.lower() if intervenant else ""

    if "selfstudy" in cours_lower or "self study" in cours_lower:
        return COLORS["selfstudy"]
    if intervenant_lower in ("selfstudy", "self study"):
        return COLORS["selfstudy"]
    if not intervenant or intervenant == "nan":
        return COLORS["empty"]
    if "cefora" in intervenant_lower:
        return COLORS["cefora"]
    return COLORS["ascent"]


def hex_to_rgb(hex_color: str):
    hex_color = hex_color.lstrip("#")
    return tuple(int(hex_color[i:i+2], 16) for i in (0, 2, 4))


def wrap_text(text: str, max_chars: int) -> list:
    words = text.split()
    lines = []
    current = ""
    for word in words:
        if len(current) + len(word) + 1 <= max_chars:
            current += (" " if current else "") + word
        else:
            if current:
                lines.append(current)
            current = word
    if current:
        lines.append(current)
    return lines


def load_font(size: int):
    font_paths = [
        "/System/Library/Fonts/Helvetica.ttc",
        "/System/Library/Fonts/SFNSDisplay.ttf",
        "/System/Library/Fonts/SFNSText.ttf",
        "/System/Library/Fonts/Arial.ttf",
        "/Library/Fonts/Arial.ttf",
        "/System/Library/Fonts/Supplemental/Arial.ttf",
        "/usr/share/fonts/truetype/dejavu/DejaVuSans.ttf",
        "/usr/share/fonts/truetype/liberation/LiberationSans-Regular.ttf",
        "/usr/share/fonts/truetype/freefont/FreeSans.ttf",
        "/usr/share/fonts/truetype/ubuntu/Ubuntu-R.ttf",
        "C:/Windows/Fonts/arial.ttf",
        "C:/Windows/Fonts/segoeui.ttf",
        "C:/Windows/Fonts/calibri.ttf",
    ]
    for path in font_paths:
        try:
            return ImageFont.truetype(path, size)
        except:
            continue
    return ImageFont.load_default()


def generate_month_image(year: int, month: int, planning: dict) -> io.BytesIO:
    day_names = ["Lundi", "Mardi", "Mercredi", "Jeudi", "Vendredi", "Samedi", "Dimanche"]
    cal = calendar.monthcalendar(year, month)
    num_weeks = len(cal)

    img_w = CELL_W * 7 + PADDING * 2
    img_h = HEADER_H + DAY_HEADER_H + CELL_H * num_weeks + PADDING * 2

    img = Image.new("RGB", (img_w, img_h), hex_to_rgb(COLORS["background"]))
    draw = ImageDraw.Draw(img)

    font_title = load_font(24)
    font_day   = load_font(14)
    font_num   = load_font(18)
    font_text  = load_font(13)

    month_name = f"{MOIS_NOM[month - 1].capitalize()} {year}"
    draw.rectangle([0, 0, img_w, HEADER_H], fill=hex_to_rgb(COLORS["header"]))
    draw.text(
        (img_w // 2, HEADER_H // 2),
        month_name,
        fill=hex_to_rgb(COLORS["text"]),
        font=font_title,
        anchor="mm"
    )

    for i, day_name in enumerate(day_names):
        x = PADDING + i * CELL_W
        y = HEADER_H
        draw.rectangle(
            [x, y, x + CELL_W, y + DAY_HEADER_H],
            fill=hex_to_rgb(COLORS["header"]),
            outline=hex_to_rgb(COLORS["grid"])
        )
        draw.text(
            (x + CELL_W // 2, y + DAY_HEADER_H // 2),
            day_name,
            fill=hex_to_rgb(COLORS["text"]),
            font=font_day,
            anchor="mm"
        )

    today = datetime.now().date()

    for week_idx, week in enumerate(cal):
        for day_idx, day in enumerate(week):
            x = PADDING + day_idx * CELL_W
            y = HEADER_H + DAY_HEADER_H + week_idx * CELL_H
            is_weekend = day_idx >= 5

            if day == 0:
                draw.rectangle(
                    [x, y, x + CELL_W, y + CELL_H],
                    fill=hex_to_rgb(COLORS["background"]),
                    outline=hex_to_rgb(COLORS["grid"])
                )
                continue

            current_date = datetime(year, month, day).date()
            day_data = planning.get(current_date, {})
            intervenant = day_data.get("intervenant", "")
            cours = day_data.get("cours", "")

            if is_weekend:
                cell_color = COLORS["weekend"]
            else:
                cell_color = get_cell_color(intervenant, cours)

            draw.rectangle(
                [x, y, x + CELL_W, y + CELL_H],
                fill=hex_to_rgb(cell_color),
                outline=hex_to_rgb(COLORS["grid"])
            )

            num_color = COLORS["today"] if current_date == today else COLORS["text"]
            draw.text((x + 8, y + 6), str(day), fill=hex_to_rgb(num_color), font=font_num)

            if not is_weekend:
                if intervenant:
                    draw.text((x + 8, y + 30), intervenant[:22], fill=hex_to_rgb(COLORS["text"]), font=font_text)

                if cours:
                    lines = wrap_text(cours, 22)
                    for line_idx, line in enumerate(lines[:3]):
                        draw.text(
                            (x + 8, y + 52 + line_idx * 16),
                            line,
                            fill=hex_to_rgb(COLORS["text_muted"]),
                            font=font_text
                        )

    buffer = io.BytesIO()
    img.save(buffer, format="PNG")
    buffer.seek(0)
    return buffer


def generate_week_image(start_date, planning: dict) -> io.BytesIO:
    monday = start_date - timedelta(days=start_date.weekday())
    day_names = ["Lundi", "Mardi", "Mercredi", "Jeudi", "Vendredi", "Samedi", "Dimanche"]

    WEEK_CELL_H = 200
    img_w = CELL_W * 7 + PADDING * 2
    img_h = HEADER_H + DAY_HEADER_H + WEEK_CELL_H + PADDING * 2

    img = Image.new("RGB", (img_w, img_h), hex_to_rgb(COLORS["background"]))
    draw = ImageDraw.Draw(img)

    font_title = load_font(24)
    font_day   = load_font(14)
    font_num   = load_font(18)
    font_text  = load_font(13)

    sunday = monday + timedelta(days=6)
    week_label = f"Semaine du {monday.day} {MOIS_NOM[monday.month - 1]} au {sunday.day} {MOIS_NOM[sunday.month - 1]} {sunday.year}"
    draw.rectangle([0, 0, img_w, HEADER_H], fill=hex_to_rgb(COLORS["header"]))
    draw.text(
        (img_w // 2, HEADER_H // 2),
        week_label,
        fill=hex_to_rgb(COLORS["text"]),
        font=font_title,
        anchor="mm"
    )

    today = datetime.now().date()

    for i in range(7):
        current_date = monday + timedelta(days=i)
        is_weekend = i >= 5
        day_data = planning.get(current_date, {})
        intervenant = day_data.get("intervenant", "")
        cours = day_data.get("cours", "")

        x = PADDING + i * CELL_W
        y = HEADER_H

        draw.rectangle(
            [x, y, x + CELL_W, y + DAY_HEADER_H],
            fill=hex_to_rgb(COLORS["header"]),
            outline=hex_to_rgb(COLORS["grid"])
        )
        draw.text(
            (x + CELL_W // 2, y + DAY_HEADER_H // 2),
            day_names[i],
            fill=hex_to_rgb(COLORS["text"]),
            font=font_day,
            anchor="mm"
        )

        y = HEADER_H + DAY_HEADER_H

        if is_weekend:
            cell_color = COLORS["weekend"]
        else:
            cell_color = get_cell_color(intervenant, cours)

        draw.rectangle(
            [x, y, x + CELL_W, y + WEEK_CELL_H],
            fill=hex_to_rgb(cell_color),
            outline=hex_to_rgb(COLORS["grid"])
        )

        num_color = COLORS["today"] if current_date == today else COLORS["text"]
        draw.text((x + 8, y + 8), str(current_date.day), fill=hex_to_rgb(num_color), font=font_num)

        if not is_weekend:
            if intervenant:
                draw.text((x + 8, y + 35), intervenant[:22], fill=hex_to_rgb(COLORS["text"]), font=font_text)

            if cours:
                lines = wrap_text(cours, 22)
                for line_idx, line in enumerate(lines[:6]):
                    draw.text(
                        (x + 8, y + 60 + line_idx * 20),
                        line,
                        fill=hex_to_rgb(COLORS["text_muted"]),
                        font=font_text
                    )

    buffer = io.BytesIO()
    img.save(buffer, format="PNG")
    buffer.seek(0)
    return buffer


def generate_day_image(date, planning: dict) -> io.BytesIO:
    day_data = planning.get(date, {})
    intervenant = day_data.get("intervenant", "")
    cours = day_data.get("cours", "")

    img_w = 500
    img_h = 300

    img = Image.new("RGB", (img_w, img_h), hex_to_rgb(COLORS["background"]))
    draw = ImageDraw.Draw(img)

    font_title = load_font(26)
    font_text  = load_font(18)
    font_muted = load_font(15)

    cell_color = get_cell_color(intervenant, cours)
    draw.rectangle([0, 0, 8, img_h], fill=hex_to_rgb(cell_color))

    day_label = f"{JOURS[date.weekday()]} {date.day} {MOIS_NOM[date.month - 1]} {date.year}"
    draw.text((30, 30), day_label, fill=hex_to_rgb(COLORS["text"]), font=font_title)

    if intervenant:
        draw.text((30, 90), f"Intervenant : {intervenant}", fill=hex_to_rgb(cell_color), font=font_text)
    else:
        draw.text((30, 90), "Pas de cours", fill=hex_to_rgb(COLORS["text_muted"]), font=font_text)

    if cours:
        lines = wrap_text(cours, 45)
        for i, line in enumerate(lines):
            draw.text((30, 140 + i * 25), line, fill=hex_to_rgb(COLORS["text_muted"]), font=font_muted)

    buffer = io.BytesIO()
    img.save(buffer, format="PNG")
    buffer.seek(0)
    return buffer


class Calendrier(commands.Cog):
    def __init__(self, bot: commands.Bot):
        self.bot = bot
        self.planning = load_planning()

    @app_commands.command(name="calendrier", description="Affiche le calendrier")
    @app_commands.describe(valeur="Ex: juillet | 23/03 | sem:23/03 | vide = mois courant")
    async def calendrier(
        self,
        interaction: discord.Interaction,
        valeur: str = None
    ):
        await interaction.response.defer()
        today = datetime.now().date()

        try:
            if valeur is None:
                buffer = generate_month_image(today.year, today.month, self.planning)
                filename = f"calendrier_{today.year}_{today.month:02d}.png"

            elif valeur.lower() in MOIS:
                month = MOIS[valeur.lower()]
                buffer = generate_month_image(today.year, month, self.planning)
                filename = f"calendrier_{today.year}_{month:02d}.png"

            elif valeur.lower().startswith("sem:"):
                try:
                    day, month = map(int, valeur[4:].split("/"))
                    date = datetime(today.year, month, day).date()
                except ValueError:
                    await interaction.followup.send("Format invalide. Utilise sem:JJ/MM (ex: sem:23/03)")
                    return
                buffer = generate_week_image(date, self.planning)
                filename = f"semaine_{date}.png"

            elif "/" in valeur:
                try:
                    day, month = map(int, valeur.split("/"))
                    date = datetime(today.year, month, day).date()
                except ValueError:
                    await interaction.followup.send("Format invalide. Utilise JJ/MM (ex: 15/03)")
                    return
                buffer = generate_day_image(date, self.planning)
                filename = f"jour_{date}.png"

            else:
                await interaction.followup.send("Format invalide. Utilise : juillet | 15/03 | sem:15/03 | ou rien pour le mois courant")
                return

            await interaction.followup.send(file=discord.File(buffer, filename=filename))

        except Exception as e:
            await interaction.followup.send(f"Erreur : {e}")

    @app_commands.command(name="planning", description="Pose une question sur le planning")
    @app_commands.describe(question="Ex: Combien de jours de self-study en mars ?")
    async def planning_ask(
        self,
        interaction: discord.Interaction,
        question: str
    ):
        await interaction.response.defer()

        try:
            context = planning_to_context(self.planning)
            today_str = f"{JOURS[datetime.now().date().weekday()]} {datetime.now().date().day} {MOIS_NOM[datetime.now().date().month - 1]} {datetime.now().date().year}"

            messages = [
                SystemMessage(content=(
                    f"Tu es un assistant qui répond à des questions sur un planning de formation.\n"
                    f"Aujourd'hui nous sommes le {today_str}.\n"
                    f"Réponds de manière concise et précise en français.\n\n"
                    f"{context}"
                )),
                HumanMessage(content=question)
            ]

            response = await self.bot.llm.ask(messages)
            answer = response.content.strip()

            embed = discord.Embed(
                title=question,
                description=answer[:4096], 
                color=0x5865F2
            )

            await interaction.followup.send(embed=embed)


        except Exception as e:
            await interaction.followup.send(f"Erreur : {e}")

    @app_commands.command(name="reload_planning", description="Reload du CSV")
    async def reload_planning(self, interaction: discord.Interaction):
        self.planning = load_planning()
        await interaction.response.send_message("Planning rechargé.")


async def setup(bot):
    await bot.add_cog(Calendrier(bot))
