import csv
import json
import requests
from pprint import pprint
import argparse

parser = argparse.ArgumentParser()
parser.add_argument('-f', '--csv_file', required=True, help='CSV file to load')
args = parser.parse_args()


class Publisher:
    """Elements for producing the results"""
    def __init__(self):
        self.publish_header = {'Content-Type': 'application/x-www-form-urlencoded'}
        self.response = None
        self.publish_url = 'http://<<<url>>>'

    def populate_db(self, probe, location, description, event_log=None):
        if event_log is None:
            event_log = 'Date+%28YYYYMMDD+HH%3AMM%29+-+Event%0D%0A------------------------------%0D%0A1900-01-01+00%3A00+-+Probe+moved+from+HC+x+to+HC+y.%0D%0A&'
        probe_object = 'location={}&' \
                         'description={}&' \
                         'eventlog={}&' \
                         'submit=Submit+New+data'.format(location, description, event_log)
        publish_url = self.publish_url + probe
        json_doc = json.dumps(probe_object)
        print(json_doc)
        try:
            self.response = requests.post(publish_url, headers=self.publish_header, data=probe_object)
        except Exception as publish_error:
            print('Got an error when trying to publish the data: http code {}, error: {}'
                  .format(self.response, publish_error))
            pass

    def csv_loader(self, file):
        with open(file) as csv_file:
            csv_reader = csv.reader(csv_file, delimiter=',')
            line_count = 0
            for row in csv_reader:
                if line_count == 0:
                    print(f'Column names are {", ".join(row)}')
                    line_count += 1
                else:
                    self.populate_db(probe=row[0], location=row[1], description=row[2], event_log=row[3])
                    line_count += 1
            print(f'Processed {line_count} lines.')

    def wrapper(self):
        self.csv_loader(args.csv_file)


if __name__ == '__main__':
    p = Publisher()
    try:
        p.wrapper()

    except IOError as e:
        print(e)

