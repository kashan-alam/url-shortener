# URL Shortener

A serverless URL shortener built on AWS. Paste a long URL, get a short link. Visiting the short link redirects you to the original URL.

**Live API endpoint:**
```
https://iez346ryha.execute-api.us-east-1.amazonaws.com/prod
```

---

## What It Does

- User opens the web form, types a long URL, clicks Shorten
- App generates a short 6-character code (e.g. DVAOlS)
- User gets a short link like `https://api-url/prod/DVAOlS`
- Anyone who visits that short link is redirected to the original URL

---

## Architecture

```
[User Browser]
      |
[ECS Fargate - Flask Frontend]   <-- Docker container, port 5000
      |                               image stored in ECR
[API Gateway]
  |           |
[Lambda:    [Lambda:
 shorten]    redirect]
      |           |
         [DynamoDB]
      code --> original_url

--- CI/CD ---
[GitHub] --> [CodePipeline] --> [CodeBuild] --> [Deploy to Lambda + ECS]
```

---

## AWS Services Used

| Service | Purpose |
|---|---|
| ECS Fargate | Runs the Flask frontend container |
| ECR | Stores the Docker image |
| API Gateway | Routes HTTP requests to Lambda |
| Lambda (shorten) | Generates short code, saves to database |
| Lambda (redirect) | Looks up code, returns redirect |
| DynamoDB | Stores code to URL mapping |
| CodePipeline | CI/CD orchestration |
| CodeBuild | Runs tests and builds Docker image |
| S3 | Stores pipeline artifacts |
| IAM | Permissions for all services |
| VPC | Networking for ECS |
| CloudWatch | Logs and monitoring |

---

## Project Structure

```
url-shortener/
├── frontend/
│   ├── app.py              Flask web app
│   ├── Dockerfile          Docker container recipe
│   ├── requirements.txt    Python dependencies
│   └── templates/
│       └── index.html      HTML form page
├── lambdas/
│   ├── shorten/
│   │   └── handler.py      Shorten Lambda function
│   └── redirect/
│       └── handler.py      Redirect Lambda function
├── tests/
│   ├── test_shorten.py     Unit tests for shorten Lambda
│   └── test_redirect.py    Unit tests for redirect Lambda
├── deployment.yaml         AWS CloudFormation infrastructure
├── buildspec.yml           CI/CD build instructions
├── .gitignore
└── README.md
```

---

## Setup and Deployment

### Prerequisites

Before starting, install these on your computer:
- Python 3.11 or higher
- AWS CLI - https://aws.amazon.com/cli/
- Docker Desktop - https://docs.docker.com/desktop/
- Git - https://git-scm.com/

### Step 1 - Configure AWS CLI

Create an IAM user in AWS Console with AdministratorAccess, get the access keys, then run:

```
aws configure
```

Enter your Access Key ID, Secret Access Key, region (us-east-1), and output format (json).

Verify it works:
```
aws sts get-caller-identity
```

### Step 2 - Clone the repository

```
git clone https://github.com/kashan-alam/url-shortener.git
cd url-shortener
```

### Step 3 - Deploy infrastructure to AWS

This one command creates everything on AWS (DynamoDB, Lambda, API Gateway, ECS, ECR, CI/CD pipeline):

```
aws cloudformation create-stack --stack-name url-shortener --template-body file://deployment.yaml --capabilities CAPABILITY_NAMED_IAM --parameters ParameterKey=GitHubOwner,ParameterValue="your-github-username" ParameterKey=GitHubRepo,ParameterValue="url-shortener" ParameterKey=GitHubToken,ParameterValue="your-github-token"
```

Wait for it to complete (3-5 minutes):
```
aws cloudformation describe-stacks --stack-name url-shortener --query "Stacks[0].StackStatus"
```

Wait until you see `CREATE_COMPLETE`.

Get your API URL:
```
aws cloudformation describe-stacks --stack-name url-shortener --query "Stacks[0].Outputs"
```

### Step 4 - Deploy Lambda code manually

