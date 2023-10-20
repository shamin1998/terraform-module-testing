# variable create_function {
#     type = bool
#     default = true
# }

# variable create_logs {
#     type = bool
#     default = false
# }

variable function_name {
    type = string
    default = "default-lambda-function"
}

variable filename {
    type = string
    default = ""
}

variable source_code_hash {
    type = string
    default = ""
}

variable role {
    type = string
    default = ""
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