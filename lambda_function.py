import boto3
import json
from datetime import datetime
import time

def lambda_handler(event, context):
    """
    Runs S3 inventory analysis and saves results as CSV files with proper headers
    Uses simplified path structure: source-stats/type/YYYYMMDD.csv
    """
    
    athena = boto3.client('athena', region_name='us-west-2')
    s3 = boto3.client('s3', region_name='us-west-2')
    
    # Configuration - Update these for your environment
    results_bucket = 'us-west-2.opendata.source.coop'
    results_prefix = 'source/source-stats/'
    database = 'source_stats'
    workgroup = 'primary'
    
    # Use the most recent inventory date (June 29, 2025)
    date_str = '250629'
    
    print(f"Starting analysis for inventory date {date_str}")
    
    # Define queries with proper headers and deduplication
    queries = {
        'accounts': {
            'query': '''
                SELECT 
                    split_part(key, '/', 1) as account,
                    COUNT(DISTINCT split_part(key, '/', 2)) as repositories,
                    COUNT(*) as objects,
                    round(SUM(size) / 1024.0 / 1024.0 / 1024.0, 2) as storage_gb,
                    round(AVG(size) / 1024.0 / 1024.0, 2) as avg_object_size_mb,
                    MIN(last_modified_date) as oldest_file,
                    MAX(last_modified_date) as newest_file
                FROM (
                    SELECT DISTINCT key, size, last_modified_date 
                    FROM inventory_data 
                    WHERE key LIKE '%/%'
                ) deduplicated
                GROUP BY split_part(key, '/', 1)
                ORDER BY storage_gb DESC
            ''',
            'header': 'account,repositories,objects,storage_gb,avg_object_size_mb,oldest_file,newest_file'
        },
        
        'repositories': {
            'query': '''
                SELECT 
                    split_part(key, '/', 1) as account,
                    split_part(key, '/', 2) as repository,
                    COUNT(*) as objects,
                    round(SUM(size) / 1024.0 / 1024.0 / 1024.0, 2) as storage_gb,
                    round(AVG(size) / 1024.0 / 1024.0, 2) as avg_object_size_mb,
                    MIN(last_modified_date) as oldest_file,
                    MAX(last_modified_date) as newest_file
                FROM (
                    SELECT DISTINCT key, size, last_modified_date 
                    FROM inventory_data 
                    WHERE key LIKE '%/%/%'
                ) deduplicated
                GROUP BY split_part(key, '/', 1), split_part(key, '/', 2)
                ORDER BY storage_gb DESC
            ''',
            'header': 'account,repository,objects,storage_gb,avg_object_size_mb,oldest_file,newest_file'
        },
        
        'source': {
            'query': '''
                WITH deduplicated_data AS (
                    SELECT DISTINCT key, size, last_modified_date 
                    FROM inventory_data 
                    WHERE key LIKE '%/%/%'
                )
                SELECT 
                    'Total Accounts' as metric,
                    CAST(COUNT(DISTINCT split_part(key, '/', 1)) AS VARCHAR) as value
                FROM deduplicated_data
                
                UNION ALL
                
                SELECT 
                    'Total Repositories',
                    CAST(COUNT(DISTINCT split_part(key, '/', 1) || '/' || split_part(key, '/', 2)) AS VARCHAR)
                FROM deduplicated_data
                
                UNION ALL
                
                SELECT 
                    'Total Objects',
                    CAST(COUNT(*) AS VARCHAR)
                FROM deduplicated_data
                
                UNION ALL
                
                SELECT 
                    'Total Storage (TB)',
                    CAST(round(SUM(size) / 1024.0 / 1024.0 / 1024.0 / 1024.0, 2) AS VARCHAR)
                FROM deduplicated_data
            ''',
            'header': 'metric,value'
        }
    }
    
    def wait_for_query_completion(execution_id, timeout=300):
        """Wait for Athena query to complete"""
        start_time = time.time()
        while time.time() - start_time < timeout:
            response = athena.get_query_execution(QueryExecutionId=execution_id)
            status = response['QueryExecution']['Status']['State']
            
            if status in ['SUCCEEDED']:
                return True
            elif status in ['FAILED', 'CANCELLED']:
                print(f"Query {execution_id} failed: {response['QueryExecution']['Status']}")
                return False
            
            time.sleep(10)
        
        print(f"Query {execution_id} timed out")
        return False
    
    def create_csv_with_header(analysis_type, query_info, date_str):
        """Create CSV file with proper header using simplified path structure"""
        temp_location = f's3://source-inventories/temp/source-stats/{analysis_type}/{date_str}/'
        
        # Handle special naming for source summary file
        if analysis_type == 'source':
            filename = f'source-stats-summary-{date_str}.csv'
        else:
            filename = f'source-stats-{analysis_type}-{date_str}.csv'
        
        final_location = f'{results_prefix}{analysis_type}/{filename}'
        
        # Run query and output to temp location
        unload_query = f'''
            UNLOAD (
                {query_info['query']}
            ) 
            TO '{temp_location}' 
            WITH (
                format = 'TEXTFILE',
                field_delimiter = ',',
                compression = 'NONE'
            )
        '''
        
        # Execute query
        response = athena.start_query_execution(
            QueryString=unload_query,
            QueryExecutionContext={'Database': database},
            ResultConfiguration={
                'OutputLocation': f's3://source-inventories/temp/athena/'
            },
            WorkGroup=workgroup
        )
        
        execution_id = response['QueryExecutionId']
        
        if not wait_for_query_completion(execution_id):
            return False
        
        # List files in temp location
        temp_prefix = f"temp/source-stats/{analysis_type}/{date_str}/"
        response = s3.list_objects_v2(Bucket='source-inventories', Prefix=temp_prefix)
        
        if 'Contents' not in response:
            print(f"No files found in temp location for {analysis_type}")
            return False
        
        # Find the data file (not manifest)
        data_files = [obj['Key'] for obj in response['Contents'] 
                     if not obj['Key'].endswith('manifest.csv') and not obj['Key'].endswith('.metadata')]
        
        if not data_files:
            print(f"No data files found for {analysis_type}")
            return False
        
        # Concatenate all data files with header
        csv_content = query_info['header'] + '\n'
        
        for file_key in data_files:
            # Get file content
            obj_response = s3.get_object(Bucket='source-inventories', Key=file_key)
            file_content = obj_response['Body'].read().decode('utf-8')
            csv_content += file_content
        
        # Write final CSV file
        s3.put_object(
            Bucket=results_bucket,
            Key=final_location,
            Body=csv_content,
            ContentType='text/csv'
        )
        
        # Clean up temp files
        for file_key in data_files:
            s3.delete_object(Bucket='source-inventories', Key=file_key)
        
        print(f"✅ Created {final_location}")
        return True
    
    def cleanup_directories():
        """Clean up temporary directories after processing"""
        try:
            # Clean up athena temp directory in source-inventories bucket
            response = s3.list_objects_v2(Bucket='source-inventories', Prefix='temp/athena/')
            
            if 'Contents' in response:
                delete_objects = [{'Key': obj['Key']} for obj in response['Contents']]
                if delete_objects:
                    s3.delete_objects(
                        Bucket='source-inventories',
                        Delete={'Objects': delete_objects}
                    )
                    print(f"🧹 Cleaned up {len(delete_objects)} files from source-inventories/temp/athena/")
            
            # Clean up source-stats temp directory in source-inventories bucket
            response = s3.list_objects_v2(Bucket='source-inventories', Prefix='temp/source-stats/')
            
            if 'Contents' in response:
                delete_objects = [{'Key': obj['Key']} for obj in response['Contents']]
                if delete_objects:
                    s3.delete_objects(
                        Bucket='source-inventories',
                        Delete={'Objects': delete_objects}
                    )
                    print(f"🧹 Cleaned up {len(delete_objects)} files from source-inventories/temp/source-stats/")
                    
        except Exception as e:
            print(f"⚠️ Warning: Could not clean up temp directories: {str(e)}")
    
    # Process each analysis type
    results = []
    
    for analysis_type, query_info in queries.items():
        try:
            if create_csv_with_header(analysis_type, query_info, date_str):
                # Use the same naming logic as in create_csv_with_header
                if analysis_type == 'source':
                    filename = f'source-stats-summary-{date_str}.csv'
                else:
                    filename = f'source-stats-{analysis_type}-{date_str}.csv'
                results.append(f"{analysis_type}/{filename}")
                print(f"✅ {analysis_type} completed successfully")
            else:
                print(f"❌ {analysis_type} failed")
        except Exception as e:
            print(f"❌ Error processing {analysis_type}: {str(e)}")
    
    # Clean up temporary directories
    cleanup_directories()
    
    return {
        'statusCode': 200,
        'body': json.dumps({
            'message': 'Analysis completed - simplified structure',
            'date': date_str,
            'files': results,
            'structure': 'source/source-stats/[type]/source-stats-[type]-YYMMDD.csv'
        })
    } 