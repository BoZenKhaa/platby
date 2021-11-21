from typing import Tuple

from googleapiclient import errors
import base64
import logging

from google_authentication import GOOGLE_CREDENTIALS
from googleapiclient.discovery import build

from payment_data import EmailAddress
from payment_info import PaymentInfo
from qr_code import qr_platba_string, QRCode

""" Inspired by
https://stackoverflow.com/questions/25944883/how-to-send-an-email-through-gmail-without-enabling-insecure-access
"""

with open('email_template_3.eml', 'rt', encoding='utf-8') as eml:
    EMAIL_TEMPLATE = eml.read()

class PaymentEmail:
    email_template = EMAIL_TEMPLATE

    def __init__(self, payment_info: PaymentInfo,
                 sender_email_address: str,
                 sender_name: str,
                 recipient_addresses: Tuple[EmailAddress], testmode=False):
        self.pi = payment_info
        self.sender = str(EmailAddress(sender_name, sender_email_address))
        self.recepients = ', '.join(str(addr) for addr in recipient_addresses)
        if testmode:
            self.ccs = self.sender
        else:
            self.ccs = str(EmailAddress(self.pi.troop.leader_name, self.pi.troop.leader_email))

    def create_email(self):
        qr_code = qr_platba_string(self.pi)
        email_text = self.email_template.format(payment_message=self.pi.payment_message,
                                                variable_symbol=self.pi.variable_symbol,
                                                specific_symbol=self.pi.specific_symbol,
                                                amount_czk=self.pi.amount_czk,
                                                human_account_number=self.pi.human_account_number,
                                                human_due_date=self.pi.human_due_date,
                                                sender=self.sender,
                                                recipients=self.recepients,
                                                ccs=self.ccs,
                                                qr_code_base64=QRCode(qr_code).base64str())
        return email_text


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
        """Send an email message.

      Args:
        user_id: User's email address. The special value "me"
        can be used to indicate the authenticated user.
        message: valid email message, with field such as recipient, body, etc.

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
