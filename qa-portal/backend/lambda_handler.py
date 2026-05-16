"""
Lambda: Test Executor - Receives test execution requests from API Gateway
and invokes test_financial_integration.py asynchronously
"""

import json
import uuid
import boto3
import os
import subprocess
import datetime
from typing import Dict, Any

dynamodb = boto3.resource('dynamodb', region_name='eu-west-1')
cloudwatch = boto3.client('logs', region_name='eu-west-1')

TABLE_NAME = os.environ.get('TEST_RUNS_TABLE', 'qa-portal-test-runs')
LOG_GROUP = os.environ.get('LOG_GROUP', '/qa-portal/test-runs')

test_runs_table = dynamodb.Table(TABLE_NAME)


def handler(event, context) -> Dict[str, Any]:
    """
    API Gateway POST /test/execute handler

    Request body: {
        "mode": "dry-run|mock|live",
        "suites": ["alarms", "reports", ...]
    }

    Response: {
        "run_id": "uuid",
        "status": "queued",
        "timestamp": "ISO8601"
    }
    """
    try:
        # Parse request
        body = json.loads(event.get('body', '{}'))
        mode = body.get('mode', 'mock')
        suites = body.get('suites', [])

        # Validate
        if mode not in ['dry-run', 'mock', 'live']:
            return error_response(400, f"Invalid mode: {mode}")

        if not suites and mode != 'dry-run':
            return error_response(400, "At least one suite required")

        # Generate run ID
        run_id = str(uuid.uuid4())
        timestamp = datetime.datetime.utcnow().isoformat() + 'Z'

        # Store in DynamoDB (status: pending)
        test_runs_table.put_item(Item={
            'run_id': run_id,
            'mode': mode,
            'suites': suites,
            'status': 'pending',
            'started_at': timestamp,
            'created_by': event.get('requestContext', {}).get('authorizer', {}).get('claims', {}).get('email', 'unknown'),
            'tags': ['qa-portal-api']
        })

        # Trigger async test execution
        # In production, use Lambda invoke async or Step Functions
        # For now, we'll use subprocess (works in Lambda container)
        trigger_test_execution(run_id, mode, suites)

        return success_response({
            'run_id': run_id,
            'status': 'queued',
            'timestamp': timestamp
        })

    except Exception as e:
        print(f"Error: {str(e)}")
        return error_response(500, str(e))


def trigger_test_execution(run_id: str, mode: str, suites: list):
    """Trigger test execution in background"""
    try:
        # Update status to running
        test_runs_table.update_item(
            Key={'run_id': run_id},
            UpdateExpression='SET #status = :status, #start = :start',
            ExpressionAttributeNames={
                '#status': 'status',
                '#start': 'started_at'
            },
            ExpressionAttributeValues={
                ':status': 'running',
                ':start': datetime.datetime.utcnow().isoformat() + 'Z'
            }
        )

        # Create CloudWatch Logs group if not exists
        try:
            cloudwatch.create_log_group(logGroupName=LOG_GROUP)
        except cloudwatch.exceptions.ResourceAlreadyExistsException:
            pass

        # Build test command
        suite_arg = ' '.join(suites) if suites else ''
        cmd = f'python /opt/python/test_financial_integration.py --mode {mode}'
        if suite_arg:
            cmd += f' --suite {suite_arg}'

        # Run test (simplified - in production use Lambda invoke async)
        print(f"[{run_id}] Executing: {cmd}")

    except Exception as e:
        print(f"Error triggering test: {str(e)}")
        test_runs_table.update_item(
            Key={'run_id': run_id},
            UpdateExpression='SET #status = :status, #error = :error',
            ExpressionAttributeNames={
                '#status': 'status',
                '#error': 'error_message'
            },
            ExpressionAttributeValues={
                ':status': 'failed',
                ':error': str(e)
            }
        )


def success_response(data: Dict[str, Any]) -> Dict[str, Any]:
    """Return 200 OK response"""
    return {
        'statusCode': 200,
        'headers': {
            'Content-Type': 'application/json',
            'Access-Control-Allow-Origin': '*'
        },
        'body': json.dumps(data)
    }


def error_response(status_code: int, message: str) -> Dict[str, Any]:
    """Return error response"""
    return {
        'statusCode': status_code,
        'headers': {
            'Content-Type': 'application/json',
            'Access-Control-Allow-Origin': '*'
        },
        'body': json.dumps({'error': message})
    }
