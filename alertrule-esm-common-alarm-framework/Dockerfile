ARG ERIC_ENM_SLES_BASE_IMAGE_NAME=sles
ARG ERIC_ENM_SLES_BASE_IMAGE_REPO=armdocker.rnd.ericsson.se/proj-ldc/common_base_os_release
ARG ERIC_ENM_SLES_BASE_IMAGE_TAG=6.16.0-13
ARG CENM_METRICS_RPM_VERSION=1.8.1

FROM ${ERIC_ENM_SLES_BASE_IMAGE_REPO}/${ERIC_ENM_SLES_BASE_IMAGE_NAME}:${ERIC_ENM_SLES_BASE_IMAGE_TAG}


ARG ERIC_ENM_SLES_BASE_IMAGE_TAG
ARG CENM_METRICS_RPM_VERSION

COPY ./image_content/scripts /etc/opt/ericsson/cenmmetrics

RUN zypper addrepo -C -G -f https://arm.sero.gic.ericsson.se/artifactory/proj-ldc-repo-rpm-local/common_base_os/sles/${ERIC_ENM_SLES_BASE_IMAGE_TAG}?ssl_verify=no COMMON_BASE_OS_SLES_REPO \
    && zypper install -l -y curl wget python3 python3-pip\
    && zypper clean --all
    
RUN wget -q https://arm1s11-eiffel004.eiffel.gic.ericsson.se:8443/nexus/content/repositories/releases/com/ericsson/oss/itpf/ERICenmcapacity_CXP9041377/${CENM_METRICS_RPM_VERSION}/ERICenmcapacity_CXP9041377-${CENM_METRICS_RPM_VERSION}.rpm


RUN rpm -i ERICenmcapacity_CXP9041377-${CENM_METRICS_RPM_VERSION}.rpm

RUN /usr/bin/pip install 'kubernetes==21.7.0' -i https://arm.rnd.ki.sw.ericsson.se/artifactory/api/pypi/pypi-remote/simple
