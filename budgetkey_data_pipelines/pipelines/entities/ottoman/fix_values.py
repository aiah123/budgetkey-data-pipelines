from datapackage_pipelines.wrapper import process


def process_row(row, *_):
    if len(row['id']) != 11:
        return None
    row['id'] = row['id'][:-2]
    row['name'] = row['name'].strip()
    row['address'] = row['address'].strip()
    return row


process(process_row=process_row)