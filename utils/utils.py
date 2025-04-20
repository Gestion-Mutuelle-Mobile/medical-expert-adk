def sanitize_for_logging(text):
    """
    Nettoie un texte des caractères qui pourraient causer des problèmes avec le logging.
    Remplace les emojis et autres caractères non-ASCII par des alternatives ou les supprime.

    Args:
        text: Le texte à nettoyer

    Returns:
        Texte nettoyé compatible avec l'encodage des logs
    """
    # Dictionnaire de remplacement pour les emojis courants
    emoji_replacements = {
        '😀': ':sourire:',
        '😃': ':sourire:',
        '😄': ':sourire:',
        '😁': ':sourire:',
        '😆': ':sourire:',
        '😅': ':sourire:',
        '🤣': ':rire:',
        '😂': ':rire:',
        '🙂': ':sourire:',
        '🙃': ':sourire:',
        '😉': ':clin_doeil:',
        '😊': ':sourire:',
        '😇': ':sourire:',
        '🥰': ':amour:',
        '😍': ':amour:',
        '🤩': ':star:',
        '😘': ':bisou:',
        '😗': ':bisou:',
        '☺️': ':sourire:',
        '😚': ':bisou:',
        '😙': ':bisou:',
        '🥲': ':sourire:',
        '😋': ':miam:',
        '😛': ':langue:',
        '😜': ':langue:',
        '🤪': ':fou:',
        '😝': ':langue:',
        '🤑': ':argent:',
        '🤗': ':calin:',
        '🤭': ':surprise:',
        '🤫': ':chut:',
        '🤔': ':reflexion:',
        # Ajoutez d'autres emojis selon vos besoins
    }

    # Remplacer les emojis connus
    for emoji, replacement in emoji_replacements.items():
        text = text.replace(emoji, replacement)

    # Pour les autres caractères non-ASCII, les remplacer par '?'
    # ou les ignorer complètement
    cleaned_text = ''
    for char in text:
        if ord(char) < 128:
            # Caractère ASCII standard
            cleaned_text += char
        else:
            # Caractère non-ASCII
            try:
                char.encode('cp1252')
                cleaned_text += char  # Si le caractère peut être encodé, le garder
            except UnicodeEncodeError:
                cleaned_text += '?'  # Sinon le remplacer par '?'

    return cleaned_text