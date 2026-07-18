import urllib.request
import json

run_id = 29618877500
url = f'https://api.github.com/repos/ShayNeeo/VAIC2026/actions/runs/{run_id}/jobs'
req = urllib.request.Request(url, headers={'User-Agent': 'Mozilla/5.0'})
try:
    with urllib.request.urlopen(req) as response:
        data = json.loads(response.read().decode('utf-8'))
        job = data['jobs'][0]
        job_id = job['id']
        print(f'Job ID: {job_id}, Name: {job["name"]}, Status: {job["status"]}, Conclusion: {job["conclusion"]}')
        
        # Check annotations
        check_run_url = job.get('check_run_url')
        if check_run_url:
            c_req = urllib.request.Request(check_run_url + "/annotations", headers={'User-Agent': 'Mozilla/5.0'})
            with urllib.request.urlopen(c_req) as c_resp:
                annotations = json.loads(c_resp.read().decode('utf-8'))
                print(f"Annotations ({len(annotations)}):")
                for ann in annotations:
                    print(f"  [{ann.get('annotation_level')}] File: {ann.get('path')}, Line: {ann.get('start_line')}")
                    print(f"  Message: {ann.get('message')}")
                    print(f"  Raw Details: {ann.get('raw_details')}")
except Exception as e:
    print('Failed:', e)
