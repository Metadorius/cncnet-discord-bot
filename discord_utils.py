class DiscordParseException(Exception):
    """An exception that is thrown when parsing Discord's representation of a channel / role / user mention fails."""

def parse_discord_str(content_str: str, type_chars: str) -> int:
    """Parses Discord's representation of a channel / role / user mention into an ID."""
    if content_str.startswith('<') and content_str.endswith('>') and content_str[1:-1].startswith(type_chars):
        return int(content_str[(1 + len(type_chars)):-1])
    raise DiscordParseException(f"{content_str} is not a valid Discord-formatted ID representation for '{type_chars}'")

def format_discord_str(discord_id: int, type_chars: str) -> str:
    """Formats an ID into a Discord's representation of a channel / role / user mention."""
    return f"<{type_chars}{discord_id}>"


# Shortcut functions

def parse_channel(content_str: str) -> int:
    """Parses Discord's representation of a channel mention into an ID."""
    return parse_discord_str(content_str, '#')

def parse_role(content_str: str) -> int:
    """Parses Discord's representation of a role mention into an ID."""
    return parse_discord_str(content_str, '@&')

def parse_user(content_str: str) -> int:
    """Parses Discord's representation of a user mention into an ID."""
    return parse_discord_str(content_str, '@!')

def format_channel(discord_id: int) -> str:
    """Formats an ID into a Discord's representation of a channel mention."""
    return format_discord_str(discord_id, '#')

def format_role(discord_id: int) -> str:
    """Formats an ID into a Discord's representation of a role mention."""
    return format_discord_str(discord_id, '@&')

def format_user(discord_id: int) -> str:
    """Formats an ID into a Discord's representation of a user mention."""
    return format_discord_str(discord_id, '@!')
