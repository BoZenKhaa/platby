from googleapiclient import errors
import base64
import logging

from google_authentication import GOOGLE_CREDENTIALS
from googleapiclient.discovery import build

from payment_info import PaymentInfo
from qr_code import qr_platba_string

""" Inspired by
https://stackoverflow.com/questions/25944883/how-to-send-an-email-through-gmail-without-enabling-insecure-access
"""

with open('email_template.eml', 'rt', encoding='utf-8') as eml:
    EMAIL_TEMPLATE = eml.read()


class PaymentEmail:
    email_template = EMAIL_TEMPLATE

    def __init__(self, payment_info: PaymentInfo,
                 sender_email_address: str,
                 sender_name: str,
                 recipient_email_address: str):
        self.pi = payment_info
        self.sender_email_address = sender_email_address
        self.sender_name = sender_name
        self.recipient_email_address = recipient_email_address

    def create_email(self):
        email_text = self.email_template.format(**{k: v for k, v in self.pi.__dict__.items()},
                                                sender=self.sender_email_address,
                                                sender_name=self.sender_name,
                                                recipient=self.recipient_email_address,
                                                recipient_name=self.pi.name,
                                                qr_code_base64=qr_platba_string(self.pi))
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
            logging.info('Message Id: %s', sent_message['id'])
        except errors.HttpError as error:
            logging.error('An HTTP error occurred: %s', error)
            sent_message = None
            status = error
        return dict(sent_msg=sent_message, attempted_message=message, send_status=status)
