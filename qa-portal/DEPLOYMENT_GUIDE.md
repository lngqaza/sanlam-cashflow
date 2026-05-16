# QA Portal - Deployment & Operations Guide

## Overview

The QA Portal is a fully AWS-native quality assurance platform for the financial impact monitoring integration. It provides:
- Web-based test execution dashboard (React SPA)
- REST API for test management (API Gateway + Lambda)
- Test history and reporting (DynamoDB + S3)
- Live test results streaming (CloudWatch Logs)

**Zero local Docker required. All deployment via GitHub Actions and AWS CloudFormation.**

---

## Architecture

```
┌─────────────────────────────┐
│   React SPA Dashboard       │
│ (S3 + CloudFront static)    │
└──────────────┬──────────────┘
               │ HTTPS/REST
               ▼
┌─────────────────────────────┐
│   API Gateway (Regional)    │
│   6 REST Endpoints          │
└──────────────┬──────────────┘
               │
    ┌──────────┼──────────┐
    ▼          ▼          ▼
┌─────────┐ ┌─────────┐ ┌──────────┐
│ Lambda  │ │DynamoDB │ │CloudWatch│
│  (5fn)  │ │ (2tbl)  │ │   Logs   │
└─────────┘ └─────────┘ └──────────┘
```

---

## Prerequisites

### For Local Development

```bash
# Clone the repo
git clone https://github.com/sanlam/sanlamconnect-qa-portal.git
cd qa-portal

# Install dependencies
cd frontend && npm install
cd ../backend && pip install -r requirements.txt
```

### For AWS Deployment

1. **AWS Account Setup:**
   - Account ID: `684756697968`
   - Region: `eu-west-1`
   - IAM Role: `github-actions-deploy` (for GitHub Actions)

2. **GitHub Secrets (for CI/CD):**
   ```
   AWS_ROLE_ARN         = arn:aws:iam::684756697968:role/github-actions-deploy
   API_BASE_URL         = https://api.sanlamconnect.com/qa-portal
   SLACK_WEBHOOK_URL    = https://hooks.slack.com/services/...
   ```

3. **AWS IAM Permissions** (attach to `github-actions-deploy` role):
   ```json
   {
     "Version": "2012-10-17",
     "Statement": [
       {
         "Effect": "Allow",
         "Action": [
           "s3:*",
           "cloudfront:*",
           "lambda:*",
           "apigateway:*",
           "dynamodb:*",
           "logs:*",
           "cloudformation:*",
           "iam:*"
         ],
         "Resource": "*"
       }
     ]
   }
   ```

---

## Local Development

### Frontend Development

```bash
cd frontend

# Install dependencies
npm install

# Start dev server (http://localhost:3000)
npm start

# Build for production
npm run build

# Test
npm test
```

**Environment Variables:**
```bash
REACT_APP_API_URL=http://localhost:3001
REACT_APP_ENVIRONMENT=development
```

### Backend Development

```bash
cd backend

# Install dependencies
pip install -r requirements.txt

# Run tests
python -m pytest

# Run locally (requires AWS credentials)
python -c "from lambda_handler import handler; print(handler({'body': '{}'}, None))"
```

**Environment Variables:**
```bash
AWS_REGION=eu-west-1
TEST_RUNS_TABLE=qa-portal-test-runs
TEST_REPORTS_TABLE=qa-portal-test-reports
LOG_GROUP=/qa-portal/test-runs
S3_BUCKET=sanlamconnect-qa-portal-684756697968
```

---

## Deployment via GitHub Actions

### Automatic Deployment

Push to main branch or use **Manual Trigger**:

```bash
# Trigger deployment via GitHub CLI
gh workflow run deploy-qa-portal.yml \
  --ref main \
  -f environment=staging
```

### Deployment Flow

1. **Checkout code** from git
2. **Build React dashboard** (`npm run build`)
3. **Upload frontend to S3** (invalidate CloudFront)
4. **Package Lambda functions** (zip with dependencies)
5. **Deploy CloudFormation stack**
   - Creates/updates API Gateway
   - Creates/updates Lambda functions
   - Creates/updates DynamoDB tables
   - Creates/updates S3, CloudFront, Logs
   - Configures IAM roles
6. **Post-deployment verification**
   - Test dashboard accessibility
   - Test API endpoints
   - Notify Slack channel

### Deployment Environments

```bash
# Staging (lowest risk, test environment)
gh workflow run deploy-qa-portal.yml -f environment=staging

# Production (live, for end users)
gh workflow run deploy-qa-portal.yml -f environment=production
```

### Monitoring Deployment

```bash
# Watch workflow run
gh run watch [RUN_ID]

# View logs
gh run view [RUN_ID] --log

# Check CloudFormation stack
aws cloudformation describe-stacks \
  --stack-name sanlamconnect-qa-portal-staging \
  --region eu-west-1
```

---

## Using the QA Portal

### Dashboard URL

After deployment, access at:
```
https://qa-portal.sanlamconnect.com/
```

(Or custom domain via Route53 alias)

### Execute Tests

1. **Select Mode:** dry-run / mock / live
   - `dry-run`: Syntax validation only (2 min)
   - `mock`: Logic validation with mock data (5 min)
   - `live`: Real integration test (45 min)

2. **Select Suites:** Check boxes for test suites to run

3. **Click "Execute Tests"** → Test queued in DynamoDB

4. **Monitor Results:** Table updates every 5 seconds

5. **Generate Report:** Download HTML or PDF when complete

### Test History

Browse past test runs in the "History" tab. Click any run to view full results and logs.

### Reports

Reports stored in S3:
```
s3://sanlamconnect-qa-portal-684756697968/reports/{report_id}.{html|pdf}
```

Presigned URLs valid for 24 hours.

---

