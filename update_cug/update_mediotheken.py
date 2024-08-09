import os
from update_cug import tools
import pandas as pd
import config
import logging
from datetime import date
from almapiwrapper.users import fetch_users, User
from typing import Optional


def workflow() -> str:
    """
    This function is the main workflow of the process to update the CUG of Mediotheken users.

    Returns
    -------
    str
        string containing the report data
    """

    # Load source data
    df_source = tools.decrypt_data(config.PATH_TO_SOURCE_DATA)

    # Rename the columns of the source data, order must be last_name, first_name, birth_date, barcode
    df_source.columns = ['last_name', 'first_name', 'birth_date', 'barcode']
    df_source['birth_date'] = pd.to_datetime(df_source['birth_date'], format='%Y-%m-%d')

    # Since data is read as string. Not available values are read as 'nan' string
    # => need to be replaced with empty string
    df_source['barcode'] = df_source['barcode'].astype(str).replace('nan', '')

    # Check if current state table exists, if no a new one is created
    if os.path.isfile(config.PATH_TO_DATA_CURRENT_STATE) is True:
        df_current_state = tools.decrypt_data(config.PATH_TO_DATA_CURRENT_STATE)
        logging.info('Current state table loaded.')
    else:
        logging.warning('No current state table -> creating a new one.')
        df_current_state = create_current_state_df(df_source)

    # Actualize the current state table, compare the current state with the source data
    # If source data changed, the current state is also updated.
    df_current_state = actualize_current_state_table(df_source, df_current_state)

    # Iterate on each user
    for i, _ in df_current_state.iterrows():

        # Check CUG of the user
        user = update_user_cug(i, df_current_state)

        # Check barcode for users, who have already the new CUG, but no barcode
        if not df_current_state.loc[i, 'barcode_added'] and df_current_state.loc[i, 'cug_updated']:
            if user is None:
                user = User(df_current_state.loc[i, 'primary_id'], zone=config.IZ)
                _ = user.data

            if user.error is False:
                df_current_state.loc[i, 'barcode_added'] = check_user_barcode(user, df_current_state.loc[i, 'barcode'])

    # Write the report
    report = update_report(df_current_state)

    # Save the current state table
    tools.encrypt_data(df_current_state, config.PATH_TO_DATA_CURRENT_STATE)

    return report


def reset_current_state_table() -> None:
    """This function is used to reset all flags of the current state table to False.

    This script can be used in case of error in the current state table.
    """
    df_source = tools.decrypt_data(config.PATH_TO_SOURCE_DATA)
    df_source.columns = ['last_name', 'first_name', 'birth_date', 'barcode']
    df_source['birth_date'] = pd.to_datetime(df_source['birth_date'], format='%Y-%m-%d')
    df_source['barcode'] = df_source['barcode'].astype(str).replace('nan', '')

    logging.info('Create a new current state table.')
    df_current_state = create_current_state_df(df_source)

    # Actualize the current state table
    df_current_state = actualize_current_state_table(df_source, df_current_state)

    # Save the current state table
    tools.encrypt_data(df_current_state, config.PATH_TO_DATA_CURRENT_STATE)


def create_current_state_df(df_source) -> pd.DataFrame:
    """If this file doesn't exist, it should be created

    This file is used to track the state of the process from the last run.
    """
    df = df_source.copy()
    df['primary_id'] = ''
    df['barcode_added'] = False
    df['cug_updated'] = False
    df['skipped'] = False
    df['message'] = ''

    # correct date format to datetime compatible format
    df['birth_date'] = pd.to_datetime(df['birth_date'], format='%d.%m.%Y')

    return df


def actualize_current_state_table(df_source: pd.DataFrame, df_current_state: pd.DataFrame) -> pd.DataFrame:
    """This function actualize the current state table with the new data of source data.

    The source data is master data. If a row doesn't exist in source data, it will be deleted
    from current state data. New row from source data will be added to current state data.

    Parameters
    ----------
    df_source: pd.DataFrame
        Source data
    df_current_state: pd.DataFrame
        Current state data

    Returns
    -------
    pd.DataFrame
        Actualized current state data
    """
    df_current_state = clean_current_state_table_col_types(df_current_state)

    df_current_state = df_source.merge(df_current_state,
                                       on=['last_name', 'first_name', 'birth_date', 'barcode'],
                                       how='left')

    df_current_state = clean_current_state_table_col_types(df_current_state)

    return df_current_state


