import discord

def message(
    title=None,
    description=None,
    color=discord.Color.blue(),
    footer="pappape Server System Ver.1.2.5\nDeveloped by Enban21 & pappape\nCopyright © 2024 pappape & Enban21. All rights reserved.",
    author=None,
    thumbnail=None,
    image=None,
    field1=None,
    field2=None,
    field3=None
):
    embed = discord.Embed(
        title=title,
        description=description,
        color=color
    )

    if footer:
        embed.set_footer(text=footer)

    if author:
        embed.set_author(name=author.get("name", "Unknown"), icon_url=author.get("icon_url"))

    if thumbnail:
        embed.set_thumbnail(url=thumbnail)

    if image:
        embed.set_image(url=image)

    if field1:
        embed.add_field(name=field1["name"], value=field1["value"], inline=field1.get("inline", False))
    
    if field2:
        embed.add_field(name=field2["name"], value=field2["value"], inline=field2.get("inline", False))

    if field3:
        embed.add_field(name=field3["name"], value=field3["value"], inline=field3.get("inline", False))

    return embed
