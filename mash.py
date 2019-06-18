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
import shutil

RUNTIME_DIR = os.environ.get('MASH_RUNTIME_DIR', 'runtime')
BIN_DIR = os.environ.get('MASH_BIN_DIR', RUNTIME_DIR+'/bin')
DATA_DIR = os.environ.get('MASH_DATA_DIR', RUNTIME_DIR+'/data')
SANDBOX_DIR = os.environ.get('MASH_SANDBOX_DIR', RUNTIME_DIR+'/sandbox')

class Mailer(object):
    def __init__(self):
        login = os.environ['MASH_SMTP_LOGIN']
        password = os.environ['MASH_SMTP_PASSWORD']
        smtp_server = os.environ['MASH_SMTP_SERVER']

        self.mail = imaplib.IMAP4_SSL(smtp_server)
        self.mail.login(login, password)
        self.mail.select('inbox')

    def get_uids(self, criterion='ALL'):
        _, data = self.mail.uid('search', None, criterion)
        return data[0].split()

    def get_message(self, uid):
        _, data = self.mail.uid('fetch', uid, '(RFC822)')
        for response_part in data:
            if isinstance(response_part, tuple):
                return email.message_from_string(response_part[1]) # pylint: disable=unsubscriptable-object

class MailDb(object):
    def __init__(self):
        self.db_path = RUNTIME_DIR + "/mails.lst"

        self.db = []
        if os.path.isfile(self.db_path):
            with open(self.db_path) as db_file:
                for line in db_file:
                    uid = line.rstrip("\n")
                    if uid not in self.db:
                        self.db.append(uid)
        # logging.debug("mail db: %s", str(self.db))

    def is_new(self, uid):
        return uid not in self.db

    def add(self, uid):
        if self.is_new(uid):
            self.db.append(uid)
            self.save()

    def save(self):
        with open(self.db_path, "w") as db_file:
            db_file.write("\n".join(self.db))

def extract_content(mail):
    """Extract mail content"""
    content = ""
    for part in mail.walk():
        if part.get_content_type() == 'text/plain':
            content += part.get_payload()
    return content

def extract_urls(content):
    """Extract data from mail"""
    url_re = re.compile(r"https?://[^/]+/[a-zA-Z0-9?=-_]+")
    for match in re.finditer(url_re, content):
        url = match.group(0)
        if url.startswith("https://www.youtube.com/")\
                or url.startswith("https://youtu.be/"):
            yield url

def download_video(url):
    """Process url"""
    youtube_dl = BIN_DIR + "/youtube-dl"

    # prepare isolation
    if os.path.isdir(SANDBOX_DIR):
        shutil.rmtree(SANDBOX_DIR)
    os.mkdir(SANDBOX_DIR)

    try:
        # download file(s)
        cmd = [youtube_dl,\
               "--extract-audio",\
               "--audio-format", "mp3",\
               "--format", "140",\
               url]
        out = subprocess.check_output(cmd, cwd=SANDBOX_DIR, stderr=subprocess.STDOUT)

        # save audio
        files = os.listdir(SANDBOX_DIR)
        for filename in files:
            if filename.endswith(".mp3"):
                org = os.path.join(SANDBOX_DIR, filename)
                dest = os.path.join(DATA_DIR, filename)

                if os.path.isfile(dest):
                    logging.warning("overwritting %s ..", dest)
                    os.remove(dest)

                logging.debug("saving %s ..", org)
                shutil.copyfile(org, dest)

        return (url, True, out)
    except subprocess.CalledProcessError as error:
        out = error.output
        logging.error("failed to download %s: %s", url, out)
        return (url, False, out)

def process():
    """Handle request"""
    mailer = Mailer()
    uids = list(mailer.get_uids())
    logging.debug("mails: %s", str(uids))

    mail_db = MailDb()
    for uid in uids:
        if mail_db.is_new(uid):
            logging.debug("mail %s is new: processing ..", uid)

            mail = mailer.get_message(uid)
            content = extract_content(mail)
            logging.debug("mail content: %s", content.rstrip("\n\r"))

            urls = list(extract_urls(content))
            logging.debug("extracted urls: %s", str(urls))
            for url in urls:
                logging.debug("downloading %s ..", url)
                _, status, _ = download_video(url)
                logging.debug("%s: %s", url, "ok" if status else "ko")
            mail_db.add(uid)

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

    # def test_extract_content(self):
        # """Test mail process"""
        # contents = list(extract_contents([]))
        # self.assertEqual(contents, [])

    def test_extract_urls(self):
        """Test content process"""
        content = "https://www.youtube.com/watch?v=EzKImzjwGyM\r\n"
        urls = list(extract_urls(content))
        self.assertEqual(urls, ["https://www.youtube.com/watch?v=EzKImzjwGyM"])

# class IntegrationTests(unittest.TestCase):
    # """Side effect functions"""
    # # pylint: disable=too-many-public-methods

    # def setUp(self):
        # # logging.basicConfig(stream=sys.stderr, level=logging.DEBUG)
        # return

    # def test_simple(self):
        # """Simple case"""
        # expected_file = "A short ocean video-EzKImzjwGyM.mp3"
        # if os.path.isfile(expected_file):
            # os.remove(expected_file)

        # process()

        # self.assertTrue(os.path.isfile(expected_file))
        # os.remove(expected_file)

    # def test_get_mails(self):
        # """Test mail getter"""
        # mails = list(get_mails())
        # self.assertEqual(len(mails), 1)

    # def test_download_videos(self):
        # """Test downloader"""
        # urls = ["https://www.youtube.com/watch?v=EzKImzjwGyM"]
        # expected_file = "A short ocean video-EzKImzjwGyM.mp3"
        # if os.path.isfile(expected_file):
            # os.remove(expected_file)

        # reports = list(download_videos(urls))

        # self.assertEqual(len(reports), 1)
        # url, status, log = reports[0]
        # self.assertEqual(url, "https://www.youtube.com/watch?v=EzKImzjwGyM")
        # if not status:
            # logging.error(log)
        # self.assertEqual(status, True)
        # self.assertTrue(len(log) > 100)

        # self.assertTrue(os.path.isfile(expected_file))
        # os.remove(expected_file)
