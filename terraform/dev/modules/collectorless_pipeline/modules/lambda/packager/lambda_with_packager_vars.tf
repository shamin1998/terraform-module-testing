# Packaging and zipping parameters

variable scripts_folder_path {
    type = string
    default = "./"
}

variable temp_package_folder {
    type = string
    default = "lambda_package_dir"
}

variable package_filename {
    type = string
    default = "lambda_package.zip"
}

# Lambda function parameters

variable function_name {
    type = string
    default = "default-lambda-with-packager"
}

variable handler {
    type = string
    # default = ""
}

variable runtime {
    type = string
    default = "python3.10"
}

variable timeout {
    type = number
    default = 3
}

variable layers {
    type = list(string)
    default = []
}

variable environment {
    type = object({
        variables = optional(map(string))
    })

    default = {
        variables = {}
    }
}

# variable asm_secret_arn {
#     default = ""
# }