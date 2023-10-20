# AWS DynamoDB Terraform Resources
####################################

### Tables ###

# Creates a Table with given parameters
resource "aws_dynamodb_table" "private_log_table" {
    # Required
    billing_mode = "PAY_PER_REQUEST"
    name           = var.name
    hash_key       = var.hash_key
    dynamic attribute {
        for_each = var.attributes
        content {
            name = attribute.value["name"]
            type = attribute.value["type"]
        }
    }

    range_key = var.range_key

    # Additional features

    dynamic global_secondary_index {
        for_each = var.global_secondary_indexes
        content {
            name = global_secondary_index.value["name"]
            hash_key = global_secondary_index.value["hash_key"]
            range_key = global_secondary_index.value["range_key"]
            projection_type = global_secondary_index.value["projection_type"]
        }
    }

    dynamic local_secondary_index {
        for_each = var.local_secondary_indexes
        content {
            name = local_secondary_index.value["name"]
            range_key = local_secondary_index.value["range_key"]
            projection_type = local_secondary_index.value["projection_type"]
            non_key_attributes = local_secondary_index.value["non_key_attributes"]
        }
    }
    # Optional parameters
    # read_capacity  = var.read_capacity
    

    # billing_mode   = var.billing_mode
    

    stream_enabled = var.stream_enabled
    stream_view_type = var.stream_view_type

}