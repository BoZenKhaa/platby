import base64
import io
import qrcode

from payment_info import PaymentInfo

PAYMENT_CODE_TEMPLATE = r"SPD*1.0*ACC:{acc_number}*AM:{amount_czk:.2f}*CC:CZK" \
                r"*MSG:{message}*X-VS:{vs}*X-SS:{ss}*DT:{due_date}"

def qr_platba_string(pi:PaymentInfo):
    """Format from https://qr-platba.cz/"""
    code = PAYMENT_CODE_TEMPLATE.format(message=pi.name, vs=pi.variable_symbol, ss=pi.specific_symbol,
                                        acc_number=pi.account_number, amount_czk=pi.amount,
                                        due_date=pi.due_date)
    return code


class QRCode:
    def __init__(self, code):
        self.img = qrcode.make(code)
        # type(img)  # qrcode.image.pil.PilImage

    def save(self, filename):
            self.img.save(f"{filename}.png")

    def base64str(self):
        """
        Convert image to base64 string, as used in the email template.
        from https://stackoverflow.com/questions/42503995/how-to-get-a-pil-image-as-a-base64-encoded-string
        """

        # Save to memory buffer
        in_mem_file = io.BytesIO()
        self.img.save(in_mem_file, format="PNG")

        # reset file pointer to start
        in_mem_file.seek(0)
        img_bytes = in_mem_file.read()

        base64_encoded_result_bytes = base64.b64encode(img_bytes)
        base64_encoded_result_str = base64_encoded_result_bytes.decode('ascii')
        return base64_encoded_result_str


if __name__ == '__main__':
    qr_code = QRCode(qr_platba_string("test", 1234, 56789))
    print(qr_code.base64str())
    qr_code.save("qr_code_test")


