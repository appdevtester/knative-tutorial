# Copyright 2020 Google LLC
# SPDX-License-Identifier: Apache-2.0

import json
import logging
import os
import pandas
import matplotlib.pyplot as plt

from flask import Flask, request
from google.cloud import bigquery
from google.cloud import storage

app = Flask(__name__)

@app.route('/', methods=['POST'])
def handle_post():
    # TODO: Read proper CloudEvent with the SDK
    app.logger.info("Received CloudEvent")
    content = json.loads(request.data)
    query_covid_dataset(content)
    return 'OK', 200

def query_covid_dataset(content):
    country = content['country']
    tableId = content['tableId']

    client = bigquery.Client()

    query = f"""
        SELECT
        date, num_reports
        FROM `covid19_jhu_csse.{tableId}`
        ORDER BY date ASC"""
    app.logger.info(f'Running query: {query}')

    query_job = client.query(query)

    results = query_job.result()
    # for row in results:
    #     print("{}: {} ".format(row.date, row.num_reports))

    df = (
        results
        .to_dataframe()
    )
    app.logger.info(df.tail())

    ax = df.plot(kind='line', x='date', y='num_reports')
    ax.set_title(f'Covid Cases in {country}')
    # ax.set_xlabel('Date')
    # ax.set_ylabel('Number of cases')
    #plt.show()

    file_name = f'chart-{tableId}.png'
    app.logger.info(f'Saving file locally: {file_name}')

    plt.savefig(file_name)

    upload_blob(file_name)

def upload_blob(file_name):
    storage_client = storage.Client()
    bucket_name = os.environ.get('BUCKET')
    bucket = storage_client.bucket(bucket_name)
    blob = bucket.blob(file_name)
    blob.upload_from_filename(file_name)
    app.logger.info(f'File {file_name} uploaded to bucket {bucket_name}')


if __name__ != '__main__':
    # Redirect Flask logs to Gunicorn logs
    gunicorn_logger = logging.getLogger('gunicorn.error')
    app.logger.handlers = gunicorn_logger.handlers
    app.logger.setLevel(gunicorn_logger.level)
    plt.switch_backend('Agg') # to prevent background UI threads
    app.logger.info('Service started...')
else:
    plt.switch_backend('Agg') # to prevent background UI threads
    app.run(debug=True, host='0.0.0.0', port=int(os.environ.get('PORT', 8080)))