## API Endpoints

### POST /test/execute

**Request:**
```json
{
  "mode": "dry-run|mock|live",
  "suites": ["CloudWatch Alarms", "Financial Calculator"]
}
```

**Response:**
```json
{
  "run_id": "uuid",
  "status": "queued",
  "timestamp": "2026-05-16T13:00:00Z"
}
```

---

### GET /test/{run_id}/status

**Response:**
```json
{
  "run_id": "uuid",
  "status": "running|completed|failed",
  "mode": "mock",
  "duration_seconds": 120,
  "results_summary": {
    "passed": 25,
    "failed": 0,
    "skipped": 4
  }
}
```

---

### GET /test/{run_id}/logs

**Response:**
```json
{
  "run_id": "uuid",
  "logs": ["[INFO] Starting test...", "✅ Test passed"],
  "last_line_count": 2
}
```

---

### GET /test/history?limit=10

**Response:**
```json
{
  "runs": [
    {
      "run_id": "uuid",
      "mode": "mock",
      "status": "completed",
      "created_at": "2026-05-16T13:00:00Z",
      "duration_seconds": 120
    }
  ],
  "total": 1
}
```

---

### POST /report/generate

**Request:**
```json
{
  "run_id": "uuid",
  "format": "html|pdf"
}
```

**Response:**
```json
{
  "report_id": "uuid-html",
  "format": "html",
  "url": "https://s3.amazonaws.com/...",
  "status": "ready"
}
```

---

## Monitoring & Troubleshooting

### CloudWatch Logs

```bash
# View Lambda errors
aws logs tail /aws/lambda/qa-portal-test-executor --follow

# View test execution logs
aws logs tail /qa-portal/test-runs --follow
```

### DynamoDB Monitoring

```bash
# List recent test runs
aws dynamodb scan \
  --table-name qa-portal-test-runs \
  --region eu-west-1 \
  --limit 10
```

### API Gateway Logs

```bash
# Enable API logs in CloudWatch
aws apigateway update-stage \
  --rest-api-id [API_ID] \
  --stage-name production \
  --patch-operations \
    op=replace,path=*/*/*/logging/loglevel,value=INFO
```

### Common Issues

**Dashboard not loading:**
```bash
# Check CloudFront distribution
aws cloudfront get-distribution-config --id [DIST_ID]

# Check S3 bucket policy
aws s3api get-bucket-policy --bucket sanlamconnect-qa-portal-684756697968
```

**API endpoints returning 500:**
```bash
# Check Lambda execution role
aws iam get-role --role-name qa-portal-lambda-execution

# Check Lambda logs
aws logs tail /aws/lambda/qa-portal-test-executor --follow --since 5m
```

**Tests not persisting to history:**
```bash
# Check DynamoDB table status
aws dynamodb describe-table --table-name qa-portal-test-runs
```

---

## Cost Optimization

**Estimated Monthly Costs:**

| Service | Usage | Cost |
|---------|-------|------|
| Lambda | 20 invocations @ 45min = 15 hours CPU/month | ~$0.30 |
| DynamoDB | 100 runs, 10KB each, on-demand | ~$1.25 |
| S3 | 1GB storage, 10GB transfer | ~$0.25 |
| CloudFront | 1GB/month | ~$0.10 |
| API Gateway | 100 requests | ~$0.35 |
| CloudWatch | 30 days logs | ~$1.00 |
| **Total** | | **~$3.25/month** |

**Cost Controls:**
- DynamoDB TTL auto-deletes runs after 90 days
- CloudWatch Logs retention set to 30 days
- S3 versioning for audit trail
- CloudFront caching (no API GW charge for cache hits)

---

## Scaling & Performance

**Current Limits (AWS Quotas):**
- Lambda: 1000 concurrent executions
- API Gateway: 10,000 requests/second
- DynamoDB: On-demand (auto-scaling)
- CloudFront: Global edge locations

**For 1000 concurrent test runs:**
- Increase Lambda concurrency to 2000
- DynamoDB on-demand handles automatically
- API Gateway scales without changes

---

## Backup & Disaster Recovery

**DynamoDB Backups:**
```bash
# Manual backup
aws dynamodb create-backup \
  --table-name qa-portal-test-runs \
  --backup-name qa-portal-backup-$(date +%Y%m%d)

# List backups
aws dynamodb list-backups --table-name qa-portal-test-runs
```

**S3 Versioning:**
- All objects versioned for recovery
- Old versions deleted after 30 days (configurable)

**CloudFormation:**
- Stack snapshots stored (can rollback)
- Template versioned in git

---

## Security

**Access Control:**
- API Gateway: Resource-based policies
- Lambda: IAM role with least-privilege
- DynamoDB: Item-level encryption (KMS optional)
- S3: Bucket policies + OAI for CloudFront only
- Secrets: AWS Secrets Manager for API keys

**Audit Trail:**
- CloudTrail logs all API calls
- CloudWatch logs all function executions
- DynamoDB Streams capture all changes
- S3 access logs available

---

## Support & Maintenance

### Regular Tasks

**Weekly:**
- Monitor CloudWatch dashboards
- Check Lambda error rates
- Review CloudFront cache hit ratios

**Monthly:**
- Review CloudWatch logs retention
- Optimize DynamoDB capacity
- Update Lambda dependencies

**Quarterly:**
- Review costs and optimize
- Update security groups
- Plan feature additions

### Getting Help

1. Check CloudWatch Logs for errors
2. Review GitHub Actions workflow logs
3. Check AWS CloudFormation events tab
4. Contact DevOps team

---

**Last Updated:** 2026-05-16  
**QA Portal Version:** 1.0  
**AWS Region:** eu-west-1  
**Deployment:** Fully Automated via GitHub Actions + CloudFormation