def update_user_cug(i: int, df: pd.DataFrame) -> Optional[User]:
    """This function fetch user and update it in the NZ. It check also the IZ
    user to know if it has already the new user group.

    Parameters
    ----------
    i: int
        Index of the user in the DataFrame

    df: pd.DataFrame
        DataFrame containing the current state of the data from the last run.
    """

    # This user is already fully processed => skip it
    if df.loc[i, 'cug_updated']:
        logging.info(f'{i + 1} / {len(df)}: SKIPPED {df.loc[i, "barcode"]}')
        return

    df.loc[i, 'message'] = ''
    logging.info(f'{i + 1} / {len(df)}: handling {df.loc[i, "barcode"]}')

    # Fetch users by name
    users = [u for u in
             fetch_users(f'last_name~{df.loc[i, "last_name"].replace(" ", "_")} '
                         f'and first_name~{df.loc[i, "first_name"].replace(" ", "_")}',
                         zone=config.IZ)
             if u.primary_id.endswith('eduid.ch')]

    if len(users) == 0:
        logging.warning(f'No match found with name {df.loc[i, "last_name"]}, {df.loc[i, "first_name"]}')
        return

    # Filter with birth date
    users_found = [u for u in users if df.loc[i, 'birth_date'] == tools.strtodate(u.data['birth_date'])]

    # Multi matches case
    if len(users_found) > 1:
        logging.error(
            f'Several accounts with same name and same birth date ({df.loc[i, "Name"]}, {df.loc[i, "Vorname"]}), '
            f'probably duplicated accounts => SKIPPED: {", ".join([u.primary_id for u in users_found])}')
        df.loc[i, 'skipped'] = True
        df.loc[i, 'message'] = (f'Several accounts with same name and same birth date ({df.loc[i, "last_name"]}, '
                                f'{df.loc[i, "first_name"]}), probably duplicated accounts => SKIPPED: '
                                f'{", ".join([u.primary_id for u in users_found])}')
        return

    # No match case
    if len(users_found) == 0:
        logging.warning(
            f'Match found with name {df.loc[i, "last_name"]}, {df.loc[i, "first_name"]}, '
            f'but no match with birth date: looking for {df.loc[i, "birth_date"].strftime("%Y-%m-%d")} / '
            f'found in alma accounts '
            f'{", ".join([u.primary_id + " (" + u.data["birth_date"][:-1] + ")" for u in users])}')

        df.loc[i, 'message'] = (f'Match found with name {df.loc[i, "last_name"]}, {df.loc[i, "first_name"]}, '
                                f'but no match with birth date: looking for'
                                f'{df.loc[i, "birth_date"].strftime("%Y-%m-%d")} / '
                                f'found in alma accounts '
                                f'{", ".join([u.primary_id + " (" + u.data["birth_date"][:-1] + ")" for u in users])} '
                                f'=> SKIPPED')
        return

    # Handle account
    user_iz = users_found[0]
    primary_id = user_iz.primary_id
    df.loc[i, 'primary_id'] = primary_id

    if user_iz.data['user_group']['value'] == config.MEDIOTHEK_USER_GROUP_CODE:
        # We set the flag "updated" to True to avoid new tests on this user
        df.loc[i, 'cug_updated'] = True
        logging.info(f'{user_iz.primary_id}: user group already "{config.MEDIOTHEK_USER_GROUP_CODE}"')
        return user_iz
    else:
        # Update the user group
        user_iz.data['user_group']['value'] = config.MEDIOTHEK_USER_GROUP_CODE
        user_iz.update(override=['user_group'])

        if user_iz.error is False:
            logging.info(f'{user_iz.primary_id}: user group updated to "{config.MEDIOTHEK_USER_GROUP_CODE}"')
            df.loc[i, 'cug_updated'] = True
            return user_iz
        else:
            logging.error(f'{user_iz.primary_id}: error updating user group')
            df.loc[i, 'message'] = 'Error updating user group'
            return


def check_user_barcode(user: User, barcode: str) -> bool:
    """Check if the barcode is already existing for the user and add it if not.

    Parameters
    ----------
    user: User
        User to check
    barcode: str
        Barcode to check if it's already existing
    """
    if barcode == '':
        logging.warning(f'{repr(user)}: no barcode provided')
        return False

    result = barcode.lower() in [identifier['value'].lower() for identifier in user.data['user_identifier']]
    logging.info(f'{repr(user)}: barcode {barcode} {"already existing" if result else "missing"}')
    return result


def clean_current_state_table_col_types(df_current_state: pd.DataFrame) -> pd.DataFrame:
    """Clean the data types of the current state table

    It fills the empty cells with the correct data type and replace 'nan' string with empty string.

    Parameters
    ----------
    df_current_state: pd.DataFrame
        Current state data
    """
    df_current_state['birth_date'] = pd.to_datetime(df_current_state['birth_date'])
    df_current_state['barcode_added'] = df_current_state['barcode_added'].fillna(False).astype(bool)
    df_current_state['cug_updated'] = df_current_state['cug_updated'].fillna(False).astype(bool)
    df_current_state['skipped'] = df_current_state['skipped'].fillna(False).astype(bool)
    df_current_state['message'] = df_current_state['message'].astype(str).replace('nan', '')
    df_current_state['barcode'] = df_current_state['barcode'].astype(str).replace('nan', '')
    return df_current_state


def update_report(df_current_state: pd.DataFrame) -> str:
    """Write the report of the process in a file

    Parameters
    ----------
    df_current_state: pd.DataFrame
        DataFrame containing the report data

    Returns
    -------
    str
        string containing the report data

    """
    if os.path.isfile(config.PATH_TO_REPORT_MEDIOTHEKEN):
        df = pd.read_csv(config.PATH_TO_REPORT_MEDIOTHEKEN,
                         dtype={'date': str,
                                'nb_users': int,
                                'nb_users_updated': int,
                                'nb_barcode_added': int,
                                'nb_users_skipped': int})
    else:
        df = pd.DataFrame(columns=['date', 'nb_users', 'nb_users_updated', 'nb_barcode_added', 'nb_users_skipped'])

    df.loc[len(df)] = {'date': date.today().isoformat(),
                       'nb_users': len(df_current_state),
                       'nb_users_updated': len(df_current_state[df_current_state['cug_updated']]),
                       'nb_barcode_added': len(df_current_state[df_current_state['barcode_added']]),
                       'nb_users_skipped': len(df_current_state[df_current_state['skipped']])}

    df.to_csv(config.PATH_TO_REPORT_MEDIOTHEKEN, index=False)

    return df.tail(5).to_markdown(index=False)
