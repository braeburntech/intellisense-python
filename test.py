#!/usr/bin/env python
# encoding: utf-8

import unittest
import json

from datetime import datetime, timedelta

from random import randint
from time import sleep, time
from decimal import *

import logging
logging.basicConfig()

from dateutil.tz import tzutc

import intellisense
import intellisense.utils

secret = 'testsecret'


def on_success(data, response):
    print 'Success', response


def on_failure(data, error):
    print 'Failure', error


class AnalyticsBasicTests(unittest.TestCase):

    def setUp(self):
        intellisense.init(secret, log_level=logging.DEBUG)

        intellisense.on_success(on_success)
        intellisense.on_failure(on_failure)

    def test_timezone_utils(self):

        now = datetime.now()
        utcnow = datetime.now(tz=tzutc())

        self.assertTrue(intellisense.utils.is_naive(now))
        self.assertFalse(intellisense.utils.is_naive(utcnow))

        fixed = intellisense.utils.guess_timezone(now)

        self.assertFalse(intellisense.utils.is_naive(fixed))

        shouldnt_be_edited = intellisense.utils.guess_timezone(utcnow)

        self.assertEqual(utcnow, shouldnt_be_edited)

    def test_clean(self):

        simple = {
            'integer': 1,
            'float': 2.0,
            'long': 200000000,
            'bool': True,
            'str': 'woo',
            'unicode': u'woo',
            'decimal': Decimal('0.142857'),
            'date': datetime.now(),
        }

        complicated = {
            'exception': Exception('This should show up'),
            'timedelta': timedelta(microseconds=20),
            'list': [1, 2, 3]
        }

        combined = dict(simple.items() + complicated.items())

        pre_clean_keys = combined.keys()

        intellisense.default_client._clean(combined)

        self.assertEqual(combined.keys(), pre_clean_keys)
        
    def test_datetime_serialization(self):
        
        data = {
            'created': datetime(2012, 3, 4, 5, 6, 7, 891011),
        }
        result = json.dumps(data, cls=intellisense.utils.DatetimeSerializer)
        
        self.assertEqual(result, '{"created": "2012-03-04T05:06:07.891011"}')

    def test_async_basic_identify(self):
        # flush after every message
        intellisense.default_client.flush_at = 1
        intellisense.default_client.async = True

        last_identifies = intellisense.stats.identifies
        last_successful = intellisense.stats.successful
        last_flushes = intellisense.stats.flushes

        intellisense.identify('ilya@analytics.io', {
            "Subscription Plan": "Free",
            "Friends": 30
        })

        self.assertEqual(intellisense.stats.identifies, last_identifies + 1)

        # this should flush because we set the flush_at to 1
        self.assertEqual(intellisense.stats.flushes, last_flushes + 1)

        # this should do nothing, as the async thread is currently active
        intellisense.flush()

        # we should see no more flushes here
        self.assertEqual(intellisense.stats.flushes, last_flushes + 1)

        sleep(1)

        self.assertEqual(intellisense.stats.successful, last_successful + 1)

    def test_async_basic_track(self):

        intellisense.default_client.flush_at = 50
        intellisense.default_client.async = True

        last_tracks = intellisense.stats.tracks
        last_successful = intellisense.stats.successful

        intellisense.track('ilya@analytics.io', 'Played a Song', {
            "Artist": "The Beatles",
            "Song": "Eleanor Rigby"
        })

        self.assertEqual(intellisense.stats.tracks, last_tracks + 1)

        intellisense.flush()

        sleep(2)

        self.assertEqual(intellisense.stats.successful, last_successful + 1)

    def test_async_full_identify(self):

        intellisense.default_client.flush_at = 1
        intellisense.default_client.async = True

        last_identifies = intellisense.stats.identifies
        last_successful = intellisense.stats.successful

        traits = {
            "Subscription Plan": "Free",
            "Friends": 30
        }

        context = {
            "ip": "12.31.42.111",
            "location": {
                "countryCode": "US",
                "region": "CA"
            },
            "userAgent": ("Mozilla/5.0 (Macintosh; Intel Mac OS X 10_7_3) " +
                "AppleWebKit/534.53.11 (KHTML, like Gecko) Version/5.1.3 " +
                "Safari/534.53.10"),
            "language": "en-us"
        }

        intellisense.identify('ilya@analytics.io', traits,
            context=context, timestamp=datetime.now())

        self.assertEqual(intellisense.stats.identifies, last_identifies + 1)

        sleep(2)

        self.assertEqual(intellisense.stats.successful, last_successful + 1)

    def test_async_full_track(self):

        intellisense.default_client.flush_at = 1
        intellisense.default_client.async = True

        last_tracks = intellisense.stats.tracks
        last_successful = intellisense.stats.successful

        properties = {
            "Artist": "The Beatles",
            "Song": "Eleanor Rigby"
        }

        intellisense.track('ilya@analytics.io', 'Played a Song',
            properties, timestamp=datetime.now())

        self.assertEqual(intellisense.stats.tracks, last_tracks + 1)

        sleep(1)

        self.assertEqual(intellisense.stats.successful, last_successful + 1)

    def test_alias(self):

        session_id = str(randint(1000000, 99999999))
        user_id = 'bob+'+session_id + '@gmail.com'

        intellisense.default_client.flush_at = 1
        intellisense.default_client.async = False

        last_aliases = intellisense.stats.aliases
        last_successful = intellisense.stats.successful

        intellisense.identify(session_id, traits={'AnonymousTrait': 'Who am I?'})
        intellisense.track(session_id, 'Anonymous Event')

        # alias the user
        intellisense.alias(session_id, user_id)

        intellisense.identify(user_id, traits={'IdentifiedTrait': 'A Hunk'})
        intellisense.track(user_id, 'Identified Event')

        self.assertEqual(intellisense.stats.aliases, last_aliases + 1)
        self.assertEqual(intellisense.stats.successful, last_successful + 5)

    def test_blocking_flush(self):

        intellisense.default_client.flush_at = 1
        intellisense.default_client.async = False

        last_tracks = intellisense.stats.tracks
        last_successful = intellisense.stats.successful

        properties = {
            "Artist": "The Beatles",
            "Song": "Eleanor Rigby"
        }

        intellisense.track('ilya@analytics.io', 'Played a Song',
            properties, timestamp=datetime.today())

        self.assertEqual(intellisense.stats.tracks, last_tracks + 1)
        self.assertEqual(intellisense.stats.successful, last_successful + 1)

    def test_time_policy(self):

        intellisense.default_client.async = False
        intellisense.default_client.flush_at = 1

        # add something so we have a reason to flush
        intellisense.track('ilya@analytics.io', 'Played a Song', {
            "Artist": "The Beatles",
            "Song": "Eleanor Rigby"
        })

        # flush to reset flush count
        intellisense.flush()

        last_flushes = intellisense.stats.flushes

        # set the flush size trigger high
        intellisense.default_client.flush_at = 50
        # set the time policy to 1 second from now
        intellisense.default_client.flush_after = timedelta(seconds=1)

        intellisense.track('ilya@analytics.io', 'Played a Song', {
            "Artist": "The Beatles",
            "Song": "Eleanor Rigby"
        })

        # that shouldn't of triggered a flush
        self.assertEqual(intellisense.stats.flushes, last_flushes)

        # sleep past the time-flush policy
        sleep(1.2)

        # submit another track to trigger the policy
        intellisense.track('ilya@analytics.io', 'Played a Song', {
            "Artist": "The Beatles",
            "Song": "Eleanor Rigby"
        })

        self.assertEqual(intellisense.stats.flushes, last_flushes + 1)

    def test_performance(self):

        to_send = 100

        target = intellisense.stats.successful + to_send

        intellisense.default_client.async = True
        intellisense.default_client.flush_at = 200
        intellisense.default_client.max_flush_size = 50
        intellisense.default_client.set_log_level(logging.DEBUG)

        for i in range(to_send):
            intellisense.track('ilya@analytics.io', 'Played a Song', {
                "Artist": "The Beatles",
                "Song": "Eleanor Rigby"
            })

        print 'Finished submitting into the queue'

        start = time()
        while intellisense.stats.successful < target:
            print ('Successful ', intellisense.stats.successful, 'Left',
                (target - intellisense.stats.successful),
                'Duration ', (time() - start))
            intellisense.flush()
            sleep(1.0)

if __name__ == '__main__':
    unittest.main()
