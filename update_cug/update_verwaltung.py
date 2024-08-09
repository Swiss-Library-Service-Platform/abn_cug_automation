from typing import List
from datetime import date
import pandas as pd
import os
from almapiwrapper.analytics import AnalyticsReport
from almapiwrapper.users import User
import config


def workflow() -> str:
    """
    Update the user group of users with an email address ending with 'ag.ch' and not already
    in the user group 'ABN_Patron-Kantonale-Verwaltung'

    Returns
    -------
    str
        string containing the report data
    """
    primary_ids = fetch_analytics_report()

    update_users(primary_ids)

    report = update_report(primary_ids)

    return report


def fetch_analytics_report() -> List[str]:
    """
    Fetch the analytics report and return the list of primary IDs of users to update

    Returns
    -------
    List[str]
        List of primary IDs of users to update
    """

    # A configured analytics read-only key is required
    report = AnalyticsReport(config.VERWALTUNG_ANALYTICS_REPORT_PATH,
                             config.IZ)

    data = report.data

    # Avoid critical error if the report is not found
    if report.error is True or data is None:
        return []

    # Filter data, additional check, analytics report should already be filtered
    filtered_data = data.loc[~data['User Group Code'].isin([config.HFGS_USER_GROUP_CODE,
                                                            config.MEDIOTHEK_USER_GROUP_CODE,
                                                            config.VERWALTUNG_USER_GROUP_CODE])]
    primary_ids = filtered_data['Primary Identifier'].tolist()

    # Limit to 50 users => limit risk in case of problem with analytics report
    return primary_ids[:50]


def update_users(primary_ids: List[str]):
    """
    Update the user group of the users

    Parameters
    ----------
    primary_ids: List[str]
        List of primary IDs of users to update
    """
    for primary_id in primary_ids:
        # Fetch user data
        u = User(primary_id, 'ABN')

        # Define user group
        u.data['user_group']['value'] = 'ABN_Patron-Kantonale-Verwaltung'

        # Update user, override is required to update user group if there is already a user group change on the account
        u.update(override=['user_group'])


def update_report(primary_ids: List[str]) -> str:
    """
    Write the report of the process

    Parameters
    ----------
    primary_ids: List[str]
        List of primary IDs of users to update

    Returns
    -------
    str
        string containing the report data
    """

    if os.path.isfile(config.PATH_TO_REPORT_VERWALTUNG):
        df = pd.read_csv(config.PATH_TO_REPORT_VERWALTUNG,
                         dtype={'date': str,
                                'nb_new_users': int})
    else:
        df = pd.DataFrame(columns=['date', 'nb_new_users'])

    df.loc[len(df)] = {'date': date.today().isoformat(),
                       'nb_new_users': len(primary_ids)}

    df.to_csv(config.PATH_TO_REPORT_VERWALTUNG, index=False)

    return df.tail(5).to_markdown(index=False)
