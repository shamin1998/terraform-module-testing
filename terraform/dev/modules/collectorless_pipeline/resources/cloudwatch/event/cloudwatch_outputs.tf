output rule_name {
    value = aws_cloudwatch_event_rule.custom_rule.name
}

output rule_arn {
    value = aws_cloudwatch_event_rule.custom_rule.arn
}