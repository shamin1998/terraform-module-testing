# AWS CloudWatch Terraform Variables
####################################

### Log Groups ###  

# variable create_lambda_log_group {
#     description = "Boolean variable signifying whether Log Group resource `lambda_log_group` is to be created"

#     type = bool
#     default = false
# }

### Event Rules ###

variable name {
    type = string
}

variable schedule_expression {
    type = string
    default = "rate(1 minute)"
}

variable function_name {
    type = string
}

variable lambda_function_arn {
    type = string
}
# variable custom_rule_params {
#     description = "Input parameters for Cloudwatch Event Rule `custom_rule`"

#     type = object({ create = optional(bool,true)
#         name = string
#         schedule_expression = optional(string)
#         event_pattern = optional(string)
#         role_arn = optional(string)
#         is_enabled = optional(bool)
#     })

#     default = { create = false
#         name = ""
#         schedule_expression = ""
#     }

#     # validation {
#     #     condition     = ((var.custom_rule_params.schedule_expression != null) || (var.custom_rule_params.event_pattern != null))
#     #     error_message = "Either one of the parameters `schedule_expression` or `event_pattern` must be specified."
#     # }
# }

# variable rate_x_minutes_rule_params {
#     description = "Input parameters for Cloudwatch Event Rule `rate_x_minutes_rule`"

#     type = object({ create = optional(bool,true)
#         name = string
#         x = number
#     })

#     default = { create = false
#         name = ""
#         x = 1
#     }

#     validation {
#         condition     = (var.rate_x_minutes_rule_params.x == floor(var.rate_x_minutes_rule_params.x)) && (var.rate_x_minutes_rule_params.x > 0)
#         error_message = "The parameter `x` must be a positive integer"
#     }
# }

# variable cron_x_minutes_rule_params {
#     description = "Input parameters for Cloudwatch Event Rule `cron_x_minutes_rule`"

#     type = object({ create = optional(bool,true)
#         name = string
#         x = number
#     })

#     default = { create = false
#         name = ""
#         x = 1
#     }

#     validation {
#         condition     = (var.cron_x_minutes_rule_params.x == floor(var.cron_x_minutes_rule_params.x)) && (var.cron_x_minutes_rule_params.x > 0)
#         error_message = "The parameter `x` must be a positive integer"
#     }
# }