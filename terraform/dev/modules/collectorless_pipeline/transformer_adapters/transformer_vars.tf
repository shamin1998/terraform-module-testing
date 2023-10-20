variable pipeline_uuid {
    type = string
}

variable aws_region {
    type = string
}

variable type {
    type = string
}

variable name {
    type = string
}

variable trigger {
    type = object({
        type = string
        name = string
        vars = optional(map(string))
    })
}

variable params {
    type = map(string)
}

variable environment {
    type = object({
        variables = map(string)
    })
    default = { variables = {} }
}
