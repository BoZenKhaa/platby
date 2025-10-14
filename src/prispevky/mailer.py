from typing import Tuple

from googleapiclient import errors
import base64
import logging

from prispevky.config import CONFIG
from prispevky.google_authentication import GOOGLE_CREDENTIALS
from googleapiclient.discovery import build

from prispevky.payment_info import PaymentInfo
from prispevky.qr_code import qr_platba_string, QRCode

from email.message import EmailMessage
from email.headerregistry import Address
from email.utils import make_msgid
import html2text as html2text
import importlib.resources as resources

""" Inspired by
https://stackoverflow.com/questions/25944883/how-to-send-an-email-through-gmail-without-enabling-insecure-access
and
https://docs.python.org/3/library/email.examples.html
"""

SENDER = Address(CONFIG['mailer']['sender_name'], addr_spec=CONFIG['mailer']['sender_address'])
SUBJECT = CONFIG['mailer']['subject']
with open(resources.files('prispevky.templates')/CONFIG['mailer']['html_template'], 'rt', encoding="utf-8") as f:
    MESSAGE_HTML_TEMPLATE = f.read()


class PaymentEmail:
    email_template = MESSAGE_HTML_TEMPLATE

    def __init__(self,
                 payment_info: PaymentInfo,
                 recipient_addresses: Tuple[Address],
                 subject: str = SUBJECT,
                 sender_email_address: Address = SENDER,
                 testmode=False):

        if testmode:
            ccs = sender_email_address
        else:
            ccs = Address(payment_info.troop.leader_name, addr_spec=payment_info.troop.leader_email)

        self.msg = self.create_email(subject, sender_email_address, payment_info, recipient_addresses, ccs)

    def save_copy(self, filename):
        # Make a local copy of what we are going to send.
        with open(f'{filename}.eml', 'wb') as f:
            f.write(bytes(self.msg))

    @staticmethod
    def create_email(subject: str, sender: Address, pi: PaymentInfo, recepients: Tuple[Address], ccs: Address):
        msg = EmailMessage()
        msg['Subject'] = subject
        msg['From'] = sender
        msg['To'] = recepients
        msg['Cc'] = ccs

        qr_code_cid = make_msgid()
        # we needed to peel the <> off the msgid for use in the html.

        usecase_specific_kwargs = {}
        if CONFIG.has_section('sts'):
            usecase_specific_kwargs = dict(number_of_sts_phones=pi.number_of_sts_phones)

        html_message = MESSAGE_HTML_TEMPLATE.format(troop=pi.troop.name,
                                                    payment_message=pi.payment_message,
                                                    variable_symbol=pi.variable_symbol,
                                                    specific_symbol=pi.specific_symbol,
                                                    amount_czk=pi.amount_czk,
                                                    human_account_number=pi.human_account_number,
                                                    human_due_date=pi.human_due_date,
                                                    qr_code_cid=qr_code_cid[1:-1],
                                                    **usecase_specific_kwargs)

        msg.set_content(html2text.html2text(html_message))
        msg.add_alternative(html_message, subtype='html')

        qr_code = QRCode(qr_platba_string(pi))
        msg.get_payload()[1].add_related(qr_code.get_image_bytes(), 'image', 'png',
                                         cid=qr_code_cid)

        return msg


class Mailer:
    def __init__(self, credentials=GOOGLE_CREDENTIALS, user_id=SENDER.addr_spec):
        """
        Args:
        user_id: User's email address. The special value "me"
        can be used to indicate the authenticated user.
        credentials:
        """
        self.user_id = user_id
        try:
            self.service = build('gmail', 'v1', credentials=credentials)
        except Exception as e:
            logging.error(e)
            raise

    @staticmethod
    def encode_email_to_gmail_message(email: EmailMessage):
        b = base64.urlsafe_b64encode(email.as_bytes())
        gmail_message = {'raw': b.decode('utf-8')}
        return gmail_message

    def send_message(self, message):
        """Send an email html_message.

      Args:
        user_id: User's email address. The special value "me"
        can be used to indicate the authenticated user.
        message: valid email html_message, with field such as recipient, body, etc.

      Returns:
        Sent Message.
      """
        message = self.encode_email_to_gmail_message(message)
        try:
            sent_message = (self.service.users().messages().send(userId=self.user_id, body=message)
                            .execute())
            status = "OK"
            logging.info(f'Message Id: {sent_message["id"]} sent.')
        except errors.HttpError as error:
            logging.error(f'An HTTP error occurred: {error}')
            sent_message = None
            status = error
        return dict(sent_msg=sent_message, attempted_message=message, send_status=status)
