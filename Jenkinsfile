pipeline {
    agent {
        label params.AGENT_LABEL ?: 'selenium'
    }

    options {
        timestamps()
        timeout(time: 90, unit: 'MINUTES')
        buildDiscarder(logRotator(numToKeepStr: '30'))
        disableConcurrentBuilds()
    }

    parameters {
        string(
            name: 'AGENT_LABEL',
            defaultValue: 'selenium',
            description: 'Jenkins agent label with Chrome, Python 3, and ZPA/network access to sugar-test.'
        )
        choice(
            name: 'TEST_MARKER',
            choices: ['smoke', 'regression', 'contacts', 'leads'],
            description: 'Pytest marker to run.'
        )
    }

    environment {
        HEADLESS = 'true'
        KEEP_BROWSER_OPEN = 'false'
        REUSE_SESSION = 'false'
        SCREENSHOT_ON_FAILURE = 'true'
        PYTEST_MARKER = "${params.TEST_MARKER}"
    }

    stages {
        stage('Checkout') {
            steps {
                checkout scm
            }
        }

        stage('Run smoke tests') {
            steps {
                withCredentials([
                    string(credentialsId: 'credaris-microsoft-username', variable: 'MICROSOFT_USERNAME'),
                    string(credentialsId: 'credaris-microsoft-password', variable: 'MICROSOFT_PASSWORD'),
                    string(credentialsId: 'credaris-sugar-username', variable: 'SUGAR_USERNAME'),
                    string(credentialsId: 'credaris-sugar-password', variable: 'SUGAR_PASSWORD'),
                ]) {
                    script {
                        if (isUnix()) {
                            sh '''
                                chmod +x scripts/ci/run_tests.sh
                                scripts/ci/run_tests.sh
                            '''
                        } else {
                            bat 'scripts\\ci\\run_tests.bat'
                        }
                    }
                }
            }
        }
    }

    post {
        always {
            junit allowEmptyResults: true, testResults: 'reports/pytest-junit.xml'
            archiveArtifacts artifacts: 'reports/**,logs/**,screenshots/**', allowEmptyArchive: true, fingerprint: true
            allure([
                includeProperties: false,
                jdk: '',
                properties: [],
                reportBuildPolicy: 'ALWAYS',
                results: [[path: 'reports/allure-results']]
            ])
        }
        failure {
            echo 'Smoke tests failed. Check Allure report, screenshots, and Jenkins console log.'
        }
    }
}
