pipeline {
    agent {
        docker {
            label 'docker'
            // Keep this version aligned with playwright in requirements.txt.
            image 'mcr.microsoft.com/playwright/python:v1.64.1-noble'
            args '--init --ipc=host'
        }
    }

    options {
        timestamps()
        timeout(time: 15, unit: 'MINUTES')
        disableConcurrentBuilds()
        buildDiscarder(logRotator(numToKeepStr: '20', artifactNumToKeepStr: '10'))
    }

    parameters {
        string(
            name: 'BASE_URL',
            defaultValue: 'https://the-internet.herokuapp.com',
            description: 'Deployment to test'
        )
    }

    environment {
        CI = 'true'
        PIP_DISABLE_PIP_VERSION_CHECK = '1'
        PYTHONPATH = '/tmp/the-internet-python'
    }

    stages {
        stage('Install dependencies') {
            steps {
                sh '''
                    python -m pip install --no-cache-dir --target "$PYTHONPATH" -r requirements.txt
                '''
            }
        }

        stage('Test') {
            steps {
                sh '''
                    mkdir -p reports
                    rm -f reports/junit.xml
                    python -m pytest --junitxml=reports/junit.xml
                '''
            }
            post {
                always {
                    junit testResults: 'reports/junit.xml', allowEmptyResults: false
                }
            }
        }
    }

    post {
        always {
            archiveArtifacts artifacts: 'reports/junit.xml,test-results/**', allowEmptyArchive: true
        }
    }
}
