import dataclasses
import logging
import re
from dataclasses import dataclass
from typing import Tuple

import pandas as pd

from mail_encoding import remove_accents


@dataclass(order=True)
class NeededColumns:
    """
    Columns in the gooogle sheet
    """
    name: str = 'Osoba'
    troop: str = 'Jednotka'
    reg_num: str = 'Registrační číslo'
    email1: str = 'E-mail (hlavní)'
    email2: str = 'Otec: mail'
    email3: str = 'Matka: mail'
    email4: str = 'E-mail (další)'
    email5: str = 'Ostatní: mail'
    paid: str = '2/2021'

    def colnames(self):
        return dataclasses.astuple(self)

    @property
    def emails(self):
        return [self.email1, self.email3, self.email2, self.email4, self.email5]


NEEDED_COLS = NeededColumns()
EMAIL_REGEX = re.compile(r"[^@]+@[^@]+\.[^@]+")


@dataclass
class EmailAddress:
    label: str
    address: str

    def is_valid(self):
        """
        From https://stackoverflow.com/questions/8022530/how-to-check-for-valid-email-address
        """
        return bool(EMAIL_REGEX.fullmatch(self.address))

    def __str__(self):
        return f'"{remove_accents(self.label)}" <{self.address}>'


def split_and_strip_emails(emails: str, separator=','):
    email_list = emails.split(separator)
    return [email.strip() for email in email_list]


def get_lists_of_emails(row: pd.Series, email_cols) -> pd.Series:
    # 'emails' string can contain multiple addresses. Get all non-empty emails
    emails_list = ((col, emails)
                   for col, emails in
                   zip(email_cols, row[email_cols].values)
                   if emails)  # if email not None or ''

    # split multiple emails in one string and strip whitespace
    email_list = tuple(EmailAddress(col, email) for col, emails in emails_list
                  for email in split_and_strip_emails(emails))

    # remove duplicates
    # reverse order so that the values first in the list are not removed when removing duplicates
    unique = {email.address: email for email in reversed(email_list)}
    unique_emails = unique.values()

    # split into two lists, valid and invalid emails
    valid_emails = (email for email in unique_emails if email.is_valid())
    invalid_emails = (email for email in unique_emails if not email.is_valid())

    new_row = pd.Series([tuple(valid_emails), tuple(invalid_emails)])
    new_row.index = ['valid_emails', 'invalid_emails']
    return new_row


class PaymentsDataFrame:
    def __init__(self, sheet_df: pd.DataFrame,
                 needed_cols: NeededColumns):
        self.cols = needed_cols
        df = self.prepare_needed_columns(sheet_df, needed_cols)

        # Extract emails into lists of valid and invalid email addresses
        emails = df.apply(get_lists_of_emails, args=(self.cols.emails,), axis=1)
        df = pd.concat([df, emails], axis=1)

        emailable = df.valid_emails.apply(len) > 0
        df_with_email = df[emailable]
        self.df_missing_email = df[~emailable]

        self.df_emailable_unpaid, self.df_emailable_paid = self.split_unpaid_rows(df_with_email, self.cols.paid)

        n_invalid_emails = df.invalid_emails.apply(len).sum()
        logging.info(f"Of {len(df)} people, missing email: {len(self.df_missing_email)},\n"
                     f"\temailable paid: {len(self.df_emailable_paid)}\n"
                     f"\temailable unpaid: {len(self.df_emailable_unpaid)}.\n "
                     f"Also there were {n_invalid_emails} invalid emails.")

    @staticmethod
    def prepare_needed_columns(df: pd.DataFrame, cols: NeededColumns) -> pd.DataFrame:
        assert set(cols.colnames()).issubset(df.columns)
        df = df.loc[:, cols.colnames()]
        df.replace({'': None}, inplace=True)
        return df

    @staticmethod
    def split_unpaid_rows(df: pd.DataFrame, paid_col) -> Tuple[pd.DataFrame, pd.DataFrame]:
        empty_payment = df.loc[:, paid_col].isnull()
        unpaid_df = df[empty_payment]
        paid_df = df[~empty_payment]
        return unpaid_df, paid_df
