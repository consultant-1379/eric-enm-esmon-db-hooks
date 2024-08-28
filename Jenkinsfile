#!/usr/bin/env groovy

/* IMPORTANT:
 *
 * In order to make this pipeline work, the following configuration on Jenkins is required:
 * - slave with a specific label (see pipeline.agent.label below)
 * - credentials plugin should be installed and have the secrets with the following names:
 *   + lciadm100credentials (token to access Artifactory)
 */

def defaultBobImage = 'armdocker.rnd.ericsson.se/sandbox/adp-staging/adp-cicd/bob.2.0:1.5.2-0'
def bob = new BobCommand()
        .bobImage(defaultBobImage)
        .envVars([ISO_VERSION: '${ISO_VERSION}', ENM_ISO_REPO_VERSION: '${ENM_ISO_REPO_VERSION}'])
        .needDockerSocket(true)
        .toString()
def GIT_COMMITTER_NAME = 'enmadm100'
def GIT_COMMITTER_EMAIL = 'enmadm100@ericsson.com'
def failedStage = ''
pipeline {
    agent {
        label 'Cloud-Native'
    }
    parameters {
        string(name: 'ISO_VERSION', description: 'The ENM ISO version (e.g. 1.65.77)')
        string(name: 'SPRINT_TAG', description: 'Tag for GIT tagging the repository after build')
    }
    stages {
        stage('Clean') {
            steps {
                deleteDir()
            }
        }
        stage('Inject Credential Files') {
            steps {
                withCredentials([file(credentialsId: 'lciadm100-docker-auth', variable: 'dockerConfig')]) {
                    sh "install -m 600 ${dockerConfig} ${HOME}/.docker/config.json"
                }
            }
        }
        stage('Checkout Base Image Git Repository') {
            steps {
                git branch: 'master',
                     credentialsId: 'enmadm100_private_key',
                     url: '${GERRIT_MIRROR}/OSS/ENM-Parent/SQ-Gate/com.ericsson.oss.itpf/eric-enm-esmon-db-hooks'
                sh '''
                    git remote set-url origin --push ${GERRIT_CENTRAL}/OSS/ENM-Parent/SQ-Gate/com.ericsson.oss.itpf/eric-enm-esmon-db-hooks
                '''
            }
        }
        stage('Linting Dockerfile') {
            steps {
                script {
                    sh "${bob} lint-dockerfile"
                    archiveArtifacts '*dockerfilelint.log'
                }
            }
            post {
                failure {
                    script {
                        failedStage = env.STAGE_NAME
                    }
                }
            }
        }
        stage('Init') {
            steps {
                sh "${bob} generate-new-version"
            }
        }
        stage('Build Docker Image') {
            steps {
                script {
                       withCredentials([usernamePassword(credentialsId: 'artifactory-seli-api-token-id', usernameVariable: 'ARM_USER', passwordVariable: 'ARM_TOKEN')]){
                        sh "${bob} build-image-with-all-tags"
                      }
                 }
            }
        }
        stage('Publish Images to Artifactory') {
            steps {
                script {
                    lastStage = env.STAGE_NAME
                }
                sh "${bob} push-image-with-all-tags"
            }
            post {
                failure {
                    script {
                        sh "${bob} remove-image"
                    }
                }
                always {
                    sh "${bob} remove-image-with-all-tags"
                }
            }
        }
        }
        post {
        success {
            script {
                sh '''
                    set +x
                    echo "success"
                '''
            }
        }
        failure {
           script {
               sh '''
                   echo "Failed"
               '''
           }
        }
    }
}


// More about @Builder: http://mrhaki.blogspot.com/2014/05/groovy-goodness-use-builder-ast.html
import groovy.transform.builder.Builder
import groovy.transform.builder.SimpleStrategy

@Builder(builderStrategy = SimpleStrategy, prefix = '')
class BobCommand {
    def bobImage = 'bob.2.0:latest'
    def envVars = [:]
    def needDockerSocket = false

    String toString() {
        def env = envVars
                .collect({ entry -> "-e ${entry.key}=\"${entry.value}\"" })
                .join(' ')

        def cmd = """\
            |docker run
            |--init
            |--rm
            |--workdir \${PWD}
            |--user \$(id -u):\$(id -g)
            |-v \${PWD}:\${PWD}
            |-v /etc/group:/etc/group:ro
            |-v /etc/passwd:/etc/passwd:ro
            |-v \${HOME}/.m2:\${HOME}/.m2
            |-v \${HOME}/.docker:\${HOME}/.docker
            |${needDockerSocket ? '-v /var/run/docker.sock:/var/run/docker.sock' : ''}
            |${env}
            |\$(for group in \$(id -G); do printf ' --group-add %s' "\$group"; done)
            |--group-add \$(stat -c '%g' /var/run/docker.sock)
            |${bobImage}
            |"""
        return cmd
                .stripMargin()           // remove indentation
                .replace('\n', ' ')      // join lines
                .replaceAll(/[ ]+/, ' ') // replace multiple spaces by one
    }
}
