#!/usr/bin/env python3
"""
DataGuardian AI - Golden Dataset Ingestion Script
Populates DataHub with realistic tables, columns, lineage, tags, owners, and dashboards.
"""

import sys
import time
from datahub.emitter.rest_emitter import DatahubRestEmitter
from datahub.emitter.mcp import MetadataChangeProposalWrapper
import datahub.metadata.schema_classes as models

# Initialize DataHub Rest Emitter
GMS_ENDPOINT = "http://localhost:8080"
emitter = DatahubRestEmitter(GMS_ENDPOINT)

print(f"📡 Connecting to DataHub GMS at {GMS_ENDPOINT}...")


# Raw Postgres Source
RAW_ORDERS_URN = "urn:li:dataset:(urn:li:dataPlatform:postgres,raw.public.raw_orders,PROD)"
RAW_CUSTOMERS_URN = "urn:li:dataset:(urn:li:dataPlatform:postgres,raw.public.raw_customers,PROD)"

# Snowflake Analytics Tables
PROD_ORDERS_URN = "urn:li:dataset:(urn:li:dataPlatform:snowflake,prod.public.orders,PROD)"
DIM_CUSTOMERS_URN = "urn:li:dataset:(urn:li:dataPlatform:snowflake,prod.analytics.dim_customers,PROD)"
FCT_SALES_URN = "urn:li:dataset:(urn:li:dataPlatform:snowflake,prod.analytics.fct_daily_sales,PROD)"

# Downstream Consumption Assets
LOOKER_DASHBOARD_URN = "urn:li:dataset:(urn:li:dataPlatform:looker,dashboards.sales_executive_v2,PROD)"
MLFLOW_MODEL_URN = "urn:li:dataset:(urn:li:dataPlatform:mlflow,models.churn_predictor,PROD)"



def emit_schema(dataset_urn: str, table_name: str, fields: list):
    """Emits SchemaMetadata aspect to DataHub."""
    schema_fields = []
    for field_name, field_type, is_pk, description in fields:
        type_class = models.NumberTypeClass() if field_type == "NUMBER" else \
                     models.DateTypeClass() if field_type == "DATE" else \
                     models.StringTypeClass()
        
        schema_fields.append(
            models.SchemaFieldClass(
                fieldPath=field_name,
                type=models.SchemaFieldDataTypeClass(type=type_class),
                nativeDataType=field_type,
                description=description,
                nullable=not is_pk,
            )
        )
        
    schema_aspect = models.SchemaMetadataClass(
        schemaName=table_name,
        platform="urn:li:dataPlatform:snowflake" if "snowflake" in dataset_urn else "urn:li:dataPlatform:postgres",
        version=0,
        hash="",
        platformSchema=models.OtherSchemaClass(rawSchema=""),
        fields=schema_fields,
    )
    
    mcp = MetadataChangeProposalWrapper(entityUrn=dataset_urn, aspect=schema_aspect)
    emitter.emit(mcp)
    print(f"✅ Emitted schema for: {table_name}")


# 2a. Schema: dim_customers
emit_schema(
    DIM_CUSTOMERS_URN,
    "prod.analytics.dim_customers",
    [
        ("customer_id", "NUMBER", True, "Primary key for customer entity"),
        ("customer_name", "STRING", False, "Full name of customer"),
        ("customer_age", "NUMBER", False, "Age of customer in years (Used in Churn ML Model)"),
        ("gender", "STRING", False, "Gender classification"),
        ("signup_date", "DATE", False, "Registration timestamp"),
        ("loyalty_tier", "STRING", False, "Gold, Silver, or Bronze tier status")
    ]
)

# 2b. Schema: prod.public.orders
emit_schema(
    PROD_ORDERS_URN,
    "prod.public.orders",
    [
        ("order_id", "NUMBER", True, "Unique order identifier"),
        ("customer_id", "NUMBER", False, "Foreign key referencing dim_customers"),
        ("order_date", "DATE", False, "Timestamp of order placement"),
        ("total_amount", "NUMBER", False, "Monetary value of order in USD"),
        ("status", "STRING", False, "PENDING, SHIPPED, DELIVERED, or CANCELLED")
    ]
)



def emit_lineage(dataset_urn: str, upstream_urns: list):
    """Emits UpstreamLineage aspect to DataHub."""
    upstreams = []
    for up_urn in upstream_urns:
        upstreams.append(
            models.UpstreamClass(
                dataset=up_urn,
                type=models.DatasetLineageTypeClass.TRANSFORMED
            )
        )
    
    lineage_aspect = models.UpstreamLineageClass(upstreams=upstreams)
    mcp = MetadataChangeProposalWrapper(entityUrn=dataset_urn, aspect=lineage_aspect)
    emitter.emit(mcp)
    print(f" Emitted lineage: {upstream_urns} ──► {dataset_urn}")


# Raw Postgres -> Snowflake Orders
emit_lineage(PROD_ORDERS_URN, [RAW_ORDERS_URN])

# Snowflake Orders + Customers -> Fact Sales
emit_lineage(FCT_SALES_URN, [PROD_ORDERS_URN, DIM_CUSTOMERS_URN])

# Fact Sales -> Looker Executive Dashboard
emit_lineage(LOOKER_DASHBOARD_URN, [FCT_SALES_URN])

# Dim Customers -> Churn Predictor ML Model
emit_lineage(MLFLOW_MODEL_URN, [DIM_CUSTOMERS_URN])


def emit_governance(dataset_urn: str, owner_email: str, tags: list):
    """Emits Ownership and GlobalTags aspects to DataHub."""
    ownership_aspect = models.OwnershipClass(
        owners=[
            models.OwnerClass(
                owner=f"urn:li:corpuser:{owner_email}",
                type=models.OwnershipTypeClass.DATAOWNER
            )
        ]
    )
    emitter.emit(MetadataChangeProposalWrapper(entityUrn=dataset_urn, aspect=ownership_aspect))
    
    tag_associations = [
        models.TagAssociationClass(tag=f"urn:li:tag:{tag_name}") for tag_name in tags
    ]
    tags_aspect = models.GlobalTagsClass(tags=tag_associations)
    emitter.emit(MetadataChangeProposalWrapper(entityUrn=dataset_urn, aspect=tags_aspect))
    
    print(f"🏷️ Emitted governance for {dataset_urn}: Owner={owner_email}, Tags={tags}")


emit_governance(DIM_CUSTOMERS_URN, "alex_data_eng@company.com", ["PII", "Tier_1", "GDPR_Sensitive"])
emit_governance(PROD_ORDERS_URN, "core_analytics@company.com", ["Gold_Tier", "Core_Finance"])

print("\n Golden Dataset Ingestion Complete! DataHub graph is fully populated.")