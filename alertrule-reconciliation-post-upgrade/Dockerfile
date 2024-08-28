ARG ERIC_ENM_SLES_BASE_IMAGE_NAME=sles
ARG ERIC_ENM_SLES_BASE_IMAGE_REPO=armdocker.rnd.ericsson.se/proj-ldc/common_base_os_release
ARG ERIC_ENM_SLES_BASE_IMAGE_TAG=6.16.0-13
FROM ${ERIC_ENM_SLES_BASE_IMAGE_REPO}/${ERIC_ENM_SLES_BASE_IMAGE_NAME}:${ERIC_ENM_SLES_BASE_IMAGE_TAG}

ARG ERIC_ENM_SLES_BASE_IMAGE_TAG

COPY ./image_content/scripts /etc/opt/ericsson/alertrules
RUN zypper addrepo -C -G -f https://arm.sero.gic.ericsson.se/artifactory/proj-ldc-repo-rpm-local/common_base_os/sles/${ERIC_ENM_SLES_BASE_IMAGE_TAG}?ssl_verify=no COMMON_BASE_OS_SLES_REPO \
    && zypper install -l -y curl python3 python3-pip\
    && zypper clean --all

RUN /usr/bin/pip install 'requests==2.24.0' -i https://arm.rnd.ki.sw.ericsson.se/artifactory/api/pypi/pypi-remote/simple

RUN /usr/bin/pip install 'psycopg2-binary==2.9.3' -i https://arm.rnd.ki.sw.ericsson.se/artifactory/api/pypi/pypi-remote/simple

