locals {
    include_azure_blob_source_adapter = ((var.type == "cloud_data_import") && (var.name == "azure_blob_reader")) ? true : false
    
}

module azure_blob_source_adapter {
    count = local.include_azure_blob_source_adapter ? 1 : 0

    source = "./cloud_data_import/azure_blob_reader"
    
    pipeline_uuid = var.pipeline_uuid

    trigger = var.trigger

    params = var.params

    environment = var.environment

    # # Pipeline variables
    # pipeline_uuid = var.pipeline_uuid
    # aws_region = var.aws_region

    # AWS Secret Manager variables
    # asm_secret_name = var.source_params.asm_secret_name
    # asm_secret_arn = var.asm_secret_arn

    # State Table variables
    # state_table_name = var.state_table_name
    # state_table_arn = var.state_table_arn

    # # Azure Blob Storage variables
    # azure_blob_storage_params = {
    #     azure_storage_account_name = try(varsource_params.azure_storage_account_name, "")
    #     azure_container_name = try(var.source_params.azure_container_name,"")
    #     # azure_container_url = try(var.source_params.azure_container_url,"")
    #     azure_parent_folder_path = try(var.source_params.azure_parent_folder_path,"")
    # }
    
    # # Lambda Function variables
    # lambda_function_params = {
    #     handler = var.source_params.lambda_function_handler_name
    #     scripts_path =  var.source_params.lambda_function_scripts_path
    # }

    # # # Lambda Layer variables
    # # lambda_layers_params = {
    # #     layer_requirements_path = var.source_params.layer_requirements_path
    # # }
}