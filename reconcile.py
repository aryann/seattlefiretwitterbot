import argparse
import logging
import os
import sys
import time

import flask
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

_app = flask.Flask(__name__)


@_app.route('/', methods=['POST'])
def reconcile():
    logging.info('getting last tweet...')
    last_tweet = _get_last_tweet_text(_api)
    logging.info('last tweet was: %s', last_tweet)

    logging.info('getting latest incidents...')
    incidents = parser.get_incidents(_fetch_dispatch_data().splitlines())
    incidents_to_tweet = []
    for incident in incidents:
        if incident['location'] in last_tweet:
            break
        incidents_to_tweet.append(incident)
    incidents_to_tweet.reverse()

    logging.info('found %d incidents to tweet.', len(incidents_to_tweet))
    for incident in incidents_to_tweet:
        status = (f"{incident['units']} dispatched to {incident['location']}, "
                  '#Seattle.'
                  f"\n\nType: {incident['type']}"
                  f"\n\n{incident['map_link']}")
        logging.info("new tweet with length %d:\n\n%s\n\n\n",
                     len(status), status)

        if not args.dry_run:
            _api.PostUpdate(status)
            time.sleep(1)

    return 'ok\n'


if __name__ == '__main__':
    logging.basicConfig(level=logging.INFO)

    arg_parser = argparse.ArgumentParser()
    arg_parser.add_argument('--dry-run',
                            default=False, action='store_true')
    args = arg_parser.parse_args()
    logging.info('flags: %s', args)

    _app.run(debug=False, host='0.0.0.0',
             port=int(os.environ.get('PORT', 8080)))
