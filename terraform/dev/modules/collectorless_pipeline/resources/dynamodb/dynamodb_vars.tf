# AWS DynamoDB Terraform Variables
####################################

### Table Parameters ###
variable name {
    type = string
}

variable hash_key {
    type = string
}

variable range_key {
    type = string
    default = ""
}

variable attributes {
    type = list(object({
        type = string
        name = string
    }))
}

variable global_secondary_indexes {
    type = list(object({
            name = string
            hash_key = string
            range_key = optional(string)
            projection_type = optional(string, "KEYS_ONLY")
            non_key_attributes = optional(list(string))
            }))
    
    default = [{
      hash_key = ""
      name = ""
    }]
}

variable local_secondary_indexes {
    type = list(object({
            name = string
            range_key = string
            projection_type = optional(string, "KEYS_ONLY")
            non_key_attributes = optional(list(string))
            }))
    
    default = [{
      range_key = ""
      name = ""
    }]
}

variable billing_mode {
    default = "PROVISIONED"
}

variable read_capacity {
    type = number
}

variable write_capacity {
    type = number
}

variable stream_enabled {
    default = false
}

variable stream_view_type {
    default = ""
}

# variable private_log_table_params {
#     description = "Input parameters for DynamoDB Table `custom_table`"

#     type = object({ create = optional(bool, true)
#         name = string
#         hash_key = string
#         attributes = list(object({
#             name = string
#             type = string
#         }))

#         range_key = optional(string)
        
#         sort_index = optional(object({
#             name = string
#             range_key = string
#             projection_type = optional(string, "KEYS_ONLY")
#             non_key_attributes = optional(list(string))
#         }))

#         optional_params = optional(map(string))
#         # billing_mode = optional(string, "PROVISIONED")
#         # write_capacity = optional(number)
#         # read_capacity = optional(number)

#         # stream_enabled = optional(bool)
#         # stream_view_type = optional(string)
        
#     })

#     default = { create = false
#         name = ""
#         hash_key = ""
#         attributes = [{
#             name = ""
#             type = ""
#         }]
#     }

#     # validation {
#     #     condition     = contains(["PROVISIONED", "PAY_PER_REQUEST"],var.custom_table_params.billing_mode)
#     #     error_message = "Valid values for parameter `billing_mode` are : { 'PROVISIONED', 'PAY_PER_REQUEST' }"
#     # }

#     # validation {
#     #     condition     = (var.custom_table_params.billing_mode != "PROVISIONED") || (var.custom_table_params.write_capacity && var.custom_table_params.read_capacity)
#     #     error_message = "If parameter `billing_mode` is 'PROVISIONED', parameters `write_capacity` and `read_capacity` must be specified."
#     # }

# }