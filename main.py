import sys, argparse
from Jenkins_create_new.pipeline_create import JenkinsCreatePipeline, GitlabCreateWebHook
import random


def start_script(template_name, gitlab_url, branch, job_name):
    jenkins = JenkinsCreatePipeline()
    gitlab = GitlabCreateWebHook()
    token_secret = "".join(random.sample('zyxwvutsrqponmlkjihgfedcbaABCDEFGHIGKLMNOPQRSTUVWSYZ', 20))
    if jenkins.judge_job_file(template_name):
        config_xml = jenkins.modify_file(gitlab_url, token_secret, branch)
        if jenkins.create_job(job_name, config_xml):
            if gitlab.check_project(gitlab_url):
                project_id = gitlab.check_project(gitlab_url)[1][0]
                gitlab.add_project_webhook(project_id, job_name, token_secret)
            else:
                sys.exit(1)
        else:
            sys.exit(1)
    else:
        sys.exit(1)


def command_line_arguments_parse():
    argument_parser = argparse.ArgumentParser(description='Tencent cloud cos argument parser')
    argument_parser.add_argument(
        '--template_name', type=str, help='Pipeline template name', dest='template_name', default=None
    )
    argument_parser.add_argument(
        '--gitlab_url', type=str, help='Gitlab warehouse address', dest='gitlab_url'
    )
    argument_parser.add_argument(
        '--branch', type=str, help="Gitlab branch", dest='branch', default=None
    )
    argument_parser.add_argument(
        '--job_name', type=str, help='Gitlab job name', dest='job_name',
    )
    return argument_parser.parse_args()


if __name__ == '__main__':
    args = command_line_arguments_parse()
    template_name, branch = None, None
    start_script(args.template_name, args.gitlab_url, args.branch, args.job_name)