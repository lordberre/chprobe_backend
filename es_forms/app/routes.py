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
es_host = '127.0.0.1'
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
#client = Elasticsearch(['http://{}:{}@{}:{}/elasticsearch'.format(es_username,es_password,es_host,es_port)])

# ES Local
client = Elasticsearch()

#### Alternative to es_poll()
#from elasticsearch_dsl import Search
#from elasticsearch_dsl import A
#s = Search(using=client, index="chprobe_mgmt-*") \
#    .filter("exists", field="probe") \
#    .filter("range", **{'@timestamp': {'gte': 'now-30d', 'lt': 'now'}})
#s = s.params(size=2000)
#response = s.execute()
#data = response.hits.hits
####

class Probe():
    def __init__(self,name,description='N/A',location='N/A',eventlog='N/A',es_id=False,es_index=False,locations=[],location_index=0):
        self.description = description
        self.location = location
        self.locations = locations
        self.location_index = location_index
        self.name = name
        self.es_id = es_id
        self.eventlog = eventlog
        self.es_url = 'http://' + es_host + ':' + str(es_port) + '/elasticsearch'
        self.es_polledindex = '{}/chprobe_mgmt-{}/_search'.format(self.es_url,date)
        self.es_targetindex = 'chprobe_mgmt-*'
        self.es_index = es_index
        self.es_doc = {
               'probe': self.name,
               'location': self.location,
               'description': self.description,
               'event_log': self.eventlog,
               '@timestamp': datetime.utcnow()
               }

    def es_poll(self,probe=False):
        """Fetch data from ES and check fields"""
        if not probe:
            return('No Probe specified')
        client.indices.refresh(index=self.es_targetindex)
        result = client.search(index=self.es_targetindex, body={"query": {"match_all": {}}})
        print('Printing result (debug):',result) if debugging else None
        try:
            locations = self.locations
            for i,doc in enumerate(result['hits']['hits']):
                probe_key = doc['_source']['probe']
                location_key = (i,doc['_source']['location'])
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
        except KeyError as e:
#            for values in e:
            pass # Somehow instantate the objects that was error:ed with something generic.
            print('keyerror',e)
            return('Error:',e)
        except IndexError as f:
            print('Error: Probe not found!')
            return((self.location_index,locations))
        else:
            return((self.location_index,locations))

    def es_insert(self):
        if not self.es_id:
            # If id doesn't exist, create a new document in todays index
            self.es_targetindex = 'chprobe_mgmt-{}'.format(date)
            self.inserter = client.index(index=self.es_targetindex, doc_type='json', body=self.es_doc)

        else:
            # Update ES document if id exists
            self.es_targetindex = self.es_index
            print('Updating this document: {} now in index: {}, with our new info: {}'.format(self.es_id,self.es_targetindex,self.es_doc)) if debugging else None
            self.inserter = client.index(index=self.es_targetindex, doc_type='json', id=self.es_id, body=self.es_doc)
        result = self.es_poll()
        return(result)

@app.route("/chprobe_mgmt/<path>", methods=['GET', 'POST'])
def endpoint(path):
    print(path)
    p = Probe(path,eventlog=default_eventlog)
    polled_data = p.es_poll(path)
    probe_exists = polled_data[0]
    locations = set(polled_data[1])

    print('event_log:',p.eventlog, 'description:',p.description) if debugging else None
    form = ProbeForm(name=path,description=p.description,location=p.location,eventlog=p.eventlog)

### List of locations for selectField # TODO
#    form = ProbeForm(name=path,description=p.description,locationlist=locations,location=p.location,eventlog=p.eventlog)
#    location_choices = list(locations)
#    location_choices.insert(0,(0,'F18'))
#    form.locationlist.default = 0
#    form.locationlist.choices = location_choices
    print('Probe index location: {}, locations: {} (Debug)'.format(probe_exists,locations)) if debugging else None

    if form.validate_on_submit():
        flash('Debug: {}, description={}, location={} , eventlog={}'.format(
            form.name.data,form.description.data, form.location.data,form.eventlog.data)) if debugging else None

        # Init the object to overwrite ES data with new data.
        p = Probe(form.name.data,form.description.data,form.location.data,form.eventlog.data,p.es_id,p.es_index)

        # Now insert it
        p.es_insert()
        print('ES id (Debug):',p.es_id) if debugging else None
        return('Probe configuration updated!')

        p.es_insert()
        return('The probe did not exist, so it was added for you')
#        return redirect(/chprobe_mgmt/{}'.format(path))

    print('DATA!!!: {}'.format(p.name)) if debugging else None
    return render_template('probe_config.html', title='Configure Probe', form=form)
