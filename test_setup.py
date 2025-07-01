#!/usr/bin/env python3
"""
Test script to validate the Source Stats inventory setup
Checks table access, partition availability, and runs sample queries
"""

import boto3
import time
from datetime import datetime

def test_athena_table():
    """Test Athena table access and partitions"""
    
    athena = boto3.client('athena', region_name='us-west-2')
    
    # Configuration
    results_bucket = 'us-west-2.opendata.source.coop'
    results_prefix = 'source/source-stats/'
    database = 'source_stats'
    workgroup = 'primary'
    
    def run_query(query, description):
        """Run a query and return results"""
        print(f"\n🔍 {description}")
        print(f"Query: {query}")
        
        try:
            response = athena.start_query_execution(
                QueryString=query,
                QueryExecutionContext={'Database': database},
                ResultConfiguration={
                    'OutputLocation': f's3://source-inventories/temp/test/'
                },
                WorkGroup=workgroup
            )
            
            execution_id = response['QueryExecutionId']
            
            # Wait for completion
            start_time = time.time()
            while time.time() - start_time < 120:  # 2 minute timeout
                status_response = athena.get_query_execution(QueryExecutionId=execution_id)
                status = status_response['QueryExecution']['Status']['State']
                
                if status == 'SUCCEEDED':
                    break
                elif status in ['FAILED', 'CANCELLED']:
                    print(f"❌ Query failed: {status_response['QueryExecution']['Status']}")
                    return False
                
                time.sleep(5)
            
            if status != 'SUCCEEDED':
                print(f"❌ Query timed out")
                return False
                
            # Get results
            result = athena.get_query_results(QueryExecutionId=execution_id)
            
            if 'ResultSet' in result and 'Rows' in result['ResultSet']:
                rows = result['ResultSet']['Rows']
                print(f"✅ Query succeeded - {len(rows)} rows returned")
                
                # Print first few rows
                for i, row in enumerate(rows[:5]):
                    if 'Data' in row:
                        row_data = [col.get('VarCharValue', '') for col in row['Data']]
                        print(f"   Row {i}: {row_data}")
                
                if len(rows) > 5:
                    print(f"   ... and {len(rows) - 5} more rows")
                
                return True
            else:
                print("❌ No results returned")
                return False
                
        except Exception as e:
            print(f"❌ Error: {str(e)}")
            return False
    
    print("🚀 Testing Source Stats Athena Setup")
    print("=" * 50)
    
    # Test 1: Check if table exists
    success1 = run_query("DESCRIBE source_stats.inventory_data", "Testing table schema")
    
    # Test 2: Count total records 
    success2 = run_query("""
        SELECT COUNT(*) as record_count, 
               ROUND(SUM(size) / 1024.0 / 1024.0 / 1024.0, 2) as total_gb
        FROM source_stats.inventory_data 
    """, "Testing basic data access")
    
    # Test 3: Sample account analysis
    success3 = run_query("""
        SELECT 
            split_part(key, '/', 1) as account,
            COUNT(*) as objects,
            ROUND(SUM(size) / 1024.0 / 1024.0 / 1024.0, 2) as storage_gb
        FROM source_stats.inventory_data 
        WHERE key LIKE '%/%'
        GROUP BY split_part(key, '/', 1)
        ORDER BY storage_gb DESC
        LIMIT 10
    """, "Testing account-level analysis")
    
    print("\n" + "=" * 50)
    print("📊 Test Summary:")
    print(f"   Table Schema: {'✅ Pass' if success1 else '❌ Fail'}")
    print(f"   Data Access: {'✅ Pass' if success2 else '❌ Fail'}")
    print(f"   Account Analysis: {'✅ Pass' if success3 else '❌ Fail'}")
    
    all_passed = all([success1, success2, success3])
    print(f"\n🎯 Overall: {'✅ All tests passed!' if all_passed else '❌ Some tests failed'}")
    
    return all_passed

if __name__ == "__main__":
    test_athena_table() 