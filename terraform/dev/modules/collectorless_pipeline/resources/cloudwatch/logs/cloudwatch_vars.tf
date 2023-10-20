# AWS CloudWatch Terraform Variables
####################################

### Log Groups ###  

# variable create_lambda_log_group {
#     description = "Boolean variable signifying whether Log Group resource `lambda_log_group` is to be created"

#     type = bool
#     default = false
# }

variable function_name {
    type = string
}

variable retention_in_days {
    default = 30
}

variable skip_destroy {
    default = false
}

# variable lambda_log_group_params {
#     description = "Input parameters for Cloudwatch Log Group `lambda_log_group`"

#     type = object({ create = optional(bool,true)
#     function_name = string
#     retention_in_days = optional(number, 30)
#     skip_destroy = optional(bool, false)
#     })

#     default = { create = false
#         function_name = ""
#     }
# }
