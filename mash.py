#!/usr/bin/python
# -*- coding: utf-8 -*-

"""Bash over mail"""

import sys
import argparse
import unittest
import logging
import os
import imaplib
import email
import re
import subprocess

def get_mails():
    """Get mailbox content"""
    login = os.environ['MASH_SMTP_LOGIN']
    password = os.environ['MASH_SMTP_PASSWORD']
    smtp_server = os.environ['MASH_SMTP_SERVER']

    mail = imaplib.IMAP4_SSL(smtp_server)
    mail.login(login, password)
    mail.select('inbox')

    _, data = mail.search(None, 'ALL')
    mail_ids = data[0]

    id_list = mail_ids.split()
    first_email_id = int(id_list[0])
    latest_email_id = int(id_list[-1])

    for i in range(latest_email_id, first_email_id, -1):
        _, data = mail.fetch(i, '(RFC822)')

        for response_part in data:
            if isinstance(response_part, tuple):
                yield email.message_from_string(response_part[1]) # pylint: disable=unsubscriptable-object

def extract_contents(mails):
    """Extract mail content"""
    for mail in mails:
        content = ""
        for part in mail.walk():
            if part.get_content_type() == 'text/plain':
                content += part.get_payload()
        yield content

def extract_urls(contents):
    """Extract data from mails"""
    url_re = re.compile(r"https?://[^/]+/[a-zA-Z0-9?=-_]+")
    for content in contents:
        for match in re.finditer(url_re, content):
            url = match.group(0)
            if url.startswith("https://www.youtube.com/")\
                    or url.startswith("https://youtu.be/"):
                yield url

def download_videos(urls):
    """Process urls"""
    bin_dir = os.environ['MASH_BIN_DIR']
    youtube_dl = bin_dir + "/youtube-dl"
    for url in urls:
        try:
            if os.path.isfile("info.json"):
                os.remove("info.json")
            cmd = [youtube_dl, "--extract-audio",\
                    "--audio-format", "mp3", "-f", "140",\
                    "-l", url]
            out = subprocess.check_output(cmd, stderr=subprocess.STDOUT)
            yield (url, True, out)
        except subprocess.CalledProcessError as error:
            yield (url, False, error.output)

def process():
    """Handle request"""
    mails = list(get_mails())
    logging.debug("retrieved %d mails", len(mails))
    contents = list(extract_contents(mails))
    logging.debug(contents)
    urls = list(extract_urls(contents))
    logging.debug(urls)
    for url, status, _ in download_videos(urls):
        logging.debug("%s: %s", url, "ok" if status else "ko")

def main():
    """Entry point"""

    # Parse options
    parser = argparse.ArgumentParser()
    parser.add_argument("-d", "--debug", action="store_true", default=False,
                        help="show debug information")
    args = parser.parse_args()

    # Configure debug
    if args.debug:
        logging.basicConfig(stream=sys.stderr, level=logging.DEBUG)
        logging.debug("Enabled debug logging")

    process()

    return 0

if __name__ == "__main__":
    sys.exit(main())

# run test suite with
# "python -m unittest <this_module_name_without_py_extension>"

class UnitTests(unittest.TestCase):
    """Pure functions"""
    # pylint: disable=too-many-public-methods

    def test_extract_contents(self):
        """Test mail process"""
        contents = list(extract_contents([]))
        self.assertEqual(contents, [])

    def test_extract_urls(self):
        """Test content process"""
        contents = ["https://www.youtube.com/watch?v=EzKImzjwGyM\r\n"]
        urls = list(extract_urls(contents))
        self.assertEqual(urls, ["https://www.youtube.com/watch?v=EzKImzjwGyM"])

class IntegrationTests(unittest.TestCase):
    """Side effect functions"""
    # pylint: disable=too-many-public-methods

    def setUp(self):
        # logging.basicConfig(stream=sys.stderr, level=logging.DEBUG)
        return

    def test_simple(self):
        """Simple case"""
        expected_file = "A short ocean video-EzKImzjwGyM.mp3"
        if os.path.isfile(expected_file):
            os.remove(expected_file)

        process()

        self.assertTrue(os.path.isfile(expected_file))
        os.remove(expected_file)

    def test_get_mails(self):
        """Test mail getter"""
        mails = list(get_mails())
        self.assertEqual(len(mails), 1)

    def test_download_videos(self):
        """Test downloader"""
        urls = ["https://www.youtube.com/watch?v=EzKImzjwGyM"]
        expected_file = "A short ocean video-EzKImzjwGyM.mp3"
        if os.path.isfile(expected_file):
            os.remove(expected_file)

        reports = list(download_videos(urls))

        self.assertEqual(len(reports), 1)
        url, status, log = reports[0]
        self.assertEqual(url, "https://www.youtube.com/watch?v=EzKImzjwGyM")
        if not status:
            logging.error(log)
        self.assertEqual(status, True)
        self.assertTrue(len(log) > 100)

        self.assertTrue(os.path.isfile(expected_file))
        os.remove(expected_file)
