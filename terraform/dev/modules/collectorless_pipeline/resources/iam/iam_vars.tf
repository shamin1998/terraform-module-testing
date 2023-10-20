variable pipeline_uuid {
    type = string
}

variable lambda_iam_role_id {
    type = string
}

variable lambda_iam_permissions {
    type = object({ all = optional(bool,false)
        allow_secrets = optional(bool,false)
        allow_s3 = optional(bool, false)
        allow_dynamodb = optional(bool, false)
        allow_logs = optional(bool, true)
        allow_sqs = optional(bool, false)
        # asm_secret_arn = optional(string)
    })

    default = { all = true
        # get_secrets = true
    }
}

# variable allow_lambda_access_s3_params {
#     type = object({ enable = optional(bool,true)
#         lambda_iam_role_id = string
#         actions = optional(list(string), ["s3:*"])
#         resources = list(string)
#     })

#     default = { enable = false
#         lambda_iam_role_id = ""
#         resources = []
#     }
# }