locals {
  package_folder_path = "/tmp/${var.function_name}_${var.temp_package_folder}"
  package_filename = "${var.function_name}_${var.package_filename}"
}

# Preparing the zipped folder your scripts
resource null_resource packaging {
  # trigers only if your scripts were changed
  triggers = {
    script_sha1 = sha1(join("", [for f in fileset(var.scripts_folder_path, "*"): filesha1(join("/",[var.scripts_folder_path,f]))]))    
  }

  # clean the folder
  provisioner local-exec {
    command = "rm -rf ${local.package_folder_path}"
  }

  # recreate the folder
  provisioner local-exec {
    command = "mkdir ${local.package_folder_path}"
  }

  # copy your script to the folder
  provisioner local-exec {
    command = "cp -a ${var.scripts_folder_path}. ${local.package_folder_path}/"
  }
}

# this resource we need to turn explicit dependencies (which Terraform couldn't check) to
# implicit dependencies (which Terraform can control and check difference)
# for more information, take a look: https://github.com/hashicorp/terraform-provider-archive/issues/11
data null_data_source packaging_changes {
  inputs = {
    null_id      = null_resource.packaging.id
    package_path = local.package_filename
  }
}
# zipping all the folder!
data archive_file package {
  type        = "zip"
  source_dir  = local.package_folder_path
  output_path = data.null_data_source.packaging_changes.outputs["package_path"]
}

module "lambda_function" {
    source = "../../../resources/lambda/function"

    function_name = var.function_name

    filename         = data.archive_file.package.output_path
    source_code_hash = data.archive_file.package.output_base64sha256

    handler = var.handler
    runtime = var.runtime
    timeout = var.timeout
    layers = var.layers

    environment = var.environment

    # create_logs = true
}

# module "iam_lambda_logging_permission" {
#     source = "../../../resources/iam"

#     lambda_logging_params = {
#       lambda_iam_role_id = module.lambda_function.role_id
#       get_secrets = true
#       asm_secret_arn = var.asm_secret_arn
#     }
# }
