locals {
    include_collectorless_transformer = ((var.type == "raw_to_mibs_transformer") && (var.name == "collectorless_transformer")) ? true : false
}

module collectorless_transformer {
    count = local.include_collectorless_transformer ? 1 : 0

    source = "./raw_to_mibs_transformer/collectorless_transformer"

    pipeline_uuid = var.pipeline_uuid

    trigger = var.trigger

    params = var.params

    environment = var.environment
    
    # aws_region = var.aws_region
    
    # # Lambda Function variables
    # lambda_function_params = {
    #     function_name = var.destination_params.lambda_function_name
    #     handler = var.destination_params.lambda_function_handler
    #     scripts_path =  var.destination_params.lambda_function_scripts_path
    #     environment = {
    #         variables = {
    #             ASM_SECRET_NAME = var.destination_params.asm_secret_name
    #             AWS_REGION_NAME = var.aws_region
    #         }
    #     }
    #     asm_secret_arn = var.destination_params.asm_secret_arn
    # }

    # s3_bucket_params = {
    #   bucket_name = var.destination_params.s3_bucket_name 
    #   bucket_arn = var.destination_params.s3_bucket_arn
    # }

}

# output testing_out {
#     value = module.collectorless_transformer[0].testing_out
# }