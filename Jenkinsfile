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
        string(
            name: 'NOTIFY_EMAIL',
            defaultValue: 'hina.siddiqui@rolustech.com',
            description: 'Email address that receives the Allure report after every build.'
        )
    }

    environment {
        HEADLESS = 'true'
        KEEP_BROWSER_OPEN = 'false'
        REUSE_SESSION = 'false'
        SCREENSHOT_ON_FAILURE = 'true'
        PYTEST_MARKER = "${params.TEST_MARKER}"
        NOTIFY_EMAIL = "${params.NOTIFY_EMAIL}"
    }

    stages {
        stage('Checkout') {
            steps {
                checkout scm
            }
        }

        stage('Run tests') {
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

        stage('Generate Allure report') {
            steps {
                script {
                    if (isUnix()) {
                        sh '''
                            chmod +x scripts/ci/generate_allure_report.sh
                            scripts/ci/generate_allure_report.sh
                        '''
                    } else {
                        bat 'scripts\\ci\\generate_allure_report.bat'
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
            script {
                sendAllureEmail()
            }
        }
        failure {
            echo 'Tests failed. Check Allure report, screenshots, and Jenkins console log.'
        }
    }
}

def sendAllureEmail() {
    def buildStatus = currentBuild.currentResult ?: 'UNKNOWN'
    def allureUrl = "${env.BUILD_URL}allure/"
    def jobName = env.JOB_NAME ?: 'credaris-selenium-automation'
    def branchName = env.BRANCH_NAME ?: env.GIT_BRANCH ?: 'main'
    def marker = params.TEST_MARKER ?: env.PYTEST_MARKER ?: 'smoke'
    def recipient = params.NOTIFY_EMAIL ?: env.NOTIFY_EMAIL ?: 'hina.siddiqui@rolustech.com'
    def hasZip = fileExists('reports/allure-report.zip')

    def attachmentLine = hasZip
        ? '<p>The Allure HTML report is attached as <b>allure-report.zip</b> (extract and open <code>index.html</code>).</p>'
        : '<p>Install Allure CLI on the agent to receive the report as a ZIP attachment. The Jenkins Allure link below is always available.</p>'

    def subject = "[Credaris Automation] ${jobName} #${env.BUILD_NUMBER} - ${buildStatus}"
    def body = """
        <html>
        <body style="font-family: Arial, sans-serif; color: #222;">
            <h2>Credaris Selenium Automation</h2>
            <table cellpadding="6" cellspacing="0" border="0">
                <tr><td><b>Job</b></td><td>${jobName}</td></tr>
                <tr><td><b>Build</b></td><td>#${env.BUILD_NUMBER}</td></tr>
                <tr><td><b>Status</b></td><td>${buildStatus}</td></tr>
                <tr><td><b>Branch</b></td><td>${branchName}</td></tr>
                <tr><td><b>Test marker</b></td><td>${marker}</td></tr>
                <tr><td><b>Build URL</b></td><td><a href="${env.BUILD_URL}">${env.BUILD_URL}</a></td></tr>
            </table>
            <p><a href="${allureUrl}"><b>View Allure Report in Jenkins</b></a></p>
            ${attachmentLine}
            <p style="color:#666;font-size:12px;">Sent automatically by Jenkins after each build.</p>
        </body>
        </html>
    """.stripIndent()

    try {
        emailext(
            to: recipient,
            subject: subject,
            body: body,
            mimeType: 'text/html',
            attachmentsPattern: hasZip ? 'reports/allure-report.zip' : '',
            attachLog: true,
            compressLog: true
        )
        echo "Allure notification sent to ${recipient}"
    } catch (Exception e) {
        echo "Email notification failed: ${e.message}"
        echo 'Configure SMTP under Manage Jenkins → System → Extended E-mail Notification.'
    }
}
