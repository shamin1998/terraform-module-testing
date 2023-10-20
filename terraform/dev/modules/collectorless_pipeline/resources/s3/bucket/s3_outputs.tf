output "bucket_name" {
    value = aws_s3_bucket.blob_storage_bucket.id
}

output "bucket_arn" {
    value = aws_s3_bucket.blob_storage_bucket.arn
}