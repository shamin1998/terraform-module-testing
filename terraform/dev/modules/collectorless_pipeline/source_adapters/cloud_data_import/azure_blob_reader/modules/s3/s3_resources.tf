# Define AWS S3 Terraform resources

resource "aws_s3_bucket" "blob_storage_bucket" {
    bucket = coalesce(var.bucket_name,"${var.bucket_name_prefix}-puuid-${var.pipeline_uuid}")
    acl = "private"
    object_lock_enabled = false 
    force_destroy = true            # To avoid persistent test buckets
}
