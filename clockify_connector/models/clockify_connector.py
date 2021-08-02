# coding: utf-8
# Part of CAPTIVEA. Odoo 12 EE.


from odoo.models import *
from datetime import datetime
import requests
from odoo import _, api, exceptions, fields, models, modules
from odoo.addons.base.models.res_users import is_selection_groups
from odoo.addons.mail.models.res_users import *
import time

class BaseModelExtend(AbstractModel):



    _inherit = 'base'

    @api.model
    def get_timesheets(self,email="ALL",start_time=None,end_time=None):
        api_key="OTllNTU1NDYtMDU0Zi00ZDUwLTg5MTUtOWZkZTI5NTI1OWFi"
        api_key = api_key
        header =  {'X-Api-Key': api_key }
        base_url = "https://api.clockify.me/api/workspaces/"
        response = requests.get(base_url,headers=header)
        # print(response.content)
        json_data = response.json()
        workspaces=[]
        work_space_users=[]
        projects={}
        for workspace in json_data:
            workspaces.append(workspace.get('id'))
        for ws in workspaces:
            url = "https://api.clockify.me/api/v1/workspaces/"+ws+'/users/'
            response = requests.get(url,headers=header)
            for user in response.json():
                work_space_users.append([ws,user.get('id'),user.get('email'),user.get('name')])

            url = "https://api.clockify.me/api/v1/workspaces/"+ws+'/projects/'
            response = requests.get(url,headers=header)

            for project in response.json():
                projects[project.get('id')]=[project.get('name'),project.get('clientName')]

        if email!="ALL":work_space_users=list(filter(lambda x:x[2]==email,work_space_users))
        dt_pattern="%Y-%m-%dT%H:%M:%SZ"
        timesheets={wsu[2]:[]for wsu in work_space_users}
        for ws in work_space_users:
            workspace_id=ws[0]
            user_id=ws[1]
            url = "https://api.clockify.me/api/v1/workspaces/"+workspace_id+'/user/'+user_id+'/time-entries'
            response = requests.get(url,headers=header)
            times_logged=response.json()
            for time_logged in times_logged:
                description=time_logged.get('description')
                pid=time_logged.get('projectId')
                start=time_logged.get('timeInterval').get('start')
                end=time_logged.get('timeInterval').get('end')
                if not end:continue
                if not start:continue
                if start_time and start_time<start:continue
                if end_time and end_time>end:continue
                start=datetime.strptime(start,dt_pattern)
                end=datetime.strptime(end,dt_pattern)
                billable=time_logged.get('billable')
                if billable:billable="Billable"
                else:billable="Not Billable"
                client="Untitled"
                project="Untitled"
                if pid in projects:
                    client=projects[pid][1]
                    project=projects[pid][0]

                timesheets[ws[2]].append((start,end,client,project,description,float(round((end-start).seconds/60/60,2)),billable))
            time.sleep(.3)
        for ts in timesheets:
            timesheets[ts]=sorted(timesheets[ts],key=lambda x:x[0],reverse=True)
        return (timesheets)
