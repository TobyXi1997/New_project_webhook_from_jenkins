import jenkins
import gitlab
import re
import sys
import logging
import random
from pathlib import Path
from Jenkins_create_new.settings.password import jenkins_password, gitlab_password

# 首先导入python-jenkins 模块 和python-gitlab 模块

print(jenkins.__file__, gitlab.__file__)

logging.basicConfig(format='%(asctime)s.%(msecs)03d [%(levelname)s] [%(filename)s:%(lineno)d] %(message)s',
                    datefmt='## %Y-%m-%d %H:%M:%S')
logging.getLogger().setLevel(logging.INFO)


class JenkinsCreatePipeline(object):

    def __init__(self):
        """
        @param: url Jenkins的地址
        @param: username  Jenkins的用户名
        @param: password Jenkins用户密码
        @param： 用户必须拥有Jenkins job的创建权限否则将无法创建JOb pipeline流水线
        """
        try:
            self.server = jenkins.Jenkins(jenkins_password["url"], jenkins_password["username"],
                                          jenkins_password["password"])
            jenkins_user = self.server.get_whoami()
            if jenkins_user['absoluteUrl']:
                version = self.server.get_version()
                logging.info("Jenkins login successful" + "Jenkins version:{}".format(version))
            else:
                logging.error("Jenkins login failed")
                sys.exit(1)
        except Exception as err:
            logging.error(err)

    def judge_job_file(self, template_name=None):
        """
        @param: template_name 已经配置好 Pipeline 流水线的模板的名字
        @param: 将模板导出成config.xml格式，并保存在本地路径，会判断本地是否存在config.xml文件,有则直接返回True，无则根据模板创建，没有模板则返回Flase。
        @param: 如已有文件需要修改模板，请删除config.xml文件
        @param: 必须配置的属性 ：不允许并发构建、触发远程构建(例如，使用脚本)、流水线-定义、SCM-Git、Repository URL、 Credentials、
        Branches to build 、 指定分支（为空时代表any、 脚本路径 ， √ 轻量级检出）
        """
        try:
            my_file = Path("config_file/config.xml")
            if my_file.is_file():
                logging.info("config.xml file already exists")
                return True
            else:
                logging.info("config.xml does not exist,Ready to start creating config.xml")
                if self.server.job_exists(template_name):
                    config_xml = self.server.get_job_config(template_name)
                    file = open('./config_file/config.xml', 'w', encoding='utf-8')
                    file.write(config_xml)
                    file.close()
                    return True
                else:
                    logging.error("Pipeline template does not exist")
                    return False
        except Exception as err:
            logging.error(err)

    @staticmethod
    def modify_file(gitlab_url, token_secret, branch=None):
        """
        @param:修改config.xml配置文件，主要修改三点， 第一点gitlab地址 第二点分支名称，测试和正式 第三点触发远程构建(例如，使用脚本)Token
        @param: 正式分支加入审批，审批通过后触发Spinnaker，测试分支Jenkins直接调用Spinnaker CD。
        @param:正式：master 测试： dev
        """
        try:
            file = open("./config_file/config.xml", "r", encoding='utf-8')
            config_xml = file.read()
            file.close()
            gitlab_front = config_xml.find("<url>") + 5
            gitlab_back = config_xml.find(r"</url>")
            replace_url = config_xml[gitlab_front:gitlab_back]
            auth_token = re.findall(r'<authToken>(.*)</authToken>', config_xml)
            config_xml = config_xml.replace(auth_token[0], token_secret)
            config_xml = config_xml.replace(replace_url, gitlab_url)
            logging.info("The replacement verification code is" + token_secret)
            logging.info("The replacement connection is" + replace_url)
            branch_name = re.findall(r'<name>(.*)</name>', config_xml)
            if not branch:
                logging.info("No replacement branch the current branch is {}!".format(branch_name))
                return config_xml
            else:
                logging.info("The branch has been replaced, the current branch is {} !".format(branch))
                config_xml = config_xml.replace(branch_name[0], "*/" + branch)
                return config_xml
        except Exception as err:
            logging.error(err)

    def create_job(self, job_name, config_xml):
        """
        @param: 创建Pipeline任务。
        @param: job_name创建的pipeline流水线名称。
        @param: 导入的pipeline流水线配置文件。
        @param:
        """
        try:
            if not self.server.job_exists(job_name):
                self.server.create_job(job_name, config_xml)
                if self.server.job_exists(job_name):
                    logging.info("Create success Pipeline")
                    return True
                else:
                    logging.error("Create failed Pipeline,Please Call OPS")
                    return False
            else:
                logging.info("This pipeline already has the same name, Please reapply ITSM")
                return True
        except Exception as err:
            logging.error(err)


class GitlabCreateWebHook():
    def __init__(self):
        url = gitlab_password['url']
        private_token = gitlab_password['private_token']
        self.gl = gitlab.Gitlab(url, private_token)

    def check_project(self, gitlab_url):
        """
        @param: gitlab_url用户自己输入的clone地址，后面会自动切片调整,clone连接必须是http:协议的
        @param: True返回 项目ID和 （项目和项目组）
        @param: False 直接终止
        """
        try:
            gitlab_url = [x for x in gitlab_url.split("/") if x != '']
            project_name = re.findall(r'(.*).git', gitlab_url[-1])
            projects = self.gl.projects.list(search=project_name, all=True)
            if projects:
                project = []
                for i in projects:
                    project.append(i.id)
                    project.append(i.path_with_namespace)
                logging.info("The corresponding project has been found")
                return True, project
            else:
                logging.error("Gitlab project not found")
                return False
        except Exception as err:
            logging.error(err)

    def add_project_webhook(self, project_id, job_name, token_secret):
        """
        @param: project_id 项目ID
        @param: job_namePipeline 名称
        @param: token_secret Jenkins生成的秘钥
        """
        try:
            project = self.gl.projects.get(project_id)
            hook = project.hooks.create(
                {'url': '{}job/{}/build?token={}'.format(jenkins_password["url"], job_name, token_secret),
                 'push_events': False, 'tag_push_events': True, 'enable_ssl_verification': True})
            data = (str(hook)).lstrip("<class 'gitlab.v4.objects.hooks.ProjectHook'> =>")
            logging.info("Webhook created successfully,data:{}".format(data))
        except Exception as err:
            logging.error(err)



# logging.info("The replacement verification code is", token_secret)
# logging.info("The replacement connection is", replace_url)
# branch_name = re.findall(r'<name>(.*)</name>', config_xml)