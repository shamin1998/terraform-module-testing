variable pipeline_uuid {
    type = string
}

variable "lambda_function_name" {
    default = ""
}

variable "lambda_function_arn" {
    default = ""
}

variable event_trigger_rate {
    default = 1
}