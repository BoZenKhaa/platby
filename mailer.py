from typing import Tuple

from googleapiclient import errors
import base64
import logging

from google_authentication import GOOGLE_CREDENTIALS
from googleapiclient.discovery import build

from payment_info import PaymentInfo
from qr_code import qr_platba_string, QRCode

from email.message import EmailMessage
from email.headerregistry import Address
from email.utils import make_msgid
import html2text as html2text

""" Inspired by
https://stackoverflow.com/questions/25944883/how-to-send-an-email-through-gmail-without-enabling-insecure-access
and
https://docs.python.org/3/library/email.examples.html
"""
with open("email_template.html", 'rt', encoding="utf-8") as f:
    MESSAGE_HTML_TEMPLATE = f.read()


class PaymentEmail:
    email_template = MESSAGE_HTML_TEMPLATE

    def __init__(self,
                 subject: str,
                 payment_info: PaymentInfo,
                 sender_email_address: Address,
                 recipient_addresses: Tuple[Address], testmode=False):

        if testmode:
            ccs = sender_email_address
        else:
            ccs = Address(payment_info.troop.leader_name, addr_spec=payment_info.troop.leader_email)

        self.msg = self.create_email(subject, payment_info, sender_email_address, recipient_addresses, ccs)

    def save_copy(self, filename):
        # Make a local copy of what we are going to send.
        with open(f'{filename}.eml', 'wb') as f:
            f.write(bytes(self.msg))

    @staticmethod
    def create_email(subject: str, pi: PaymentInfo, sender: Address, recepients: Tuple[Address], ccs: Address):
        msg = EmailMessage()
        msg['Subject'] = subject
        msg['From'] = sender
        msg['To'] = recepients
        msg['Cc'] = ccs

        qr_code_cid = make_msgid()
        html_message = MESSAGE_HTML_TEMPLATE.format(payment_message=pi.payment_message,
                                                    variable_symbol=pi.variable_symbol,
                                                    specific_symbol=pi.specific_symbol,
                                                    amount_czk=pi.amount_czk,
                                                    human_account_number=pi.human_account_number,
                                                    human_due_date=pi.human_due_date,
                                                    qr_code_cid=qr_code_cid)

        msg.set_content(html2text.html2text(html_message))
        msg.add_alternative(html_message, subtype='html')

        qr_code = QRCode(qr_platba_string(pi))
        msg.get_payload()[1].add_related(qr_code.get_image_bytes(), 'image', 'png',
                                         cid=qr_code_cid)

        return msg


class Mailer:
    def __init__(self, credentials=GOOGLE_CREDENTIALS):
        try:
            self.service = build('gmail', 'v1', credentials=credentials)
        except Exception as e:
            logging.error(e)
            raise

    @staticmethod
    def encode_email_to_gmail_message(email_str: str):
        b = base64.urlsafe_b64encode(email_str.encode('utf-8'))
        gmail_message = {'raw': b.decode('utf-8')}
        return gmail_message

    def send_message(self, user_id, message):
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
            sent_message = (self.service.users().messages().send(userId=user_id, body=message)
                            .execute())
            status = "OK"
            logging.info(f'Message Id: {sent_message["id"]} sent.')
        except errors.HttpError as error:
            logging.error(f'An HTTP error occurred: {error}')
            sent_message = None
            status = error
        return dict(sent_msg=sent_message, attempted_message=message, send_status=status)
