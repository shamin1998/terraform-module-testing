output function_arn {
    value = module.lambda_function.arn
}

output function_role_id {
    value = module.lambda_function.role_id
}