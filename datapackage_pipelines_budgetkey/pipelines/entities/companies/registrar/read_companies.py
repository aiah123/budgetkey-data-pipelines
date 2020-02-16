import requests
from dataflows import (
    Flow, load, concatenate, update_resource,
    set_primary_key, set_type, printer
)
from datapackage_pipelines_budgetkey.common.google_chrome import google_chrome_driver



# Map the original column headers (in Hebrew) to the new column names (in English)
COLUMN_HEADERS_MAPPER = {
    'שם חברה': 'company_name',
    'מספר חברה':'id',
    'שם באנגלית':'company_name_eng',
    'סוג תאגיד':'company_type',
    'סטטוס חברה':'company_status',
    'תאור חברה':'company_description',
    'מטרת החברה':'company_goal',
    'תאריך התאגדות':'company_registration_date',
    'חברה ממשלתית':'company_is_government',
    'מגבלות':'company_limit',
    'מפרה':'company_is_mafera',
    'שנה אחרונה של דוח שנתי (שהוגש)':'company_last_report_year',
    'שם עיר':'company_city',
    'מיקוד':'company_postal_code',
    'ת.ד.':'company_pob',
    'מדינה':'company_country',
    'אצל':'company_located_at',
}



def _get_columns_mapping_dict():
    """
    Prepares the dict object for the concatenate function, which 'creates' new column names for existing column data

    Returns:
        dict: A dict of format {'new_column_header': ['original_column_header]},
    """

    columns_mapping_dict = {}
    for original_header in COLUMN_HEADERS_MAPPER:
        new_header = COLUMN_HEADERS_MAPPER[original_header]
        columns_mapping_dict[new_header] = [original_header]
    return columns_mapping_dict

def clear_bool_values(package):
    for res in package.pkg.descriptor['resources']:
        for field in res['schema']['fields']:
            if 'falseValues' in field:
                del field['falseValues']
            if 'trueValues' in field:
                del field['trueValues']
    yield package.pkg
    yield from package


def fetch_rows():
    params = dict(
        offset=0,
        limit=1000,
        resource_id='f004176c-b85f-4542-8901-7b3176f9a054'
    )
    url = 'https://data.gov.il/api/action/datastore_search'
    while True:
        resp = requests.get(url, params=params).json()
        if len(resp['result']['records']) == 0:
            break
        for x in resp['result']['records']:
            x['מספר חברה'] = str(x['מספר חברה']) if x['מספר חברה'] is not None else x['מספר חברה']
            x['מיקוד'] = str(x['מיקוד']) if x['מיקוד'] is not None else x['מיקוד']
            x['ת.ד.'] = str(x['ת.ד.']) if x['ת.ד.'] is not None else x['ת.ד.']
            for k, v in list(x.items()):
                if isinstance(v, str) and '~' in v:
                    x[k] = v.replace('~', '״')
            yield x
        params['offset'] += 1000


def flow(*_):
    # gcd = google_chrome_driver()
    # download = gcd.download('https://data.gov.il/dataset/246d949c-a253-4811-8a11-41a137d3d613/resource/f004176c-b85f-4542-8901-7b3176f9a054/download/f004176c-b85f-4542-8901-7b3176f9a054.csv')
    return Flow(
        fetch_rows(),
        concatenate(_get_columns_mapping_dict(), target=dict(name='company-details')),
        set_type('id', type='string'),
        set_type('company_registration_date', type='date', format='%Y-%m-%dT%H:%M:%S'),
        set_type('company_is_government', type='boolean', falseValues=['לא'], trueValues=['כן']),
        set_type('company_is_mafera', type='boolean', falseValues=['לא'], trueValues=['מפרה', 'התראה']),
        set_type('company_last_report_year', type='integer'),
        clear_bool_values,
        update_resource(**{'dpp:streaming': True}, resources='company-details'),
        set_primary_key(['id'], resources='company-details'),
        printer(),
    )


if __name__ == '__main__':
    flow().process()
