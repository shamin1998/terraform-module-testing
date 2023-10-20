locals {
    include_oic_uploader = ((var.type == "api_file_uploader") && (var.name == "cisco_oic_uploader")) ? true : false
}

module oic_uploader {
    count = local.include_oic_uploader ? 1 : 0

    source = "./api_file_uploader/cisco_oic_uploader"

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
#     value = module.oic_uploader[0].testing_out
# }