import logging
import os
import sys
from datetime import date, datetime
import config
from cryptography.fernet import Fernet
import pandas as pd
from io import BytesIO
from typing import List

# sendmail is a custom local package
from sendmail import sendmail


def configure_logger() -> str:
    """
    Configure the logger for the application
    """
    # Close previous handlers
    for handler in logging.root.handlers[:]:
        logging.root.removeHandler(handler)

    # Log configuration
    message_format = "%(asctime)s - %(levelname)s - %(message)s"

    if not os.path.exists(f'{config.REPOSITORY_PATH}/log'):
        os.mkdir(f'{config.REPOSITORY_PATH}/log')

    log_file_path = f'{config.REPOSITORY_PATH}/log/log_cug_update_{date.today().isoformat()}.txt'
    logging.basicConfig(format=message_format,
                        level=logging.INFO,
                        handlers=[logging.FileHandler(log_file_path),
                                  logging.StreamHandler(sys.stdout)],
                        force=True)

    return log_file_path


def close_loggers() -> None:
    """
    Close the logger
    """
    logging.shutdown()


def decrypt_data(file_path) -> pd.DataFrame:
    """Decrypt the data from the file and return CSV pandas dataframe

    Note:
        The data is encrypted using Fernet encryption algorithm.
        The secret key is stored in the environment variable `abn_slsp_exchange_secret`.
        The file is decrypted and read into a pandas dataframe.
        Separator is ';'.
    """
    # the data in the repo is encrypted as a second protection
    # we have to decrypt it first
    cipher_suite = Fernet(os.getenv('abn_slsp_exchange_secret'))

    with open(file_path, "rb") as encrypted_file:
        encrypted_data = encrypted_file.read()

    # decrypting into memory
    decrypted_data = cipher_suite.decrypt(encrypted_data)

    # We use BytesIO to feed data in memory into pd
    data_stream = BytesIO(decrypted_data)
    try:
        df = pd.read_csv(data_stream, sep=';')
        return df

    except pd.errors.ParserError:
        logging.error(f'Error reading file {file_path}.')
        sys.exit(1)


def encrypt_data(data: pd.DataFrame, file_path: str) -> None:
    """Encrypt the data and write to the file

    Note:
        The data is encrypted using Fernet encryption algorithm.
        The secret key is stored in the environment variable `abn_slsp_exchange_secret`.
        The file is encrypted and written to the file.
    """
    cipher_suite = Fernet(os.getenv('abn_slsp_exchange_secret'))
    data_stream = BytesIO()
    data.to_csv(data_stream, sep=';', index=False)
    data_stream.seek(0)
    encrypted_data = cipher_suite.encrypt(data_stream.read())

    with open(file_path, "wb") as encrypted_file:
        encrypted_file.write(encrypted_data)


def decrypt_log_file(log_file_path: str) -> str:
    """Decrypt the log file and return the decrypted file path

    Note:
        The data is encrypted using Fernet encryption algorithm.
        The secret key is stored in the environment variable `abn_slsp_exchange_secret`.
        The file is decrypted and written to the file.
    """
    cipher_suite = Fernet(os.getenv('abn_slsp_exchange_secret'))

    with open(log_file_path, "rb") as encrypted_file:
        encrypted_data = encrypted_file.read()

    decrypted_data = cipher_suite.decrypt(encrypted_data)

    decrypted_file_path = log_file_path[:-4] + '_decrypted.log'
    with open(decrypted_file_path, "wb") as decrypted_file:
        decrypted_file.write(decrypted_data)

    return decrypted_file_path


def encrypt_log_file(log_file_path: str) -> str:
    """Encrypt the log file and write to the file

    Note:
        The data is encrypted using Fernet encryption algorithm.
        The secret key is stored in the environment variable `abn_slsp_exchange_secret`.
        The file is encrypted and written to the file.
    """
    cipher_suite = Fernet(os.getenv('abn_slsp_exchange_secret'))

    with open(log_file_path, "rb") as log_file:
        log_data = log_file.read()

    encrypted_data = cipher_suite.encrypt(log_data)

    encrypted_log_file_path = f'{config.REPOSITORY_PATH}/log/encrypted_log.txt'
    with open(encrypted_log_file_path, "wb") as encrypted_file:
        encrypted_file.write(encrypted_data)

    return encrypted_log_file_path


def strtodate(txt: str) -> datetime:
    """Convert date string to datetime format

    Parameters
    ----------
    txt: str

    Returns
    -------
    datetime
        txt converted into datetime format
    """
    return datetime.strptime(txt, '%Y-%m-%dZ')


def send_report(reports: List[str]) -> None:
    """Send an email with the report attached

    Parameters
    ----------
    reports: List[str]
        List of reports to send
    """

    reports = '\n\n****************\n\n'.join(reports)

    # At least one user group updated
    sendmail(config.REPORT_DESTINATION,
             'ABN CUG processes report',
             reports)
