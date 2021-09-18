import sys, argparse
import random
from Jenkins_create_new.pipeline_create import JenkinsCreatePipeline, GitlabCreateWebHook





if __name__ == "__main__":
    job_name = "test-pipline-wx1"
    template_name = "jenkins-test-devops"
    gitlab_url = "http://gitlab-bigdata.huan.tv/blueking-devops/jenkins-test-devops.git"
    branch = "master"
    token_secret = "".join(random.sample('zyxwvutsrqponmlkjihgfedcbaABCDEFGHIGKLMNOPQRSTUVWSYZ', 20))

    jenkins = JenkinsCreatePipeline()
    gitlab = GitlabCreateWebHook()
    # jenkins.judge_job_file(template_name)
    # jenkins.modify_file(gitlab_url, branch)
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