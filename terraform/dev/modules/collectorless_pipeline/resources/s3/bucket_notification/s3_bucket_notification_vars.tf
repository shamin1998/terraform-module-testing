variable notify {
    type = string
}

variable lambda_function_arn {
    type = string
    # default = ""
}

variable bucket_name {
    type = string
}

variable bucket_arn {
    type = string
}

variable events {
    type = list(string)
    default = ["s3:ObjectCreated:*"]
}

variable filter_prefix {
    type = string
    default = ""
}

variable filter_suffix {
    type = string
    default = ""
}