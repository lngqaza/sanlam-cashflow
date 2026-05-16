"""DynamoDB CRUD operations for QA Portal"""

import boto3
import os
from datetime import datetime
from typing import Dict, Any, List

dynamodb = boto3.resource('dynamodb', region_name='eu-west-1')

TEST_RUNS_TABLE = os.environ.get('TEST_RUNS_TABLE', 'qa-portal-test-runs')
TEST_REPORTS_TABLE = os.environ.get('TEST_REPORTS_TABLE', 'qa-portal-test-reports')


class TestRunsDB:
    def __init__(self):
        self.table = dynamodb.Table(TEST_RUNS_TABLE)

    def create_run(self, run_id: str, mode: str, suites: list, created_by: str) -> Dict[str, Any]:
        """Create new test run record"""
        item = {
            'run_id': run_id,
            'mode': mode,
            'suites': suites,
            'status': 'pending',
            'created_at': datetime.utcnow().isoformat() + 'Z',
            'created_by': created_by,
            'tags': ['qa-portal']
        }
        self.table.put_item(Item=item)
        return item

    def update_status(self, run_id: str, status: str, data: Dict[str, Any] = None) -> Dict[str, Any]:
        """Update run status"""
        update_expr = 'SET #status = :status'
        expr_values = {':status': status}
        expr_names = {'#status': 'status'}

        if data:
            for key, value in data.items():
                update_expr += f', #{key} = :{key}'
                expr_values[f':{key}'] = value
                expr_names[f'#{key}'] = key

        response = self.table.update_item(
            Key={'run_id': run_id},
            UpdateExpression=update_expr,
            ExpressionAttributeNames=expr_names,
            ExpressionAttributeValues=expr_values,
            ReturnValues='ALL_NEW'
        )
        return response['Attributes']

    def get_run(self, run_id: str) -> Dict[str, Any]:
        """Get test run by ID"""
        response = self.table.get_item(Key={'run_id': run_id})
        return response.get('Item', {})

    def list_runs(self, limit: int = 10) -> List[Dict[str, Any]]:
        """List recent test runs"""
        response = self.table.scan(Limit=limit)
        # Sort by created_at descending
        items = response.get('Items', [])
        items.sort(key=lambda x: x.get('created_at', ''), reverse=True)
        return items[:limit]


class TestReportsDB:
    def __init__(self):
        self.table = dynamodb.Table(TEST_REPORTS_TABLE)

    def create_report(self, report_id: str, run_id: str, format: str, s3_url: str) -> Dict[str, Any]:
        """Create new test report record"""
        item = {
            'report_id': report_id,
            'run_id': run_id,
            'format': format,
            's3_url': s3_url,
            'status': 'ready',
            'generated_at': datetime.utcnow().isoformat() + 'Z'
        }
        self.table.put_item(Item=item)
        return item

    def get_report(self, report_id: str) -> Dict[str, Any]:
        """Get report by ID"""
        response = self.table.get_item(Key={'report_id': report_id})
        return response.get('Item', {})

    def list_reports_by_run(self, run_id: str) -> List[Dict[str, Any]]:
        """List reports for a test run"""
        response = self.table.query(
            IndexName='run_id-index',
            KeyConditionExpression='run_id = :run_id',
            ExpressionAttributeValues={':run_id': run_id}
        )
        return response.get('Items', [])
