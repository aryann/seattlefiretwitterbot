import logging
import os
import sys
import time

import requests
import twitter

import parser


_DATA_URL = ('http://www2.seattle.gov/fire/realtime911/'
             'getRecsForDatePub.asp?action=Today&incDate=&rad1=des')
_USER_ID = '1276990331880267777'


def _fetch_dispatch_data():
    response = requests.get(_DATA_URL)
    response.raise_for_status()
    return response.text


def _get_last_tweet_text(api):
    timeline = api.GetUserTimeline(user_id=_USER_ID, count=10)
    if not timeline:
        raise ValueError()
    return timeline[0].text


_api = twitter.Api(consumer_key=os.environ['API_KEY'],
                   consumer_secret=os.environ['API_KEY_SECRET'],
                   access_token_key=os.environ['ACCESS_TOKEN'],
                   access_token_secret=os.environ['ACCESS_TOKEN_SECRET'])


def reconcile():
    logging.info('getting last tweet...')
    last_tweet = _get_last_tweet_text(_api)
    logging.info('last tweet was: %s', last_tweet)

    logging.info('getting latest incidents...')
    incidents = parser.get_incidents(_fetch_dispatch_data().splitlines())
    incidents_to_tweet = []
    for incident in incidents:
        if (incident['units'] in last_tweet and
                incident['location'] in last_tweet):
            break
        incidents_to_tweet.append(incident)
    incidents_to_tweet.reverse()

    logging.info('found %d incidents to tweet', len(incidents_to_tweet))
    for incident in incidents_to_tweet:
        status = (f"{incident['units']} dispatched to {incident['location']}, "
                  '#Seattle.'
                  f"\n\nType: {incident['type']}"
                  f"\n\n{incident['map_link']}")
        logging.info("new tweet with length %d: <%s>",
                     len(status), status)

        if not os.environ.get('DRY_RUN', False):
            try:
                _api.PostUpdate(status)
                logging.info('posted tweet')
            except twitter.error.TwitterError as e:
                logging.error('error posting status: %s', e)
            time.sleep(1)

    return 'ok\n'


if __name__ == '__main__':
    reconcile()

