import dataclasses
import logging
import re
from dataclasses import dataclass
from typing import Tuple, List
import pandas as pd


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


def valid_email(email: str):
    """
    From https://stackoverflow.com/questions/8022530/how-to-check-for-valid-email-address
    """
    return bool(EMAIL_REGEX.fullmatch(email))


class PaymentsDataFrame:
    def __init__(self, sheet_df: pd.DataFrame,
                 needed_cols: NeededColumns):
        self.cols = needed_cols
        df = self.prepare_needed_columns(sheet_df, needed_cols)
        df_with_email, self.df_missing_email = self.split_missing_emails(df, self.cols.emails)

        selected_emails = self.split_multiple_emails(self.pick_first_valid_email(df_with_email, self.cols.emails))
        self.validate_emails(selected_emails)
        df_with_email.loc[:, 'selected_email'] = self.split_multiple_emails(selected_emails)

        self.df_emailable_unpaid, self.df_emailable_paid = self.split_unpaid_rows(df_with_email, self.cols.paid)

        logging.info(f"Of {len(df)} people, missing email: {len(self.df_missing_email)},"
                     f" emailable paid:{len(self.df_emailable_paid)}"
                     f" emailable unpaid:{len(self.df_emailable_unpaid)}")

    @staticmethod
    def validate_emails(emails: pd.Series):
        bad_emails = emails[~emails.apply(valid_email)]
        if len(bad_emails) > 0:
            raise ValueError(f"Some bad emails were selected: {bad_emails}")
        else:
            return True

    @staticmethod
    def split_multiple_emails(emails: pd.Series):
        return emails.apply(lambda em: em.split(', ')[0])

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

    @staticmethod
    def split_missing_emails(df: pd.DataFrame, email_cols: List[str]) -> Tuple[pd.DataFrame, pd.DataFrame]:
        missing_email_selector = df.loc[:, email_cols].isnull().all(axis=1)
        df_missing_email = df[missing_email_selector]
        df_with_email = df[~missing_email_selector]
        return df_with_email.copy(), df_missing_email.copy()

    @staticmethod
    def pick_first_valid_email(df: pd.DataFrame, email_cols: List[str]) -> pd.Series:
        return df.loc[:, email_cols].apply(lambda row: row.loc[row.first_valid_index()], axis=1)
