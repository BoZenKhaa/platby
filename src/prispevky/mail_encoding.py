import unidecode


def body_utf8_representation(input_str: str):
    """
    Replaces characters with codepoint <128 with hex value of utf8 code.
    The hex value uses capitalized characters and replaces the python hex sign '\\x' with '=''
    This is the representation used in the email body.
    """
    def mail_encode(v: str):
        return str(v.encode('utf8'))[2:-1].replace('\\x', '=').upper()

    return ''.join([i if ord(i) < 128 else mail_encode(i) for i in input_str])

def remove_accents(input_str:str):
    return unidecode.unidecode(input_str)