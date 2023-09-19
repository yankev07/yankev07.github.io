from api import logger
from app import app
from google.cloud import storage
import os


def _get_bucket():
    storage_client = storage.Client.from_service_account_json(app.config['GOOGLE_APPLICATION_CREDENTIALS'],
                                                              project=app.config['GOOGLE_TEMPLATES_PROJECT'])

    try:
        return storage_client.get_bucket(app.config['GOOGLE_TEMPLATES_BUCKET'])
    except:
        logger.critical(None, 'could not obtain handle to bucket %s' % app.config['GOOGLE_TEMPLATES_BUCKET'])
        return None


def validate(name):
    bucket = _get_bucket()

    if bucket:
        files = list()
        prefix = 'Templates/%s/' % name

        for blob in bucket.list_blobs(prefix=prefix):
            if blob.name != prefix:
                files.append({'name': blob.name, 'generation': blob.generation})

        if files:
            return files

        logger.error(None, 'template %s does not exist' % name)


def download(name, destdir, info=None):
    bucket = _get_bucket()

    if bucket:
        os.makedirs(destdir, exist_ok=True)

        if info:
            blobs = [bucket.blob(i['name'], generation=i['generation']) for i in info]
        else:
            blobs = bucket.list_blobs(prefix='Templates/%s' % name)

        try:
            for b in blobs:
                b.download_to_filename(os.path.join(destdir, b.name.split('/')[-1]))

            return True
        except:
            logger.error(None, 'could not download template %s' % name)


def listall():
    bucket = _get_bucket()

    if bucket:
        templates = list()

        # filter blobs whose name end in "main.tf" (ie if template does not contain main.tf, it is not considered
        # a template)
        for blob in filter(lambda b: b.name.endswith('/main.tf'), bucket.list_blobs(prefix='Templates')):
            # template name will be folder sitting just below /Templates
            name = blob.name.split('/')[1]

            # don't add name to list twice (could happen if template has a subtree containing multiple main.tf's)
            if name not in templates:
                templates.append(name)

        return templates