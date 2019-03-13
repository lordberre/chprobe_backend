# Version 0.2

from app import app
from app.forms import ProbeForm
from flask import render_template, flash, redirect, url_for
from elasticsearch import Elasticsearch
from datetime import datetime

# Vars
timepattern = '%Y-%m-%dT%H:%M:%S.%Z'
debugging = False

# Target index for the new doc
date = datetime.now().strftime("%Y.%m.%d")
es_port = 9200
es_host = 'srv-chprobes-node-1.int.comhem.com'
es_username = ''
es_password = ''

# Default event log table
default_eventlog = ("""
Date (YYYYMMDD HH:MM) - Event
------------------------------
1900-01-01 00:00 - Probe moved from HC x to HC y.
""")

# Create ES object
# Kibana proxy
# client = Elasticsearch(['http://{}:{}@{}:{}/elasticsearch'.format(es_username,es_password,es_host,es_port)])

# ES chprobes node
client = Elasticsearch(['http://{}:{}'.format(es_host, es_port)])


class Probe:
    def __init__(self, name, description='N/A', location='N/A', eventlog='N/A', es_id=False,
                 es_index=False, location_index=0):
        self.description = description
        self.location = location
        self.locations = list()
        self.location_index = location_index
        self.name = name
        self.timestamp = None
        self.es_id = es_id
        self.eventlog = eventlog
        self.es_url = 'http://' + es_host + ':' + str(es_port) + '/elasticsearch'
        self.es_polledindex = '{}/chprobe_mgmt-{}/_search'.format(self.es_url, date)
        self.es_targetindex = 'chprobe_mgmt-*'
        self.es_index = es_index
        self.es_doc = {
               'probe': self.name,
               'location': self.location,
               'description': self.description,
               'event_log': self.eventlog,
               '@timestamp': datetime.utcnow()
               }

    def es_poll(self, probe=False, probe_key=None):
        """Fetch data from ES and check fields"""
        if not probe:
            return 'No Probe specified'
        client.indices.refresh(index=self.es_targetindex)
        result = client.search(size=10000, index=self.es_targetindex, body={"query": {"match_all": {}}})
        # result = client.search(index=self.es_targetindex, body={"query": "query_string": {"query": probe_query}})
        try:
            locations = self.locations
            for i, doc in enumerate(result['hits']['hits']):
                probe_key = doc['_source']['probe']
                location_key = (i, doc['_source']['location'])
                locations.append(location_key)
                if probe in probe_key:
                    self.es_id = doc['_id']
                    self.es_index = doc['_index']
                    self.name = doc['_source']['probe']
                    self.location_index = i
                    self.description = doc['_source']['description']
                    self.location = doc['_source']['location']
                    self.eventlog = doc['_source']['event_log']
                    self.timestamp = doc['_source']['@timestamp']
                    print(doc)

            if debugging:
                print(
                    """probe (from api call): {} \n
                     probe key (from elastic query): {} \n
                     location: {} and description: {} (from elastic query)""".format(
                        probe, probe_key, self.location, self.description))
        except KeyError as e:
            pass  # Somehow instantate the objects that was error:ed with something generic.
            print('keyerror', e)
            return 'Error:', e
        except IndexError:
            print('Error: Probe not found!')
            return self.location_index, locations
        else:
            return self.location_index, locations

    def es_insert(self):
        if not self.es_id:
            # If id doesn't exist, create a new document in todays index
            self.es_targetindex = 'chprobe_mgmt-{}'.format(date)
            self.inserter = client.index(index=self.es_targetindex, doc_type='json', body=self.es_doc)

        else:
            # Update ES document if id exists
            self.es_targetindex = self.es_index
            print('Updating this document: {} now in index: {}, with our new info: {}'
                  .format(self.es_id, self.es_targetindex, self.es_doc)) if debugging else None
            self.inserter = client.index(index=self.es_targetindex, doc_type='json', id=self.es_id, body=self.es_doc)
        result = self.es_poll()
        return result


@app.route("/chprobe_mgmt/<path>", methods=['GET', 'POST'])
def endpoint(path):
    print(path)
    p = Probe(path, eventlog=default_eventlog)
    polled_data = p.es_poll(path)
    probe_exists = polled_data[0]
    locations = set(polled_data[1])

    print('event_log:', p.eventlog, 'description:', p.description) if debugging else None
    form = ProbeForm(name=path, description=p.description, location=p.location, eventlog=p.eventlog)

    print('Probe index location: {}, locations: {} (Debug)'.format(probe_exists, locations)) if debugging else None

    if form.validate_on_submit():
        flash('Debug: {}, description={}, location={} , eventlog={}'.format(
            form.name.data, form.description.data, form.location.data, form.eventlog.data)) if debugging else None

        # Init the object to overwrite ES data with new data.
        p = Probe(form.name.data, form.description.data, form.location.data, form.eventlog.data, p.es_id, p.es_index)

        # Now insert it
        p.es_poll(path)  # Update the object (poll es) first
        p.es_insert()
        print('ES id (Debug):', p.es_id) if debugging else None
        # return(redirect('/chprobe_mgmt/' + path))
        return 'Probe configuration updated!'

    print('DATA!!!: {}'.format(p.name)) if debugging else None
    return render_template('probe_config.html', title='Configure Probe', form=form)

