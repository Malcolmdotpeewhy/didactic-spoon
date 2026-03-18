import requests,urllib3,base64  
urllib3.disable_warnings()  
dt=open(r'C:\Users\Administrator\Riot Games\League of Legends\lockfile').read().split(':')  
headers={'Authorization': 'Basic ' + base64.b64encode(b'riot:' + dt[3].encode()).decode()}  
res=requests.get(f'https://127.0.0.1:{dt[2]}/lol-game-queues/v1/queues',headers=headers,verify=False)  
open('queues.json','w',encoding='utf-8').write(res.text)  
