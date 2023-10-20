output "log_table_arn" {
    value = module.dynamodb.table_arn
}

output "params_for_lambda" {
    value = module.dynamodb.params_for_lambda
}

# output "log_table_name" {
#     value = module.dynamodb.params_for_lambda.name
# }

# output "log_table_hash_key" {
#     value = module.dynamodb.params_for_lambda.hash_key
# }

# output "log_table_range_key" {
#     value = module.dynamodb.params_for_lambda.range_key
# }

# output "log_table_sort_index_name" {
#     value = module.dynamodb.params_for_lambda.sort_index_name
# }

# output "log_table_timestamp_key" {
#     value = module.dynamodb.params_for_lambda.timestamp_key
# }
