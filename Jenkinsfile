pipeline {
    agent {
        docker {
            label 'docker'
            // Build the root Dockerfile on this agent's Docker daemon first.
            image 'the-internet-playwright:latest'
            args '--init --ipc=host'
        }
    }

    options {
        timestamps()
        timeout(time: 15, unit: 'MINUTES')
        disableConcurrentBuilds()
        buildDiscarder(logRotator(numToKeepStr: '20', artifactNumToKeepStr: '10'))
    }

    environment {
        CI = 'true'
        BASE_URL = 'https://the-internet.herokuapp.com'
        WORKERS = '4'
    }

    stages {
        stage('Test') {
            steps {
                sh '''
                    mkdir -p reports
                    rm -f reports/junit.xml
                    /opt/venv/bin/python -m pytest -n "$WORKERS" --junitxml=reports/junit.xml
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
