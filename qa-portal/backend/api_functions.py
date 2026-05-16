"""API Lambda functions: status, logs, history, report generator"""

import json
import boto3
import os
from datetime import datetime
from dynamodb_service import TestRunsDB, TestReportsDB

cloudwatch_logs = boto3.client('logs', region_name='eu-west-1')
s3_client = boto3.client('s3', region_name='eu-west-1')

test_runs_db = TestRunsDB()
test_reports_db = TestReportsDB()

LOG_GROUP = os.environ.get('LOG_GROUP', '/qa-portal/test-runs')
S3_BUCKET = os.environ.get('S3_BUCKET', 'sanlamconnect-qa-portal')


# ==================== GET /test/{run_id}/status ====================
def test_status_handler(event, context):
    """Get test run status"""
    run_id = event['pathParameters']['run_id']

    try:
        run = test_runs_db.get_run(run_id)
        if not run:
            return error_response(404, f"Run not found: {run_id}")

        return success_response({
            'run_id': run_id,
            'status': run.get('status'),
            'mode': run.get('mode'),
            'suites': run.get('suites', []),
            'started_at': run.get('started_at'),
            'completed_at': run.get('completed_at'),
            'duration_seconds': run.get('duration_seconds'),
            'results_summary': run.get('results_summary', {})
        })
    except Exception as e:
        return error_response(500, str(e))


# ==================== GET /test/{run_id}/logs ====================
def test_logs_handler(event, context):
    """Get test run logs from CloudWatch"""
    run_id = event['pathParameters']['run_id']

    try:
        log_stream = f"test-runs/{run_id}"
        response = cloudwatch_logs.get_log_events(
            logGroupName=LOG_GROUP,
            logStreamName=log_stream,
            limit=100
        )

        logs = [event['message'] for event in response.get('events', [])]

        return success_response({
            'run_id': run_id,
            'logs': logs,
            'last_line_count': len(logs)
        })
    except cloudwatch_logs.exceptions.ResourceNotFoundException:
        return success_response({
            'run_id': run_id,
            'logs': ['No logs yet'],
            'last_line_count': 0
        })
    except Exception as e:
        return error_response(500, str(e))


# ==================== GET /test/history ====================
def test_history_handler(event, context):
    """Get test run history"""
    limit = int(event['queryStringParameters'].get('limit', 10)) if event.get('queryStringParameters') else 10

    try:
        runs = test_runs_db.list_runs(limit=limit)

        return success_response({
            'runs': [
                {
                    'run_id': run['run_id'],
                    'mode': run['mode'],
                    'status': run['status'],
                    'created_at': run.get('created_at'),
                    'duration_seconds': run.get('duration_seconds'),
                    'created_by': run.get('created_by')
                }
                for run in runs
            ],
            'total': len(runs)
        })
    except Exception as e:
        return error_response(500, str(e))


# ==================== POST /report/generate ====================
def report_generator_handler(event, context):
    """Generate test report (PDF or HTML)"""
    try:
        body = json.loads(event['body'])
        run_id = body['run_id']
        format = body.get('format', 'html')

        # Get test run data
        run = test_runs_db.get_run(run_id)
        if not run:
            return error_response(404, f"Run not found: {run_id}")

        # Generate report
        report_id = f"{run_id}-{format}"
        report_content = generate_report(run, format)

        # Store in S3
        s3_key = f"reports/{report_id}.{format}"
        s3_client.put_object(
            Bucket=S3_BUCKET,
            Key=s3_key,
            Body=report_content,
            ContentType='application/pdf' if format == 'pdf' else 'text/html'
        )

        # Create presigned URL (valid for 24 hours)
        presigned_url = s3_client.generate_presigned_url(
            'get_object',
            Params={'Bucket': S3_BUCKET, 'Key': s3_key},
            ExpiresIn=86400
        )

        # Save report record
        test_reports_db.create_report(report_id, run_id, format, presigned_url)

        return success_response({
            'report_id': report_id,
            'format': format,
            'url': presigned_url,
            'status': 'ready'
        })
    except Exception as e:
        return error_response(500, str(e))


# ==================== GET /report/{report_id} ====================
def report_download_handler(event, context):
    """Download report (redirect to presigned URL)"""
    report_id = event['pathParameters']['report_id']

    try:
        report = test_reports_db.get_report(report_id)
        if not report:
            return error_response(404, f"Report not found: {report_id}")

        return {
            'statusCode': 302,
            'headers': {
                'Location': report['s3_url'],
                'Access-Control-Allow-Origin': '*'
            }
        }
    except Exception as e:
        return error_response(500, str(e))


# ==================== HELPER FUNCTIONS ====================

def generate_report(run: dict, format: str) -> str:
    """Generate report content (HTML or PDF)"""
    if format == 'html':
        return generate_html_report(run)
    elif format == 'pdf':
        return generate_pdf_report(run)
    else:
        raise ValueError(f"Unknown format: {format}")


def generate_html_report(run: dict) -> str:
    """Generate HTML report"""
    results = run.get('results_summary', {})
    html = f"""
    <html>
    <head>
        <title>QA Test Report - {run['run_id']}</title>
        <style>
            body {{ font-family: Arial, sans-serif; margin: 20px; }}
            h1 {{ color: #2c3e50; }}
            .summary {{ background: #ecf0f1; padding: 15px; border-radius: 5px; }}
            .passed {{ color: #27ae60; }}
            .failed {{ color: #e74c3c; }}
            .skipped {{ color: #f39c12; }}
        </style>
    </head>
    <body>
        <h1>QA Test Report</h1>
        <div class="summary">
            <p><strong>Run ID:</strong> {run['run_id']}</p>
            <p><strong>Mode:</strong> {run['mode']}</p>
            <p><strong>Status:</strong> {run['status']}</p>
            <p><strong>Created:</strong> {run.get('created_at', 'N/A')}</p>
            <p><strong>Duration:</strong> {run.get('duration_seconds', 'N/A')} seconds</p>
        </div>
        <h2>Results</h2>
        <p><span class="passed">✓ Passed: {results.get('passed', 0)}</span></p>
        <p><span class="failed">✗ Failed: {results.get('failed', 0)}</span></p>
        <p><span class="skipped">→ Skipped: {results.get('skipped', 0)}</span></p>
    </body>
    </html>
    """
    return html


def generate_pdf_report(run: dict) -> bytes:
    """Generate PDF report (stub - use reportlab in production)"""
    # In production: use reportlab or weasyprint
    # For now, return HTML as bytes
    return generate_html_report(run).encode('utf-8')


def success_response(data: dict) -> dict:
    """Return 200 OK response"""
    return {
        'statusCode': 200,
        'headers': {
            'Content-Type': 'application/json',
            'Access-Control-Allow-Origin': '*'
        },
        'body': json.dumps(data)
    }


def error_response(status_code: int, message: str) -> dict:
    """Return error response"""
    return {
        'statusCode': status_code,
        'headers': {
            'Content-Type': 'application/json',
            'Access-Control-Allow-Origin': '*'
        },
        'body': json.dumps({'error': message})
    }
