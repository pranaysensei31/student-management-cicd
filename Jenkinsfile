pipeline {

    agent any

    stages {

        stage('Install Dependencies') {
            steps {
                sh 'python3 -m pip install -r requirements.txt'
            }
        }

        stage('Run Tests') {
            steps {
                sh 'pytest -v'
            }
        }

        stage('Build Docker Image') {
            steps {
                sh 'docker build -t student-management-cicd .'
            }
        }

        stage('Deploy') {
            steps {
                sh 'docker rm -f student-management-app || true'
                sh 'docker run -d --name student-management-app -p 5001:5000 student-management-cicd'
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