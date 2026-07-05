pipeline {
    agent {
        label params.AGENT_LABEL ?: 'windows-dakota-perf'
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
            defaultValue: 'windows-dakota-perf',
            description: 'Jenkins agent label (Windows node with Chrome, Python 3, and ZPA/network access).'
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
        HEADLESS = 'false'
        KEEP_BROWSER_OPEN = 'false'
        REUSE_SESSION = 'true'
        CHROME_USER_DATA_DIR = 'C:\\jenkins-agent\\.chrome-profile\\credaris-automation'
        SUGAR_LOAD_TIMEOUT = '90'
        SCREENSHOT_ON_FAILURE = 'true'
        PYTEST_MARKER = "${params.TEST_MARKER}"
        NOTIFY_EMAIL = "${params.NOTIFY_EMAIL}"
        PYTHONIOENCODING = 'utf-8'
        PYTHONUNBUFFERED = '1'
    }

    stages {
        stage('Checkout') {
            steps {
                checkout scm
            }
        }

        stage('Prepare CI session') {
            steps {
                bat 'scripts\\ci\\prepare_ci_session.bat'
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
            // Work around a known Allure Commandline 2.40+ Windows launcher bug
            // (allure-framework/allure2#3351): allure.bat's "endlocal & java ..."
            // clears APP_HOME right before starting Java, so the plugin's report
            // silently loses its "Behaviors" and "Packages" tabs (500 error /
            // "Unexpected token '<'" — the underlying data/behaviors.json and
            // data/packages.json never get written). Pre-setting APP_HOME here
            // survives that endlocal, since it restores the OUTER scope's value
            // instead of clearing it.
            withEnv(["APP_HOME=C:\\jenkins-agent\\tools\\org.allurereport.jenkins.tools.AllureCommandlineInstallation\\Allure"]) {
                allure([
                    includeProperties: false,
                    jdk: '',
                    properties: [],
                    reportBuildPolicy: 'ALWAYS',
                    results: [[path: 'reports/allure-results']]
                ])
            }
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
    // Uses global Jenkins SMTP: smtp.gmail.com:587 (credential smtp-rolustech-hina)
    def result = currentBuild.currentResult ?: 'UNKNOWN'
    def allureUrl = "${env.BUILD_URL}allure/"
    def marker = params.TEST_MARKER ?: env.PYTEST_MARKER ?: 'smoke'
    def recipient = params.NOTIFY_EMAIL ?: env.NOTIFY_EMAIL ?: 'hina.siddiqui@rolustech.com'
    def hasZip = fileExists('reports/allure-report.zip')
    def statusColor = result == 'SUCCESS' ? '#2ecc71' : (result == 'UNSTABLE' ? '#f39c12' : '#e74c3c')
    def zipLine = hasZip
        ? '<p style="margin:12px 0 0;font-size:12px;color:#666;">Allure HTML is also attached as <b>allure-report.zip</b> (extract and open <code>index.html</code>).</p>'
        : ''

    def subject = "[${result}] ${env.JOB_NAME} #${env.BUILD_NUMBER} — Credaris Selenium Automation"
    def body = """
<!DOCTYPE html>
<html>
<head><meta charset="utf-8"></head>
<body style="font-family:Segoe UI,Arial,sans-serif;background:#f5f5f5;margin:0;padding:24px;">
  <table width="100%" cellpadding="0" cellspacing="0" style="max-width:640px;margin:0 auto;background:#fff;border-radius:8px;overflow:hidden;box-shadow:0 2px 8px rgba(0,0,0,.08);">
    <tr><td style="background:#343a40;color:#fff;padding:20px 24px;">
      <div style="font-size:12px;letter-spacing:1px;opacity:.8;">ALLURE REPORT</div>
      <div style="font-size:22px;font-weight:600;margin-top:4px;">Credaris Selenium Automation</div>
      <div style="font-size:13px;margin-top:8px;opacity:.9;">${env.JOB_NAME} &middot; Build #${env.BUILD_NUMBER}</div>
    </td></tr>
    <tr><td style="padding:24px;">
      <div style="font-size:48px;font-weight:700;color:${statusColor};">${result}</div>
      <p style="color:#666;margin:8px 0 20px;">Marker: ${marker} &middot; Agent: ${params.AGENT_LABEL}</p>
      <table width="100%" cellpadding="0" cellspacing="0" style="margin-bottom:20px;">
        <tr>
          <td style="background:#f8f9fa;padding:12px;border-radius:6px;width:33%;text-align:center;">
            <div style="font-size:11px;color:#888;">PASSED</div>
            <div style="font-size:20px;font-weight:600;color:#2ecc71;">\${TEST_COUNTS,var="pass"}</div>
          </td>
          <td style="width:8px;"></td>
          <td style="background:#f8f9fa;padding:12px;border-radius:6px;width:33%;text-align:center;">
            <div style="font-size:11px;color:#888;">FAILED</div>
            <div style="font-size:20px;font-weight:600;color:#e74c3c;">\${TEST_COUNTS,var="fail"}</div>
          </td>
          <td style="width:8px;"></td>
          <td style="background:#f8f9fa;padding:12px;border-radius:6px;width:33%;text-align:center;">
            <div style="font-size:11px;color:#888;">TOTAL</div>
            <div style="font-size:20px;font-weight:600;">\${TEST_COUNTS,var="total"}</div>
          </td>
        </tr>
      </table>
      <p style="margin:0 0 12px;">
        <a href="${allureUrl}" style="display:inline-block;background:#fd5a3e;color:#fff;text-decoration:none;padding:12px 20px;border-radius:6px;font-weight:600;">Open Allure Report</a>
      </p>
      <p style="margin:0 0 12px;">
        <a href="${env.BUILD_URL}" style="color:#007bff;">View build in Jenkins</a>
      </p>
      ${zipLine}
      <p style="font-size:12px;color:#999;margin-top:24px;">Sent via Jenkins SMTP (smtp.gmail.com) to ${recipient}.</p>
    </td></tr>
  </table>
</body>
</html>
"""

    try {
        emailext(
            to: recipient,
            replyTo: 'hina.siddiqui@rolustech.com',
            subject: subject,
            body: body,
            mimeType: 'text/html',
            attachmentsPattern: hasZip ? 'reports/allure-report.zip' : '',
            attachLog: false
        )
        echo "Allure notification sent to ${recipient}"
    } catch (Exception err) {
        echo "Email skipped (check Email Extension plugin and global SMTP in Manage Jenkins → System): ${err.message}"
    }
}
