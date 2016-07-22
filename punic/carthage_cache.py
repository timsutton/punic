__all__ = ['CarthageCache']

import re
import hashlib
from pathlib2 import Path
from .logger import *
import zipfile
import boto
import boto.s3
import os
import tempfile
from tqdm import tqdm
import pureyaml
from .shshutil import *

class CarthageCache(object):

    def __init__(self, config):
        self.config = config

        d = pureyaml.load(Path('.carthage_cache.yml').open())

        client_options = d[':aws_s3_client_options']
        self.AWS_ACCESS_KEY_ID = client_options[':access_key_id']
        self.AWS_SECRET_ACCESS_KEY = client_options[':secret_access_key']
        self.bucket_name = d[':bucket_name']
#        self.region = client_options.get(':region', None)

    @property
    def archives_directory_path(self):
        path = self.config.library_directory / "Archives"
        if not path.exists():
            path.mkdir(parents = True)
        return path

    def hash_for_project(self):
        output = self.config.xcode.check_call('xcrun swift -version')
        swift_version = re.search(r'Swift version ((?:\d+\.)*(?:\d+))', output).group(1)

        resolve_file = Path('Cartfile.resolved').open().read()
        data = '{}{}'.format(resolve_file, swift_version)
        hash = hashlib.sha256(data).hexdigest()
        return hash

    def archive_name_for_project(self):
        return '{}.zip'.format(self.hash_for_project())

    def archive(self):

        hash = self.hash_for_project()
        archive_file_name = self.archive_name_for_project()

        archive_path = self.archives_directory_path / archive_file_name
        if archive_path.exists():
            logger.info('Archive already exists in {}. Not recreating.'.format(self.archives_directory_path))
            return archive_path

        logger.info("Creating zipfile.")

        temp_dir = tempfile.mkdtemp()
        temp_archive_path = Path(temp_dir) / archive_file_name

        with zipfile.ZipFile(str(temp_archive_path), 'w', zipfile.ZIP_DEFLATED) as archive:
            def zipdir(root, ziph):
                all_files = list(walk_directory(root))

                logger.info('Computing total size')
                total_size = sum([file.stat().st_size for file in all_files])

                logger.info('Zipping')
                bar = tqdm(total=total_size, unit='B', unit_scale=True)
                for file in all_files:
                    ziph.write(str(file), str(file.relative_to(root)))
                    bar.update(file.stat().st_size)

            zipdir('Carthage/Build', archive)

        copyfile(temp_archive_path, archive_path)

        return archive_path

    def publish(self, archive_path = None):
        if not archive_path:
            archive_path = self.archive()

        conn = boto.connect_s3(self.AWS_ACCESS_KEY_ID, self.AWS_SECRET_ACCESS_KEY)
        bucket = conn.create_bucket(self.bucket_name, location=boto.s3.connection.Location.DEFAULT)
        key_name = archive_path.name

        if bucket.get_key(archive_path.name):
            logger.info('Archive already exists on S3. Skipping download.')
            return



        k = bucket.new_key(key_name)
        file_size = archive_path.stat().st_size

        bar = tqdm(total=file_size, unit='B', unit_scale=True)
        def percent_cb(complete, total):
            if not complete:
                return
            bar.update(complete - bar.n)

        k.set_contents_from_filename(str(archive_path), cb=percent_cb, num_cb=100)
        bar.close()

    def fetch(self, force = False):
        archive_file_name = self.archive_name_for_project()
        archive_path = self.archives_directory_path / archive_file_name
        if archive_path.exists() and not force:
            return archive_path

        logger.info("Downloading archive {} from {}".format(archive_file_name, self.bucket_name))

        connection = boto.connect_s3(self.AWS_ACCESS_KEY_ID, self.AWS_SECRET_ACCESS_KEY)
        bucket = connection.get_bucket(self.bucket_name)

        key = bucket.get_key(archive_file_name)
        content_length = int(key.content_length)

        bar = tqdm(total=content_length, unit='B', unit_scale=True)
        def percent_cb(complete, total):
            if not complete:
                return
            bar.update(complete - bar.n)

        temp_dir = tempfile.mkdtemp()
        temp_archive_path = Path(temp_dir) / archive_file_name

        key.get_contents_to_filename(str(temp_archive_path), cb=percent_cb, num_cb=100)
        bar.close()

        if force and archive_path.exists():
            archive_path.unlink()

        copyfile(temp_archive_path, archive_path)

        return archive_path

    def install(self):
        archive_path = self.fetch(force = False)

        temp_dir = Path(tempfile.mkdtemp())

        logger.info('Expanding archive.')
        with zipfile.ZipFile(str(archive_path)) as archive:
            archive.extractall(str(temp_dir))

        if self.config.build_path.exists():
            rmtree(self.config.build_path)

        logger.info('Replacing {}.'.format(self.config.build_path))
        move(temp_dir, self.config.build_path)


def walk_directory(path):
    for root, dirs, files in os.walk(str(path)):
        for file in files:
            yield (Path(root) / file)
