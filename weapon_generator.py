import json


wtype = input("Type(attack/defense): ")
damage_dealt = input('dmg dealt: ')
self_heal = input('self heal: ')

data = {'type': wtype}
if damage_dealt:
    data.update({'dmg_dealt': damage_dealt})
if self_heal:
    data.update({'self_heal': self_heal})
print("===Prettified===")
print(json.dumps(data, indent=4))
print("===Ready to Paste===")
print(json.dumps(data))
