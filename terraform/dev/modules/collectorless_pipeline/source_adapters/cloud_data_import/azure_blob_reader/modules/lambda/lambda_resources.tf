# Defining AWS Lambda Terraform resources
locals {
  lambda_function_name = var.lambda_function_params.function_name != "" ? var.lambda_function_params.function_name : "${var.lambda_function_params.function_name_prefix}-puuid-${var.pipeline_uuid}"
}
# Preparing the zipped folder your scripts
resource null_resource packaging {
  # trigers only if your scripts were changed
  triggers = {
    script_sha1 = sha1(join("", [for f in fileset(var.lambda_function_params.scripts_path, "*"): filesha1(join("/",[var.lambda_function_params.scripts_path,f]))]))
    
  }

  # clean the folder
  provisioner local-exec {
    command = "rm -rf /tmp/${var.lambda_function_params.temp_package_folder}"
  }

  # recreate the folder
  provisioner local-exec {
    command = "mkdir /tmp/${var.lambda_function_params.temp_package_folder}"
  }

  # copy your script to the folder
  provisioner local-exec {
    command = "cp -a ${var.lambda_function_params.scripts_path}. /tmp/${var.lambda_function_params.temp_package_folder}/"
  }
}

# this resource we need to turn explicit dependencies (which Terraform couldn't check) to
# implicit dependencies (which Terraform can control and check difference)
# for more information, take a look: https://github.com/hashicorp/terraform-provider-archive/issues/11
data null_data_source packaging_changes {
  inputs = {
    null_id      = null_resource.packaging.id
    package_path = var.lambda_function_params.package_filename
  }
}
# zipping all the folder!
data archive_file package {
  type        = "zip"
  source_dir  = "/tmp/${var.lambda_function_params.temp_package_folder}"
  output_path = data.null_data_source.packaging_changes.outputs["package_path"]
}

data "aws_iam_policy_document" "lambda_service_policy" {
  statement {
    sid    = ""
    effect = "Allow"

    principals {
      identifiers = ["lambda.amazonaws.com"]
      type        = "Service"
    }

    actions = ["sts:AssumeRole"]
  }
}

resource "aws_iam_role" "lambda_iam_role" {
  name               = "${local.lambda_function_name}_role"
  assume_role_policy = data.aws_iam_policy_document.lambda_service_policy.json
}

resource "aws_lambda_function" "azure_blob_transfer_lambda" {
  function_name = var.lambda_function_params.function_name

  filename         = data.archive_file.package.output_path
  source_code_hash = data.archive_file.package.output_base64sha256

  role    = aws_iam_role.lambda_iam_role.arn
  handler = "${var.lambda_function_params.handler}"
  runtime = "python3.10"
  timeout = 300
  layers = var.lambda_function_params.layers

  environment {
    variables = {
      # Pipeline parameters
      PIPELINE_UUID = var.pipeline_uuid
      AWS_REGION_NAME = var.aws_region

      # AWS Secrets Manager parameters
      ASM_SECRET_NAME = var.asm_secret_name

      # Azure Blob Storage parameters
      AZURE_PARENT_FOLDER = var.azure_blob_storage_params.azure_parent_folder_path
      # AZURE_STORAGE_ACCOUNT_NAME = var.azure_blob_storage_params.azure_storage_account_name
      # AZURE_CONTAINER_NAME = var.azure_blob_storage_params.azure_container_name

      # DynamoDB log table parameters
      DYNAMODB_TABLE_NAME = var.state_table_name

      # S3 bucket parameters
      S3_BUCKET_NAME = var.s3_bucket_params.s3_bucket_name
      S3_DEST_FOLDER = var.s3_bucket_params.s3_dest_folder_path

      # SNS topic parameters
      SNS_TOPIC_ARN = var.sns_topic_params.sns_topic_arn
    }
  }
}