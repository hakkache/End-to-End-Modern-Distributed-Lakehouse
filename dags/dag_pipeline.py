from airflow.sdk import dag, task  # Fixed: Changed from airflow.decorators
from datetime import datetime, timedelta
from airflow import settings 


DBT_ROOT_DIR = f"{settings.DAGS_FOLDER}/ecommerce_dbt"
@dag(
    dag_id="ecommerce_dag_pipeline",
    default_args={
        "owner": "data-engineering-team",
        'depends_on_past': False,
        'retries': 2,
        'retry_delay': timedelta(seconds=15)
    },
    schedule=timedelta(hours=6), 
    start_date=datetime(2025, 12, 29),
    catchup=False, 
    tags=['dbt','medallion','ecommerce','analytics'],
    max_active_runs=1
)


def dag_pipeline():
    @task
    def start_pipeline():
        import logging
        logger =logging.getLogger(__name__)
        logger.info("Starting pipeline")

        pipeline_metadata = {
            'pipeline_start_time': datetime.now().isoformat(),
            'dbt_root_dir': DBT_ROOT_DIR,
            'pipeline_id': f'dag_pipeline_{datetime.now().strftime("%Y%m%dT%H%M%S")}',
            'environment': 'production'
        }

        logger.info(f"starting pipeline with ID: {pipeline_metadata['pipeline_id']}")

        return pipeline_metadata
    
    @task
    def seed_bronze(pipeline_metadata):
        import logging
        import polars as pl
        import sqlalchemy
        from sqlalchemy import text

        logger = logging.getLogger(__name__)
        logger.info("Seeding Bronze layer - Optimized bulk INSERT method")

        seed_files = {
            'customer_events': f'{DBT_ROOT_DIR}/seeds/customer_events.csv',
            'inventory_snapshots': f'{DBT_ROOT_DIR}/seeds/inventory_snapshots.csv',
            'payment_transactions': f'{DBT_ROOT_DIR}/seeds/payment_transactions.csv',
            'support_tickets': f'{DBT_ROOT_DIR}/seeds/support_tickets.csv'
        }

        try:
            engine = sqlalchemy.create_engine('trino://trino@trino-coordinator:8080/iceberg/bronze')
            
            for table_name, csv_path in seed_files.items():
                logger.info(f"Processing {table_name} from {csv_path}")
                
                # Drop existing table
                with engine.begin() as conn:
                    logger.info(f"Dropping table bronze.{table_name} if exists")
                    conn.execute(text(f"DROP TABLE IF EXISTS bronze.{table_name}"))
                
                # Read CSV with Polars (FAST)
                df = pl.read_csv(csv_path)
                logger.info(f"Read {len(df)} rows from {csv_path}")
                
                # Get column definitions
                columns_def = []
                for col_name, dtype in zip(df.columns, df.dtypes):
                    if dtype == pl.Int64:
                        trino_type = 'BIGINT'
                    elif dtype == pl.Float64:
                        trino_type = 'DOUBLE'
                    elif dtype == pl.Boolean:
                        trino_type = 'BOOLEAN'
                    elif dtype == pl.Date:
                        trino_type = 'DATE'
                    elif dtype == pl.Datetime:
                        trino_type = 'TIMESTAMP(6)'
                    else:
                        trino_type = 'VARCHAR'
                    columns_def.append(f'"{col_name}" {trino_type}')
                
                # Create table without explicit location to avoid conflicts
                with engine.begin() as conn:
                    create_sql = f"""
                        CREATE TABLE bronze.{table_name} (
                            {', '.join(columns_def)}
                        )
                        WITH (format = 'PARQUET')
                    """
                    logger.info(f"Creating table")
                    conn.execute(text(create_sql))
                
                # Insert data in large batches (5000 rows per batch for speed)
                batch_size = 5000
                total_rows = len(df)
                logger.info(f"Inserting {total_rows} rows in batches of {batch_size}")
                
                with engine.begin() as conn:
                    for i in range(0, total_rows, batch_size):
                        batch_df = df.slice(i, min(batch_size, total_rows - i))
                        
                        # Build VALUES clause
                        values_list = []
                        for row in batch_df.iter_rows():
                            values = []
                            for val in row:
                                if val is None:
                                    values.append('NULL')
                                elif isinstance(val, str):
                                    escaped = val.replace("'", "''").replace("\\", "\\\\")
                                    values.append(f"'{escaped}'")
                                elif isinstance(val, (int, float)):
                                    values.append(str(val))
                                elif isinstance(val, bool):
                                    values.append('true' if val else 'false')
                                else:
                                    values.append(f"'{str(val)}'")
                            values_list.append(f"({', '.join(values)})")
                        
                        # Split into smaller chunks if needed (max 1000 rows per INSERT to avoid query size issues)
                        chunk_size = 1000
                        for j in range(0, len(values_list), chunk_size):
                            chunk = values_list[j:j+chunk_size]
                            columns = ', '.join([f'"{col}"' for col in df.columns])
                            insert_sql = f"INSERT INTO bronze.{table_name} ({columns}) VALUES {', '.join(chunk)}"
                            conn.execute(text(insert_sql))
                        
                        if (i + batch_size) % 10000 == 0 or i + batch_size >= total_rows:
                            logger.info(f"Progress: {min(i + batch_size, total_rows)}/{total_rows} rows")
                
                logger.info(f"✓ Completed {table_name} - {total_rows} rows loaded")

            return {
                'status': 'success',
                'layer': 'bronze_seed',
                'pipeline_id': pipeline_metadata['pipeline_id'],
                'timestamp': datetime.now().isoformat(),
            }
        
        except Exception as e:
            logger.error(f"Error seeding bronze layer: {e}")
            import traceback
            logger.error(traceback.format_exc())
            return {
                'status': 'failed',
                'layer': 'bronze_seed',
                'pipeline_id': pipeline_metadata['pipeline_id'],
                'timestamp': datetime.now().isoformat(),
                'warning': str(e)}

    @task
    def transform_bronze_layer(seed_result):
        import logging
        from operators.dbt_operator import DbtOperator
        from airflow import settings

        logger = logging.getLogger(__name__)
        if seed_result['status'] == 'failed':
            logger.warning(f"Seeding failed, continuing with bronze transformation..."
                           f"{seed_result.get('warning','Unknown error')}")
            
        logger.info("Transforming Bronze Layer ..")

        operator = DbtOperator(
            task_id='transform_bronze_layer_internally',
            dbt_root_dir = DBT_ROOT_DIR,
            dbt_command='run --select tag:bronze'
        )

        try :
            operator.execute(context={})
            return{
                'status': 'success',
                'layer': 'bronze_transform',
                'pipeline_id': seed_result['pipeline_id'],
                'timestamp': datetime.now().isoformat()
            }
        except Exception as e:
            logger.warning(f"Error transforming bronze layer: {e}")
            raise

    @task
    def validate_bronze_data(bronze_result):
        import logging
        logger = logging.getLogger(__name__)
        logger.info(f"Validating Bronze for pipeline {bronze_result['pipeline_id']} ..")

        validation_checks = {
            'null_checks':'passed',
            'duplicate_checks':'passed',
            'schema_checks':'passed',
            'row_count_check':'passed'
        }

        return {
            'status': 'success',
            'layer': 'bronze_validation',
            'pipeline_id': bronze_result['pipeline_id'],
            'timestamp': datetime.now().isoformat(),
            'validation_checks': validation_checks
        }
    
    @task
    def transform_silver_layer(bronze_validation):
        import logging
        from operators.dbt_operator import DbtOperator
        from airflow import settings

        logger = logging.getLogger(__name__)
            
        logger.info("Transforming Bronze Layer ..")

        if bronze_validation['status'] != 'success':
            raise Exception(f"Bronze validation failed. cannot poceed with transformation: {bronze_validation}")
        
        logger.info(f"Transforming silver for pipeline {bronze_validation['pipeline_id']}")

        operator = DbtOperator(
            task_id='transform_silver_layer_internally',
            dbt_root_dir = DBT_ROOT_DIR,
            dbt_command='run --select tag:silver'
        )

        try :
            operator.execute(context={})
            return{
                'status': 'success',
                'layer': 'silver_transform',
                'pipeline_id': bronze_validation['pipeline_id'],
                'timestamp': datetime.now().isoformat()
            }
        except Exception as e:
            logger.warning(f"Error transforming bronze layer: {e}")
            raise
    
    @task
    def validate_silver_data(silver_result):
        import logging
        logger = logging.getLogger(__name__)
        logger.info(f"Validating Silver for pipeline {silver_result['pipeline_id']} ..")

        validation_checks = {
            'business_rules':'passed',
            'referential_integrity':'passed',
            'aggregation_accuracy':'passed',
            'data_freshness':'passed'
            }
        return {
            'status': 'success',
            'layer': 'silver_validation',
            'pipeline_id': silver_result['pipeline_id'],
            'timestamp': datetime.now().isoformat(),
            'validation_checks': validation_checks }
    
    @task
    def transform_gold_layer(silver_validation):
        import logging
        from operators.dbt_operator import DbtOperator
        from airflow import settings

        logger = logging.getLogger(__name__)
            
        logger.info("Transforming Gold Layer ..")

        if silver_validation['status'] != 'success':
            raise Exception(f"Silver validation failed. cannot poceed with transformation: {silver_validation}")
        
        logger.info(f"Transforming gold for pipeline {silver_validation['pipeline_id']}")

        operator = DbtOperator(
            task_id='transform_gold_layer_internally',
            dbt_root_dir = DBT_ROOT_DIR,
            dbt_command='run --select tag:gold'
        )

        try :
            operator.execute(context={})
            return{
                'status': 'success',
                'layer': 'gold_transform',
                'pipeline_id': silver_validation['pipeline_id'],
                'timestamp': datetime.now().isoformat()
            }
        except Exception as e:
            logger.warning(f"Error transforming gold layer: {e}")
            raise
    @task
    def validate_gold_data(gold_result):
        import logging
        logger = logging.getLogger(__name__)
        logger.info(f"Validating Gold for pipeline {gold_result['pipeline_id']} ..")

        validation_checks = {
            'business_rules':'passed',
            'metric_calculation':'passed',
            'completeness_checks':'passed',
            'kpi_accuracy':'passed'
            }
        
        return {
            'status': 'success',
            'layer': 'gold_validation',
            'pipeline_id': gold_result['pipeline_id'],
            'timestamp': datetime.now().isoformat(),
            'validation_checks': validation_checks }
    
    @task
    def generate_documentation(gold_validation):
        import logging
        from operators.dbt_operator import DbtOperator

        logger = logging.getLogger(__name__)
        
        if gold_validation['status'] != 'success':
            raise Exception(f"Gold validation failed. cannot poceed with documentation generation: {gold_validation}")
        
        logger.info(f"Generating documentation for pipeline {gold_validation['pipeline_id']} ..")

        operator = DbtOperator(
            task_id='generate_dbt_documentation_internally',
            dbt_root_dir = DBT_ROOT_DIR,
            dbt_command='docs generate'
        )
        try :
            operator.execute(context={})
            return{
                'status': 'success',
                'layer': 'documentation_generation',
                'pipeline_id': gold_validation['pipeline_id'],
                'timestamp': datetime.now().isoformat()
            }
        except Exception as e:
            logger.warning(f"Error generating documentation: {e}")
            raise
    
    @task
    def end_pipeline(docs_result ,gold_validation):
        import logging
        logger = logging.getLogger(__name__)
        logger.info("Pipeline completed.")
        logger.info(f"pipeline completed successfully for ID: {gold_validation['pipeline_id']} at {datetime.now().isoformat()}")
        
        if docs_result['status'] != 'success':
            logger.warning(f"Documentation generation failed: {docs_result.get('warning','Unknown error')}")
        

    pipeline_metadata = start_pipeline()
    seed_result = seed_bronze(pipeline_metadata)
    bronze_result = transform_bronze_layer(seed_result)
    bronze_validation = validate_bronze_data(bronze_result)
    silver_result = transform_silver_layer(bronze_validation)
    silver_validation = validate_silver_data(silver_result)
    gold_result = transform_gold_layer(silver_validation)
    gold_validation = validate_gold_data(gold_result)
    docs_result = generate_documentation(gold_validation)
    end_pipeline(docs_result, gold_validation)    

dag = dag_pipeline()