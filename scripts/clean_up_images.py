import logging
import subprocess

LIST_IMAGES_COMMAND_PREFIX = 'gcloud container images list-tags'
DELETE_IMAGES_COMMAND_PREFIX = 'gcloud container images delete'

# Allow at most 3 versions of images stored at container registry
ALLOWED_SIZE = 3


def delete_old_images(image_name):
    list_command = LIST_IMAGES_COMMAND_PREFIX + \
        ' gcr.io/python-compatibility-tools/{}'.format(image_name) + ' --format=get(digest)'
    digests = subprocess.check_output(list_command.split(' '))
    digests_list = digests.decode('utf-8').strip('\n').split('\n')
    num_of_digests = len(digests_list)

    if num_of_digests > ALLOWED_SIZE:
        to_delete = digests_list[ALLOWED_SIZE:]
        print(to_delete)
        for digest in to_delete:
            command = DELETE_IMAGES_COMMAND_PREFIX + \
                ' gcr.io/python-compatibility-tools/{}@{}'.format(image_name, digest) \
                + ' --force-delete-tags'
            subprocess.check_output(command.split(' '))
            logging.info('Removed image {}@{}'.format(image_name, digest))


def main():
    for image_name in ['python27', 'python36']:
        delete_old_images(image_name)


if __name__ == '__main__':
    main()

