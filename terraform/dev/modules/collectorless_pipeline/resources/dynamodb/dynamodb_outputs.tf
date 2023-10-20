output "params_for_lambda" {
    value = {
        name = aws_dynamodb_table.private_log_table.name
        hash_key = aws_dynamodb_table.private_log_table.hash_key
        range_key = aws_dynamodb_table.private_log_table.range_key
        sort_index = var.local_secondary_indexes[0].name
        timestamp_key = var.local_secondary_indexes[0].range_key
        pipeline_uuid_key = var.global_secondary_indexes[0].hash_key
    }
}

output "name" {
    value = aws_dynamodb_table.private_log_table.name
}

output "table_arn" {
    value = aws_dynamodb_table.private_log_table.arn
}
