import urllib.request
import json
import time

url = 'https://api.github.com/repos/ShayNeeo/VAIC2026/actions/runs'
req = urllib.request.Request(url, headers={'User-Agent': 'Mozilla/5.0'})
try:
    with urllib.request.urlopen(req) as response:
        data = json.loads(response.read().decode('utf-8'))
        found = False
        for run in data.get('workflow_runs', []):
            if run['head_branch'] == 'fix/offline-ci-run-v3':
                found = True
                print(f'Run ID: {run["id"]}, Name: {run["name"]}, Status: {run["status"]}, Conclusion: {run["conclusion"]}')
                
                # Fetch jobs
                jobs_url = run['jobs_url']
                jobs_req = urllib.request.Request(jobs_url, headers={'User-Agent': 'Mozilla/5.0'})
                with urllib.request.urlopen(jobs_req) as j_resp:
                    j_data = json.loads(j_resp.read().decode('utf-8'))
                    for job in j_data.get('jobs', []):
                        print(f'  Job: {job["name"]}, Status: {job["status"]}, Conclusion: {job["conclusion"]}')
                        for step in job.get('steps', []):
                            print(f'    Step: {step["name"]}, Status: {step["status"]}, Conclusion: {step["conclusion"]}')
                break
        if not found:
            print("No runs found for branch fix/offline-ci-run-v3 yet.")
except Exception as e:
    print('Failed to fetch jobs:', e)
