import dataclasses
import logging
from dataclasses import dataclass
from email.headerregistry import Address
from typing import Tuple

import pandas as pd

from prispevky.config import CONFIG


@dataclass(order=True)
class NeededColumns:
    """
    Columns in the gooogle sheet
    TODO: this should be saved differently to allow specifying columns on the fly
    """
    name: str = 'Osoba'
    troop: str = 'Jednotka'
    reg_num: str = 'Registrační číslo'
    email1: str = 'E-mail (hlavní)'
    email2: str = 'Otec: mail'
    email3: str = 'Matka: mail'
    email4: str = 'E-mail (další)'
    email5: str = 'Ostatní: mail'
    amount_due: str = CONFIG['sheet_columns']['amount_due']
    amount_paid: str = CONFIG['sheet_columns']['amount_paid']

    def colnames(self):
        return dataclasses.astuple(self)

    @property
    def czk_amounts(self):
        return self.amount_due, self.amount_paid

    @property
    def emails(self):
        return [self.email1, self.email3, self.email2, self.email4, self.email5]


def split_and_strip_emails(emails: str, separator=','):
    email_list = emails.split(separator)
    return [email.strip() for email in email_list]


def get_lists_of_emails(row: pd.Series, email_cols) -> pd.Series:
    # 'emails' string can contain multiple addresses. Get all non-empty emails
    raw_addresses_list = ((col, emails)
                          for col, emails in
                          zip(email_cols, row[email_cols].values)
                          if emails)  # if email not None or ''

    address_list = []
    invalid_emails = []
    for col, addresses in raw_addresses_list:
        # split multiple emails in one string and strip whitespace
        for email in split_and_strip_emails(addresses):
            try:
                address = Address(col, addr_spec=email)
                # don't add duplicate email addresses
                if address.addr_spec not in [addr.addr_spec for addr in address_list]:
                    address_list.append(address)
            except ValueError as e:
                logging.warning(f"Incorrect email address read: '{col}': '{email}'; {e}")
                invalid_emails.append((col, email))

    new_row = pd.Series([tuple(address_list), tuple(invalid_emails)])
    new_row.index = ['valid_addresses', 'invalid_addresses']
    return new_row


class PaymentsDataFrame:
    def __init__(self, sheet_df: pd.DataFrame,
                 needed_cols: NeededColumns):
        self.cols = needed_cols
        df = self.prepare_needed_columns(sheet_df, needed_cols)

        # Extract emails into lists of valid and invalid email addresses
        emails = df.apply(get_lists_of_emails, args=(self.cols.emails,), axis=1)
        df = pd.concat([df, emails], axis=1)

        # TODO: instead of splitting the df into different dataframes for emailable, paid, ..., I could just use one
        #  dataframes with flags, and filter depending on the flag.

        emailable = df.valid_addresses.apply(len) > 0
        df_with_email = df.loc[emailable]
        self.df_missing_email = df.loc[~emailable]

        df_with_email = self.convert_currency_columns_to_number_and_fill_na(df_with_email, self.cols)

        self.df_emailable_unpaid, self.df_emailable_paid = self.split_unpaid_rows(df_with_email, self.cols)

        n_invalid_addresses = df.invalid_addresses.apply(len).sum()
        logging.info(f"Of {len(df)} people, missing email: {len(self.df_missing_email)},\n"
                     f"\temailable paid: {len(self.df_emailable_paid)}\n"
                     f"\temailable unpaid: {len(self.df_emailable_unpaid)}.\n "
                     f"Also there were {n_invalid_addresses} invalid emails.")

    @staticmethod
    def prepare_needed_columns(df: pd.DataFrame, cols: NeededColumns) -> pd.DataFrame:
        assert set(cols.colnames()).issubset(df.columns), \
            f"Sheets don't have the needed column: {set(cols.colnames()) - set(df.columns)} (have following: \n {df.columns})"
        df = df.loc[:, cols.colnames()]
        df.replace({'': None}, inplace=True)
        return df

    @staticmethod
    def convert_currency_columns_to_number_and_fill_na(df: pd.DataFrame, cols: NeededColumns) -> pd.DataFrame:
        df_fixed = df.copy()
        payments = df.loc[:, cols.czk_amounts].fillna(0)
        for col in cols.czk_amounts:
            df_fixed.loc[:, col] = pd.to_numeric(payments.loc[:, col])
        return df_fixed

    @staticmethod
    def split_unpaid_rows(df: pd.DataFrame, cols: NeededColumns) -> Tuple[pd.DataFrame, pd.DataFrame]:
        payments = df.loc[:, cols.czk_amounts]
        paid = payments.loc[:, cols.amount_paid] >= payments.loc[:, cols.amount_due]
        unpaid_df = df[~paid]
        paid_df = df[paid]
        return unpaid_df, paid_df

    @staticmethod
    def split_simple_unpaid_rows(df: pd.DataFrame, paid_col) -> Tuple[pd.DataFrame, pd.DataFrame]:
        empty_payment = df.loc[:, paid_col].isnull()
        unpaid_df = df[empty_payment]
        paid_df = df[~empty_payment]
        return unpaid_df, paid_df
