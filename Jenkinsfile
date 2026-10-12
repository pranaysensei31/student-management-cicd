pipeline {

    agent any

    stages {

        stage('Install Dependencies') {
    steps {
        sh '/Library/Frameworks/Python.framework/Versions/3.13/bin/python3 -m pip install -r requirements.txt'
    }
}
        stage('Run Tests') {
            steps {
                sh '/Library/Frameworks/Python.framework/Versions/3.13/bin/python3 -m pytest -v'
            }
        }

        stage('Build Docker Image') {
            steps {
                sh '/usr/local/bin/docker build -t student-management-cicd .'
            }
        }

        stage('Deploy') {
            steps {
                sh '/usr/local/bin/docker rm -f student-management-app || true'
                sh '/usr/local/bin/docker run -d --name student-management-app -p 5001:5000 student-management-cicd'
            }
        }
    }

    post {

        success {
            echo 'CI/CD Pipeline completed successfully!'
        }

        failure {
            echo 'CI/CD Pipeline failed.'
        }
    }
}