```
cd lambdas\shorten
powershell Compress-Archive -Path * -DestinationPath ..\..\shorten.zip -Force
cd ..\redirect
powershell Compress-Archive -Path * -DestinationPath ..\..\redirect.zip -Force
cd ..\..
aws lambda update-function-code --function-name url-shortener-shorten --zip-file fileb://shorten.zip
aws lambda update-function-code --function-name url-shortener-redirect --zip-file fileb://redirect.zip
```

### Step 5 - Push Docker image and start frontend

Login to ECR:
```
aws ecr get-login-password --region us-east-1 | docker login --username AWS --password-stdin YOUR_ACCOUNT_ID.dkr.ecr.us-east-1.amazonaws.com
```

Build and push:
```
docker build -t url-shortener-frontend ./frontend
docker tag url-shortener-frontend:latest YOUR_ACCOUNT_ID.dkr.ecr.us-east-1.amazonaws.com/url-shortener-frontend:latest
docker push YOUR_ACCOUNT_ID.dkr.ecr.us-east-1.amazonaws.com/url-shortener-frontend:latest
```

Create ECS service:
```
aws ecs create-service --cluster url-shortener-cluster --service-name url-shortener-frontend --task-definition url-shortener-frontend --desired-count 1 --launch-type FARGATE --network-configuration "awsvpcConfiguration={subnets=[YOUR_SUBNET_ID],securityGroups=[YOUR_SECURITY_GROUP_ID],assignPublicIp=ENABLED}"
```

Replace YOUR_SUBNET_ID and YOUR_SECURITY_GROUP_ID with the values from the CloudFormation outputs.

---

## Running the Application

### Get the frontend IP address

Every time ECS restarts, the IP changes. Run these commands to get the current IP:

```
aws ecs list-tasks --cluster url-shortener-cluster
```

Copy the task ARN, then:
```
aws ecs describe-tasks --cluster url-shortener-cluster --tasks YOUR_TASK_ARN --query "tasks[0].attachments[0].details[?name=='networkInterfaceId'].value" --output text
```

Copy the network interface ID, then:
```
aws ec2 describe-network-interfaces --network-interface-ids YOUR_ENI_ID --query "NetworkInterfaces[0].Association.PublicIp" --output text
```

Open in browser:
```
http://YOUR_PUBLIC_IP:5000
```

### Test the API directly

Shorten a URL:
```powershell
Invoke-WebRequest -Uri "https://iez346ryha.execute-api.us-east-1.amazonaws.com/prod/shorten" -Method POST -Headers @{"Content-Type"="application/json"} -Body '{"url": "https://www.google.com"}' | Select-Object -ExpandProperty Content
```

Test redirect - open in browser:
```
https://iez346ryha.execute-api.us-east-1.amazonaws.com/prod/DVAOlS
```

---

## Running Tests Locally

Create a virtual environment:
```
python -m venv venv
venv\Scripts\activate
pip install pytest boto3 flask requests
```

Run tests:
```
pytest tests/ -v
```

---

## Stopping the Application (to avoid charges)

Stop ECS container:
```
aws ecs update-service --cluster url-shortener-cluster --service url-shortener-frontend --desired-count 0
```

This stops ECS charges. Lambda, DynamoDB, and API Gateway only charge when used so they cost nothing when idle.

---

## Starting the Application Again

Start ECS container:
```
aws ecs update-service --cluster url-shortener-cluster --service url-shortener-frontend --desired-count 1
```

Wait 2 minutes then get the new public IP using the commands in the "Get the frontend IP address" section above.

---

## Deleting Everything (full cleanup)

If you want to delete all AWS resources:

First empty the S3 bucket:
```
aws s3 rm s3://url-shortener-artifacts-YOUR_ACCOUNT_ID --recursive
```

Then delete the CloudFormation stack:
```
aws cloudformation delete-stack --stack-name url-shortener
```

---

## CI/CD Pipeline

Every push to the main branch automatically:
1. Downloads code from GitHub
2. Runs all unit tests
3. If tests pass - builds Docker image and pushes to ECR
4. Deploys new Lambda code
5. Updates ECS service

If any test fails, deployment stops and nothing is updated.

View pipeline status:
```
https://us-east-1.console.aws.amazon.com/codesuite/codepipeline/pipelines/url-shortener-pipeline/view
```