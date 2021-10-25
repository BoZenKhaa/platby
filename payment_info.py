import datetime
from dataclasses import dataclass
import pandas as pd
from unidecode import unidecode

from config import CONFIG
from payment_data import NEEDED_COLS

IBAN_ACC_NUMBER = CONFIG['payment']['iban']
AMOUNT_CZK = CONFIG['payment']['amount_czk']
SS_PREFIX = CONFIG['payment']['ss_prefix']
DUE_DATE = datetime.date.today() + datetime.timedelta(days=10)
PAYMENT_MESSAGE = CONFIG['payment']['message_template']


@dataclass
class Troop:
    name: str
    text_code: str
    num_code: str
    leader_name: str
    leader_email: str

    @property
    def specific_symbol(self):
        return f"{SS_PREFIX}{self.num_code}"

    @classmethod
    def from_string(cls, coma_separated_fields: str):
        args = [v.strip() for v in coma_separated_fields.split(',')]
        return cls(*args)


troops = [Troop.from_string(v) for k, v in CONFIG['troops'].items()]
TROOPS = {troop.name: troop for troop in troops}


@dataclass
class PaymentInfo:
    _name: str
    troop: Troop
    variable_symbol: str
    _due_date: datetime.date
    amount_czk: str
    iban_account_number: str

    def __post_init__(self):
        assert len(self._name) > 5
        assert len(self.variable_symbol) > 2
        assert int(self.amount_czk) > 0

    @property
    def name(self):
        return unidecode(self._name)

    @property
    def specific_symbol(self):
        return self.troop.specific_symbol

    @property
    def payment_message(self):
        # Unidecode to get rid of accents
        msg = unidecode(PAYMENT_MESSAGE.format(troop_code=self.troop.text_code, name=self.name))
        # trim to 60 characters
        msg = msg[:61]
        assert len(msg) <= 60
        return msg

    @property
    def human_account_number(self):
        """Parses IBAN format into human form.

        CZkk bbbb ssss sscc cccc cccc
        Where:
        b = National bank code
        s = Account number prefix
        c = Account number

        See https://en.wikipedia.org/wiki/International_Bank_Account_Number"""
        country = self.iban_account_number[:2]
        checksum = self.iban_account_number[2:4]
        bank = self.iban_account_number[4:8]
        prefix = self.iban_account_number[8:14]
        account_number = self.iban_account_number[14:24]

        assert f"{country}{checksum}{bank}{prefix}{account_number}" == self.iban_account_number

        return f"{prefix}-{account_number}/{bank}"

    @property
    def qr_code_due_date(self):
        return self._due_date.strftime("%Y%m%d")

    @property
    def human_due_date(self):
        return self._due_date.strftime("%d. %m. %Y")

    @classmethod
    def from_df_row(cls, row: pd.Series):
        troop = TROOPS[row.loc[NEEDED_COLS.troop]]
        return cls(row.loc[NEEDED_COLS.name],
                   troop,
                   row.loc[NEEDED_COLS.reg_num],
                   DUE_DATE,
                   AMOUNT_CZK,
                   IBAN_ACC_NUMBER)
