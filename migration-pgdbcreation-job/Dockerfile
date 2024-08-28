ARG OS_BASE_IMAGE_NAME=sles
ARG OS_BASE_IMAGE_REPO=armdocker.rnd.ericsson.se/proj-ldc/common_base_os_release
ARG OS_BASE_IMAGE_TAG=6.16.0-13
ARG BINARY_URL=https://arm.sero.gic.ericsson.se/artifactory/proj-pc-cnom-generic-local
ARG NODEJS_VERSION=18.17.1

FROM ${OS_BASE_IMAGE_REPO}/${OS_BASE_IMAGE_NAME}:${OS_BASE_IMAGE_TAG}
ARG OS_BASE_IMAGE_TAG

RUN zypper addrepo -C -G -f https://arm.sero.gic.ericsson.se/artifactory/proj-ldc-repo-rpm-local/common_base_os/sles/${OS_BASE_IMAGE_TAG}?ssl_verify=no COMMON_BASE_OS_SLES_REPO \
    && zypper install -l -y wget \
    && zypper clean --all

WORKDIR /
ENV PATH=/bin:${PATH}


ARG BINARY_URL
ARG NODEJS_VERSION
RUN wget -q ${BINARY_URL}/nodejs/node-v$NODEJS_VERSION-linux-x64.tar.gz \
    && tar -xzf node-v$NODEJS_VERSION-linux-x64.tar.gz \
    && rm node-v$NODEJS_VERSION-linux-x64.tar.gz \
    && chown -R root:root node-v$NODEJS_VERSION-linux-x64 \
    && ln -s ../node-v$NODEJS_VERSION-linux-x64/bin/node bin/node \
    && ln -s ../node-v$NODEJS_VERSION-linux-x64/bin/npm bin/npm


COPY ./image_content/scripts /etc/opt/ericsson/pgdbcreation
WORKDIR /etc/opt/ericsson/pgdbcreation
RUN /bin/npm install
